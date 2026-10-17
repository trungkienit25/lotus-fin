import React, { useMemo } from "react";
import { marked } from "marked";
import katex from "katex";
import DOMPurify from "dompurify";

export interface CopilotMessageBodyProps {
  content: string;
  className?: string;
}

/**
 * Configure marked options once
 */
marked.setOptions({
  breaks: true,
  gfm: true,
});

/**
 * Safely renders rich Markdown and LaTeX math formulas.
 * Strategy:
 * 1. Pre-extract LaTeX blocks ($$...$$ and $...$) into HTML rendered directly by KaTeX.
 * 2. Replace with safe unique placeholders so Markdown parser doesn't break LaTeX syntax (e.g. \frac, \_, *).
 * 3. Convert Markdown to HTML via marked.
 * 4. Substitute placeholders back with KaTeX rendered math HTML.
 * 5. Sanitize complete HTML via DOMPurify, allowing KaTeX MathML and SVG elements.
 */
export const CopilotMessageBody: React.FC<CopilotMessageBodyProps> = ({
  content,
  className = "",
}) => {
  const sanitizedHtml = useMemo(() => {
    if (!content) return "";
    const mathStore: string[] = [];

    // 1. Extract Display Math: $$ ... $$ or \[ ... \]
    let prepared = content.replace(/(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\])/g, (match) => {
      const isSquareBracket = match.startsWith("\\[");
      const expr = isSquareBracket ? match.slice(2, -2).trim() : match.slice(2, -2).trim();
      try {
        const rendered = katex.renderToString(expr, {
          displayMode: true,
          throwOnError: false,
          output: "htmlAndMathml",
        });
        const placeholder = `<!--MATH_BLOCK_${mathStore.length}-->`;
        mathStore.push(`<div class="my-3 overflow-x-auto py-1 text-center">${rendered}</div>`);
        return `\n\n${placeholder}\n\n`;
      } catch {
        return match;
      }
    });

    // 2. Extract Inline Math: $ ... $ or \( ... \)
    // Note: Do not match literal money like $100 without trailing closing $
    prepared = prepared.replace(/(\\\([\s\S]*?\\\)|\$(?!\s)([^$\n]+?)(?<!\s)\$)/g, (match, _p1, innerExpr) => {
      const expr = match.startsWith("\\(") ? match.slice(2, -2).trim() : (innerExpr || match.slice(1, -1)).trim();
      try {
        const rendered = katex.renderToString(expr, {
          displayMode: false,
          throwOnError: false,
          output: "htmlAndMathml",
        });
        const placeholder = `<!--MATH_INLINE_${mathStore.length}-->`;
        mathStore.push(`<span class="inline-block px-1 align-middle">${rendered}</span>`);
        return placeholder;
      } catch {
        return match;
      }
    });

    // 3. Parse Markdown with marked
    let rawHtml = marked.parse(prepared) as string;

    // 4. Restore KaTeX HTML from placeholders
    rawHtml = rawHtml.replace(/<!--MATH_(?:BLOCK|INLINE)_(\d+)-->/g, (_m, idx) => {
      return mathStore[Number(idx)] || "";
    });

    // 5. Sanitize HTML via DOMPurify allowing KaTeX math tags and attributes
    return DOMPurify.sanitize(rawHtml, {
      USE_PROFILES: { html: true, mathMl: true, svg: true },
      ADD_TAGS: [
        "math",
        "semantics",
        "mrow",
        "mfrac",
        "mn",
        "mo",
        "mi",
        "ms",
        "mspace",
        "mtext",
        "annotation",
        "annotation-xml",
        "svg",
        "path",
        "line",
      ],
      ADD_ATTR: [
        "display",
        "xmlns",
        "mathvariant",
        "encoding",
        "aria-hidden",
        "viewBox",
        "d",
      ],
    });
  }, [content]);

  return (
    <div
      className={`prose prose-slate max-w-none text-slate-800 text-xs sm:text-sm leading-relaxed 
        [&_p]:mb-2.5 [&_p:last-child]:mb-0 [&_ul]:list-disc [&_ul]:ml-5 [&_ul]:my-2 
        [&_ol]:list-decimal [&_ol]:ml-5 [&_ol]:my-2 [&_li]:mb-1 
        [&_h1]:text-lg [&_h1]:font-bold [&_h1]:mt-3 [&_h1]:mb-1.5 
        [&_h2]:text-base [&_h2]:font-bold [&_h2]:mt-2.5 [&_h2]:mb-1 
        [&_h3]:text-sm [&_h3]:font-bold [&_h3]:mt-2 [&_h3]:mb-1 
        [&_table]:w-full [&_table]:border-collapse [&_table]:my-2.5 
        [&_th]:bg-slate-50 [&_th]:border [&_th]:border-slate-200 [&_th]:p-2 [&_th]:text-left 
        [&_td]:border [&_td]:border-slate-200 [&_td]:p-2 
        [&_pre]:bg-slate-900 [&_pre]:text-slate-100 [&_pre]:p-3 [&_pre]:rounded-xl [&_pre]:overflow-x-auto 
        [&_code]:font-mono [&_code]:text-pink-600 [&_code]:bg-slate-100 [&_code]:px-1.5 [&_code]:py-0.5 [&_code]:rounded 
        ${className}`}
      dangerouslySetInnerHTML={{ __html: sanitizedHtml }}
    />
  );
};

export default CopilotMessageBody;

import React, { useMemo } from "react";
import katex from "katex";

export interface CopilotMessageBodyProps {
  content: string;
  className?: string;
}

/**
 * Component to safely render a block or inline LaTeX snippet via KaTeX
 */
const LatexSpan: React.FC<{ math: string; displayMode?: boolean }> = ({ math, displayMode = false }) => {
  const html = useMemo(() => {
    try {
      return katex.renderToString(math, {
        displayMode,
        throwOnError: false,
        output: "htmlAndMathml",
      });
    } catch {
      return math;
    }
  }, [math, displayMode]);

  return (
    <span
      className={displayMode ? "block my-2.5 overflow-x-auto text-center" : "inline-block px-1"}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
};

/**
 * Renders inline text, handling inline LaTeX ($...$ or \(...\)) and markdown bold/code
 */
const FormattedInlineText: React.FC<{ text: string }> = ({ text }) => {
  // Regex splitting by:
  // 1. Display math: $$...$$ or \[...\]
  // 2. Inline math: $...$ or \(...\)
  // 3. Bold: **...**
  // 4. Inline code: `...`
  const tokens = useMemo(() => {
    const parts: Array<{ type: "text" | "latex-display" | "latex-inline" | "bold" | "code"; value: string }> = [];
    const regex = /(\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]|\$(?!\$)[\s\S]*?\$|\\\([\s\S]*?\\\)|\*\*[\s\S]*?\*\*|`[^`]+`)/g;

    let lastIndex = 0;
    let match: RegExpExecArray | null;

    while ((match = regex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: "text", value: text.substring(lastIndex, match.index) });
      }

      const matchStr = match[0];
      if (matchStr.startsWith("$$") && matchStr.endsWith("$$")) {
        parts.push({ type: "latex-display", value: matchStr.slice(2, -2).trim() });
      } else if (matchStr.startsWith("\\[") && matchStr.endsWith("\\]")) {
        parts.push({ type: "latex-display", value: matchStr.slice(2, -2).trim() });
      } else if (matchStr.startsWith("\\(") && matchStr.endsWith("\\)")) {
        parts.push({ type: "latex-inline", value: matchStr.slice(2, -2).trim() });
      } else if (matchStr.startsWith("$") && matchStr.endsWith("$")) {
        parts.push({ type: "latex-inline", value: matchStr.slice(1, -1).trim() });
      } else if (matchStr.startsWith("**") && matchStr.endsWith("**")) {
        parts.push({ type: "bold", value: matchStr.slice(2, -2) });
      } else if (matchStr.startsWith("`") && matchStr.endsWith("`")) {
        parts.push({ type: "code", value: matchStr.slice(1, -1) });
      }
      lastIndex = regex.lastIndex;
    }

    if (lastIndex < text.length) {
      parts.push({ type: "text", value: text.substring(lastIndex) });
    }

    return parts;
  }, [text]);

  return (
    <>
      {tokens.map((token, idx) => {
        if (token.type === "latex-display") {
          return <LatexSpan key={idx} math={token.value} displayMode={true} />;
        }
        if (token.type === "latex-inline") {
          return <LatexSpan key={idx} math={token.value} displayMode={false} />;
        }
        if (token.type === "bold") {
          return (
            <strong key={idx} className="font-semibold text-slate-900">
              <FormattedInlineText text={token.value} />
            </strong>
          );
        }
        if (token.type === "code") {
          return (
            <code key={idx} className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-pink-600">
              {token.value}
            </code>
          );
        }
        return <span key={idx}>{token.value}</span>;
      })}
    </>
  );
};

/**
 * Safely renders rich message content, KaTeX formulas, lists, and headings.
 */
export const CopilotMessageBody: React.FC<CopilotMessageBodyProps> = ({ content, className = "" }) => {
  if (!content) return null;

  const paragraphs = content.split(/\n\n+/);

  return (
    <div className={`space-y-2.5 break-words text-slate-800 ${className}`}>
      {paragraphs.map((para, pIdx) => {
        const trimmed = para.trim();
        if (!trimmed) return null;

        // Display LaTeX block on its own line: $$ ... $$ or \[ ... \]
        if (
          (trimmed.startsWith("$$") && trimmed.endsWith("$$")) ||
          (trimmed.startsWith("\\[") && trimmed.endsWith("\\]"))
        ) {
          const rawFormula = trimmed.startsWith("$$") ? trimmed.slice(2, -2).trim() : trimmed.slice(2, -2).trim();
          return <LatexSpan key={pIdx} math={rawFormula} displayMode={true} />;
        }

        // Render bullet list lines
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const lines = trimmed.split("\n");
          return (
            <ul key={pIdx} className="list-disc list-inside space-y-1 my-1 pl-1">
              {lines.map((line, lIdx) => {
                const itemContent = line.replace(/^[-*]\s*/, "");
                return (
                  <li key={lIdx} className="text-slate-700 leading-relaxed">
                    <FormattedInlineText text={itemContent} />
                  </li>
                );
              })}
            </ul>
          );
        }

        // Render heading
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={pIdx} className="text-sm font-bold text-slate-900 mt-2 mb-1">
              <FormattedInlineText text={trimmed.replace(/^###\s*/, "")} />
            </h3>
          );
        }
        if (trimmed.startsWith("## ")) {
          return (
            <h2 key={pIdx} className="text-base font-bold text-slate-900 mt-2.5 mb-1.5">
              <FormattedInlineText text={trimmed.replace(/^##\s*/, "")} />
            </h2>
          );
        }

        return (
          <p key={pIdx} className="text-slate-700 leading-relaxed">
            <FormattedInlineText text={para} />
          </p>
        );
      })}
    </div>
  );
};

export default CopilotMessageBody;

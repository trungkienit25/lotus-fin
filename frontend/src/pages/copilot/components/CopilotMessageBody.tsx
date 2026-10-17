import React from "react";
import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";

export interface CopilotMessageBodyProps {
  content: string;
  className?: string;
}

export const CopilotMessageBody: React.FC<CopilotMessageBodyProps> = ({
  content,
  className = "",
}) => {
  if (!content) return null;

  return (
    <div className={`break-words text-slate-800 leading-relaxed text-sm ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm, remarkMath]}
        rehypePlugins={[[rehypeKatex, { output: "htmlAndMathml", throwOnError: false }]]}
        components={{
          // Custom render Headings
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-slate-900 mt-4 mb-2 pb-1 border-b border-slate-200">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-slate-900 mt-3 mb-1.5">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-semibold text-slate-900 mt-2 mb-1">{children}</h3>
          ),

          // Custom render Paragraphs
          p: ({ children }) => <p className="mb-2.5 last:mb-0 leading-relaxed">{children}</p>,

          // Custom render Lists
          ul: ({ children }) => (
            <ul className="list-disc list-outside ml-5 space-y-1 my-2 text-slate-700">
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol className="list-decimal list-outside ml-5 space-y-1 my-2 text-slate-700">
              {children}
            </ol>
          ),
          li: ({ children }) => <li className="leading-relaxed">{children}</li>,

          // Custom render Blockquote
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-slate-300 pl-3 italic text-slate-600 my-2">
              {children}
            </blockquote>
          ),

          // Custom render Table (GFM)
          table: ({ children }) => (
            <div className="overflow-x-auto my-3 rounded-lg border border-slate-200">
              <table className="min-w-full divide-y divide-slate-200 text-left text-xs border-collapse">
                {children}
              </table>
            </div>
          ),
          th: ({ children }) => (
            <th className="bg-slate-50 px-3 py-2 font-semibold text-slate-700 border-b border-slate-200">
              {children}
            </th>
          ),
          td: ({ children }) => (
            <td className="px-3 py-2 border-b border-slate-100">{children}</td>
          ),

          // Custom render Inline Code vs Code Block
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || "");
            const isInline = !match && !String(children).includes("\n");

            if (isInline) {
              return (
                <code
                  className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-[12px] text-pink-600 font-medium"
                  {...props}
                >
                  {children}
                </code>
              );
            }

            return (
              <pre className="rounded-xl overflow-x-auto my-3 text-xs bg-slate-900 text-slate-100 p-3.5 font-mono leading-relaxed border border-slate-800">
                <code className={className} {...props}>
                  {String(children).replace(/\n$/, "")}
                </code>
              </pre>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
};

export default CopilotMessageBody;

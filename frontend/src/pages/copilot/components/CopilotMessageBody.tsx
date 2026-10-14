import React from "react";

export interface CopilotMessageBodyProps {
  content: string;
  className?: string;
}

/**
 * Safely renders untrusted text using React text nodes.
 * Avoids dangerouslySetInnerHTML, script/img injection, and raw markdown parsing.
 * Preserves paragraphs and basic list lines safely.
 */
export const CopilotMessageBody: React.FC<CopilotMessageBodyProps> = ({ content, className = "" }) => {
  if (!content) return null;

  const paragraphs = content.split("\n\n");

  return (
    <div className={`space-y-2.5 whitespace-pre-wrap break-words text-gray-800 ${className}`}>
      {paragraphs.map((para, pIdx) => {
        const trimmed = para.trim();
        if (!trimmed) return null;

        // Render bullet list safely if all lines or first line starts with bullet
        if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
          const lines = trimmed.split("\n");
          return (
            <ul key={pIdx} className="list-disc list-inside space-y-1 my-1 pl-1">
              {lines.map((line, lIdx) => (
                <li key={lIdx} className="text-gray-700">
                  {line.replace(/^[-*]\s*/, "")}
                </li>
              ))}
            </ul>
          );
        }

        // Render simple heading safely
        if (trimmed.startsWith("### ")) {
          return (
            <h3 key={pIdx} className="text-sm font-bold text-gray-900 mt-2 mb-1">
              {trimmed.replace(/^###\s*/, "")}
            </h3>
          );
        }

        return (
          <p key={pIdx} className="text-gray-700">
            {para}
          </p>
        );
      })}
    </div>
  );
};

export default CopilotMessageBody;

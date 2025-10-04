import React from 'react';

export default function MarkdownRenderer({ content }) {
  if (!content) return null;

  // Simple markdown parser
  const parseMarkdown = (text) => {
    // Split by lines
    const lines = text.split('\n');
    const elements = [];
    let inCodeBlock = false;
    let codeBlockLines = [];
    let codeBlockLang = '';

    lines.forEach((line, index) => {
      // Code blocks
      if (line.trim().startsWith('```')) {
        if (!inCodeBlock) {
          inCodeBlock = true;
          codeBlockLang = line.trim().substring(3);
          codeBlockLines = [];
        } else {
          inCodeBlock = false;
          elements.push(
            <pre key={`code-${index}`} className="bg-gray-800 text-gray-100 p-4 rounded-lg overflow-x-auto my-3">
              <code className="text-sm font-mono">{codeBlockLines.join('\n')}</code>
            </pre>
          );
          codeBlockLines = [];
        }
        return;
      }

      if (inCodeBlock) {
        codeBlockLines.push(line);
        return;
      }

      // Headers
      if (line.startsWith('### ')) {
        elements.push(<h3 key={index} className="text-lg font-semibold mt-4 mb-2 text-gray-900">{line.substring(4)}</h3>);
      } else if (line.startsWith('## ')) {
        elements.push(<h2 key={index} className="text-xl font-bold mt-4 mb-2 text-gray-900">{line.substring(3)}</h2>);
      } else if (line.startsWith('# ')) {
        elements.push(<h1 key={index} className="text-2xl font-bold mt-4 mb-3 text-gray-900">{line.substring(2)}</h1>);
      }
      // Lists
      else if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
        const content = line.trim().substring(2);
        elements.push(
          <li key={index} className="ml-4 mb-1 text-gray-700">
            {parseInlineMarkdown(content)}
          </li>
        );
      }
      else if (/^\d+\.\s/.test(line.trim())) {
        const content = line.trim().replace(/^\d+\.\s/, '');
        elements.push(
          <li key={index} className="ml-4 mb-1 text-gray-700 list-decimal">
            {parseInlineMarkdown(content)}
          </li>
        );
      }
      // Paragraphs
      else if (line.trim()) {
        elements.push(
          <p key={index} className="mb-2 text-gray-700 leading-relaxed">
            {parseInlineMarkdown(line)}
          </p>
        );
      }
      // Empty lines
      else {
        elements.push(<div key={index} className="h-2"></div>);
      }
    });

    return elements;
  };

  // Parse inline markdown (bold, italic, code, links)
  const parseInlineMarkdown = (text) => {
    const parts = [];
    let remaining = text;
    let key = 0;

    while (remaining.length > 0) {
      // Inline code
      const codeMatch = remaining.match(/`([^`]+)`/);
      if (codeMatch && codeMatch.index === 0) {
        parts.push(
          <code key={key++} className="bg-gray-200 text-purple-700 px-1.5 py-0.5 rounded text-sm font-mono">
            {codeMatch[1]}
          </code>
        );
        remaining = remaining.substring(codeMatch[0].length);
        continue;
      }

      // Bold
      const boldMatch = remaining.match(/\*\*([^*]+)\*\*/);
      if (boldMatch && boldMatch.index === 0) {
        parts.push(<strong key={key++} className="font-bold text-gray-900">{boldMatch[1]}</strong>);
        remaining = remaining.substring(boldMatch[0].length);
        continue;
      }

      // Italic
      const italicMatch = remaining.match(/\*([^*]+)\*/);
      if (italicMatch && italicMatch.index === 0) {
        parts.push(<em key={key++} className="italic">{italicMatch[1]}</em>);
        remaining = remaining.substring(italicMatch[0].length);
        continue;
      }

      // Links
      const linkMatch = remaining.match(/\[([^\]]+)\]\(([^)]+)\)/);
      if (linkMatch && linkMatch.index === 0) {
        parts.push(
          <a key={key++} href={linkMatch[2]} className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">
            {linkMatch[1]}
          </a>
        );
        remaining = remaining.substring(linkMatch[0].length);
        continue;
      }

      // Regular text
      const nextSpecial = remaining.search(/[`*\[]/);
      if (nextSpecial === -1) {
        parts.push(<span key={key++}>{remaining}</span>);
        break;
      } else {
        parts.push(<span key={key++}>{remaining.substring(0, nextSpecial)}</span>);
        remaining = remaining.substring(nextSpecial);
      }
    }

    return parts;
  };

  return <div className="markdown-content">{parseMarkdown(content)}</div>;
}


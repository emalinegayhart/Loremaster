import { useState, ReactNode } from 'react';
import ReactMarkdown from 'react-markdown';

interface MessageSection {
  title: string;
  content: string;
}

interface MessageProps {
  message: {
    role: 'user' | 'assistant';
    content: string;
    sections?: MessageSection[];
    loading?: boolean;
    streaming?: boolean;
  };
}

export default function Message({ message }: MessageProps): ReactNode {
  const [openSection, setOpenSection] = useState<number | null>(null);

  if (message.role === 'user') {
    return (
      <div className="message message-user">
        <div className="message-avatar">🧙</div>
        <div className="message-bubble">{message.content}</div>
      </div>
    );
  }

  if (message.loading) {
    return (
      <div className="message message-assistant">
        <div className="message-avatar">⚔️</div>
        <div className="message-bubble loading">
          <span className="dot" />
          <span className="dot" />
          <span className="dot" />
        </div>
      </div>
    );
  }

  const sections = message.sections || [];

  return (
    <div className="message message-assistant">
      <div className="message-avatar">⚔️</div>
      <div className="message-bubble">
        <ReactMarkdown
          components={{
            a: ({ href, children }: { href?: string; children: ReactNode }) => (
              <a href={href} target="_blank" rel="noreferrer">
                {children}
              </a>
            ),
          }}
        >
          {message.content}
        </ReactMarkdown>
        {message.streaming && <span className="cursor">▋</span>}

        {sections.length > 0 && (
          <div className="chips">
            {sections.map((section, i): ReactNode => (
              <button
                key={i}
                className={`chip ${openSection === i ? 'chip-active' : ''}`}
                onClick={(): void => setOpenSection(openSection === i ? null : i)}
              >
                {section.title}
              </button>
            ))}
          </div>
        )}

        {openSection !== null && sections[openSection] && (
          <div className="section-content">
            <h3 className="section-title">{sections[openSection].title}</h3>
            <p>{sections[openSection].content}</p>
          </div>
        )}
      </div>
    </div>
  );
}

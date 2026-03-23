import { useState } from "react";
import ReactMarkdown from "react-markdown";

export default function Message({ message }) {
  const isUser = message.role === "user";
  const [openSection, setOpenSection] = useState(null);

  if (isUser) {
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
          <span className="dot" /><span className="dot" /><span className="dot" />
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
            a: ({ href, children }) => (
              <a href={href} target="_blank" rel="noreferrer">{children}</a>
            ),
          }}
        >
          {message.content}
        </ReactMarkdown>
        {message.streaming && <span className="cursor">▋</span>}

        {sections.length > 0 && (
          <div className="chips">
            {sections.map((section, i) => (
              <button
                key={i}
                className={`chip ${openSection === i ? "chip-active" : ""}`}
                onClick={() => setOpenSection(openSection === i ? null : i)}
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

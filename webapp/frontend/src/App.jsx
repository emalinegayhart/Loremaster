import { useState, useRef, useEffect } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function cleanMarkdown(text) {
  return text.replace(/\(\[[^\]]+\]\([^)]*$/, "").trim();
}

const WOW_SUGGESTIONS = [
  "What is Thunderfury, Blessed Blade of the Windseeker?",
  "Worgens... why?",
  "Is Outland in Azeroth?",
  "Who is Archmage Medivh?",
  "What is twinking?",
];

function Message({ message }) {
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

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text) {
    const userMessage = text || input.trim();
    if (!userMessage || loading) return;

    setInput("");
    setLoading(true);

    const newMessages = [...messages, { role: "user", content: userMessage }];
    setMessages(newMessages);

    setMessages((prev) => [...prev, { role: "assistant", loading: true }]);

    try {
      const res = await fetch(`https://loremaster-production.up.railway.app/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: newMessages }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let sections = [];

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "",
          sections: [],
          streaming: true,
        };
        return updated;
      });

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });

        if (chunk.includes("[SECTIONS_JSON]")) {
          const parts = chunk.split("[SECTIONS_JSON]");
          fullText += parts[0];
          try { sections = JSON.parse(parts[1]); } catch (_) {}
        } else {
          fullText += chunk;
          setMessages((prev) => {
            const updated = [...prev];
            updated[updated.length - 1] = {
              role: "assistant",
              content: fullText,
              sections: [],
              streaming: true,
            };
            return updated;
          });
        }
      }

      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: cleanMarkdown(fullText),
          sections,
          streaming: false,
        };
        return updated;
      });

    } catch (err) {
      setMessages((prev) => {
        const updated = [...prev];
        updated[updated.length - 1] = {
          role: "assistant",
          content: "Something went wrong. Is the backend running?",
          sections: [],
          streaming: false,
        };
        return updated;
      });
    } finally {
      setLoading(false);
    }
  }

  function handleKeyDown(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  const isEmpty = messages.length === 0;

  return (
    <div className="app">
      <header className="header" onClick={() => { setMessages([]); setInput(""); }} style={{ cursor: "pointer" }}>
        <h1>Loremaster</h1>
        <p>Uncover the secrets of Azeroth</p>
      </header>

      <main className="chat-container">
        {isEmpty ? (
          <div className="empty-state">
            <div className="empty-icon">⚔️</div>
            <h2>What would you like to know?</h2>
            <div className="suggestions">
              {WOW_SUGGESTIONS.map((s) => (
                <button key={s} className="suggestion" onClick={() => sendMessage(s)}>
                  {s}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="messages">
            {messages.map((m, i) => (
              <Message key={i} message={m} />
            ))}
            <div ref={bottomRef} />
          </div>
        )}
      </main>

      <footer className="input-area">
        <textarea
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask about WoW lore, characters, items, quests..."
          rows={1}
          disabled={loading}
        />
        <button
          className="send-btn"
          onClick={() => sendMessage()}
          disabled={loading || !input.trim()}
        >
          {loading ? "..." : "Send"}
        </button>
      </footer>
    </div>
  );
}

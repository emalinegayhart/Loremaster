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

const RESOURCES = [
  { name: "Raidbots",      url: "https://www.raidbots.com/simbot",    desc: "Simulate your character's DPS and gear upgrades" },
  { name: "Icy Veins",     url: "https://www.icy-veins.com/",         desc: "Class guides and raid strategies" },
  { name: "Wowhead",       url: "https://www.wowhead.com/",           desc: "Item database, quests, and guides" },
  { name: "Raider.io",     url: "https://raider.io/",                 desc: "Mythic+ rankings and character scores" },
  { name: "Warcraft Logs", url: "https://www.warcraftlogs.com/",      desc: "Raid and dungeon performance analysis" },
  { name: "Bloodmallet",   url: "https://bloodmallet.com/",           desc: "Trinket and item comparisons" },
  { name: "Keystone.guru", url: "https://keystone.guru/",             desc: "Plan and share M+ dungeon routes" },
  { name: "CurseForge",    url: "https://www.curseforge.com/",        desc: "Browse and install WoW addons" },
  { name: "Reddit",        url: "https://www.reddit.com/r/wow/",      desc: "WoW community discussions on r/wow" },
];

function ResourceSidebar() {
  return (
    <nav className="resource-sidebar">
      <div className="sidebar-title">Other Resources</div>
      {RESOURCES.map((r) => (
        <a
          key={r.name}
          href={r.url}
          target="_blank"
          rel="noreferrer"
          className="sidebar-btn"
          data-tooltip={r.desc}
        >
          {r.name}
        </a>
      ))}
      <a
        href="https://github.com/emzra/loremaster"
        target="_blank"
        rel="noreferrer"
        className="sidebar-github"
        data-tooltip="View source on GitHub"
      >
        <svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0 0 24 12c0-6.63-5.37-12-12-12z" />
        </svg>
      </a>
    </nav>
  );
}

function CoffeeModal() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => setVisible(true), 10000);
    return () => clearTimeout(timer);
  }, []);

  if (!visible) return null;

  return (
    <div className="coffee-modal">
      <button className="coffee-close" onClick={() => setVisible(false)}>✕</button>
      <a href="https://buymeacoffee.com/emzra" target="_blank" rel="noreferrer">
        ☕ Buy the creator a coffee!
      </a>
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
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8080"}/api/chat`, {
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
    <div className="layout">
    <ResourceSidebar />
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

      <CoffeeModal />

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
    </div>
  );
}

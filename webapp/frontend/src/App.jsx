import { useState, useRef, useEffect } from "react";
import "./App.css";
import Message from "./components/Message";
import ResourceSidebar from "./components/ResourceSidebar";
import CoffeeModal from "./components/CoffeeModal";

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

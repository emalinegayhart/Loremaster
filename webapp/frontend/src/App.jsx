import { useReducer, useRef, useEffect } from "react";
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

const initialState = {
  messages: [],
  input: "",
  loading: false,
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_INPUT":
      return { ...state, input: action.payload };

    case "SEND":
      return {
        ...state,
        loading: true,
        input: "",
        messages: [
          ...state.messages,
          { role: "user", content: action.payload },
          { role: "assistant", loading: true },
        ],
      };

    case "STREAM_START":
      return {
        ...state,
        messages: state.messages.map((m, i) =>
          i === state.messages.length - 1
            ? { role: "assistant", content: "", sections: [], streaming: true }
            : m
        ),
      };

    case "STREAM_CHUNK":
      return {
        ...state,
        messages: state.messages.map((m, i) =>
          i === state.messages.length - 1
            ? { ...m, content: action.payload }
            : m
        ),
      };

    case "COMPLETE":
      return {
        ...state,
        loading: false,
        messages: state.messages.map((m, i) =>
          i === state.messages.length - 1
            ? { role: "assistant", content: action.payload.content, sections: action.payload.sections, streaming: false }
            : m
        ),
      };

    case "ERROR":
      return {
        ...state,
        loading: false,
        messages: state.messages.map((m, i) =>
          i === state.messages.length - 1
            ? { role: "assistant", content: action.payload, sections: [], streaming: false }
            : m
        ),
      };

    case "RESET":
      return initialState;

    default:
      return state;
  }
}

export default function App() {
  const [state, dispatch] = useReducer(reducer, initialState);
  const { messages, input, loading } = state;
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function sendMessage(text) {
    const userMessage = text || input.trim();
    if (!userMessage || loading) return;

    dispatch({ type: "SEND", payload: userMessage });

    try {
      const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8080"}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...messages, { role: "user", content: userMessage }],
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let fullText = "";
      let sections = [];

      dispatch({ type: "STREAM_START" });

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
          dispatch({ type: "STREAM_CHUNK", payload: fullText });
        }
      }

      dispatch({
        type: "COMPLETE",
        payload: { content: cleanMarkdown(fullText), sections },
      });

    } catch (err) {
      dispatch({
        type: "ERROR",
        payload: "Something went wrong. Is the backend running?",
      });
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
        <header className="header" onClick={() => dispatch({ type: "RESET" })} style={{ cursor: "pointer" }}>
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
            onChange={(e) => dispatch({ type: "SET_INPUT", payload: e.target.value })}
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

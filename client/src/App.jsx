import { useState, useRef, useEffect } from "react";
import "./App.css";

export default function Chat() {

  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [streamMode, setStreamMode] = useState(true); 
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: "user", content: input };
    const newMessages = [...messages, userMessage];
    
    setMessages(newMessages);
    setInput("");
    setLoading(true);

    if (!streamMode) {
      // ---------- NOT STREAMING ----------
      try {
        const res = await fetch("http://localhost:8000/?stream=false", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: input, thread_id: 1 }),
        });
        const data = await res.json();
        setMessages([...newMessages, { role: "ai", content: data.reply }]);
      } catch (err) {
        setMessages([...newMessages, { role: "ai", content: "⚠️ 500" }]);
      } finally {
        setLoading(false);
      }
    } else {
      // ---------- STREAMING ----------
      let aiMessage = { role: "ai", content: "" };
      setMessages([...newMessages, aiMessage]);

      const eventSource = new EventSource(
        `http://localhost:8000/?stream=true&message=${encodeURIComponent(input)}&thread_id=1`
      );

      eventSource.onmessage = (event) => {
        if (event.data === "[DONE]") {
          setLoading(false);
          eventSource.close();
        } else {
          const data = JSON.parse(event.data);
          aiMessage.content += data.token;
          setMessages([...newMessages, { ...aiMessage }]);
        }
      };

      eventSource.onerror = () => {
        aiMessage.content += "\n⚠️ 500";
        setMessages([...newMessages, { ...aiMessage }]);
        setLoading(false);
        eventSource.close();
      };
    }
  };

  return (
    <div className="chat-container">
      {/* Toggle en haut à gauche */}
      <div className="chat-header">
        <label className="chat-toggle">
          <input
            type="checkbox"
            checked={streamMode}
            onChange={(e) => setStreamMode(e.target.checked)}
          />
          <span>Streaming</span>
        </label>
      </div>
      {/* Messages */}
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`message ${m.role === "user" ? "user-message" : "bot-message"}`}
          >
            {m.content}
          </div>
        ))}

        {loading && (
          <div className="typing-indicator">IA est en train d'écrire...</div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Zone input */}
      <div className="chat-input">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Écrivez un message..."
          onKeyDown={(e) =>
            e.key === "Enter" && !e.shiftKey && (e.preventDefault(), sendMessage())
          }
        />
        <button id="sendButton" onClick={sendMessage}>➤</button>
      </div>
    </div>
  );
}

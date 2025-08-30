import { useState, useRef, useEffect } from "react";
import "./App.css";
import { fetchEventSource } from '@microsoft/fetch-event-source'

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
      try {
        const res = await fetch("http://127.0.0.1:9000/?stream=false", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message: input, thread_id: 1 }),
        });
        const data = await res.json();
        setMessages([...newMessages, { role: "ai", content: data.reply }]);
      } catch (err) {
        setMessages([...newMessages, { role: "ai", content: err.message }]);
      } finally {
        setLoading(false);
      }
    } else {
      const aiMessage = { role: "ai", content: "" };
      let currentMessages = [...newMessages, aiMessage];
      setMessages(currentMessages);
      
      try {
        await fetchEventSource("http://127.0.0.1:9000/?stream=true", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            stream: true,
            message: input,
            thread_id: 1,
          }),
          onmessage(event) {
            if (event.data === "[DONE]") {
              setLoading(false);
            } else {
              const data = JSON.parse(event.data);
              setMessages(prevMessages => {
                const updated = [...prevMessages];
                updated[updated.length - 1] = {
                  ...updated[updated.length - 1],
                  content: updated[updated.length - 1].content + data.token
                };
                return updated;
              });
            }
          },
          onerror(err) {
            setMessages(prevMessages => {
              const updated = [...prevMessages];
              updated[updated.length - 1] = {
                ...updated[updated.length - 1],
                content: updated[updated.length - 1].content + "\n⚠️ Erreur de connexion"
              };
              return updated;
            });
            setLoading(false);
            throw err;
          },
        });
      } catch (err) {
        console.error("Streaming error:", err);
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="chat-container">
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
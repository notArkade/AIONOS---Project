import { useState } from "react";
import { sendChatMessage } from "../services/api";
import ChatMessage from "./ChatMessage";
import LoadingState from "./LoadingState";

const quickActions = ["What's on my calendar?", "What are my open tasks?", "Who is waiting on me?", "Who am I waiting on?", "What's urgent?", "Prepare me for board prep."];

export default function ChatWindow() {
  const [messages, setMessages] = useState([{ role: "assistant", content: "Good morning, Arjun. I can help you navigate your commitments, meetings, and follow-ups using the source data.", timestamp: new Date().toISOString() }]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(message = input) {
    const trimmed = message.trim();
    if (!trimmed || loading) return;
    setInput("");
    setMessages((current) => [...current, { role: "user", content: trimmed, timestamp: new Date().toISOString() }]);
    setLoading(true);
    try {
      const response = await sendChatMessage(trimmed);
      setMessages((current) => [...current, { role: "assistant", content: response.answer, sources: response.sources, timestamp: new Date().toISOString() }]);
    } catch (error) {
      setMessages((current) => [...current, { role: "assistant", content: `I couldn't reach the assistant service. ${error.message}`, timestamp: new Date().toISOString(), onRetry: () => submit(trimmed) }]);
    } finally {
      setLoading(false);
    }
  }

  return <section className="chat-panel" id="chat"><div className="chat-header"><div><p className="eyebrow">Ask your assistant</p><h2>Executive desk</h2></div><span className="online-label"><span className="status-dot" /> Ready</span></div><div className="quick-actions">{quickActions.map((action) => <button type="button" key={action} onClick={() => submit(action)}>{action}</button>)}</div><div className="conversation">{messages.map((message, index) => <ChatMessage key={`${message.role}-${index}`} message={message} />)}{loading && <LoadingState label="Reviewing source data" />}</div><form className="chat-input" onSubmit={(event) => { event.preventDefault(); submit(); }}><input value={input} onChange={(event) => setInput(event.target.value)} placeholder="Ask about your priorities..." aria-label="Ask the executive assistant" /><button type="submit" disabled={loading || !input.trim()}>Send</button></form></section>;
}
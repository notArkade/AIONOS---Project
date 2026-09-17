import SourceList from "./SourceList";

export default function ChatMessage({ message }) {
  return <div className={`chat-message ${message.role}`}><div className="message-bubble">{message.content.split("\n").map((line, index) => <p key={`${line}-${index}`}>{line || "\u00a0"}</p>)}{message.sources && <SourceList sources={message.sources} />}</div></div>;
}
export default function SummaryCard({ label, value, note, tone = "ink" }) {
  return (
    <article className={`summary-card ${tone}`}>
      <p>{label}</p>
      <strong>{value}</strong>
      <span>{note}</span>
    </article>
  );
}
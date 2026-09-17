function ItemMeta({ item }) {
  const date = item.deadline || item.scheduled_start;
  const formattedDate = date
    ? new Date(date).toLocaleDateString(undefined, { month: "short", day: "numeric" })
    : null;
  return <span className="item-meta">{item.owner || item.ownership}{formattedDate ? `  •  ${formattedDate}` : ""}</span>;
}

export default function TaskList({ items = [], title = "Open tasks" }) {
  return (
    <section className="panel task-panel">
      <div className="section-heading"><div><p className="eyebrow">Commitments</p><h2>{title}</h2></div><span className="count-badge">{items.length}</span></div>
      {items.length === 0 ? <p className="empty-state">No items are recorded here.</p> : <div className="item-list">{items.map((item) => <article className="list-item" key={item.id}><span className="check-mark" aria-hidden="true">{item.status === "completed" ? "✓" : ""}</span><div><h3>{item.title}</h3><ItemMeta item={item} /><p>{item.details?.[0]}</p></div></article>)}</div>}
    </section>
  );
}
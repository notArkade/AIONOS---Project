export default function Header({ asOf }) {
  const formattedDate = asOf
    ? new Date(asOf).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" })
    : null;

  return (
    <header className="topbar">
      <div className="brand-mark" aria-hidden="true">A</div>
      <div>
        <p className="eyebrow">Executive Productivity Agent</p>
        <h1>Arjun Malhotra <span>• VP Sales</span></h1>
      </div>
      <div className="as-of">
        <span className="status-dot" />
        <span>Source-grounded view</span>
        {formattedDate && <time dateTime={asOf}>As of {formattedDate}</time>}
      </div>
    </header>
  );
}
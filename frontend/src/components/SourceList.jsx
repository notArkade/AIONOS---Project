export default function SourceList({ sources = [] }) {
  if (!sources.length) return null;
  return <div className="source-list"><span>Sources</span>{sources.slice(0, 4).map((source) => <span className="source-pill" key={`${source.source_id}-${source.source_reference}`}>{source.source_reference}</span>)}</div>;
}
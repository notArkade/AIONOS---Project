export default function LoadingState({ label = "Loading source data" }) {
  return <div className="loading-state"><span className="spinner" />{label}</div>;
}
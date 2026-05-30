export function MetricCard({ label, value, compact = false }) {
  return (
    <div className={compact ? "metric-card compact" : "metric-card"}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

export function InfoCard({ title, body }) {
  return (
    <div className="info-card">
      <span>{title}</span>
      <p>{body}</p>
    </div>
  );
}

export function StatusPanel({ title, body, variant = "normal" }) {
  const className = variant === "error" ? "status-panel error" : "status-panel";
  return (
    <section className={className}>
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

function StatusBanner({ error, success }) {
  if (!error && !success) {
    return null;
  }

  return (
    <div className={`status-banner ${error ? "status-banner--error" : "status-banner--success"}`}>
      <p>{error || success}</p>
    </div>
  );
}

export default StatusBanner;

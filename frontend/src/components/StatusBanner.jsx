import { AlertCircle, CheckCircle } from "lucide-react";

function StatusBanner({ error, success }) {
  if (!error && !success) return null;

  return (
    <div className="toast-wrap">
      <div className={`toast toast--${error ? "error" : "success"}`}>
        {error ? <AlertCircle size={15} /> : <CheckCircle size={15} />}
        <span>{error || success}</span>
      </div>
    </div>
  );
}

export default StatusBanner;

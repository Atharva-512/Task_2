import useHealth from "../hooks/useHealth.js";
import styles from "./BackendStatusBadge.module.css";

export default function BackendStatusBadge() {
  const { data, loading, error } = useHealth();
  const isConnected = !loading && !error && Boolean(data);

  return (
    <span
      className={`${styles.badge} ${isConnected ? styles.connected : styles.disconnected}`}
    >
      <span className={styles.dot} />
      {loading
        ? "Checking Backend..."
        : isConnected
          ? "Backend Connected"
          : "Backend Disconnected"}
    </span>
  );
}

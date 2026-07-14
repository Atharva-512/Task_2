import styles from "./EmptyState.module.css";

export default function EmptyState({ message = "No data available." }) {
  return (
    <div className={styles.wrapper}>
      <svg
        className={styles.icon}
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.5"
        aria-hidden="true"
      >
        <rect x="3" y="10" width="4" height="8" rx="1" />
        <rect x="10" y="6" width="4" height="12" rx="1" />
        <rect x="17" y="13" width="4" height="5" rx="1" />
      </svg>
      <p className={styles.message}>{message}</p>
    </div>
  );
}

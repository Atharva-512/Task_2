import styles from "./KpiCard.module.css";

const TREND_ICON = {
  up: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="4 15 10 9 14 13 20 6" />
      <polyline points="14 6 20 6 20 12" />
    </svg>
  ),
  down: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="4 9 10 15 14 11 20 18" />
      <polyline points="14 18 20 18 20 12" />
    </svg>
  ),
  neutral: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="4" y1="12" x2="20" y2="12" />
    </svg>
  ),
};

export default function KpiCard({ title, value, trend = "neutral" }) {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <p className={styles.title}>{title}</p>
        <span className={`${styles.trendIcon} ${styles[trend]}`}>
          {TREND_ICON[trend]}
        </span>
      </div>
      <p className={styles.value}>{value}</p>
    </div>
  );
}

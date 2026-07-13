import styles from "./KpiCard.module.css";

export default function KpiCard({ title, value }) {
  return (
    <div className={styles.card}>
      <p className={styles.title}>{title}</p>
      <p className={styles.value}>{value}</p>
    </div>
  );
}

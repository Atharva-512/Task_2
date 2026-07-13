import styles from "./DashboardPanel.module.css";

export default function DashboardPanel({ title, children, className = "" }) {
  return (
    <section className={`${styles.panel} ${className}`}>
      <h2 className={styles.title}>{title}</h2>
      <div className={styles.body}>{children}</div>
    </section>
  );
}

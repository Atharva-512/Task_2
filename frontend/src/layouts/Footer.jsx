import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p className={styles.title}>
        Restaurant POS Analytics Dashboard
      </p>

      <p className={styles.subtitle}>
        Built with React • FastAPI • DuckDB • Recharts
      </p>
    </footer>
  );
}
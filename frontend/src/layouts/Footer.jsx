import styles from "./Footer.module.css";

export default function Footer() {
  return (
    <footer className={styles.footer}>
      <p className={styles.title}>Restaurant POS Analytics</p>
      <p className={styles.subtitle}>Powered by React • FastAPI • DuckDB</p>
    </footer>
  );
}

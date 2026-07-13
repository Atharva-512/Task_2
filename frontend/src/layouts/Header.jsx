import styles from "./Header.module.css";

export default function Header({ onMenuClick }) {
  return (
    <header className={styles.header}>
      <button
        className={styles.menuButton}
        onClick={onMenuClick}
        aria-label="Toggle navigation"
      >
        <span className={styles.bar} />
        <span className={styles.bar} />
        <span className={styles.bar} />
      </button>
      <h1 className={styles.title}>Dashboard</h1>
    </header>
  );
}

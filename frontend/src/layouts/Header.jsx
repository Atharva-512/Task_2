import styles from "./Header.module.css";

export default function Header({ onMenuClick }) {
  return (
    <header className={styles.header}>
      <button
        type="button"
        className={styles.menuButton}
        onClick={onMenuClick}
        aria-label="Open navigation menu"
      >
        <span className={styles.bar} />
        <span className={styles.bar} />
        <span className={styles.bar} />
      </button>

      <h1 className={styles.title}>
        {window.innerWidth <= 768 ? "Dashboard" : "Restaurant POS Analytics"}
      </h1>
    </header>
  );
}
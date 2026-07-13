import styles from "./LoadingScreen.module.css";

export default function LoadingScreen({ message = "Loading..." }) {
  return (
    <div className={styles.wrapper}>
      <div className={styles.spinner} />
      <p className={styles.message}>{message}</p>
    </div>
  );
}

import styles from "./ErrorMessage.module.css";

export default function ErrorMessage({
  message = "Something went wrong.",
  onRetry,
}) {
  return (
    <div className={styles.wrapper}>
      <p className={styles.message}>{message}</p>
      {onRetry && (
        <button className={styles.retryButton} onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

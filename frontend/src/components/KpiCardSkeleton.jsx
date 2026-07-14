import Skeleton from "./Skeleton.jsx";
import styles from "./KpiCard.module.css";

export default function KpiCardSkeleton() {
  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <Skeleton width="55%" height="12px" />
        <Skeleton width="20px" height="20px" radius="50%" />
      </div>
      <Skeleton width="75%" height="30px" />
    </div>
  );
}

import Skeleton from "./Skeleton.jsx";
import styles from "./ChartSkeleton.module.css";

export default function ChartSkeleton() {
  return (
    <div className={styles.wrapper}>
      <div className={styles.bars}>
        <Skeleton width="14%" height="60%" />
        <Skeleton width="14%" height="85%" />
        <Skeleton width="14%" height="45%" />
        <Skeleton width="14%" height="95%" />
        <Skeleton width="14%" height="70%" />
        <Skeleton width="14%" height="55%" />
      </div>
      <Skeleton width="100%" height="1px" />
    </div>
  );
}

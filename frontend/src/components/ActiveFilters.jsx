import styles from "./ActiveFilters.module.css";

export default function ActiveFilters({ filters }) {
  const chips = [];

  if (filters.startDate || filters.endDate) {
    const start = filters.startDate || "…";
    const end = filters.endDate || "…";
    chips.push({ key: "date", label: `Date: ${start} → ${end}` });
  }
  if (filters.platform) {
    chips.push({ key: "platform", label: `Platform: ${filters.platform}` });
  }
  if (filters.brand) {
    chips.push({ key: "brand", label: `Brand: ${filters.brand}` });
  }

  if (chips.length === 0) {
    return null;
  }

  return (
    <div className={styles.wrapper}>
      <span className={styles.label}>Active Filters:</span>
      <div className={styles.chips}>
        {chips.map((chip) => (
          <span key={chip.key} className={styles.chip}>
            {chip.label}
          </span>
        ))}
      </div>
    </div>
  );
}

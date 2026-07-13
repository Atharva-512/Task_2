import styles from "./FilterToolbar.module.css";

export default function FilterToolbar({
  filters,
  onChange,
  onReset,
  platforms,
  brands,
  loading,
  error,
}) {
  function handleField(field) {
    return (event) => {
      onChange({ ...filters, [field]: event.target.value });
    };
  }

  return (
    <div className={styles.toolbar}>
      <div className={styles.field}>
        <label className={styles.label} htmlFor="start-date">
          Start Date
        </label>
        <input
          id="start-date"
          type="date"
          className={styles.input}
          value={filters.startDate}
          onChange={handleField("startDate")}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="end-date">
          End Date
        </label>
        <input
          id="end-date"
          type="date"
          className={styles.input}
          value={filters.endDate}
          onChange={handleField("endDate")}
        />
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="platform">
          Platform
        </label>
        <select
          id="platform"
          className={styles.input}
          value={filters.platform}
          onChange={handleField("platform")}
          disabled={loading}
        >
          <option value="">All Platforms</option>
          {(platforms ?? []).map((platform) => (
            <option key={platform} value={platform}>
              {platform}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.field}>
        <label className={styles.label} htmlFor="brand">
          Brand
        </label>
        <select
          id="brand"
          className={styles.input}
          value={filters.brand}
          onChange={handleField("brand")}
          disabled={loading}
        >
          <option value="">All Brands</option>
          {(brands ?? []).map((brand) => (
            <option key={brand} value={brand}>
              {brand}
            </option>
          ))}
        </select>
      </div>

      <button type="button" className={styles.resetButton} onClick={onReset}>
        Reset Filters
      </button>

      {error && <span className={styles.errorNote}>Filters unavailable: {error}</span>}
    </div>
  );
}

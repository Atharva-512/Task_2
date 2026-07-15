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
  const handleField = (field) => (event) => {
    onChange({
      ...filters,
      [field]: event.target.value,
    });
  };

  return (
    <section className={styles.toolbar} aria-label="Dashboard Filters">
      <div className={styles.fields}>
        <div className={styles.field}>
          <label htmlFor="start-date" className={styles.label}>
            Start Date
          </label>

          <input
            id="start-date"
            type="date"
            className={styles.input}
            value={filters.startDate}
            onChange={handleField("startDate")}
            disabled={loading}
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="end-date" className={styles.label}>
            End Date
          </label>

          <input
            id="end-date"
            type="date"
            className={styles.input}
            value={filters.endDate}
            onChange={handleField("endDate")}
            disabled={loading}
          />
        </div>

        <div className={styles.field}>
          <label htmlFor="platform" className={styles.label}>
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
          <label htmlFor="brand" className={styles.label}>
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
      </div>

      <button
        type="button"
        className={styles.resetButton}
        onClick={onReset}
      >
        Reset Filters
      </button>

      {error && (
        <span
          className={styles.errorNote}
          role="alert"
        >
          Filters unavailable: {error}
        </span>
      )}
    </section>
  );
}
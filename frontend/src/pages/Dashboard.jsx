import LoadingScreen from "../components/LoadingScreen.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import useSummary from "../hooks/useSummary.js";
import usePlatformPerformance from "../hooks/usePlatformPerformance.js";
import useBrandPerformance from "../hooks/useBrandPerformance.js";
import useDailySales from "../hooks/useDailySales.js";
import useFilters from "../hooks/useFilters.js";
import styles from "./Dashboard.module.css";

export default function Dashboard() {
  const summary = useSummary();
  const platformPerformance = usePlatformPerformance();
  const brandPerformance = useBrandPerformance();
  const dailySales = useDailySales();
  const filters = useFilters();

  const sections = [
    { title: "Summary", state: summary },
    { title: "Platform Performance", state: platformPerformance },
    { title: "Brand Performance", state: brandPerformance },
    { title: "Daily Sales", state: dailySales },
    { title: "Filters", state: filters },
  ];

  return (
    <div className={styles.page}>
      {sections.map(({ title, state }) => (
        <section key={title}>
          <h2>{title}</h2>
          {state.loading && <LoadingScreen message={`Loading ${title}...`} />}
          {state.error && (
            <ErrorMessage
              message={`Failed to load ${title}: ${state.error}`}
              onRetry={state.refetch}
            />
          )}
          {!state.loading && !state.error && (
            <pre>{JSON.stringify(state.data, null, 2)}</pre>
          )}
        </section>
      ))}
    </div>
  );
}

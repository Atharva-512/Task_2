import { useEffect, useMemo, useState } from "react";
import ErrorMessage from "../components/ErrorMessage.jsx";
import KpiCard from "../components/KpiCard.jsx";
import KpiCardSkeleton from "../components/KpiCardSkeleton.jsx";
import DashboardPanel from "../components/DashboardPanel.jsx";
import FilterToolbar from "../components/FilterToolbar.jsx";
import ActiveFilters from "../components/ActiveFilters.jsx";
import ChartSkeleton from "../components/ChartSkeleton.jsx";
import DailySalesChart from "../components/charts/DailySalesChart.jsx";
import PlatformPerformanceChart from "../components/charts/PlatformPerformanceChart.jsx";
import BrandPerformanceChart from "../components/charts/BrandPerformanceChart.jsx";
import useSummary from "../hooks/useSummary.js";
import useDailySales from "../hooks/useDailySales.js";
import usePlatformPerformance from "../hooks/usePlatformPerformance.js";
import useBrandPerformance from "../hooks/useBrandPerformance.js";
import useFilters from "../hooks/useFilters.js";
import { formatCurrency, formatNumber } from "../utils/format.js";
import styles from "./Dashboard.module.css";

const DEFAULT_FILTERS = {
  startDate: "",
  endDate: "",
  platform: "",
  brand: "",
};

const KPI_TRENDS = {
  grossSales: "up",
  totalOrders: "up",
  averageOrderValue: "neutral",
  totalTax: "neutral",
  totalDiscount: "down",
};

function PanelContent({ loading, error, onRetry, children }) {
  if (loading) {
    return <ChartSkeleton />;
  }
  if (error) {
    return <ErrorMessage message={error} onRetry={onRetry} />;
  }
  return children;
}

function buildQueryParams(filters) {
  const params = {};
  if (filters.startDate) params.start_date = filters.startDate;
  if (filters.endDate) params.end_date = filters.endDate;
  if (filters.platform) params.platform = filters.platform;
  if (filters.brand) params.brand = filters.brand;
  return params;
}

function formatTimestamp(date) {
  return date.toLocaleString("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

export default function Dashboard() {
  const [filters, setFilters] = useState(DEFAULT_FILTERS);
  const [lastUpdated, setLastUpdated] = useState(null);
  const queryParams = useMemo(() => buildQueryParams(filters), [filters]);

  const {
    data: filterOptions,
    loading: filterOptionsLoading,
    error: filterOptionsError,
  } = useFilters();

  const {
    data: summary,
    loading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useSummary(queryParams);

  const {
    data: dailySales,
    loading: dailySalesLoading,
    error: dailySalesError,
    refetch: refetchDailySales,
  } = useDailySales(queryParams);

  const {
    data: platformPerformance,
    loading: platformLoading,
    error: platformError,
    refetch: refetchPlatform,
  } = usePlatformPerformance(queryParams);

  const {
    data: brandPerformance,
    loading: brandLoading,
    error: brandError,
    refetch: refetchBrand,
  } = useBrandPerformance(queryParams);

  const allLoaded =
    !summaryLoading && !dailySalesLoading && !platformLoading && !brandLoading;
  const anyError = summaryError || dailySalesError || platformError || brandError;

  useEffect(() => {
    if (allLoaded && !anyError) {
      setLastUpdated(new Date());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allLoaded, anyError, summary, dailySales, platformPerformance, brandPerformance]);

  const grossSales =
  summary?.total_sales ??
  summary?.gross_sales ??
  summary?.grossSales;
  const totalOrders = summary?.total_orders ?? summary?.totalOrders;
  const averageOrderValue =
    summary?.average_order_value ?? summary?.averageOrderValue;
  const totalTax = summary?.total_tax ?? summary?.totalTax;
  const totalDiscount = summary?.total_discount ?? summary?.totalDiscount;

  return (
    <div className={styles.page}>
      <div className={styles.headerRow}>
        <div className={styles.headingGroup}>
          <h1 className={styles.heading}>Restaurant POS Dashboard</h1>
          <span className={styles.lastUpdated}>
            {lastUpdated
              ? `Last Updated: ${formatTimestamp(lastUpdated)}`
              : "Last Updated: —"}
          </span>
        </div>
      </div>

      <FilterToolbar
        filters={filters}
        onChange={setFilters}
        onReset={() => setFilters(DEFAULT_FILTERS)}
        platforms={filterOptions?.platforms}
        brands={filterOptions?.brands}
        loading={filterOptionsLoading}
        error={filterOptionsError}
      />

      <ActiveFilters filters={filters} />

      {summaryError ? (
        <ErrorMessage
          message={`Failed to load summary: ${summaryError}`}
          onRetry={refetchSummary}
        />
      ) : (
        <div className={styles.kpiRow}>
          {summaryLoading ? (
            <>
              <KpiCardSkeleton />
              <KpiCardSkeleton />
              <KpiCardSkeleton />
              <KpiCardSkeleton />
              <KpiCardSkeleton />
            </>
          ) : (
            <>
              <KpiCard
                title="Gross Sales"
                value={formatCurrency(grossSales)}
                trend={KPI_TRENDS.grossSales}
              />
              <KpiCard
                title="Total Orders"
                value={formatNumber(totalOrders)}
                trend={KPI_TRENDS.totalOrders}
              />
              <KpiCard
                title="Average Order Value"
                value={formatCurrency(averageOrderValue)}
                trend={KPI_TRENDS.averageOrderValue}
              />
              <KpiCard title="Total Tax" value={formatCurrency(totalTax)} trend={KPI_TRENDS.totalTax} />
              <KpiCard
                title="Total Discount"
                value={formatCurrency(totalDiscount)}
                trend={KPI_TRENDS.totalDiscount}
              />
            </>
          )}
        </div>
      )}

      <div className={styles.chartsGrid}>
        <DashboardPanel title="Daily Sales Trend">
          <PanelContent
            loading={dailySalesLoading}
            error={dailySalesError}
            onRetry={refetchDailySales}
          >
            <DailySalesChart data={dailySales ?? []} />
          </PanelContent>
        </DashboardPanel>

        <DashboardPanel title="Platform Performance">
          <PanelContent
            loading={platformLoading}
            error={platformError}
            onRetry={refetchPlatform}
          >
            <PlatformPerformanceChart data={platformPerformance ?? []} />
          </PanelContent>
        </DashboardPanel>

        <DashboardPanel title="Brand Performance">
          <PanelContent
            loading={brandLoading}
            error={brandError}
            onRetry={refetchBrand}
          >
            <BrandPerformanceChart data={brandPerformance ?? []} />
          </PanelContent>
        </DashboardPanel>
      </div>
    </div>
  );
}

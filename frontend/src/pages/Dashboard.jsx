import LoadingScreen from "../components/LoadingScreen.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import KpiCard from "../components/KpiCard.jsx";
import DashboardPanel from "../components/DashboardPanel.jsx";
import DailySalesChart from "../components/charts/DailySalesChart.jsx";
import PlatformPerformanceChart from "../components/charts/PlatformPerformanceChart.jsx";
import BrandPerformanceChart from "../components/charts/BrandPerformanceChart.jsx";
import useSummary from "../hooks/useSummary.js";
import useDailySales from "../hooks/useDailySales.js";
import usePlatformPerformance from "../hooks/usePlatformPerformance.js";
import useBrandPerformance from "../hooks/useBrandPerformance.js";
import { formatCurrency, formatNumber } from "../utils/format.js";
import styles from "./Dashboard.module.css";

function PanelContent({ loading, error, onRetry, loadingMessage, children }) {
  if (loading) {
    return <LoadingScreen message={loadingMessage} />;
  }
  if (error) {
    return <ErrorMessage message={error} onRetry={onRetry} />;
  }
  return children;
}

export default function Dashboard() {
  const {
    data: summary,
    loading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useSummary();

  const {
    data: dailySales,
    loading: dailySalesLoading,
    error: dailySalesError,
    refetch: refetchDailySales,
  } = useDailySales();

  const {
    data: platformPerformance,
    loading: platformLoading,
    error: platformError,
    refetch: refetchPlatform,
  } = usePlatformPerformance();

  const {
    data: brandPerformance,
    loading: brandLoading,
    error: brandError,
    refetch: refetchBrand,
  } = useBrandPerformance();

  const grossSales = summary?.gross_sales ?? summary?.grossSales;
  const totalOrders = summary?.total_orders ?? summary?.totalOrders;
  const averageOrderValue =
    summary?.average_order_value ?? summary?.averageOrderValue;
  const totalTax = summary?.total_tax ?? summary?.totalTax;
  const totalDiscount = summary?.total_discount ?? summary?.totalDiscount;

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Restaurant POS Dashboard</h1>

      {summaryLoading && <LoadingScreen message="Loading summary..." />}
      {summaryError && (
        <ErrorMessage
          message={`Failed to load summary: ${summaryError}`}
          onRetry={refetchSummary}
        />
      )}

      {!summaryLoading && !summaryError && (
        <div className={styles.kpiRow}>
          <KpiCard title="Gross Sales" value={formatCurrency(grossSales)} />
          <KpiCard title="Total Orders" value={formatNumber(totalOrders)} />
          <KpiCard
            title="Average Order Value"
            value={formatCurrency(averageOrderValue)}
          />
          <KpiCard title="Total Tax" value={formatCurrency(totalTax)} />
          <KpiCard
            title="Total Discount"
            value={formatCurrency(totalDiscount)}
          />
        </div>
      )}

      <DashboardPanel title="Daily Sales Trend">
        <PanelContent
          loading={dailySalesLoading}
          error={dailySalesError}
          onRetry={refetchDailySales}
          loadingMessage="Loading daily sales..."
        >
          <DailySalesChart data={dailySales ?? []} />
        </PanelContent>
      </DashboardPanel>

      <DashboardPanel title="Platform Performance">
        <PanelContent
          loading={platformLoading}
          error={platformError}
          onRetry={refetchPlatform}
          loadingMessage="Loading platform performance..."
        >
          <PlatformPerformanceChart data={platformPerformance ?? []} />
        </PanelContent>
      </DashboardPanel>

      <DashboardPanel title="Brand Performance">
        <PanelContent
          loading={brandLoading}
          error={brandError}
          onRetry={refetchBrand}
          loadingMessage="Loading brand performance..."
        >
          <BrandPerformanceChart data={brandPerformance ?? []} />
        </PanelContent>
      </DashboardPanel>
    </div>
  );
}

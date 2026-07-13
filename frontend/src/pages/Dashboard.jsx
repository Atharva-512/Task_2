import LoadingScreen from "../components/LoadingScreen.jsx";
import ErrorMessage from "../components/ErrorMessage.jsx";
import KpiCard from "../components/KpiCard.jsx";
import DashboardPanel from "../components/DashboardPanel.jsx";
import useSummary from "../hooks/useSummary.js";
import styles from "./Dashboard.module.css";

function formatCurrency(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "—";
  }
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(Number(value));
}

function formatNumber(value) {
  if (value === undefined || value === null || Number.isNaN(Number(value))) {
    return "—";
  }
  return new Intl.NumberFormat("en-IN").format(Number(value));
}

export default function Dashboard() {
  const { data: summary, loading, error, refetch } = useSummary();

  const grossSales = summary?.gross_sales ?? summary?.grossSales;
  const totalOrders = summary?.total_orders ?? summary?.totalOrders;
  const averageOrderValue =
    summary?.average_order_value ?? summary?.averageOrderValue;
  const totalTax = summary?.total_tax ?? summary?.totalTax;
  const totalDiscount = summary?.total_discount ?? summary?.totalDiscount;

  return (
    <div className={styles.page}>
      <h1 className={styles.heading}>Restaurant POS Dashboard</h1>

      {loading && <LoadingScreen message="Loading summary..." />}
      {error && (
        <ErrorMessage
          message={`Failed to load summary: ${error}`}
          onRetry={refetch}
        />
      )}

      {!loading && !error && (
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
        Chart will be added in Phase 6.2
      </DashboardPanel>

      <DashboardPanel title="Platform Performance">
        Chart will be added in Phase 6.2
      </DashboardPanel>

      <DashboardPanel title="Brand Performance">
        Chart will be added in Phase 6.2
      </DashboardPanel>
    </div>
  );
}

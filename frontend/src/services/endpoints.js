import api from "./api.js";

export function getHealth() {
  return api.get("/health").then((res) => res.data);
}

export function getSummary(params = {}) {
  return api.get("/api/summary", { params }).then((res) => res.data);
}

export function getPlatformPerformance(params = {}) {
  return api.get("/api/platform-performance", { params }).then((res) => res.data);
}

export function getBrandPerformance(params = {}) {
  return api.get("/api/brand-performance", { params }).then((res) => res.data);
}

export function getDailySales(params = {}) {
  return api.get("/api/daily-sales", { params }).then((res) => res.data);
}

export function getFilters() {
  return api.get("/api/filters").then((res) => res.data);
}

import useFetch from "./useFetch.js";
import { getPlatformPerformance } from "../services/endpoints.js";

export default function usePlatformPerformance(queryParams = {}) {
  return useFetch(() => getPlatformPerformance(queryParams), [queryParams]);
}
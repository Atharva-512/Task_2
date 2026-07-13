import useFetch from "./useFetch.js";
import { getBrandPerformance } from "../services/endpoints.js";

export default function useBrandPerformance() {
  return useFetch(() => getBrandPerformance());
}

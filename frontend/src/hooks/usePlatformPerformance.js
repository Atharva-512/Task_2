import useFetch from "./useFetch.js";
import { getPlatformPerformance } from "../services/endpoints.js";

export default function usePlatformPerformance() {
  return useFetch(() => getPlatformPerformance());
}

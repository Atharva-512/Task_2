import useFetch from "./useFetch.js";
import { getSummary } from "../services/endpoints.js";

export default function useSummary(queryParams = {}) {
  return useFetch(() => getSummary(queryParams), [queryParams]);
}
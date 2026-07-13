import useFetch from "./useFetch.js";
import { getSummary } from "../services/endpoints.js";

export default function useSummary() {
  return useFetch(() => getSummary());
}

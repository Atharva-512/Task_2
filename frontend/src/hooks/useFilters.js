import useFetch from "./useFetch.js";
import { getFilters } from "../services/endpoints.js";

export default function useFilters() {
  return useFetch(() => getFilters());
}

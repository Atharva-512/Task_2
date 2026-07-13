import useFetch from "./useFetch.js";
import { getDailySales } from "../services/endpoints.js";

export default function useDailySales() {
  return useFetch(() => getDailySales());
}

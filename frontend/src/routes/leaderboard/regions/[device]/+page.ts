import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, params, url }) => {
  const device = params.device;
  const searchQuery = url.searchParams.get("q") || "";
  const sortBy = url.searchParams.get("sort") || "score";
  const order = url.searchParams.get("order") || "desc";

  const apiUrl = `${API_BASE}/regional-leaderboard/?device=${device}&q=${searchQuery}&sort=${sortBy}&order=${order}`;
  const response = await fetch(apiUrl);

  if (!response.ok) {
    return { regions: [], device, searchQuery, sortBy, order };
  }

  const regions = await response.json();

  return {
    regions,
    device,
    searchQuery,
    sortBy,
    order,
  };
};

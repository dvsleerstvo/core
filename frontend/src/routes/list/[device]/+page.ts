import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, params, url }) => {
  const device = params.device; // 'pc' or 'mobile'
  const searchQuery = url.searchParams.get("q") || "";

  // Use the correctly formatted parameter 'q'
  const apiUrl = `${API_BASE}/levels/?device=${device}&q=${encodeURIComponent(searchQuery)}`;

  const fetchOptions: RequestInit = {
    credentials: "include",
  };

  const response = await fetch(apiUrl, fetchOptions);

  if (!response.ok) {
    return { levels: [], next: null, device, searchQuery };
  }

  const data = await response.json();

  return {
    levels: data.results || data, // Handle both paginated and non-paginated
    next: data.next,
    device,
    searchQuery,
  };
};

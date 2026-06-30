import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, params }) => {
  const { code } = params;

  const apiUrl = `${API_BASE}/region/${code}/`;
  const response = await fetch(apiUrl);

  if (!response.ok) {
    return { profile: null };
  }

  const data = await response.json();

  return {
    profile: data,
  };
};

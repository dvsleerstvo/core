import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, params }) => {
  const { id } = params;

  const apiUrl = `${API_BASE}/users/${id}/`;
  // We don't need to manually pass headers, SvelteKit's fetch handles it
  const response = await fetch(apiUrl);

  if (!response.ok) {
    return { user: null };
  }

  const userData = await response.json();

  return {
    profile: userData,
  };
};

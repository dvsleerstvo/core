import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";
import { error } from "@sveltejs/kit";

export const load: PageLoad = async ({ fetch }) => {
  const res = await fetch(`${API_BASE}/levels/all_for_submit/`);
  if (!res.ok) {
    throw error(500, "Could not load levels");
  }
  const levels = await res.json();
  return { levels };
};

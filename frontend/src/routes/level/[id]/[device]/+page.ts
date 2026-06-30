import { API_BASE } from "$lib/api";
import type { PageLoad } from "./$types";

export const load: PageLoad = async ({ fetch, params }) => {
  const { id, device } = params;

  const apiUrl = `${API_BASE}/levels/${id}/?device=${device}`;
  const response = await fetch(apiUrl);

  if (!response.ok) {
    return {
      level: null,
      error: "Level not found",
    };
  }

  const levelData = await response.json();

  return {
    level: levelData,
    device,
  };
};

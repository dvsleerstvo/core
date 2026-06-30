import { writable } from "svelte/store";

export const deviceType = writable<"pc" | "mobile">("pc");
export const user = writable<any>(null); // Placeholder for user auth state

import { redirect } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async () => {
  // Перенаправляем на эндпоинт Django
  throw redirect(302, "http://localhost:8000/accounts/discord/login/");
};

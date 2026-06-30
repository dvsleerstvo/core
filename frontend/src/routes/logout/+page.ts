import { redirect } from "@sveltejs/kit";
import type { PageLoad } from "./$types";

export const load: PageLoad = async () => {
  // Перенаправляем на созданный ранее API эндпоинт выхода
  throw redirect(302, "http://localhost:8000/api/v2/auth/logout/");
};

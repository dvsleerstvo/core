import { browser } from "$app/environment";

// В браузере используем относительный путь (через Nginx на 80 порту)
// На сервере (SSR) используем внутреннее имя контейнера Django в Docker-сети
export const API_BASE = browser ? "/api/v2" : "http://web:8000/api/v2";

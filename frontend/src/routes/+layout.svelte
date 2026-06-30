<script lang="ts">
  import { deviceType, user } from "$lib/stores";
  import { page } from "$app/state";
  import { onMount } from "svelte";
  import { API_BASE } from "$lib/api";
  import { browser } from "$app/environment";
  import { navigating } from "$app/stores";
  import Spinner from "$lib/components/Spinner.svelte";
  import { fade } from "svelte/transition";

  let { children } = $props();

  async function checkAuth() {
    if (!browser) return;
    try {
      const res = await fetch(`${API_BASE}/auth/me/`, {
        // Important: send cookies with request
        credentials: "include",
      });
      const data = await res.json();
      if (data.authenticated) {
        $user = data;
      } else {
        $user = null;
      }
    } catch (e) {
      console.error("Auth check failed", e);
      $user = null;
    }
  }

  onMount(() => {
    checkAuth();
  });

  const loginUrl = browser ? "/accounts/discord/login/" : "#";
</script>

<header
  class="p-2 fixed-top w-100 shadow-sm"
  style="background: rgba(0,0,0,0.8); backdrop-filter: blur(15px);"
>
  <div class="container">
    <nav class="navbar navbar-expand-lg navbar-dark p-0">
      <div class="container-fluid p-0">
        <h1 class="h4 mb-0 d-flex align-items-center" id="project-name">
          <img
            src="/img/tiger.png"
            alt="Tiger"
            style="height: 1.5em; margin-right: 10px;"
          />
          <a
            href="/"
            style="text-decoration: none !important; color: var(--primary);"
            >ДВ СЛЕЕРСТВО</a
          >
        </h1>

        <button
          class="navbar-toggler border-0 shadow-none"
          type="button"
          data-bs-toggle="collapse"
          data-bs-target="#navbarNav"
          aria-controls="#navbarNav"
          aria-expanded="false"
          aria-label="Toggle navigation"
        >
          <span class="navbar-toggler-icon"></span>
        </button>

        <div
          class="collapse navbar-collapse justify-content-end mt-2 mt-lg-0"
          id="navbarNav"
        >
          <ul class="navbar-nav gap-2">
            <li class="nav-item dropdown">
              <a
                class="btn btn-primary dropdown-toggle w-100"
                href="#"
                id="dropdownList"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                Лист
              </a>
              <ul
                class="dropdown-menu dropdown-menu-dark"
                aria-labelledby="dropdownList"
              >
                <li>
                  <a
                    class="dropdown-item"
                    href="/list/pc"
                    onclick={() => ($deviceType = "pc")}>ПК</a
                  >
                </li>
                <li>
                  <a
                    class="dropdown-item"
                    href="/list/mobile"
                    onclick={() => ($deviceType = "mobile")}>Мобильный</a
                  >
                </li>
              </ul>
            </li>
            <li class="nav-item dropdown">
              <a
                class="btn btn-primary dropdown-toggle w-100"
                href="#"
                id="dropdownTop"
                data-bs-toggle="dropdown"
                aria-expanded="false"
              >
                Топ
              </a>
              <ul
                class="dropdown-menu dropdown-menu-dark"
                aria-labelledby="dropdownTop"
              >
                <li><h6 class="dropdown-header">Игроки</h6></li>
                <li><a class="dropdown-item" href="/leaderboard/pc">ПК</a></li>
                <li>
                  <a class="dropdown-item" href="/leaderboard/mobile"
                    >Мобильный</a
                  >
                </li>
                <li><hr class="dropdown-divider" /></li>
                <li><h6 class="dropdown-header">Регионы</h6></li>
                <li>
                  <a class="dropdown-item" href="/leaderboard/regions/pc">ПК</a>
                </li>
                <li>
                  <a class="dropdown-item" href="/leaderboard/regions/mobile"
                    >Мобильный</a
                  >
                </li>
              </ul>
            </li>
            <li class="nav-item">
              <a
                href="https://t.me/dvsleerstvo"
                class="btn btn-primary d-flex align-items-center justify-content-center w-100"
              >
                <i class="fab fa-telegram me-2"></i>
                <span>Телеграм</span>
              </a>
            </li>

            {#if $user}
              <li class="nav-item dropdown">
                <a
                  class="btn btn-primary dropdown-toggle d-flex align-items-center justify-content-center w-100"
                  href="#"
                  id="dropdownUser"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  <i class="fab fa-discord me-2"></i>
                  <span class="text-truncate" style="max-width: 150px;">
                    {$user.username}
                  </span>
                </a>
                <ul
                  class="dropdown-menu dropdown-menu-end dropdown-menu-dark"
                  aria-labelledby="dropdownUser"
                >
                  {#if $user.gd_user_id}
                    <li>
                      <a
                        class="dropdown-item d-flex align-items-center"
                        href="/user/{$user.gd_user_id}"
                      >
                        <i class="fas fa-user me-2"></i> Профиль
                      </a>
                    </li>
                    <li>
                      <a
                        class="dropdown-item d-flex align-items-center"
                        href="/submit"
                      >
                        <i class="fas fa-plus-circle me-2"></i> Отправить рекорд
                      </a>
                    </li>
                    <li>
                      <button
                        class="dropdown-item d-flex align-items-center no-active-highlight"
                        onclick={async (e) => {
                          e.stopPropagation();
                          $user.notifications_enabled =
                            !$user.notifications_enabled;
                          await fetch(`${API_BASE}/auth/settings/`, {
                            method: "POST",
                            headers: {
                              "Content-Type": "application/json",
                              "X-CSRFToken":
                                (document.cookie.match(/csrftoken=([^;]+)/) ||
                                  [])[1] || "",
                            },
                            body: JSON.stringify({
                              notifications_enabled:
                                $user.notifications_enabled,
                            }),
                            credentials: "include",
                          });
                        }}
                      >
                        <i
                          class="fas {$user.notifications_enabled
                            ? 'fa-bell'
                            : 'fa-bell-slash'} me-2 text-white"
                        ></i>
                        <span
                          >Уведомления: {$user.notifications_enabled
                            ? "ВКЛ"
                            : "ВЫКЛ"}</span
                        >
                      </button>
                    </li>
                    <li><hr class="dropdown-divider" /></li>
                  {/if}
                  <li>
                    <button
                      class="dropdown-item d-flex align-items-center text-danger"
                      onclick={async (e) => {
                        e.preventDefault();
                        await fetch(`${API_BASE}/auth/logout/`, {
                          method: "POST",
                          headers: {
                            "Content-Type": "application/json",
                            "X-CSRFToken":
                              (document.cookie.match(/csrftoken=([^;]+)/) ||
                                [])[1] || "",
                          },
                          credentials: "include",
                        });
                        window.location.href = "/";
                      }}
                    >
                      <i class="fas fa-sign-out-alt me-2"></i> Выйти
                    </button>
                  </li>
                </ul>
              </li>
            {:else}
              <li class="nav-item">
                <a
                  href={loginUrl}
                  class="btn btn-primary d-flex align-items-center justify-content-center w-100"
                >
                  <i class="fab fa-discord me-2"></i>
                  <span>Войти</span>
                </a>
              </li>
            {/if}
          </ul>
        </div>
      </div>
    </nav>
  </div>
</header>

<main>
  {#if $navigating}
    <div class="loading-overlay" out:fade={{ duration: 200 }}>
      <Spinner message="Синхронизация..." />
    </div>
  {/if}
  {@render children()}
</main>

<style>
  .loading-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.85);
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(10px);
  }

  .no-active-highlight:active,
  .no-active-highlight:focus,
  .no-active-highlight:hover {
    background-color: transparent !important;
    color: #fff !important;
  }
</style>

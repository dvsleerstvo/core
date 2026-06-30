<script lang="ts">
  import { user } from "$lib/stores";
  import { API_BASE } from "$lib/api";
  import { onMount } from "svelte";
  import { slide, fade } from "svelte/transition";

  let { data } = $props();

  let selectedLevel = $state<any>(null);
  let progress = $state(100);
  let video = $state("");
  let selectedDevice = $state("");

  let message = $state({ text: "", type: "" });
  let isSubmitting = $state(false);

  // Умный поиск уровней
  let searchQuery = $state("");
  let isDropdownOpen = $state(false);

  // Фильтруем все уровни без ограничений .slice()
  const filteredLevels = $derived(
    data.levels.filter(
      (l: any) =>
        l.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        l.creator.toLowerCase().includes(searchQuery.toLowerCase()),
    ),
  );

  function selectLevel(level: any) {
    selectedLevel = level;
    searchQuery = level.name;
    isDropdownOpen = false;
  }

  function getCookie(name: string) {
    let cookieValue = null;
    if (
      typeof document !== "undefined" &&
      document.cookie &&
      document.cookie !== ""
    ) {
      const cookies = document.cookie.split(";");
      for (let i = 0; i < cookies.length; i++) {
        const cookie = cookies[i].trim();
        if (cookie.substring(0, name.length + 1) === name + "=") {
          cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
          break;
        }
      }
    }
    return cookieValue;
  }

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    if (isSubmitting || !selectedLevel || !selectedDevice) return;

    isSubmitting = true;
    message = { text: "", type: "" };

    try {
      const res = await fetch(`${API_BASE}/record-requests/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCookie("csrftoken") || "",
        },
        body: JSON.stringify({
          level: selectedLevel.id,
          progress,
          video,
          device: selectedDevice,
        }),
        credentials: "include",
      });

      const result = await res.json();

      if (res.ok) {
        message = {
          text: "Ваш рекорд успешно отправлен и ожидает проверки модераторами!",
          type: "success",
        };
        selectedLevel = null;
        progress = 100;
        video = "";
        selectedDevice = "";
        searchQuery = "";
      } else {
        console.error("Submission failed:", result);
        message = {
          text:
            result.error ||
            JSON.stringify(result) ||
            "Ошибка при отправке заявки",
          type: "danger",
        };
      }
    } catch (err) {
      message = {
        text: "Произошла ошибка при соединении с сервером",
        type: "danger",
      };
    } finally {
      isSubmitting = false;
    }
  }

  function handleClickOutside(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (!target.closest(".level-select-container")) {
      isDropdownOpen = false;
    }
  }

  onMount(() => {
    window.addEventListener("click", handleClickOutside);
    return () => window.removeEventListener("click", handleClickOutside);
  });
</script>

<svelte:head>
  <title>Отправить рекорд - ДВ СЛЕЕРСТВО</title>
  <link rel="stylesheet" href="/css/submit_record.css" />
</svelte:head>

<div class="container my-5 pt-5">
  <div class="row justify-content-center">
    <div class="col-md-8 col-lg-6">
      <div class="detail-wrapper position-relative overflow-hidden p-4 p-md-5">
        <div
          class="position-absolute top-0 start-50 translate-middle-x"
          style="width: 250px; height: 150px; background: var(--primary); filter: blur(100px); opacity: 0.15; pointer-events: none;"
        ></div>

        <div class="text-center mb-5">
          <span
            class="badge mb-2 px-3 py-2"
            style="background: linear-gradient(135deg, var(--primary), var(--accent)); font-weight: 800; letter-spacing: 1px;"
          >
            ФОРМА
          </span>
          <h2
            class="display-5 fw-bold mb-0"
            style="text-shadow: 0 0 25px rgba(249, 115, 22, 0.3);"
          >
            Отправить рекорд
          </h2>
        </div>

        {#if !$user}
          <div class="text-center py-4">
            <p class="text-white opacity-75">
              Пожалуйста, войдите через Discord, чтобы отправить рекорд.
            </p>
            <a
              href="/login"
              class="btn btn-primary px-4 py-2"
              style="border-radius: 10px;">Войти</a
            >
          </div>
        {:else if !$user.gd_user_id}
          <div class="text-center">
            <div
              class="alert alert-danger"
              style="background: rgba(220, 53, 69, 0.1); border: 1px solid #dc3545; color: #fff; border-radius: 12px; padding: 25px;"
            >
              <i
                class="fas fa-exclamation-triangle fa-3x mb-3 text-danger"
                style="text-shadow: 0 0 15px rgba(220, 53, 69, 0.5);"
              ></i>
              <h5 class="fw-bold mb-3">Аккаунт не привязан</h5>
              <p class="mb-0 opacity-75">
                Ваш аккаунт Discord еще не привязан к профилю игрока в листе.
                Пожалуйста, обратитесь к администратору для привязки аккаунта.
              </p>
            </div>
          </div>
        {:else}
          {#if message.text}
            <div
              class="alert alert-{message.type} alert-dismissible fade show"
              role="alert"
              style="background: rgba(255,255,255,0.05); color: #fff; border: 1px solid {message.type ===
              'success'
                ? 'var(--primary)'
                : '#dc3545'}; border-radius: 12px;"
            >
              {message.text}
              <button
                type="button"
                class="btn-close btn-close-white"
                onclick={() => (message.text = "")}
                aria-label="Close"
              ></button>
            </div>
          {/if}

          <form onsubmit={handleSubmit}>
            <!-- Поиск уровня -->
            <div class="mb-4 position-relative level-select-container">
              <label for="level-search" class="form-label"
                ><i class="fas fa-layer-group me-2 text-accent"></i> Уровень</label
              >

              <div class="search-box-wrapper">
                <input
                  type="text"
                  id="level-search"
                  class="form-control custom-input search-input"
                  placeholder="Начните вводить название..."
                  bind:value={searchQuery}
                  oninput={() => (isDropdownOpen = true)}
                  onclick={(e) => {
                    e.stopPropagation();
                    isDropdownOpen = true;
                  }}
                  autocomplete="off"
                />
                <button
                  type="button"
                  class="dropdown-toggle-btn"
                  onclick={(e) => {
                    e.stopPropagation();
                    isDropdownOpen = !isDropdownOpen;
                  }}
                >
                  <i
                    class="fas fa-chevron-down {isDropdownOpen
                      ? 'rotated'
                      : ''}"
                  ></i>
                </button>
              </div>

              {#if isDropdownOpen}
                <div
                  class="custom-dropdown shadow-lg"
                  transition:slide={{ duration: 200 }}
                >
                  <div class="dropdown-scroll-area">
                    {#each filteredLevels as level}
                      <button
                        type="button"
                        class="dropdown-item {selectedLevel?.id === level.id
                          ? 'active'
                          : ''}"
                        onclick={() => selectLevel(level)}
                      >
                        <div
                          class="d-flex justify-content-between align-items-center mb-1"
                        >
                          <span class="level-name-text fw-bold"
                            >{level.name}</span
                          >
                          <span class="rank-badge">#{level.place}</span>
                        </div>
                        <div class="creator-text">
                          <i class="fas fa-tools me-1 small opacity-50"></i>
                          {level.creator}
                        </div>
                      </button>
                    {:else}
                      <div class="p-3 text-center text-muted">
                        Ничего не найдено
                      </div>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>

            <!-- Прогресс -->
            <div class="mb-4">
              <label for="progress" class="form-label"
                ><i class="fas fa-percent me-2 text-accent"></i> Прогресс (%)</label
              >
              <div class="d-flex align-items-center gap-3">
                <input
                  type="range"
                  class="form-range flex-grow-1"
                  min="1"
                  max="100"
                  bind:value={progress}
                />
                <input
                  type="number"
                  name="progress"
                  id="progress"
                  class="form-control custom-input progress-number-input"
                  required
                  min="1"
                  max="100"
                  bind:value={progress}
                />
              </div>
            </div>

            <!-- Видео -->
            <div class="mb-4">
              <label for="video" class="form-label"
                ><i class="fab fa-youtube me-2 text-accent"></i> Ссылка на видео</label
              >
              <input
                type="url"
                name="video"
                id="video"
                class="form-control custom-input"
                required
                placeholder="https://youtube.com/watch?v=..."
                bind:value={video}
              />
            </div>

            <!-- Устройство -->
            <div class="mb-5">
              <label class="form-label d-block"
                ><i class="fas fa-desktop me-2 text-accent"></i> Устройство</label
              >
              <div class="device-selector">
                <button
                  type="button"
                  class="device-btn {selectedDevice === 'PC' ? 'active' : ''}"
                  onclick={() => (selectedDevice = "PC")}
                >
                  <i class="fas fa-desktop"></i>
                  <span>PC</span>
                </button>
                <button
                  type="button"
                  class="device-btn {selectedDevice === 'Mobile'
                    ? 'active'
                    : ''}"
                  onclick={() => (selectedDevice = "Mobile")}
                >
                  <i class="fas fa-mobile-alt"></i>
                  <span>Mobile</span>
                </button>
              </div>
            </div>

            <button
              type="submit"
              class="btn btn-primary w-100 py-3 submit-btn"
              disabled={isSubmitting || !selectedLevel || !selectedDevice}
            >
              {#if isSubmitting}
                <span class="spinner-border spinner-border-sm me-2"></span> ОТПРАВКА...
              {:else}
                <i class="fas fa-paper-plane me-2"></i> ОТПРАВИТЬ ЗАЯВКУ
              {/if}
            </button>
          </form>
        {/if}
      </div>
    </div>
  </div>
</div>

<style>
  .search-box-wrapper {
    position: relative;
    display: flex;
    align-items: center;
  }
  .custom-input {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
    color: #fff !important;
    border-radius: 10px !important;
  }
  .custom-input::placeholder {
    color: rgba(255, 255, 255, 0.4) !important;
  }

  .search-input {
    padding-right: 50px !important;
  }
  .progress-number-input {
    width: 80px;
    text-align: center;
    padding-right: 12px !important;
    font-weight: 700;
    opacity: 1 !important;
  }

  .dropdown-toggle-btn {
    position: absolute;
    right: 0;
    top: 0;
    bottom: 0;
    width: 50px;
    background: transparent;
    border: none;
    color: rgba(255, 255, 255, 0.3);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 2;
  }
  .dropdown-toggle-btn i.rotated {
    transform: rotate(180deg);
  }

  .custom-dropdown {
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    background: #111;
    border: 1px solid rgba(249, 115, 22, 0.4);
    border-radius: 12px;
    margin-top: 8px;
    z-index: 1000;
    backdrop-filter: blur(15px);
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.8);
    overflow: hidden;
  }

  .dropdown-scroll-area {
    max-height: 400px;
    overflow-y: auto;
  }

  /* Красивый скроллбар */
  .dropdown-scroll-area::-webkit-scrollbar {
    width: 6px;
  }
  .dropdown-scroll-area::-webkit-scrollbar-track {
    background: transparent;
  }
  .dropdown-scroll-area::-webkit-scrollbar-thumb {
    background: var(--primary);
    border-radius: 10px;
  }

  .dropdown-item {
    width: 100%;
    padding: 12px 20px;
    border: none;
    background: transparent;
    color: #fff;
    text-align: left;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    transition: 0.2s;
  }
  .dropdown-item:hover {
    background: rgba(249, 115, 22, 0.1);
  }
  .dropdown-item:hover .level-name-text {
    color: var(--primary);
  }
  .dropdown-item.active {
    background: rgba(249, 115, 22, 0.2);
    border-left: 4px solid var(--primary);
  }

  .rank-badge {
    font-size: 0.75rem;
    padding: 2px 8px;
    background: rgba(255, 255, 255, 0.1);
    border-radius: 4px;
    color: var(--primary);
    font-weight: 800;
  }

  .creator-text {
    font-size: 0.8rem;
    color: #aaa;
  }

  .device-selector {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 15px;
  }
  .device-btn {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 15px;
    color: #fff;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    transition: 0.3s;
  }
  .device-btn.active {
    background: rgba(249, 115, 22, 0.1);
    border-color: var(--primary);
    box-shadow: 0 0 20px rgba(249, 115, 22, 0.2);
  }
  .device-btn.active i {
    color: var(--primary);
    opacity: 1;
  }

  .form-range::-webkit-slider-thumb {
    background-color: var(--primary);
  }
  .form-range::-moz-range-thumb {
    background-color: var(--primary);
  }
  .submit-btn {
    border-radius: 12px;
    font-size: 1.1rem;
    letter-spacing: 1px;
  }
</style>

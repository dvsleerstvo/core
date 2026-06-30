<script lang="ts">
  import { deviceType, user } from "$lib/stores";
  import { onMount, tick } from "svelte";
  import { API_BASE } from "$lib/api";
  import Spinner from "$lib/components/Spinner.svelte";
  import { browser } from "$app/environment";

  let { data } = $props();
  let levels = $state(data.levels);
  let nextUrl = $state(data.next);
  let isLoadingMore = $state(false);
  let observerTarget: HTMLElement | null = $state(null);

  // Функция для очистки URL, который возвращает Django REST Framework
  function cleanUrl(url: string | null) {
    if (!url) return null;
    try {
      // Если url абсолютный (http...), создаем объект URL и берем только путь и параметры
      const parsed = new URL(
        url,
        browser ? window.location.origin : "http://localhost",
      );
      return parsed.pathname + parsed.search;
    } catch (e) {
      // Если не удалось распарсить, возвращаем как есть или пробуем старый метод
      if (url.includes("web:8000")) {
        return url.replace("http://web:8000", "");
      }
      return url;
    }
  }

  $effect(() => {
    $deviceType = data.device as "pc" | "mobile";
    levels = data.levels;
    nextUrl = cleanUrl(data.next);
  });

  async function loadMore() {
    if (!nextUrl || isLoadingMore) return;
    isLoadingMore = true;

    try {
      const res = await fetch(nextUrl, { credentials: "include" });
      if (res.ok) {
        const newData = await res.json();
        const newLevels = newData.results || [];
        levels = [...levels, ...newLevels];
        nextUrl = cleanUrl(newData.next);
      }
    } catch (e) {
      console.error("Failed to load more levels", e);
    } finally {
      isLoadingMore = false;
    }
  }

  // Следим за целью и URL подгрузки
  $effect(() => {
    if (browser && observerTarget) {
      const observer = new IntersectionObserver(
        (entries) => {
          const entry = entries[0];
          if (entry.isIntersecting && nextUrl && !isLoadingMore) {
            loadMore();
          }
        },
        {
          threshold: 0,
          rootMargin: "0px 0px 600px 0px",
        },
      );

      observer.observe(observerTarget);
      return () => observer.disconnect();
    }
  });
</script>

<svelte:head>
  <title>Главная - ДВ СЛЕЕРСТВО</title>
  <!-- Подключаем оригинальные стили -->
  <link rel="stylesheet" href="/css/level.css" />
  <link rel="stylesheet" href="/css/search.css" />
</svelte:head>

<div class="container my-4 pt-5 pt-lg-4">
  <!-- Поиск -->
  <div class="row mb-4 mb-lg-5 justify-content-center">
    <div class="col-12 col-md-8 col-lg-5">
      <form method="GET" action="/list/{data.device}">
        <div
          class="input-group search-container shadow"
          style="border-radius: 12px; overflow: hidden; border: 1px solid rgba(249, 115, 22, 0.4); background: rgba(255, 255, 255, 0.05);"
        >
          <span
            class="input-group-text border-0"
            style="background: transparent;"
          >
            <i
              class="fas fa-search"
              style="color: var(--primary); opacity: 0.8; font-size: 1.1rem;"
            ></i>
          </span>

          <input
            type="text"
            name="q"
            value={data.searchQuery}
            class="form-control border-0 text-light shadow-none"
            placeholder="Поиск уровня..."
            style="background: transparent;"
          />

          {#if data.searchQuery}
            <a
              href="/list/{data.device}"
              class="btn btn-outline-secondary border-0 d-flex align-items-center justify-content-center"
              style="width: 40px; background: rgba(255, 255, 255, 0.1);"
            >
              <i class="fas fa-times text-light"></i>
            </a>
          {/if}

          <button type="submit" class="btn btn-primary px-4"> Искать </button>
        </div>
      </form>
    </div>
  </div>

  <!-- Список уровней -->
  <div class="level-list">
    {#each levels as level, i}
      <a
        href="/level/{level.level_id}/{data.device}"
        class="level-card text-decoration-none text-white {level.is_passed
          ? 'passed'
          : ''}"
      >
        <div class="level-img">
          <img src={level.thumbnail_url} alt={level.name} loading="lazy" />
          {#if level.is_passed}
            <div class="passed-badge shadow-lg">
              <i class="fas fa-check-circle me-1"></i> ПРОЙДЕНО
            </div>
          {/if}
        </div>

        <div class="level-info">
          <div class="level-header">
            <div class="level-title">
              <h5>#{level.list_rank || i + 1} – {level.name}</h5>
            </div>
          </div>

          <div class="level-details">
            <div class="d-flex flex-wrap gap-2">
              <span
                ><i class="fas fa-globe me-1 text-primary"></i> Global:
                <strong>#{level.place}</strong></span
              >
              <span
                ><i class="far fa-paper-plane me-1 text-info"></i> Опубликован:
                <strong>{level.published}</strong></span
              >
            </div>
          </div>
        </div>
      </a>
    {:else}
      <div class="text-center py-5 w-100" style="grid-column: 1 / -1;">
        <div class="opacity-25">
          {#if data.searchQuery}
            <i class="fas fa-search-minus display-4 mb-3 text-light"></i>
            <p class="text-light">
              По запросу «<strong>{data.searchQuery}</strong>» уровней не
              найдено
            </p>
          {:else}
            <i class="fas fa-list display-4 mb-3 text-light"></i>
            <p class="text-light">Нет уровней для отображения</p>
          {/if}
        </div>
      </div>
    {/each}
  </div>

  <!-- Индикатор загрузки следующих уровней -->
  <div bind:this={observerTarget} class="py-5" style="min-height: 100px;">
    {#if nextUrl && isLoadingMore}
      <Spinner size="40px" message="Загрузка уровней..." />
    {/if}
  </div>
</div>

<style>
  /* Глобальные стили для подсвеченных уровней */
  :global(.level-card.passed) {
    border: 2px solid var(--primary) !important;
    box-shadow: 0 0 25px rgba(249, 115, 22, 0.2) !important;
    background: rgba(249, 115, 22, 0.05) !important;
  }

  .passed-badge {
    position: absolute;
    top: 12px;
    right: 12px;
    background: var(--primary);
    color: #fff;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 900;
    letter-spacing: 1px;
    z-index: 2;
    border: 2px solid rgba(255, 255, 255, 0.2);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
  }

  @media (max-width: 768px) {
    :global(.level-list) {
      grid-template-columns: 1fr !important;
      gap: 25px !important;
      padding: 0 15px;
    }

    :global(.level-card) {
      flex-direction: column !important;
      height: auto !important;
      border-radius: 16px !important;
      overflow: hidden;
      background: rgba(255, 255, 255, 0.03) !important;
      border: 1px solid rgba(255, 255, 255, 0.1) !important;
    }

    :global(.level-img) {
      width: 100% !important;
      height: 180px !important;
      border-radius: 0 !important;
    }

    :global(.level-img img) {
      object-fit: cover !important;
    }

    :global(.level-info) {
      padding: 20px !important;
      text-align: center !important;
      width: 100% !important;
    }

    :global(.level-header) {
      justify-content: center !important;
      margin-bottom: 10px !important;
    }

    :global(.level-title h5) {
      font-size: 1.4rem !important;
      font-weight: 800 !important;
      margin: 0 !important;
    }

    :global(.level-details) {
      justify-content: center !important;
      font-size: 0.85rem !important;
      opacity: 0.8 !important;
    }

    :global(.level-details .d-flex) {
      justify-content: center !important;
      gap: 15px !important;
    }

    .passed-badge {
      font-size: 0.7rem;
      padding: 4px 10px;
      top: 10px;
      right: 10px;
    }
  }
</style>

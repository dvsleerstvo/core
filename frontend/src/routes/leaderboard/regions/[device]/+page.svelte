<script lang="ts">
  import { deviceType } from "$lib/stores";
  let { data } = $props();

  $effect(() => {
    $deviceType = data.device as "pc" | "mobile";
  });

  const isMobile = $derived(data.device === "mobile");
</script>

<svelte:head>
  <title>Топ регионов - ДВ СЛЕЕРСТВО</title>
  <!-- Подключаем специфичные стили, которые были в Django шаблоне -->
  <link rel="stylesheet" href="/css/table.css" />
  <link rel="stylesheet" href="/css/leaderboard.css" />
  <link rel="stylesheet" href="/css/search.css" />
</svelte:head>

<div class="container my-5">
  <div class="detail-wrapper position-relative overflow-hidden">
    <div
      class="position-absolute top-0 start-50 translate-middle-x"
      style="width: 300px; height: 100px; background: var(--primary); filter: blur(120px); opacity: 0.15; pointer-events: none;"
    ></div>

    <div class="text-center mb-4">
      <h1
        class="display-5 fw-bold"
        style="text-shadow: 0 0 25px rgba(249, 115, 22, 0.3);"
      >
        {isMobile ? "Топ Регионов (Mobile)" : "Топ Регионов (PC)"}
      </h1>
    </div>

    <div class="row mb-5 justify-content-center">
      <div class="col-md-6 col-lg-5">
        <form method="GET" action="/leaderboard/regions/{data.device}">
          {#if data.sortBy}<input
              type="hidden"
              name="sort"
              value={data.sortBy}
            />{/if}
          {#if data.order}<input
              type="hidden"
              name="order"
              value={data.order}
            />{/if}

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
              placeholder="Поиск региона..."
              style="background: transparent;"
            />

            {#if data.searchQuery}
              <a
                href="/leaderboard/regions/{data.device}?sort={data.sortBy}&order={data.order}"
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

    <div class="table-responsive">
      <table class="table table-dark align-middle custom-leaderboard-table">
        <thead>
          <tr>
            <th scope="col" class="text-center" style="width: 80px;">РАНГ</th>
            <th scope="col">РЕГИОН</th>

            <th scope="col" class="text-center">
              <a
                href="/leaderboard/regions/{data.device}?sort=score&order={data.sortBy ===
                  'score' && data.order === 'desc'
                  ? 'asc'
                  : 'desc'}{data.searchQuery ? '&q=' + data.searchQuery : ''}"
                class="text-decoration-none sortable-header"
              >
                ОЧКИ
                {#if data.sortBy === "score"}
                  {#if data.order === "asc"}
                    <i class="fas fa-sort-up ms-1 text-primary"></i>
                  {:else}
                    <i class="fas fa-sort-down ms-1 text-primary"></i>
                  {/if}
                {:else}
                  <i class="fas fa-sort ms-1" style="opacity: 0.3;"></i>
                {/if}
              </a>
            </th>

            <th scope="col" class="d-none d-md-table-cell text-end">
              <a
                href="/leaderboard/regions/{data.device}?sort=hardest&order={data.sortBy ===
                  'hardest' && data.order === 'desc'
                  ? 'asc'
                  : 'desc'}{data.searchQuery ? '&q=' + data.searchQuery : ''}"
                class="text-decoration-none sortable-header"
              >
                ХАРДЕСТ
                {#if data.sortBy === "hardest"}
                  {#if data.order === "asc"}
                    <i class="fas fa-sort-up ms-1 text-primary"></i>
                  {:else}
                    <i class="fas fa-sort-down ms-1 text-primary"></i>
                  {/if}
                {:else}
                  <i class="fas fa-sort ms-1" style="opacity: 0.3;"></i>
                {/if}
              </a>
            </th>
          </tr>
        </thead>
        <tbody>
          {#each data.regions as reg}
            <tr class="leaderboard-row {reg.rank <= 3 ? 'top-player-row' : ''}">
              <td class="text-center">
                <div class="rank-container">
                  {#if reg.rank === 1}
                    <span class="rank-icon gold">1</span>
                  {:else if reg.rank === 2}
                    <span class="rank-icon silver">2</span>
                  {:else if reg.rank === 3}
                    <span class="rank-icon bronze">3</span>
                  {:else}
                    <span class="rank-number">#{reg.rank}</span>
                  {/if}
                </div>
              </td>
              <td>
                <div class="d-flex align-items-center gap-3">
                  <span
                    class="flag flag-{reg.region_code} shadow-sm"
                    style="--flag-size: 1.2rem; border-radius: 3px;"
                  ></span>
                  <a
                    href="/region/{reg.region_code}"
                    class="player-name-link fw-bold"
                  >
                    {reg.region_name}
                  </a>
                </div>
              </td>
              <td class="text-center">
                <div class="score-badge">
                  {Math.round(reg.total_score * 100) / 100}
                </div>
              </td>
              <td class="d-none d-md-table-cell text-end">
                <div class="hardest-level-text">
                  {reg.best_place !== 999999 ? reg.hardest_name : "—"}
                </div>
              </td>
            </tr>
          {:else}
            <tr>
              <td colspan="4" class="text-center py-5">
                <div class="opacity-25">
                  {#if data.searchQuery}
                    <i class="fas fa-search-minus display-4 mb-3"></i>
                    <p>
                      По запросу «<strong>{data.searchQuery}</strong>» ничего не
                      найдено
                    </p>
                  {:else}
                    <i class="fas fa-users-slash display-4 mb-3"></i>
                    <p>Нет данных для отображения</p>
                  {/if}
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>

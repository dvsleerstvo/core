<script lang="ts">
  import { deviceType } from "$lib/stores";
  let { data } = $props();

  $effect(() => {
    $deviceType = data.device as "pc" | "mobile";
  });

  const level = $derived(data.level);
  const isPC = $derived(data.device.toLowerCase() === "pc");
</script>

<svelte:head>
  {#if level}
    <title>#{level.rank} – {level.name} - ДВ СЛЕЕРСТВО</title>
  {/if}
  <!-- Подключаем оригинальные стили -->
  <link rel="stylesheet" href="/css/video.css" />
  <link rel="stylesheet" href="/css/table.css" />
  <link rel="stylesheet" href="/css/level_detail.css" />
</svelte:head>

{#if level}
  <div class="container my-5">
    <div class="detail-wrapper position-relative overflow-hidden">
      <div
        class="position-absolute top-0 start-50 translate-middle-x"
        style="width: 200px; height: 100px; background: var(--primary); filter: blur(100px); opacity: 0.15; pointer-events: none;"
      ></div>

      <div class="text-white text-center mb-5">
        <span
          class="badge mb-2 px-3 py-2"
          style="background: linear-gradient(135deg, var(--primary), var(--accent)); font-weight: 800; letter-spacing: 1px;"
        >
          МЕСТО #{level.rank}
        </span>
        <h1
          class="display-4 fw-bold"
          style="text-shadow: 0 0 25px rgba(249, 115, 22, 0.3);"
        >
          {level.name}
        </h1>

        <div
          class="d-flex justify-content-center gap-4 mt-3 flex-wrap opacity-75"
        >
          <span class="fs-6"
            ><i class="fas fa-user-edit me-2 text-accent"></i>Создатель:
            <strong class="text-white">{level.creator}</strong></span
          >
          <span class="fs-6"
            ><i class="fas fa-check-circle me-2 text-accent"></i>Верификатор:
            <strong class="text-white">{level.verifier}</strong></span
          >
        </div>
      </div>

      <div class="row justify-content-center g-4 mb-5">
        <div class="col-auto">
          <div
            class="px-5 py-3 rounded-4 text-center border border-primary border-opacity-25"
            style="background: rgba(249, 115, 22, 0.05); backdrop-filter: blur(5px);"
          >
            <small
              class="text-uppercase fw-bold opacity-50"
              style="color: var(--primary); letter-spacing: 2px;"
              >100% Очки</small
            >
            <div class="h2 m-0 fw-bold" style="color: var(--accent);">
              {Number(
                isPC
                  ? level.completion_points_pc
                  : level.completion_points_mobile,
              ).toLocaleString(undefined, {
                minimumFractionDigits: 0,
                maximumFractionDigits: 2,
              })}
            </div>
          </div>
        </div>
        {#if isPC ? level.list_percentage_pc : level.list_percentage_mobile}
          <div class="col-auto">
            <div
              class="px-5 py-3 rounded-4 text-center border border-warning border-opacity-25"
              style="background: rgba(251, 191, 36, 0.05); backdrop-filter: blur(5px);"
            >
              <small
                class="text-uppercase fw-bold opacity-50"
                style="color: var(--accent); letter-spacing: 2px;"
                >List% ({isPC
                  ? level.list_percentage_pc
                  : level.list_percentage_mobile}%)</small
              >
              <div class="h2 m-0 fw-bold" style="color: #fff;">
                {Number(
                  isPC ? level.list_points_pc : level.list_points_mobile,
                ).toLocaleString(undefined, {
                  minimumFractionDigits: 0,
                  maximumFractionDigits: 2,
                })}
              </div>
            </div>
          </div>
        {/if}
      </div>

      <div class="row justify-content-center mb-5">
        <div class="col-12 col-lg-10">
          <div
            class="video-container p-1 rounded-4"
            style="background: linear-gradient(135deg, rgba(249, 115, 22, 0.3), transparent);"
          >
            <iframe
              src={level.display_video_url}
              title={level.name}
              frameborder="0"
              allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
              referrerpolicy="strict-origin-when-cross-origin"
              allowfullscreen
              class="rounded-3"
            ></iframe>
          </div>
        </div>
      </div>

      <div class="mt-5">
        <div
          class="d-flex align-items-center justify-content-center gap-3 mb-4"
        >
          <div
            style="height: 1px; width: 50px; background: linear-gradient(to left, var(--primary), transparent);"
          ></div>
          <h3 class="m-0 fw-bold">
            РЕКОРДЫ <span class="ms-2 opacity-50 fs-5"
              >({level.victors.length})</span
            >
          </h3>
          <div
            style="height: 1px; width: 50px; background: linear-gradient(to right, var(--primary), transparent);"
          ></div>
        </div>

        <div class="table-responsive">
          <table class="table table-dark table-hover align-middle custom-table">
            <thead>
              <tr>
                <th class="text-center" width="80">Флаг</th>
                <th>Игрок</th>
                <th class="text-center">Прогресс</th>
                <th class="text-end" width="120">Видео</th>
              </tr>
            </thead>
            <tbody>
              {#each level.victors as victor, i}
                <tr class="victor-row">
                  <td class="text-center">
                    <span
                      class="flag flag-{victor.username_detail
                        .region} shadow-sm"
                    ></span>
                  </td>
                  <td>
                    <a
                      href="/user/{victor.username_detail.id}"
                      class="player-link fw-semibold text-white"
                    >
                      {victor.username_detail.username}
                    </a>
                  </td>
                  <td class="text-center">
                    <div class="progress-badge">
                      <span class="fw-bold">
                        {victor.progress === 100
                          ? "100%"
                          : victor.progress + "%"}
                      </span>
                    </div>
                  </td>
                  <td class="text-end">
                    {#if victor.youtube}
                      <a href={victor.youtube} target="_blank" class="btn-yt">
                        <i class="fab fa-youtube"></i>
                      </a>
                    {:else}
                      <span class="opacity-25">—</span>
                    {/if}
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
{:else}
  <div class="container my-5 pt-5 text-center">
    <h2 class="text-danger">Уровень не найден</h2>
    <a href="/" class="btn btn-primary mt-3">Вернуться на главную</a>
  </div>
{/if}

<style>
  .victor-row {
    transition: all 0.3s ease;
  }

  .victor-row:hover {
    background: rgba(249, 115, 22, 0.05) !important;
  }

  .progress-badge {
    display: inline-block;
    padding: 4px 16px;
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.2);
    border-radius: 20px;
    color: var(--accent);
    transition: 0.3s;
  }

  .victor-row:hover .progress-badge {
    background: var(--primary);
    color: #fff;
    box-shadow: 0 0 15px rgba(249, 115, 22, 0.4);
  }

  @media (max-width: 768px) {
    .display-4 {
      font-size: 2rem;
    }
    .h2 {
      font-size: 1.5rem;
    }

    .px-5 {
      padding-left: 1.5rem !important;
      padding-right: 1.5rem !important;
    }

    :global(.custom-table) {
      font-size: 0.85rem;
    }

    .progress-badge {
      padding: 2px 10px;
      font-size: 0.8rem;
    }
  }
</style>

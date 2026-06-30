<script lang="ts">
  import { user } from "$lib/stores";
  import { API_BASE } from "$lib/api";
  import { onMount } from "svelte";

  let { data } = $props();

  // Используем состояние, которое инициализируется из данных load
  let profile = $state(data.profile);

  // Если данные из функции load изменились (например, перешли на другой профиль), обновляем локальное состояние
  $effect(() => {
    if (data.profile) {
      profile = data.profile;
    }
  });

  // Фоновое обновление на клиенте, чтобы гарантированно подгрузить приватные данные (заявки)
  async function refreshProfile() {
    if (!profile) return;
    try {
      const res = await fetch(`${API_BASE}/users/${profile.id}/`, {
        credentials: "include",
      });
      if (res.ok) {
        const latestData = await res.json();
        // Обновляем только если получили больше данных (заявки) или данные изменились
        profile = latestData;
      }
    } catch (e) {
      console.error("Failed to refresh profile on client", e);
    }
  }

  onMount(() => {
    refreshProfile();
  });

  function formatDate(dateStr: string) {
    if (!dateStr) return "";
    const d = new Date(dateStr);
    return d.toLocaleString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }
</script>

<svelte:head>
  {#if profile}
    <title>{profile.username} - ДВ СЛЕЕРСТВО</title>
  {/if}
  <link rel="stylesheet" href="/css/user_profile.css" />
  <link rel="stylesheet" href="/css/statistic.css" />
</svelte:head>

{#if profile}
  <div class="container my-5 pt-5">
    <div class="detail-wrapper position-relative overflow-hidden">
      <div
        class="position-absolute top-0 start-50 translate-middle-x"
        style="width: 300px; height: 150px; background: var(--primary); filter: blur(120px); opacity: 0.1; pointer-events: none;"
      ></div>

      <div class="text-center mb-5">
        <div
          class="d-inline-flex align-items-center justify-content-center gap-3 mb-3"
        >
          {#if profile.region}
            <span
              class="flag flag-{profile.region} shadow-lg"
              style="--flag-size: 2rem; border-radius: 4px;"
            ></span>
          {/if}
          <h1
            class="display-4 fw-bold mb-0"
            style="text-shadow: 0 0 30px rgba(249, 115, 22, 0.4);"
          >
            {profile.username}
          </h1>
        </div>
        <div
          class="text-uppercase ls-2 opacity-50 fw-bold"
          style="font-size: 0.8rem; letter-spacing: 3px; color: var(--accent);"
        >
          Профиль игрока
        </div>
      </div>

      <div class="stats-grid mb-5">
        {#if Number(profile.score_pc) > 0}
          <div class="stat-card border-primary border-opacity-10">
            <span>Ранг (ПК)</span>
            <h3 class="fw-800">#{profile.rank_pc || "—"}</h3>
          </div>
          <div class="stat-card border-warning border-opacity-10">
            <span>Очки (ПК)</span>
            <h3 style="color: var(--primary) !important;">
              {Number(profile.score_pc).toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </h3>
          </div>
        {/if}

        {#if Number(profile.score_mobile) > 0}
          <div class="stat-card border-primary border-opacity-10">
            <span>Ранг (Моб)</span>
            <h3 class="fw-800">#{profile.rank_mobile || "—"}</h3>
          </div>
          <div class="stat-card border-warning border-opacity-10">
            <span>Очки (Моб)</span>
            <h3 style="color: var(--primary) !important;">
              {Number(profile.score_mobile).toLocaleString(undefined, {
                maximumFractionDigits: 2,
              })}
            </h3>
          </div>
        {/if}
      </div>

      <div class="row g-4">
        {#if Number(profile.score_pc) > 0 || profile.victors_on_pc?.length > 0}
          <div
            class="col-12 {Number(profile.score_mobile) > 0 ||
            profile.victors_on_mobile?.length > 0
              ? 'col-lg-6'
              : ''}"
          >
            <div class="record-section p-4 rounded-4 h-100">
              <h4 class="mb-4 d-flex align-items-center gap-2">
                <i class="fas fa-desktop" style="color: var(--primary);"></i>
                <span>PC Records</span>
                <span
                  class="ms-auto badge bg-white bg-opacity-10 fw-normal fs-6"
                  >{profile.victors_on_pc?.length || 0}</span
                >
              </h4>

              <div class="mb-4">
                <h6 class="record-subtitle">Пройдено</h6>
                <div class="d-flex flex-wrap gap-2">
                  {#each profile.victors_on_pc || [] as victor}
                    <a
                      href={victor.youtube}
                      target="_blank"
                      class="record-pill completed text-decoration-none"
                    >
                      {victor.level_detail.name}
                    </a>
                  {/each}
                </div>
              </div>

              {#if profile.progress_on_pc?.length > 0}
                <div>
                  <h6 class="record-subtitle text-warning">Прогресс</h6>
                  <div class="d-flex flex-wrap gap-2">
                    {#each profile.progress_on_pc as rec}
                      <a
                        href={rec.youtube}
                        target="_blank"
                        class="record-pill progress-tag text-decoration-none"
                      >
                        {rec.level_detail.name}
                        <span class="ms-1 opacity-75">{rec.progress}%</span>
                      </a>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}

        {#if Number(profile.score_mobile) > 0 || profile.victors_on_mobile?.length > 0}
          <div
            class="col-12 {Number(profile.score_pc) > 0 ||
            profile.victors_on_pc?.length > 0
              ? 'col-lg-6'
              : ''}"
          >
            <div class="record-section p-4 rounded-4 h-100">
              <h4 class="mb-4 d-flex align-items-center gap-2">
                <i
                  class="fas fa-mobile-alt text-accent"
                  style="color: var(--primary);"
                ></i>
                <span>Mobile Records</span>
                <span
                  class="ms-auto badge bg-white bg-opacity-10 fw-normal fs-6"
                  >{profile.victors_on_mobile?.length || 0}</span
                >
              </h4>

              <div class="mb-4">
                <h6 class="record-subtitle">Пройдено</h6>
                <div class="d-flex flex-wrap gap-2">
                  {#each profile.victors_on_mobile || [] as victor}
                    <a
                      href={victor.youtube}
                      target="_blank"
                      class="record-pill completed text-decoration-none"
                    >
                      {victor.level_detail.name}
                    </a>
                  {/each}
                </div>
              </div>

              {#if profile.progress_on_mobile?.length > 0}
                <div>
                  <h6 class="record-subtitle text-warning">Прогресс</h6>
                  <div class="d-flex flex-wrap gap-2">
                    {#each profile.progress_on_mobile as rec}
                      <a
                        href={rec.youtube}
                        target="_blank"
                        class="record-pill progress-tag text-decoration-none"
                      >
                        {rec.level_detail.name}
                        <span class="ms-1 opacity-75">{rec.progress}%</span>
                      </a>
                    {/each}
                  </div>
                </div>
              {/if}
            </div>
          </div>
        {/if}
      </div>

      {#if profile.record_requests && profile.record_requests.length > 0}
        <div class="row mt-5">
          <div class="col-12">
            <div
              class="record-section p-4 rounded-4 position-relative overflow-hidden"
            >
              <div
                class="position-absolute top-0 start-50 translate-middle-x"
                style="width: 150px; height: 100px; background: var(--primary); filter: blur(80px); opacity: 0.1; pointer-events: none;"
              ></div>

              <h4 class="mb-4 d-flex align-items-center gap-2">
                <i
                  class="fas fa-inbox text-accent"
                  style="color: var(--primary);"
                ></i>
                <span>Мои заявки на рекорды</span>
                <span
                  class="ms-auto badge bg-white bg-opacity-10 fw-normal fs-6"
                  >{profile.record_requests.length}</span
                >
              </h4>

              <div class="table-responsive">
                <table
                  class="table table-dark align-middle custom-leaderboard-table mb-0"
                >
                  <thead>
                    <tr>
                      <th scope="col">УРОВЕНЬ</th>
                      <th scope="col" class="text-center">ПРОГРЕСС</th>
                      <th scope="col" class="text-center">УСТРОЙСТВО</th>
                      <th scope="col" class="d-none d-md-table-cell text-center"
                        >ДАТА</th
                      >
                      <th scope="col" class="text-end">СТАТУС</th>
                    </tr>
                  </thead>
                  <tbody>
                    {#each profile.record_requests as req}
                      <tr class="leaderboard-row">
                        <td class="fw-bold fs-6">
                          {req.level_detail.name}
                          {#if req.notes}
                            <div class="moderator-note mt-1">
                              <i class="fas fa-comment-dots me-1 opacity-50"
                              ></i>
                              {req.notes}
                            </div>
                          {/if}
                        </td>
                        <td class="text-center">
                          <div
                            class="score-badge"
                            style="color: #fff; background: rgba(255,255,255,0.05); border-color: rgba(255,255,255,0.1);"
                          >
                            {req.progress}%
                          </div>
                        </td>
                        <td
                          class="text-center"
                          style="color: rgba(255,255,255,0.5);"
                        >
                          {#if req.device === "PC"}
                            <i class="fas fa-desktop me-1"></i>
                          {:else}
                            <i class="fas fa-mobile-alt me-1"></i>
                          {/if}
                          {req.device}
                        </td>
                        <td
                          class="d-none d-md-table-cell text-center"
                          style="color: rgba(255,255,255,0.4); font-size: 0.85rem;"
                        >
                          {formatDate(req.created_at)}
                        </td>
                        <td class="text-end">
                          {#if req.status === "pending"}
                            <span
                              class="badge bg-warning text-dark px-3 py-2 rounded-pill shadow-sm"
                              ><i class="fas fa-clock me-1"></i> На модерации</span
                            >
                          {:else if req.status === "approved"}
                            <span
                              class="badge bg-success px-3 py-2 rounded-pill shadow-sm"
                              ><i class="fas fa-check me-1"></i> Одобрено</span
                            >
                          {:else if req.status === "rejected"}
                            <span
                              class="badge bg-danger px-3 py-2 rounded-pill shadow-sm"
                              ><i class="fas fa-times me-1"></i> Отклонено</span
                            >
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
      {/if}
    </div>
  </div>
{:else}
  <div class="container py-5 text-center">
    <div class="spinner-border text-primary" role="status"></div>
    <p class="mt-3 text-muted">Загрузка профиля...</p>
  </div>
{/if}

<style>
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 220px));
    justify-content: center;
    gap: 1.5rem;
    width: 100%;
    max-width: 1000px;
    margin: 0 auto 3rem auto;
  }

  .stats-grid > div {
    width: 100%;
  }

  /* Global classes like leaderboard-row, custom-leaderboard-table, and score-badge are used from CSS files */
  :global(.custom-leaderboard-table) {
    --bs-table-bg: transparent !important;
    border-collapse: separate;
    border-spacing: 0 12px;
    background: transparent !important;
  }

  :global(.custom-leaderboard-table thead th) {
    border: none !important;
    color: rgba(255, 255, 255, 0.5);
    font-size: 0.75rem;
    letter-spacing: 1.5px;
    padding-bottom: 10px;
    text-transform: uppercase;
  }

  :global(.leaderboard-row) {
    background: rgba(255, 255, 255, 0.02) !important;
    transition: all 0.3s ease !important;
  }

  :global(.leaderboard-row:hover) {
    background: rgba(255, 255, 255, 0.05) !important;
    transform: scale(1.005);
  }

  :global(.leaderboard-row td) {
    border: none !important;
    padding: 16px 20px !important;
  }

  :global(.leaderboard-row td:first-child) {
    border-top-left-radius: 12px;
    border-bottom-left-radius: 12px;
  }
  :global(.leaderboard-row td:last-child) {
    border-top-right-radius: 12px;
    border-bottom-right-radius: 12px;
  }

  .moderator-note {
    font-size: 0.75rem;
    font-weight: normal;
    color: #f97316;
    padding: 4px 8px;
    background: rgba(249, 115, 22, 0.05);
    border-radius: 6px;
    display: inline-block;
  }

  .settings-panel {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .form-switch .form-check-input {
    cursor: pointer;
    width: 3em;
    height: 1.5em;
  }

  .form-switch .form-check-input:checked {
    background-color: var(--primary);
    border-color: var(--primary);
  }

  :global(.score-badge) {
    display: inline-block;
    padding: 6px 16px;
    background: rgba(249, 115, 22, 0.1);
    border: 1px solid rgba(249, 115, 22, 0.2);
    border-radius: 10px;
    color: var(--primary);
    font-weight: 800;
    font-size: 0.95rem;
  }

  @media (max-width: 768px) {
    .display-4 {
      font-size: 2.2rem;
    }

    .stats-grid {
      grid-template-columns: 1fr 1fr;
      gap: 10px;
      padding: 0 10px;
    }

    .stat-card h3 {
      font-size: 1.2rem;
    }
    .stat-card span {
      font-size: 0.7rem;
    }

    .record-section {
      padding: 1.5rem !important;
    }

    .record-pill {
      font-size: 0.8rem;
      padding: 6px 12px;
    }
  }
</style>

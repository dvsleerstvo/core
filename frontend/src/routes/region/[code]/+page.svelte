<script lang="ts">
  let { data } = $props();
  const profile = $derived(data.profile);

  let activeTab = $state("records");
</script>

<svelte:head>
  {#if profile}
    <title>{profile.region_name} - ДВ СЛЕЕРСТВО</title>
  {/if}
  <link rel="stylesheet" href="/css/user_profile.css" />
  <link rel="stylesheet" href="/css/statistic.css" />
  <link rel="stylesheet" href="/css/leaderboard.css" />
  <link rel="stylesheet" href="/css/region_profile.css" />
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
          <span
            class="flag flag-{profile.region_code} shadow-lg"
            style="--flag-size: 2rem; border-radius: 4px;"
          ></span>
          <h1
            class="display-4 fw-bold mb-0"
            style="text-shadow: 0 0 30px rgba(249, 115, 22, 0.4);"
          >
            {profile.region_name}
          </h1>
        </div>
        <div
          class="text-uppercase ls-2 opacity-50 fw-bold"
          style="font-size: 0.8rem; letter-spacing: 3px; color: var(--accent);"
        >
          Профиль региона
        </div>
      </div>

      <div class="d-flex flex-wrap justify-content-center gap-4 mb-5">
        {#if Number(profile.score_pc) > 0}
          <div class="stat-card-container">
            <div class="stat-card border-primary border-opacity-10">
              <span>Ранг (ПК)</span>
              <h3 class="fw-800">#{profile.rank_pc}</h3>
            </div>
          </div>
          <div class="stat-card-container">
            <div class="stat-card border-warning border-opacity-10">
              <span>Очки (ПК)</span>
              <h3 style="color: var(--primary) !important;">
                {Number(profile.score_pc).toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
            </div>
          </div>
        {/if}

        {#if Number(profile.score_mobile) > 0}
          <div class="stat-card-container">
            <div class="stat-card border-primary border-opacity-10">
              <span>Ранг (Моб)</span>
              <h3 class="fw-800">#{profile.rank_mobile}</h3>
            </div>
          </div>
          <div class="stat-card-container">
            <div class="stat-card border-warning border-opacity-10">
              <span>Очки (Моб)</span>
              <h3 style="color: var(--primary) !important;">
                {Number(profile.score_mobile).toLocaleString(undefined, {
                  maximumFractionDigits: 2,
                })}
              </h3>
            </div>
          </div>
        {/if}
      </div>

      <ul
        class="nav nav-pills justify-content-center mb-4 gap-3 region-tabs"
        id="regionTabs"
        role="tablist"
      >
        <li class="nav-item">
          <button
            class="nav-link {activeTab === 'records'
              ? 'active'
              : ''} rounded-pill px-4"
            onclick={() => (activeTab = "records")}
          >
            <i class="fas fa-trophy me-2"></i>Рекорды
          </button>
        </li>
        <li class="nav-item">
          <button
            class="nav-link {activeTab === 'players'
              ? 'active'
              : ''} rounded-pill px-4"
            onclick={() => (activeTab = "players")}
          >
            <i class="fas fa-users me-2"></i>Игроки
          </button>
        </li>
      </ul>

      <div class="tab-content">
        {#if activeTab === "records"}
          <div class="row g-4">
            {#if profile.score_pc > 0 || profile.victors_on_pc.length > 0}
              <div
                class="col-12 {profile.score_mobile > 0 ||
                profile.victors_on_mobile.length > 0
                  ? 'col-lg-6'
                  : ''}"
              >
                <div class="record-section p-4 rounded-4 h-100">
                  <h4 class="mb-4 d-flex align-items-center gap-2">
                    <i class="fas fa-desktop" style="color: var(--primary);"
                    ></i>
                    <span>PC Records</span>
                    <span
                      class="ms-auto badge bg-white bg-opacity-10 fw-normal fs-6"
                      >{profile.victors_on_pc.length}</span
                    >
                  </h4>

                  <div class="mb-4">
                    <h6 class="record-subtitle">Пройдено</h6>
                    <div class="d-flex flex-wrap gap-2">
                      {#each profile.victors_on_pc as rec}
                        <a
                          href="/level/{rec.level_detail.level_id}/pc"
                          class="record-pill completed text-decoration-none"
                        >
                          {rec.level_detail.name}
                        </a>
                      {/each}
                    </div>
                  </div>

                  {#if profile.progress_on_pc.length > 0}
                    <div>
                      <h6 class="record-subtitle text-warning">Прогресс</h6>
                      <div class="d-flex flex-wrap gap-2">
                        {#each profile.progress_on_pc as rec}
                          <a
                            href="/level/{rec.level_detail.level_id}/pc"
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

            {#if profile.score_mobile > 0 || profile.victors_on_mobile.length > 0}
              <div
                class="col-12 {profile.score_pc > 0 ||
                profile.victors_on_pc.length > 0
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
                      >{profile.victors_on_mobile.length}</span
                    >
                  </h4>

                  <div class="mb-4">
                    <h6 class="record-subtitle">Пройдено</h6>
                    <div class="d-flex flex-wrap gap-2">
                      {#each profile.victors_on_mobile as rec}
                        <a
                          href="/level/{rec.level_detail.level_id}/mobile"
                          class="record-pill completed text-decoration-none"
                        >
                          {rec.level_detail.name}
                        </a>
                      {/each}
                    </div>
                  </div>

                  {#if profile.progress_on_mobile.length > 0}
                    <div>
                      <h6 class="record-subtitle text-warning">Прогресс</h6>
                      <div class="d-flex flex-wrap gap-2">
                        {#each profile.progress_on_mobile as rec}
                          <a
                            href="/level/{rec.level_detail.level_id}/mobile"
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
        {:else if activeTab === "players"}
          <div class="record-section p-4 rounded-4">
            <div class="table-responsive">
              <table class="table align-middle custom-leaderboard-table mb-0">
                <thead>
                  <tr>
                    <th scope="col" class="text-center" style="width: 80px;"
                      >РАНГ</th
                    >
                    <th scope="col">ИГРОК</th>
                    <th scope="col" class="text-center">ОЧКИ (ПК)</th>
                    <th scope="col" class="text-center">ОЧКИ (МОБ)</th>
                    <th scope="col" class="text-center">СУММА</th>
                  </tr>
                </thead>
                <tbody>
                  {#each profile.players as player}
                    <tr
                      class="leaderboard-row {player.region_rank <= 3
                        ? 'top-player-row'
                        : ''}"
                    >
                      <td class="text-center">
                        <div class="rank-container">
                          {#if player.region_rank === 1}
                            <span class="rank-icon gold">1</span>
                          {:else if player.region_rank === 2}
                            <span class="rank-icon silver">2</span>
                          {:else if player.region_rank === 3}
                            <span class="rank-icon bronze">3</span>
                          {:else}
                            <span class="rank-number"
                              >#{player.region_rank}</span
                            >
                          {/if}
                        </div>
                      </td>
                      <td>
                        <a
                          href="/user/{player.id}"
                          class="player-name-link fw-bold text-white text-decoration-none"
                        >
                          {player.username}
                        </a>
                      </td>
                      <td class="text-center">
                        <div
                          class="score-badge"
                          style="font-size: 0.9rem; padding: 4px 12px; opacity: 0.8;"
                        >
                          {Number(player.score_pc).toFixed(2)}
                        </div>
                      </td>
                      <td class="text-center">
                        <div
                          class="score-badge"
                          style="font-size: 0.9rem; padding: 4px 12px; opacity: 0.8;"
                        >
                          {Number(player.score_mobile).toFixed(2)}
                        </div>
                      </td>
                      <td class="text-center">
                        <div
                          class="score-badge"
                          style="background: rgba(249, 115, 22, 0.2); border-color: rgba(249, 115, 22, 0.5);"
                        >
                          {Number(player.total_score).toFixed(2)}
                        </div>
                      </td>
                    </tr>
                  {:else}
                    <tr>
                      <td colspan="5" class="text-center py-5">
                        <div class="opacity-50">
                          <i class="fas fa-users-slash display-4 mb-3"></i>
                          <p>В этом регионе пока нет игроков</p>
                        </div>
                      </td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          </div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .stat-card-container {
    flex: 0 1 200px;
    min-width: 150px;
  }

  :global(.custom-leaderboard-table) {
    --bs-table-bg: transparent !important;
    border-collapse: separate;
    border-spacing: 0 12px;
    background: transparent !important;
  }

  :global(.leaderboard-row) {
    background: rgba(255, 255, 255, 0.02) !important;
    transition: all 0.3s ease !important;
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
</style>

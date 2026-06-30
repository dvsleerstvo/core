<script lang="ts">
  import { deviceType } from "$lib/stores";
  import { onMount, tick } from "svelte";
  import { browser } from "$app/environment";
  import { API_BASE } from "$lib/api";

  let { data } = $props();

  $effect(() => {
    $deviceType = data.device as "pc" | "mobile";
  });

  const isMobile = $derived(data.device === "mobile");

  let mapVisible = $state(false);
  let mapInitialized = false;
  let L: any;
  let map: any;
  let sidebarTitle: string = $state("Регион");
  let sidebarPlayers: any[] = $state([]);

  const regionNames: Record<string, string> = {
    RB: "Республика Бурятия",
    RSYA: "Республика Саха (Якутия)",
    ZK: "Забайкальский Край",
    KK: "Камчатский Край",
    PK: "Приморский Край",
    KHK: "Хабаровский Край",
    AO: "Амурская Область",
    MO: "Магаданская Область",
    SO: "Сахалинская Область",
    JAO: "Еврейская Автономная Область",
    CHAO: "Чукотский Автономный Округ",
  };

  const isoToInternal: Record<string, string> = {
    "RU-BU": "RB",
    "RU-SA": "RSYA",
    "RU-ZAB": "ZK",
    "RU-KAM": "KK",
    "RU-PRI": "PK",
    "RU-KHA": "KHK",
    "RU-AMU": "AO",
    "RU-MAG": "MO",
    "RU-SAK": "SO",
    "RU-YEV": "JAO",
    "RU-CHU": "CHAO",
  };

  const regionISOToName: Record<string, string> = {
    "RU-BU": "Бурятия",
    "RU-SA": "Якутия",
    "RU-ZAB": "Забайкалье",
    "RU-KAM": "Камчатка",
    "RU-PRI": "Приморье",
    "RU-KHA": "Хабаровск",
    "RU-AMU": "Амурская обл.",
    "RU-MAG": "Магадан",
    "RU-SAK": "Сахалин",
    "RU-YEV": "ЕАО",
    "RU-CHU": "Чукотка",
  };

  let regionData: any = {};

  function processRegionData() {
    regionData = {};
    data.players.forEach((p: any) => {
      if (!p.region) return;
      if (!regionData[p.region])
        regionData[p.region] = { score: 0, cities: {} };
      regionData[p.region].score += parseFloat(
        isMobile ? p.score_mobile : p.score_pc,
      );
      const city = p.city || "Другие города";
      if (!regionData[p.region].cities[city])
        regionData[p.region].cities[city] = [];
      regionData[p.region].cities[city].push(p);
    });
  }

  async function initMap() {
    if (!browser || mapInitialized) return;

    // Ensure Yandex Maps API is loaded
    // @ts-ignore
    if (typeof ymaps === "undefined") {
      console.error("Yandex Maps API not loaded");
      return;
    }

    const leaflet = await import("leaflet");
    L = leaflet.default;

    // Standard icon fix for Leaflet in Vite
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png",
      iconUrl: "https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png",
      shadowUrl:
        "https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png",
    });

    // @ts-ignore - Leaflet.Yandex needs L globally or a specific way to load
    await import("leaflet-plugins/layer/tile/Yandex");

    map = L.map("map-leaflet", { zoomControl: false }).setView([62, 135], 4);
    L.control.zoom({ position: "bottomright" }).addTo(map);

    // @ts-ignore
    const yandexLayer = new L.Yandex("map");
    yandexLayer.addTo(map);

    processRegionData();

    try {
      const res = await fetch("/data/regions_small.geojson");
      const geoData = await res.json();

      L.geoJSON(geoData, {
        filter: (f: any) =>
          isoToInternal[f.properties["iso3166-2"] || f.properties["ref"]],
        style: {
          fillColor: "#f97316",
          weight: 1.5,
          opacity: 0.8,
          color: "#fff",
          fillOpacity: 0.1,
        },
        onEachFeature: (feature: any, layer: any) => {
          layer.on({
            mouseover: () =>
              layer.setStyle({ weight: 3, color: "#f97316", fillOpacity: 0.2 }),
            mouseout: () =>
              layer.setStyle({ weight: 1.5, color: "#fff", fillOpacity: 0.1 }),
            click: (e: any) => {
              L.DomEvent.stopPropagation(e);
              const iso =
                feature.properties["iso3166-2"] || feature.properties["ref"];
              const internalCode = isoToInternal[iso];
              const name =
                regionISOToName[iso] || feature.properties.name || "Регион";
              showSidebar(internalCode, regionNames[internalCode] || name);
            },
          });
        },
      }).addTo(map);
    } catch (e) {
      console.error("Failed to load GeoJSON", e);
    }

    mapInitialized = true;
    map.invalidateSize();
  }

  function showSidebar(code: string, title: string) {
    sidebarTitle = title;
    const rData = regionData[code];
    if (!rData) {
      sidebarPlayers = [];
    } else {
      const players: any[] = [];
      Object.entries(rData.cities).forEach(
        ([city, cityPlayers]: [string, any]) => {
          players.push({
            city,
            players: [...cityPlayers].sort((a: any, b: any) =>
              isMobile
                ? Number(b.score_mobile) - Number(a.score_mobile)
                : Number(b.score_pc) - Number(a.score_pc),
            ),
          });
        },
      );
      sidebarPlayers = players;
    }
    document.getElementById("map-sidebar")?.classList.add("active");
  }

  async function toggleMap() {
    mapVisible = !mapVisible;
    if (mapVisible) {
      await tick();
      setTimeout(initMap, 200);
    }
  }
</script>

<svelte:head>
  <title>Таблица лидеров - ДВ СЛЕЕРСТВО</title>
  <link
    rel="stylesheet"
    href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
  />
  <link rel="stylesheet" href="/css/table.css" />
  <link rel="stylesheet" href="/css/leaderboard.css" />
  <link rel="stylesheet" href="/css/search.css" />
  <!-- Яндекс Карты API ОБЯЗАТЕЛЬНО -->
  <script
    src="https://api-maps.yandex.ru/2.1/?lang=ru_RU"
    type="text/javascript"
  ></script>
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
        {isMobile ? "Топ Игроков (Mobile)" : "Топ Игроков (PC)"}
      </h1>

      <div class="text-center mb-3">
        <button
          onclick={toggleMap}
          class="btn btn-sm btn-outline-warning"
          style="border-radius: 20px;"
        >
          <i
            class="fas {mapVisible ? 'fa-eye-slash' : 'fa-map-marked-alt'} me-2"
          ></i>
          {mapVisible ? "Скрыть карту" : "Показать карту"}
        </button>
      </div>
    </div>

    <div
      class="map-animation-wrapper {mapVisible
        ? 'map-expanded'
        : 'map-collapsed'}"
    >
      <div
        class="map-wrapper mb-5"
        style="height: 700px; background: #000; border-radius: 24px; overflow: hidden; position: relative; border: 1px solid rgba(255,255,255,0.08);"
      >
        <div id="map-sidebar" class="map-sidebar">
          <div class="sidebar-header">
            <h5 class="mb-0 fw-bold text-truncate text-white">
              {sidebarTitle}
            </h5>
            <button
              class="btn btn-link text-light p-0"
              onclick={() =>
                document
                  .getElementById("map-sidebar")
                  ?.classList.remove("active")}
            >
              <i class="fas fa-times"></i>
            </button>
          </div>
          <div class="sidebar-content">
            {#each sidebarPlayers as group}
              <div class="city-header-mini">{group.city}</div>
              {#each group.players as p}
                <a href="/user/{p.id}" class="player-card">
                  <img
                    src="/img/icons/{encodeURIComponent(p.username)}.png"
                    class="player-icon-mini"
                    onerror={(e) =>
                      (e.currentTarget.src =
                        "https://gdbrowser.com/iconkit/premade/cube_1.png")}
                    alt={p.username}
                  />
                  <div class="player-info-mini">
                    <span class="player-name-mini text-white">{p.username}</span
                    >
                    <span class="player-score-mini">
                      {Number(isMobile ? p.score_mobile : p.score_pc).toFixed(
                        2,
                      )} pts
                    </span>
                  </div>
                </a>
              {/each}
            {/each}
          </div>
        </div>
        <div id="map-leaflet" style="width: 100%; height: 100%;"></div>
      </div>
    </div>

    <!-- Таблица и поиск остаются ниже... -->
    <div class="row mb-5 justify-content-center">
      <div class="col-md-6 col-lg-5">
        <form method="GET" action="/leaderboard/{data.device}">
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
              placeholder="Поиск игрока..."
              style="background: transparent;"
            />
            {#if data.searchQuery}
              <a
                href="/leaderboard/{data.device}"
                class="btn btn-outline-secondary border-0 d-flex align-items-center justify-content-center"
                style="width: 40px; background: rgba(255, 255, 255, 0.1);"
              >
                <i class="fas fa-times text-light"></i>
              </a>
            {/if}
            <button type="submit" class="btn btn-primary px-4">Искать</button>
          </div>
        </form>
      </div>
    </div>

    <div class="table-responsive">
      <table class="table table-dark align-middle custom-leaderboard-table">
        <thead>
          <tr>
            <th scope="col" class="text-center" style="width: 80px;">РАНГ</th>
            <th scope="col">
              <a
                href="/leaderboard/{data.device}?sort=username&order={data.sortBy ===
                  'username' && data.order === 'asc'
                  ? 'desc'
                  : 'asc'}{data.searchQuery ? '&q=' + data.searchQuery : ''}"
                class="text-decoration-none sortable-header"
              >
                ИГРОК
                {#if data.sortBy === "username"}
                  <i
                    class="fas fa-sort-{data.order === 'asc'
                      ? 'up'
                      : 'down'} ms-1 text-primary"
                  ></i>
                {:else}
                  <i class="fas fa-sort ms-1 opacity-25"></i>
                {/if}
              </a>
            </th>
            <th scope="col" class="text-center">
              <a
                href="/leaderboard/{data.device}?sort=score&order={data.sortBy ===
                  'score' && data.order === 'desc'
                  ? 'asc'
                  : 'desc'}{data.searchQuery ? '&q=' + data.searchQuery : ''}"
                class="text-decoration-none sortable-header"
              >
                ОЧКИ
                {#if data.sortBy === "score"}
                  <i
                    class="fas fa-sort-{data.order === 'asc'
                      ? 'up'
                      : 'down'} ms-1 text-primary"
                  ></i>
                {:else}
                  <i class="fas fa-sort ms-1 opacity-25"></i>
                {/if}
              </a>
            </th>
            <th scope="col" class="d-none d-md-table-cell text-end">
              <a
                href="/leaderboard/{data.device}?sort=hardest&order={data.sortBy ===
                  'hardest' && data.order === 'asc'
                  ? 'desc'
                  : 'asc'}{data.searchQuery ? '&q=' + data.searchQuery : ''}"
                class="text-decoration-none sortable-header"
              >
                ХАРДЕСТ
                {#if data.sortBy === "hardest"}
                  <i
                    class="fas fa-sort-{data.order === 'asc'
                      ? 'up'
                      : 'down'} ms-1 text-primary"
                  ></i>
                {:else}
                  <i class="fas fa-sort ms-1 opacity-25"></i>
                {/if}
              </a>
            </th>
          </tr>
        </thead>
        <tbody>
          {#each data.players as player}
            <tr
              class="leaderboard-row {player.rank <= 3 ? 'top-player-row' : ''}"
            >
              <td class="text-center">
                <div class="rank-container">
                  {#if player.rank === 1}
                    <span class="rank-icon gold">1</span>
                  {:else if player.rank === 2}
                    <span class="rank-icon silver">2</span>
                  {:else if player.rank === 3}
                    <span class="rank-icon bronze">3</span>
                  {:else}
                    <span class="rank-number">#{player.rank}</span>
                  {/if}
                </div>
              </td>
              <td>
                <div class="d-flex align-items-center gap-3">
                  <span
                    class="flag flag-{player.region} shadow-sm"
                    style="--flag-size: 1.2rem; border-radius: 3px;"
                  ></span>
                  <a href="/user/{player.id}" class="player-name-link fw-bold">
                    {player.username}
                  </a>
                </div>
              </td>
              <td class="text-center">
                <div class="score-badge">
                  {Number(
                    isMobile ? player.score_mobile : player.score_pc,
                  ).toLocaleString(undefined, {
                    minimumFractionDigits: 0,
                    maximumFractionDigits: 2,
                  })}
                </div>
              </td>
              <td class="d-none d-md-table-cell text-end">
                <div class="hardest-level-text">
                  {(isMobile
                    ? player.hardest_mobile_name
                    : player.hardest_pc_name) || "—"}
                </div>
              </td>
            </tr>
          {:else}
            <tr>
              <td colspan="4" class="text-center py-5">
                <div class="opacity-25">
                  <i class="fas fa-users-slash display-4 mb-3"></i>
                  <p>Игроки не найдены</p>
                </div>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>
</div>

<style>
  :root {
    --map-primary: #f97316;
    --map-primary-glow: rgba(249, 115, 22, 0.4);
    --map-card-bg: rgba(25, 25, 25, 0.6);
    --map-sidebar-bg: rgba(10, 10, 10, 0.95);
    --map-glass: rgba(15, 15, 15, 0.85);
    --map-border: rgba(255, 255, 255, 0.08);
  }

  .map-animation-wrapper {
    max-height: 0;
    opacity: 0;
    overflow: hidden;
    transition: all 0.5s ease-in-out;
  }
  .map-expanded {
    max-height: 800px;
    opacity: 1;
    margin-bottom: 2rem;
  }

  .map-sidebar {
    position: absolute;
    top: 20px;
    right: -400px;
    bottom: 20px;
    width: 350px;
    background: var(--map-sidebar-bg);
    z-index: 1001;
    border-radius: 24px;
    border: 1px solid var(--map-border);
    backdrop-filter: blur(20px);
    transition: all 0.5s cubic-bezier(0.16, 1, 0.3, 1);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: -20px 0 50px rgba(0, 0, 0, 0.7);
  }
  :global(.map-sidebar.active) {
    right: 20px;
  }

  .sidebar-header {
    padding: 24px;
    border-bottom: 1px solid var(--map-border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  .sidebar-content {
    flex: 1;
    overflow-y: auto;
    padding: 20px;
  }

  .player-card {
    background: var(--map-card-bg);
    border-radius: 12px;
    padding: 10px;
    margin-bottom: 8px;
    display: flex;
    align-items: center;
    gap: 12px;
    border: 1px solid rgba(255, 255, 255, 0.03);
    text-decoration: none;
    color: white;
    transition: 0.2s;
    cursor: pointer;
  }
  .player-card:hover {
    transform: translateX(5px);
    background: rgba(255, 255, 255, 0.05);
    border-color: var(--map-primary);
  }

  .player-info-mini {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
  }
  .player-name-mini {
    font-weight: 700;
    display: block;
    font-size: 1.05rem;
    margin-bottom: 2px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }
  .player-score-mini {
    color: var(--map-primary);
    font-weight: 700;
    font-size: 0.85rem;
  }
  .player-icon-mini {
    width: 36px;
    height: 36px;
    border-radius: 10px;
    object-fit: contain;
    background: #000;
    border: 1px solid rgba(255, 255, 255, 0.05);
    padding: 4px;
  }

  .city-header-mini {
    font-size: 0.75rem;
    font-weight: 800;
    text-transform: uppercase;
    color: var(--map-primary);
    margin: 25px 0 10px 0;
    display: flex;
    align-items: center;
    gap: 10px;
  }
  .city-header-mini::after {
    content: "";
    flex: 1;
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
  }

  @media (max-width: 768px) {
    .display-5 {
      font-size: 1.8rem;
    }

    :global(.custom-leaderboard-table) {
      font-size: 0.85rem;
    }

    :global(.leaderboard-row td) {
      padding: 12px 10px !important;
    }

    .score-badge {
      padding: 4px 10px;
      font-size: 0.8rem;
    }

    .rank-icon {
      width: 24px;
      height: 24px;
      font-size: 0.8rem;
    }

    .map-expanded {
      max-height: 400px;
    }
    .map-wrapper {
      height: 400px !important;
    }

    .map-sidebar {
      width: 100%;
      right: -100%;
      top: 0;
      bottom: 0;
      border-radius: 0;
    }
    :global(.map-sidebar.active) {
      right: 0;
    }
  }
</style>

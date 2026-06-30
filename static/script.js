document.addEventListener('DOMContentLoaded', function() {
    const rawData = document.getElementById('players-data')?.textContent;
    const mapLeafletEl = document.getElementById('map-leaflet');
    
    // Если мы на странице лидерборда с новой картой, не запускаем старый скрипт
    if (document.getElementById('layers-toggle-btn')) {
        return;
    }

    if (!rawData || !mapLeafletEl) return;

    const players = JSON.parse(rawData);
    const toggleMapBtn = document.getElementById('toggle-map-btn');
    const mapAnimWrapper = document.getElementById('map-animation-wrapper');
    const sidebar = document.getElementById('map-sidebar');
    const sidebarTitle = document.getElementById('sidebar-title');
    const sidebarContent = document.getElementById('sidebar-content');
    const closeSidebarBtn = document.getElementById('close-sidebar');

    const regionNames = {
        'RU-BU': 'Республика Бурятия', 'RU-SA': 'Республика Саха (Якутия)', 'RU-ZAB': 'Забайкальский Край',
        'RU-KAM': 'Камчатский Край', 'RU-PRI': 'Приморский Край', 'RU-KHA': 'Хабаровский Край',
        'RU-AMU': 'Амурская Область', 'RU-MAG': 'Магаданская Область', 'RU-SAK': 'Сахалинская Область',
        'RU-YEV': 'Еврейская Автономная Область', 'RU-CHU': 'Чукотский Автономный Округ'
    };

    const isoToInternal = {
        'RU-BU': 'RB', 'RU-SA': 'RSYA', 'RU-ZAB': 'ZK',
        'RU-KAM': 'KK', 'RU-PRI': 'PK', 'RU-KHA': 'KHK',
        'RU-AMU': 'AO', 'RU-MAG': 'MO', 'RU-SAK': 'SO',
        'RU-YEV': 'JAO', 'RU-CHU': 'CHAO'
    };

    const regionData = {};
    players.forEach(p => {
        if (!p.region) return;
        if (!regionData[p.region]) regionData[p.region] = { score: 0, cities: {} };
        regionData[p.region].score += parseFloat(p.score);
        const cityName = p.city || "Другие города";
        if (!regionData[p.region].cities[cityName]) regionData[p.region].cities[cityName] = [];
        regionData[p.region].cities[cityName].push(p);
    });

    const maxScore = Math.max(...Object.values(regionData).map(d => d.score), 1);

    function getIconUrl(player) {
        return `/static/img/icons/${encodeURIComponent(player.username)}.png`;
    }
    const fallbackIcon = "https://gdbrowser.com/iconkit/premade/cube_1.png";

    const map = L.map('map-leaflet', {
        zoomSnap: 0.1,
        attributionControl: false,
        zoomControl: true,
        backgroundColor: '#111'
    }).setView([62, 135], 3);

    // Создаем отдельный слой для городов, который всегда выше регионов
    map.createPane('citiesPane');
    map.getPane('citiesPane').style.zIndex = 650;

    let geojsonLayer;
    let citiesLayer = L.layerGroup().addTo(map);

    function style(feature) {
        const isoCode = feature.properties['iso3166-2'] || feature.properties['ISO3166-2'] || feature.properties['ref'] || feature.properties['iso_code'];
        const internalCode = isoToInternal[isoCode];
        const data = regionData[internalCode] || { score: 0 };
        
        return {
            fillColor: '#f97316',
            weight: 1,
            opacity: 1,
            color: 'rgba(255,255,255,0.1)',
            fillOpacity: data.score > 0 ? 0.1 + (0.8 * (data.score / maxScore)) : 0.03
        };
    }

    function onEachFeature(feature, layer) {
        const isoCode = feature.properties['iso3166-2'] || feature.properties['ISO3166-2'] || feature.properties['ref'] || feature.properties['iso_code'];
        const internalCode = isoToInternal[isoCode];
        const name = regionNames[isoCode] || feature.properties.name || "Неизвестный регион";
        const data = regionData[internalCode] || { score: 0 };

        layer.on({
            mouseover: function(e) {
                const layer = e.target;
                layer.setStyle({
                    weight: 2,
                    color: '#f97316',
                    fillOpacity: data.score > 0 ? 0.9 : 0.2
                });
            },
            mouseout: function(e) {
                geojsonLayer.resetStyle(e.target);
            },
            click: function(e) {
                const isMobile = window.innerWidth <= 992;
                const paddingRight = isMobile ? 20 : 400;
                const bounds = e.target.getBounds();
                
                if (Math.abs(bounds.getEast() - bounds.getWest()) > 180) {
                    map.setView(bounds.getCenter(), isMobile ? 4 : 5);
                } else {
                    map.fitBounds(bounds, { 
                        paddingTopLeft: [20, 20],
                        paddingBottomRight: [paddingRight, 20],
                        maxZoom: 7,
                        animate: true
                    });
                }
                showSidebar(internalCode, name);
            }
        });

        layer.bindTooltip(`
            <div class="text-center">
                <div class="fw-bold" style="color: #f97316">${name}</div>
                <div class="small opacity-75">${data.score.toFixed(2)} очков</div>
            </div>
        `, { sticky: true, className: 'map-tooltip-custom' });
    }

    fetch('/static/regions_small.geojson')
        .then(response => response.json())
        .then(data => {
            const regionFeatures = data.features.filter(f => {
                const iso = f.properties['iso3166-2'] || f.properties['ISO3166-2'] || f.properties['ref'] || f.properties['iso_code'];
                const internalCode = isoToInternal[iso];
                const isPolygon = f.geometry.type === 'Polygon' || f.geometry.type === 'MultiPolygon';
                return internalCode && isPolygon && regionData[internalCode];
            });

            let cityFeatures = data.features.filter(f => {
                if (f.geometry.type !== 'Point' || !f.properties.place) return false;
                const regionIso = f.properties.region_iso;
                const internalCode = isoToInternal[regionIso];
                return internalCode && regionData[internalCode];
            });

            geojsonLayer = L.geoJSON({ type: "FeatureCollection", features: regionFeatures }, {
                style: style,
                onEachFeature: onEachFeature
            }).addTo(map);

            function updateCities() {
                citiesLayer.clearLayers();
                
                cityFeatures.forEach(city => {
                    const cityName = city.properties.name;
                    const regionIso = city.properties.region_iso;
                    const internalCode = isoToInternal[regionIso];
                    const cityPlayers = regionData[internalCode]?.cities[cityName] || [];
                    const cityScore = cityPlayers.reduce((sum, p) => sum + parseFloat(p.score), 0);

                    if (cityScore > 0) {
                        const marker = L.circleMarker([city.geometry.coordinates[1], city.geometry.coordinates[0]], {
                            radius: 10 + Math.min(cityScore / 5, 15),
                            fillColor: '#f97316',
                            color: '#fff',
                            weight: 2,
                            opacity: 1,
                            fillOpacity: 0.9,
                            className: 'city-marker',
                            pane: 'citiesPane'
                        });

                        marker.bindTooltip(`
                            <div class="city-tooltip-content">
                                <div class="fw-bold">${cityName}</div>
                                <div class="small text-warning">${cityScore.toFixed(2)} pts</div>
                            </div>
                        `, { 
                            permanent: true, 
                            direction: 'top',
                            offset: [0, -30],
                            className: 'city-label-active'
                        });

                        marker.on('click', (e) => {
                            L.DomEvent.stopPropagation(e);
                            showSidebar(internalCode, cityName, cityName);
                        });

                        citiesLayer.addLayer(marker);
                    }
                });
            }

            map.on('zoomend', updateCities);
            updateCities();

            if (regionFeatures.length > 0) {
                const totalBounds = geojsonLayer.getBounds();
                if (Math.abs(totalBounds.getEast() - totalBounds.getWest()) > 180) {
                    map.setView([65, 150], 3);
                } else {
                    map.fitBounds(totalBounds, { padding: [30, 30] });
                }
            }
        })
        .catch(err => console.error("Ошибка загрузки GeoJSON:", err));

    function showSidebar(regionCode, title, filterCity = null) {
        const data = regionData[regionCode];
        sidebarTitle.textContent = title;
        sidebarContent.innerHTML = '';
        
        if (!data || Object.keys(data.cities).length === 0) {
            sidebarContent.innerHTML = '<div class="text-center opacity-50 my-5">Нет игроков</div>';
        } else {
            const citiesToDisplay = filterCity ? [filterCity] : Object.keys(data.cities);
            
            const otherCityName = "Другие города";
            const sortedCities = citiesToDisplay.filter(c => c !== otherCityName).sort((a, b) => {
                const sA = (data.cities[a] || []).reduce((sum, p) => sum + p.score, 0);
                const sB = (data.cities[b] || []).reduce((sum, p) => sum + p.score, 0);
                return sB - sA;
            });
            if (data.cities[otherCityName] && (!filterCity || filterCity === otherCityName)) sortedCities.push(otherCityName);

            sortedCities.forEach(city => {
                if (!data.cities[city]) return;
                
                const section = document.createElement('div');
                section.className = 'city-header';
                section.innerHTML = `<div class="d-flex align-items-center gap-2"><span class="text-uppercase fw-bold" style="font-size: 0.7rem; letter-spacing: 1px;">${city}</span></div>`;
                sidebarContent.appendChild(section);

                data.cities[city].sort((a, b) => b.score - a.score).forEach(player => {
                    const card = document.createElement('a');
                    card.href = `/user/${player.id}`;
                    card.className = 'sidebar-player-card text-decoration-none text-light';
                    card.innerHTML = `
                        <div class="position-relative">
                            <img src="${getIconUrl(player)}" 
                                 onerror="this.src='${fallbackIcon}'; this.onerror=null;"
                                 class="sidebar-player-icon" 
                                 alt="icon" 
                                 style="min-width: 44px; min-height: 44px;">
                            ${player.is_online ? '<span class="position-absolute bottom-0 end-0 bg-success border border-dark rounded-circle" style="width: 10px; height: 10px; box-shadow: 0 0 5px #198754;"></span>' : ''}
                        </div>
                        <div class="sidebar-player-info">
                            <span class="sidebar-player-name">${player.username}</span>
                            <div class="sidebar-player-stats"><div class="score-line">${player.score.toFixed(2)} pts</div><div class="hardest-line">${player.hardest}</div></div>
                        </div>
                        <div class="rank-badge">#${player.rank}</div>
                    `;
                    sidebarContent.appendChild(card);
                });
            });
        }
        sidebar.classList.add('active');
    }

    if (closeSidebarBtn) {
        closeSidebarBtn.addEventListener('click', () => {
            sidebar.classList.remove('active');
        });
    }

    if (toggleMapBtn && mapAnimWrapper) {
        toggleMapBtn.addEventListener('click', function() {
            mapAnimWrapper.classList.toggle('map-collapsed');
            const isHidden = mapAnimWrapper.classList.contains('map-collapsed');
            toggleMapBtn.innerHTML = isHidden ? '<i class="fas fa-eye me-2"></i>Показать карту' : '<i class="fas fa-eye-slash me-2"></i>Скрыть карту';
            if (!isHidden) {
                setTimeout(() => map.invalidateSize(), 300);
            }
        });
    }
});

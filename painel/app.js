/**
 * AgroCloud — Lógica do Painel de Telemetria
 * Projeto: Cloud para Telemetria de Tratores — Fatec Bebedouro
 *
 * Integração com AWS DynamoDB via SDK JavaScript.
 * Lê a tabela "TelemetriaTratores" com Scan e atualiza os gráficos/tabelas.
 *
 * Estrutura de dados esperada (gerada por enviar_telemetria.py):
 *   {
 *     id_trator  : "TRATOR-001",          // Partition Key
 *     timestamp  : "2025-06-10T14:32:08Z", // Sort Key
 *     motor      : { temperatura_celsius, rpm, pressao_oleo_bar, nivel_combustivel_pct },
 *     gps        : { latitude, longitude, altitude_metros, velocidade_kmh },
 *     ambiente   : { temperatura_externa_celsius, umidade_relativa_pct },
 *     status_operacional: "trabalhando" | "em_transito" | "parado"
 *   }
 *
 * MODO DEMO: Se o DynamoDB não estiver acessível, o painel usa dados simulados
 * realistas para apresentação. Isso acontece automaticamente.
 */

// ── Gerador de dados de demonstração ─────────────────────────────────────────
function rnd(min, max, dec = 2) {
    return parseFloat((Math.random() * (max - min) + min).toFixed(dec));
}

function gerarRegistroDemo(idTrator, offsetMinutos = 0) {
    const ts = new Date(Date.now() - offsetMinutos * 60000).toISOString();
    const statusOpts = ['trabalhando', 'trabalhando', 'trabalhando', 'em_transito', 'parado'];
    return {
        id_trator: idTrator,
        timestamp: ts,
        motor: {
            temperatura_celsius:    rnd(82, 108),
            rpm:                    Math.floor(rnd(1300, 2500, 0)),
            pressao_oleo_bar:       rnd(2.8, 4.9),
            nivel_combustivel_pct:  rnd(22, 95, 1),
        },
        gps: {
            latitude:           rnd(-21.00, -20.90, 6),
            longitude:          rnd(-48.60, -48.50, 6),
            altitude_metros:    rnd(485, 515, 1),
            velocidade_kmh:     rnd(0, 18, 1),
        },
        ambiente: {
            temperatura_externa_celsius: rnd(20, 36, 1),
            umidade_relativa_pct:        rnd(42, 88, 1),
        },
        status_operacional: statusOpts[Math.floor(Math.random() * statusOpts.length)],
        id_registro: crypto.randomUUID ? crypto.randomUUID() : Math.random().toString(36),
    };
}

function gerarDadosDemo() {
    const cache = { 'TRATOR-001': [], 'TRATOR-002': [], 'TRATOR-003': [] };
    const tratores = ['TRATOR-001', 'TRATOR-002', 'TRATOR-003'];
    // Gerar 20 leituras históricas por trator (últimas 2 horas)
    tratores.forEach(t => {
        for (let i = 19; i >= 0; i--) {
            cache[t].push(gerarRegistroDemo(t, i * 6));  // a cada 6 min
        }
    });
    return cache;
}

// ── Configuração ──────────────────────────────────────────────────────────────
const CONFIG      = window.AWS_CONFIG;
const TRATORES    = CONFIG.tratores;
const TABLE_NAME  = CONFIG.tableName;
const REFRESH_MS  = CONFIG.refreshInterval;

// ── Elementos DOM ──────────────────────────────────────────────────────────────
const statusEl     = document.getElementById('aws-status');
const statusDot    = document.getElementById('status-dot');
const lastUpdateEl = document.getElementById('last-update');
const tempValueEl  = document.getElementById('temp-value');
const rpmValueEl   = document.getElementById('rpm-value');
const ativosEl     = document.getElementById('ativos-value');
const fuelValueEl  = document.getElementById('fuel-value');

// Cache de todos os dados recebidos do DynamoDB, agrupados por trator
const dadosCache = { 'TRATOR-001': [], 'TRATOR-002': [], 'TRATOR-003': [] };

// ── Inicialização do AWS SDK ───────────────────────────────────────────────────
function initAWS() {
    AWS.config.update({
        accessKeyId:     CONFIG.accessKeyId,
        secretAccessKey: CONFIG.secretAccessKey,
        region:          CONFIG.region,
    });
    return new AWS.DynamoDB.DocumentClient();
}

const docClient = initAWS();

// ── Configuração padrão dos gráficos Chart.js ─────────────────────────────────
Chart.defaults.color        = '#6b7280';
Chart.defaults.font.family  = 'Inter';

const CHART_COLORS = {
    'TRATOR-001': { border: '#16a34a', background: 'rgba(22,163,74,0.12)'  },
    'TRATOR-002': { border: '#0284c7', background: 'rgba(2,132,199,0.12)'   },
    'TRATOR-003': { border: '#d97706', background: 'rgba(217,119,6,0.12)'  },
};

const commonOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
        legend: { display: false },
        tooltip: {
            backgroundColor: 'rgba(17,24,39,0.92)',
            padding: 10,
            cornerRadius: 8,
            titleFont: { size: 13, weight: '600' },
            bodyFont:  { size: 13 },
        }
    },
    animation: { duration: 400 },
};

// ── Inicializar gráficos ───────────────────────────────────────────────────────
function criarGrafico(canvasId, cor, yOptions = {}) {
    const ctx = document.getElementById(canvasId).getContext('2d');
    return new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                data: [],
                borderColor:     cor.border,
                backgroundColor: cor.background,
                borderWidth: 2.5,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: '#ffffff',
                pointBorderColor:     cor.border,
                pointRadius: 3,
                pointHoverRadius: 6,
            }]
        },
        options: {
            ...commonOptions,
            scales: {
                y: { ...yOptions, grid: { color: '#f3f4f6' } },
                x: { grid: { display: false }, ticks: { maxTicksLimit: 10 } }
            }
        }
    });
}

const tempChart = criarGrafico('tempChart', CHART_COLORS['TRATOR-001'], { suggestedMin: 78, suggestedMax: 115 });
const rpmChart  = criarGrafico('rpmChart',  CHART_COLORS['TRATOR-002'], { suggestedMin: 1000, suggestedMax: 2800 });
const fuelChart = criarGrafico('fuelChart', CHART_COLORS['TRATOR-003'], { suggestedMin: 0, suggestedMax: 100 });

// GPS: Scatter Plot com 3 datasets (um por trator)
const gpsChart = new Chart(document.getElementById('gpsChart').getContext('2d'), {
    type: 'scatter',
    data: {
        datasets: TRATORES.map(t => ({
            label: t,
            data: [],
            backgroundColor: CHART_COLORS[t].border,
            borderColor:     CHART_COLORS[t].border,
            pointRadius: 6,
            pointHoverRadius: 9,
        }))
    },
    options: {
        ...commonOptions,
        plugins: { ...commonOptions.plugins, legend: { display: true } },
        scales: {
            x: { title: { display: true, text: 'Longitude' } },
            y: { title: { display: true, text: 'Latitude'  } },
        }
    }
});

// ── Atualizar gráficos com filtro de trator ───────────────────────────────────
function atualizarGrafico(chart, idTrator, campo) {
    const itens = (dadosCache[idTrator] || []).slice(-20);
    if (itens.length === 0) return;

    const labels = itens.map(i => new Date(i.timestamp).toLocaleTimeString('pt-BR'));
    chart.data.labels               = labels;
    chart.data.datasets[0].data    = itens.map(campo);
    chart.data.datasets[0].borderColor     = CHART_COLORS[idTrator].border;
    chart.data.datasets[0].backgroundColor = CHART_COLORS[idTrator].background;
    chart.update();
}

function atualizarGraficoGPS() {
    TRATORES.forEach((t, idx) => {
        const itens = (dadosCache[t] || []).slice(-30);
        gpsChart.data.datasets[idx].data = itens.map(i => ({
            x: parseFloat(i.gps.longitude),
            y: parseFloat(i.gps.latitude),
        }));
    });
    gpsChart.update();
}

// ── Atualizar KPI Cards do Painel Geral ──────────────────────────────────────
function atualizarKPIs() {
    const ultimosPorTrator = TRATORES.map(t => {
        const lista = dadosCache[t];
        return lista.length ? lista[lista.length - 1] : null;
    }).filter(Boolean);

    if (ultimosPorTrator.length === 0) return;

    const temps = ultimosPorTrator.map(d => parseFloat(d.motor.temperatura_celsius));
    const rpms  = ultimosPorTrator.map(d => d.motor.rpm);
    const fuels = ultimosPorTrator.map(d => parseFloat(d.motor.nivel_combustivel_pct));

    const tempMax  = Math.max(...temps).toFixed(1);
    const rpmMedio = Math.round(rpms.reduce((a,b)=>a+b,0) / rpms.length);
    const fuelMin  = Math.min(...fuels).toFixed(1);
    const ativos   = ultimosPorTrator.filter(d => d.status_operacional === 'trabalhando').length;

    tempValueEl.textContent  = `${tempMax} °C`;
    rpmValueEl.textContent   = `${rpmMedio.toLocaleString('pt-BR')} RPM`;
    ativosEl.textContent     = `${ativos} / 3`;
    fuelValueEl.textContent  = `${fuelMin}%`;

    // Alerta visual de combustível baixo
    if (parseFloat(fuelMin) < 25) {
        fuelValueEl.style.color = '#dc2626';
    } else {
        fuelValueEl.style.color = '';
    }

    // Alerta visual de temperatura alta
    if (parseFloat(tempMax) > 105) {
        tempValueEl.style.color = '#dc2626';
    } else {
        tempValueEl.style.color = '';
    }
}

// ── Atualizar Tabela de Frota ──────────────────────────────────────────────────
function atualizarTabelaFrota() {
    const tbody = document.getElementById('tabela-tratores');
    const linhas = TRATORES.map(t => {
        const lista = dadosCache[t];
        if (!lista || lista.length === 0) {
            return `<tr><td colspan="9" style="text-align:center;color:#9ca3af;">${t} — aguardando dados...</td></tr>`;
        }
        const d = lista[lista.length - 1];
        const hora = new Date(d.timestamp).toLocaleTimeString('pt-BR');
        const temp = parseFloat(d.motor.temperatura_celsius).toFixed(1);
        const rpm  = parseInt(d.motor.rpm).toLocaleString('pt-BR');
        const fuel = parseFloat(d.motor.nivel_combustivel_pct).toFixed(1);
        const lat  = parseFloat(d.gps.latitude).toFixed(5);
        const lng  = parseFloat(d.gps.longitude).toFixed(5);
        const vel  = parseFloat(d.gps.velocidade_kmh).toFixed(1);
        const statusClass = d.status_operacional.replace(' ', '_');
        const statusLabel = {
            trabalhando: 'Trabalhando',
            em_transito: 'Em Trânsito',
            parado:      'Parado',
        }[d.status_operacional] || d.status_operacional;

        const tempColor = parseFloat(temp) > 105 ? 'color:#dc2626;font-weight:700;' : '';
        const fuelColor = parseFloat(fuel) < 25  ? 'color:#dc2626;font-weight:700;' : '';

        return `
            <tr>
                <td><strong>${t}</strong></td>
                <td>${hora}</td>
                <td style="${tempColor}">${temp} °C</td>
                <td>${rpm}</td>
                <td style="${fuelColor}">${fuel}%</td>
                <td>${lat}</td>
                <td>${lng}</td>
                <td>${vel}</td>
                <td><span class="status-badge ${d.status_operacional}">${statusLabel}</span></td>
            </tr>`;
    });

    tbody.innerHTML = linhas.join('');

    // Atualizar cards individuais
    const frota = document.getElementById('frota-cards');
    frota.innerHTML = TRATORES.map(t => {
        const lista = dadosCache[t];
        if (!lista || lista.length === 0) return '';
        const d = lista[lista.length - 1];
        const statusLabel = { trabalhando: 'Trabalhando', em_transito: 'Em Trânsito', parado: 'Parado' }[d.status_operacional] || d.status_operacional;
        return `
            <div class="frota-card">
                <div class="frota-card-header">
                    <strong>🚜 ${t}</strong>
                    <span class="status-badge ${d.status_operacional}">${statusLabel}</span>
                </div>
                <div class="frota-card-metrics">
                    <div class="frota-metric">
                        <span class="label">🌡️ Temperatura</span>
                        <span class="value">${parseFloat(d.motor.temperatura_celsius).toFixed(1)} °C</span>
                    </div>
                    <div class="frota-metric">
                        <span class="label">⚙️ RPM</span>
                        <span class="value">${parseInt(d.motor.rpm).toLocaleString('pt-BR')}</span>
                    </div>
                    <div class="frota-metric">
                        <span class="label">⛽ Combustível</span>
                        <span class="value">${parseFloat(d.motor.nivel_combustivel_pct).toFixed(1)}%</span>
                    </div>
                    <div class="frota-metric">
                        <span class="label">🏎️ Velocidade</span>
                        <span class="value">${parseFloat(d.gps.velocidade_kmh).toFixed(1)} km/h</span>
                    </div>
                </div>
            </div>`;
    }).join('');
}

// ── Buscar dados do DynamoDB (com fallback para modo demo) ───────────────────
let modoDemo = false;

function processarDados(items) {
    // Agrupar e ordenar por trator/timestamp
    items.forEach(item => {
        if (item.motor && dadosCache[item.id_trator] !== undefined) {
            const cacheTrator = dadosCache[item.id_trator];
            // Verifica se este registro já foi adicionado
            const jaExiste = cacheTrator.some(i => i.id_registro === item.id_registro);
            if (!jaExiste) {
                cacheTrator.push(item);
                // Manter histórico das últimas 30 leituras no front-end
                if (cacheTrator.length > 30) {
                    cacheTrator.shift();
                }
            }
        }
    });
    TRATORES.forEach(t => {
        dadosCache[t].sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp));
    });

    // Atualizar UI
    atualizarKPIs();
    atualizarTabelaFrota();
    atualizarGraficoGPS();

    // Atualizar gráficos com o trator selecionado
    const tTemp = document.getElementById('trator-select-temp').value;
    const tRpm  = document.getElementById('trator-select-rpm').value;
    const tFuel = document.getElementById('trator-select-fuel').value;
    atualizarGrafico(tempChart, tTemp, i => parseFloat(i.motor.temperatura_celsius));
    atualizarGrafico(rpmChart,  tRpm,  i => i.motor.rpm);
    atualizarGrafico(fuelChart, tFuel, i => parseFloat(i.motor.nivel_combustivel_pct));
}

function ativarModoDemo() {
    if (!modoDemo) {
        modoDemo = true;
        console.warn('[AgroCloud] DynamoDB inacessível — ativando modo de demonstração.');
    }
    statusEl.textContent = '● Modo Demo';
    statusEl.style.color = '#f59e0b';
    statusDot.className  = 'status-indicator';
    statusDot.style.backgroundColor = '#f59e0b';
    lastUpdateEl.textContent = 'Demo: ' + new Date().toLocaleTimeString('pt-BR');

    // Gera novos dados demo a cada ciclo para parecer ao vivo
    const demoCache = gerarDadosDemo();
    TRATORES.forEach(t => { dadosCache[t] = demoCache[t]; });
    atualizarKPIs();
    atualizarTabelaFrota();
    atualizarGraficoGPS();
    const tTemp = document.getElementById('trator-select-temp').value;
    const tRpm  = document.getElementById('trator-select-rpm').value;
    const tFuel = document.getElementById('trator-select-fuel').value;
    atualizarGrafico(tempChart, tTemp, i => parseFloat(i.motor.temperatura_celsius));
    atualizarGrafico(rpmChart,  tRpm,  i => i.motor.rpm);
    atualizarGrafico(fuelChart, tFuel, i => parseFloat(i.motor.nivel_combustivel_pct));
}

function fetchDados() {
    statusEl.textContent = 'Sincronizando...';
    statusEl.style.color = '';

    docClient.scan({ TableName: TABLE_NAME }, (err, data) => {
        if (err) {
            console.error('[DynamoDB] Erro ao buscar dados:', err);
            ativarModoDemo();
            return;
        }

        if (!data.Items || data.Items.length === 0) {
            // Tabela vazia — usa demo
            ativarModoDemo();
            return;
        }

        // Verificar se os dados têm a estrutura correta (motor.*)
        const temEstrutura = data.Items.some(i => i.motor);
        if (!temEstrutura) {
            console.warn('[AgroCloud] Dados não têm estrutura esperada (motor.*). Usando demo.');
            ativarModoDemo();
            return;
        }

        // Dados reais do DynamoDB!
        modoDemo = false;
        statusEl.textContent = '✓ Conectado AWS';
        statusEl.style.color = '#16a34a';
        statusDot.className  = 'status-indicator online';
        statusDot.style.backgroundColor = '';
        lastUpdateEl.textContent = 'AWS: ' + new Date().toLocaleTimeString('pt-BR');
        processarDados(data.Items);
    });
}

// ── Ouvir mudanças nos selects de trator ────────────────────────────────────
document.getElementById('trator-select-temp').addEventListener('change', e => {
    atualizarGrafico(tempChart, e.target.value, i => parseFloat(i.motor.temperatura_celsius));
});
document.getElementById('trator-select-rpm').addEventListener('change', e => {
    atualizarGrafico(rpmChart,  e.target.value, i => i.motor.rpm);
});
document.getElementById('trator-select-fuel').addEventListener('change', e => {
    atualizarGrafico(fuelChart, e.target.value, i => parseFloat(i.motor.nivel_combustivel_pct));
});

// ── Navegação de Abas ─────────────────────────────────────────────────────────
const navMap = {
    'nav-painel':      'tab-painel',
    'nav-frota':       'tab-frota',
    'nav-temperatura': 'tab-temperatura',
    'nav-rpm':         'tab-rpm',
    'nav-gps':         'tab-gps',
    'nav-combustivel': 'tab-combustivel',
    'nav-drones':      'tab-drones',
};

Object.entries(navMap).forEach(([navId, tabId]) => {
    document.getElementById(navId).addEventListener('click', () => {
        // Desativar todos
        document.querySelectorAll('nav li').forEach(li => li.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tab => tab.style.display = 'none');

        // Ativar selecionado
        document.getElementById(navId).classList.add('active');
        document.getElementById(tabId).style.display = 'flex';

        // Forçar atualização dos gráficos após exibição
        setTimeout(() => {
            tempChart.resize(); rpmChart.resize(); fuelChart.resize(); gpsChart.resize();
        }, 50);
    });
});

// ── Iniciar ────────────────────────────────────────────────────────────────────
fetchDados();
setInterval(fetchDados, REFRESH_MS);

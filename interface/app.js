const state = {
  summary: null,
  lookup: null,
};

const fmt = new Intl.NumberFormat("pt-BR");

function setText(selector, value) {
  const el = document.querySelector(selector);
  if (el) el.textContent = value;
}

function metricValue(value) {
  if (typeof value === "number") return fmt.format(value);
  return value ?? "--";
}

function animateNumber(selector, value, decimals = 0) {
  const el = document.querySelector(selector);
  if (!el || typeof value !== "number") {
    setText(selector, metricValue(value));
    return;
  }

  const duration = 850;
  const start = performance.now();

  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = value * eased;
    el.textContent = decimals > 0 ? current.toFixed(decimals) : fmt.format(Math.round(current));

    if (progress < 1) {
      requestAnimationFrame(frame);
    } else {
      el.textContent = decimals > 0 ? value.toFixed(decimals) : fmt.format(value);
    }
  }

  requestAnimationFrame(frame);
}

function timeValue(value) {
  if (typeof value !== "number") return "--";
  if (value < 0.001) return `${(value * 1000).toFixed(3)} ms`;
  return `${value.toFixed(4)} s`;
}

function attr(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function fileName(path) {
  return String(path ?? "--").split(/[\\/]/).pop();
}

function displayVizTitle(title) {
  return title === "Componentes conexas" ? "Ilhas do grafo" : title;
}

function avgTime(items) {
  if (!items?.length) return null;
  return items.reduce((total, item) => total + (item.tempo_s ?? 0), 0) / items.length;
}

function movieInfo(id) {
  return state.lookup?.movies?.[id] ?? {
    titulo: id,
    ano: "",
    generos: "genero nao informado",
    nota: "",
  };
}

function renderMetrics(dataset) {
  animateNumber('[data-field="num_vertices"]', dataset.num_vertices);
  animateNumber('[data-field="num_arestas"]', dataset.num_arestas);
  animateNumber('[data-field="grau_medio"]', dataset.grau?.medio, 2);
  animateNumber('[data-field="componentes_conexas"]', dataset.componentes_conexas);
}


function renderResults(summary) {
  const bfs = summary.buscas?.bfs ?? [];
  const dfs = summary.buscas?.dfs ?? [];
  const dijkstra = summary.dijkstra ?? [];
  const bellmanFord = summary.bellman_ford ?? [];
  const dijkstraOk = dijkstra.filter((item) => !item.sem_caminho).length;
  const bfCycle = bellmanFord.some((item) => item.ciclo_negativo);

  document.getElementById("results-summary").innerHTML = [
    `
      <article class="result-stat">
        <h3>buscas</h3>
        <span>${bfs.length + dfs.length}</span>
        <p>bfs percorre a ilha do filme por camadas para medir alcance e niveis de vizinhanca.<br>dfs usa as mesmas fontes, aprofunda os caminhos e ajuda a confirmar ciclos.</p>
        <small>${metricValue(summary.buscas?.fontes_principais?.length ?? 0)} filmes de partida usados tanto na bfs quanto na dfs.</small>
      </article>
    `,
    `
      <article class="result-stat">
        <h3>dijkstra</h3>
        <span>${dijkstraOk}/${dijkstra.length}</span>
        <p>usa o peso invertido da similaridade para achar o menor custo entre filmes. quanto mais atores e generos em comum, menor fica o peso da aresta no caminho.</p>
        <small>rotas encontradas dentro dos pares origem-destino.</small>
      </article>
    `,
    `
      <article class="result-stat">
        <h3>bellman-ford</h3>
        <span>${bfCycle ? "ok" : "--"}</span>
        <p>roda em grafos dirigidos de validacao para provar que o codigo lida com peso negativo e tambem bloqueia ciclo negativo quando ele aparece.</p>
        <small>casos sinteticos separados do grafo imdb principal.</small>
      </article>
    `,
  ].join("");
}

function renderBenchmarkOutput(summary) {
  const benchmark = summary.benchmark ?? {};
  const benchmarkHtml = Object.entries(benchmark).map(([name, items]) => {
    const maxVisited = Math.max(...items.map((item) => item.visitados ?? 0));
    const detail = name === "dijkstra"
      ? `${items.length} pares`
      : name === "bellman_ford"
        ? `${items.length} casos artificiais`
        : `${items.length} fontes`;

    return `
      <article class="benchmark-row">
        <strong>${attr(name.replace("_", "-"))}</strong>
        <span>${detail}</span>
        <div class="benchmark-tempo-medio-line">
          <span class="benchmark-tempo-medio-label">benchmark / tempo medio</span>
          <span class="benchmark-tempo-medio-val">${timeValue(avgTime(items))}</span>
        </div>
        <em>${maxVisited > 0 ? `${metricValue(maxVisited)} visitados` : "validacao curta"}</em>
      </article>
    `;
  }).join("");

  document.getElementById("benchmark-output").innerHTML = `
    <article class="result-panel results-bench-sticky">
      <header>
        <h3 class="saidas-pane-title">Benchmark - Tempo Medio</h3>
      </header>
      <div class="benchmark-list">${benchmarkHtml}</div>
    </article>
  `;
}

function compactSearch(item) {
  return {
    source: item.source,
    filme: movieInfo(item.source).titulo,
    visitados: item.visitados,
    camadas: item.camadas,
    ciclo_na_componente: item.ciclo_na_componente,
    tempo_s: item.tempo_s,
  };
}

function compactDijkstra(item) {
  return {
    source: item.source,
    source_filme: movieInfo(item.source).titulo,
    target: item.target,
    target_filme: movieInfo(item.target).titulo,
    sem_caminho: item.sem_caminho,
    custo_total: item.custo_total,
    tamanho_caminho: item.tamanho_caminho,
    caminho_amostra: (item.caminho ?? []).slice(0, 6),
    tempo_s: item.tempo_s,
  };
}

function renderRawOutputs(summary) {
  const consolidated = {
    dataset: {
      vertices: summary.dataset?.num_vertices,
      arestas: summary.dataset?.num_arestas,
      ilhas: summary.dataset?.componentes_conexas,
      maior_ilha: summary.dataset?.maior_componente_conexa,
      grau_medio: summary.dataset?.grau?.medio,
    },
    bfs_dfs: {
      bfs: (summary.buscas?.bfs ?? []).map(compactSearch),
      dfs: (summary.buscas?.dfs ?? []).map(compactSearch),
    },
    dijkstra: (summary.dijkstra ?? []).map(compactDijkstra),
    bellman_ford: (summary.bellman_ford ?? []).map((item) => ({
      dataset: fileName(item.dataset),
      source: item.source,
      ciclo_negativo: item.ciclo_negativo,
      distancias: item.distancias,
      tempo_s: item.tempo_s,
    })),
  };

  document.getElementById("raw-output-pane").innerHTML = `
    <article class="result-panel raw-output-merged">
      <header>
        <h3 class="saidas-pane-title">parte2_report.json filtrada</h3>
      </header>
      <pre class="raw-output-merged-pre"><code>${attr(JSON.stringify(consolidated, null, 2))}</code></pre>
    </article>
  `;
}

function renderVisualizations(visualizacoes) {
  const html = visualizacoes
    .map((viz) => {
      const title = displayVizTitle(viz.titulo);

      return `
        <article
          class="viz-card"
          role="button"
          tabindex="0"
          aria-label="abrir grafico ${attr(title)}"
          data-viz-src="${attr(viz.arquivo)}"
          data-viz-title="${attr(title)}"
          data-viz-caption="${attr(viz.tipo)}"
        >
          <img src="${viz.arquivo}" alt="${title}">
          <div>
            <h3>${title}</h3>
            <p>${viz.tipo}</p>
          </div>
        </article>
      `;
    })
    .join("");

  document.getElementById("viz-grid").innerHTML = html;
}

function setupVizModal() {
  const modal = document.getElementById("viz-modal");
  const image = document.getElementById("modal-image");
  const title = document.getElementById("modal-title");
  const caption = document.getElementById("modal-caption");
  const grid = document.getElementById("viz-grid");

  function openModal(card) {
    title.textContent = card.dataset.vizTitle;
    caption.textContent = card.dataset.vizCaption;
    image.src = card.dataset.vizSrc;
    image.alt = card.dataset.vizTitle;
    modal.classList.add("is-open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");
  }

  function closeModal() {
    modal.classList.remove("is-open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
    image.src = "";
  }

  grid.addEventListener("click", (event) => {
    const card = event.target.closest(".viz-card");
    if (card) openModal(card);
  });

  grid.addEventListener("keydown", (event) => {
    const card = event.target.closest(".viz-card");
    if (!card) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      openModal(card);
    }
  });

  modal.addEventListener("click", (event) => {
    if (event.target.matches("[data-close-modal]")) closeModal();
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && modal.classList.contains("is-open")) {
      closeModal();
    }
  });
}

function setupGraphFullscreen() {
  const graphArea = document.querySelector(".graph-area");
  const button = document.getElementById("graph-fullscreen-btn");
  if (!graphArea || !button) return;

  function setFullscreen(active) {
    graphArea.classList.toggle("is-fullscreen", active);
    document.body.classList.toggle("graph-fullscreen-open", active);
    button.textContent = active ? "restaurar" : "maximizar";
  }

  button.addEventListener("click", () => {
    setFullscreen(!graphArea.classList.contains("is-fullscreen"));
  });

  window.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && graphArea.classList.contains("is-fullscreen")) {
      setFullscreen(false);
    }
  });
}

function setupViews() {
  const triggers = [...document.querySelectorAll("[data-view]")];
  const tabs = [...document.querySelectorAll(".nav [data-view]")];
  const panels = [...document.querySelectorAll("[data-view-panel]")];
  const validViews = new Set(panels.map((panel) => panel.dataset.viewPanel));

  function showView(view) {
    const nextView = validViews.has(view) ? view : "inicio";

    tabs.forEach((tab) => {
      tab.classList.toggle("is-active", tab.dataset.view === nextView);
    });

    panels.forEach((panel) => {
      panel.classList.toggle("is-active", panel.dataset.viewPanel === nextView);
    });

    if (window.location.hash !== `#${nextView}`) {
      window.history.replaceState(null, "", `#${nextView}`);
    }
  }

  triggers.forEach((tab) => {
    tab.addEventListener("click", (event) => {
      event.preventDefault();
      showView(tab.dataset.view);
    });
  });

  window.addEventListener("hashchange", () => {
    showView(window.location.hash.replace("#", ""));
  });

  showView(window.location.hash.replace("#", "") || "inicio");
}

async function init() {
  const [summaryResponse, lookupResponse] = await Promise.all([
    fetch("data/parte2_summary.json"),
    fetch("data/parte2_lookup.json"),
  ]);
  state.summary = await summaryResponse.json();
  state.lookup = await lookupResponse.json();

  setupViews();
  renderMetrics(state.summary.dataset);
  renderResults(state.summary);
  renderBenchmarkOutput(state.summary);
  renderRawOutputs(state.summary);
  renderVisualizations(state.summary.visualizacoes);
  setupVizModal();
  setupGraphFullscreen();
}

init().catch((err) => {
  console.error(err);
  document.body.classList.add("load-error");
});

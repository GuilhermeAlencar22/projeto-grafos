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

function table(headers, rows) {
  return `
    <div class="table-wrap">
      <table class="result-table">
        <thead>
          <tr>${headers.map((header) => `<th>${header}</th>`).join("")}</tr>
        </thead>
        <tbody>
          ${rows
            .map((row) => `<tr>${row.map((cell) => `<td>${cell}</td>`).join("")}</tr>`)
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function avgTime(items) {
  if (!items?.length) return null;
  return items.reduce((total, item) => total + (item.tempo_s ?? 0), 0) / items.length;
}

function pathPreview(item) {
  if (item.sem_caminho) {
    return '<span class="status-warn">sem caminho</span>';
  }

  const path = item.caminho ?? [];
  const preview = path.map(attr).join(" -> ");
  const total = item.tamanho_caminho ?? path.length;
  const suffix = total > path.length ? ` ... <small>${total} nos no caminho completo</small>` : "";

  return `<div class="path-preview">${preview}${suffix}</div>`;
}

function movieInfo(id) {
  return state.lookup?.movies?.[id] ?? {
    titulo: id,
    ano: "",
    generos: "genero nao informado",
    nota: "",
  };
}

function movieCard(id, label = "filme") {
  const movie = movieInfo(id);
  const meta = [
    movie.ano,
    movie.generos,
    movie.nota ? `nota ${movie.nota}` : "",
  ].filter(Boolean);

  return `
    <article class="movie-card">
      <span class="movie-label">${label}</span>
      <strong>${attr(movie.titulo)}</strong>
      <em>${attr(id)}</em>
      <p>${attr(meta.join(" | ") || "metadados indisponiveis")}</p>
    </article>
  `;
}

function movieChip(id) {
  const movie = movieInfo(id);
  return `
    <span class="path-chip" title="${attr(id)}">
      ${attr(movie.titulo)}
      <small>${attr(id)}</small>
    </span>
  `;
}

function edgeKey(a, b) {
  return [a, b].sort().join("|");
}

function edgeInfo(a, b) {
  return state.lookup?.edges?.[edgeKey(a, b)] ?? null;
}

function connectionFacts(item) {
  const path = item.caminho ?? [];
  let edge = null;
  let label = "";

  if (item.source && item.target) {
    edge = edgeInfo(item.source, item.target);
    label = "ligacao direta";
  }

  if (!edge && path.length > 1) {
    edge = edgeInfo(path[0], path[1]);
    label = "primeiro passo do caminho";
  }

  if (!edge) {
    return `
      <div class="connection-facts muted-facts">
        <span>atores em comum</span>
        <strong>--</strong>
        <small>sem aresta direta registrada para esse par</small>
      </div>
    `;
  }

  return `
    <div class="connection-facts">
      <span>${label}</span>
      <strong>${edge.actors_common} atores em comum</strong>
      <small>similaridade ${edge.similaridade} | peso ${edge.peso}</small>
    </div>
  `;
}

function pathCards(item) {
  const path = item.caminho ?? [];
  if (item.sem_caminho) {
    return '<div class="path-strip"><span class="status-warn">sem caminho entre as ilhas</span></div>';
  }

  const visible = path.slice(0, 8).map(movieChip).join("");
  const suffix = item.tamanho_caminho > path.length
    ? `<span class="path-chip more">+ ${item.tamanho_caminho - path.length} nos</span>`
    : "";

  return `<div class="path-strip">${visible}${suffix}</div>`;
}

function renderMetrics(dataset) {
  setText('[data-field="num_vertices"]', metricValue(dataset.num_vertices));
  setText('[data-field="num_arestas"]', metricValue(dataset.num_arestas));
  setText('[data-field="grau_medio"]', dataset.grau?.medio?.toFixed(2) ?? "--");
  setText(
    '[data-field="componentes_conexas"]',
    metricValue(dataset.componentes_conexas)
  );
}

function card(title, rows) {
  return `
    <article class="algorithm-card">
      <h3>${title}</h3>
      ${rows.map((row) => `<p>${row}</p>`).join("")}
    </article>
  `;
}

function renderAlgorithms(summary) {
  const firstBfs = summary.buscas?.bfs?.[0];
  const firstDfs = summary.buscas?.dfs?.[0];
  const firstDijkstra = summary.dijkstra?.find((item) => !item.sem_caminho);
  const bfCycle = summary.bellman_ford?.find((item) => item.ciclo_negativo);

  const html = [
    card("bfs", [
      `fontes no mapa: ${summary.buscas?.fontes_principais?.length ?? 0}`,
      `camadas abertas: ${firstBfs?.camadas ?? "--"}`,
      `alcance: ${metricValue(firstBfs?.visitados)} filmes`,
    ]),
    card("dfs", [
      `fontes no mapa: ${summary.buscas?.fontes_principais?.length ?? 0}`,
      `ciclo encontrado: ${firstDfs?.ciclo_na_componente ? "sim" : "nao"}`,
      `alcance: ${metricValue(firstDfs?.visitados)} filmes`,
    ]),
    card("dijkstra", [
      `pares em cena: ${summary.dijkstra?.length ?? 0}`,
      `rota exemplo: ${firstDijkstra?.source ?? "--"} -> ${firstDijkstra?.target ?? "--"}`,
      `custo do corte: ${firstDijkstra?.custo_total ?? "--"}`,
    ]),
    card("bellman-ford", [
      `casos testados: ${summary.bellman_ford?.length ?? 0}`,
      `ciclo negativo: ${bfCycle ? "detectado" : "nao detectado"}`,
      `pesos negativos sob controle`,
    ]),
  ].join("");

  document.getElementById("algorithm-grid").innerHTML = html;
}

function renderResults(summary) {
  const bfs = summary.buscas?.bfs ?? [];
  const dfs = summary.buscas?.dfs ?? [];
  const dijkstra = summary.dijkstra ?? [];
  const bellmanFord = summary.bellman_ford ?? [];
  const benchmark = summary.benchmark ?? {};
  const dijkstraOk = dijkstra.filter((item) => !item.sem_caminho).length;
  const bfCycle = bellmanFord.some((item) => item.ciclo_negativo);

  document.getElementById("results-summary").innerHTML = [
    `
      <article class="result-stat">
        <span>buscas</span>
        <strong>${bfs.length + dfs.length}</strong>
        <p>bfs e dfs executados em ${metricValue(summary.buscas?.fontes_principais?.length ?? 0)} fontes.</p>
      </article>
    `,
    `
      <article class="result-stat">
        <span>dijkstra</span>
        <strong>${dijkstraOk}/${dijkstra.length}</strong>
        <p>pares com caminho encontrado usando pesos nao negativos.</p>
      </article>
    `,
    `
      <article class="result-stat">
        <span>bellman-ford</span>
        <strong>${bfCycle ? "ok" : "--"}</strong>
        <p>validacao com peso negativo e ciclo negativo detectado.</p>
      </article>
    `,
    `
      <article class="result-stat">
        <span>benchmark</span>
        <strong>${Object.keys(benchmark).length}</strong>
        <p>familias de medicoes registradas em tempo de execucao.</p>
      </article>
    `,
  ].join("");

  const buscaHtml = [
    ...bfs.map((item) => ({ ...item, algoritmo: "bfs" })),
    ...dfs.map((item) => ({ ...item, algoritmo: "dfs" })),
  ]
    .map((item) => `
      <article class="search-result-item">
        ${movieCard(item.source, `${item.algoritmo} | fonte`)}
        <div class="mini-stats">
          <span><strong>${metricValue(item.visitados)}</strong> visitados</span>
          <span><strong>${item.camadas ?? "ordem"}</strong> ${item.camadas ? "camadas" : "amostrada"}</span>
          <span><strong>${timeValue(item.tempo_s)}</strong> tempo</span>
        </div>
        ${item.ciclo_na_componente
          ? '<span class="status-warn">ciclo encontrado</span>'
          : '<span class="status-ok">sem ciclo</span>'}
      </article>
    `)
    .join("");

  const dijkstraHtml = dijkstra
    .map((item) => `
      <article class="route-card">
        <div class="route-movies">
          ${movieCard(item.source, "origem")}
          <span class="route-arrow">para</span>
          ${movieCard(item.target, "destino")}
        </div>
        <div class="route-stats">
          ${item.sem_caminho
            ? '<span class="status-warn">sem caminho</span>'
            : '<span class="status-ok">caminho encontrado</span>'}
          <span>custo: <strong>${item.custo_total ?? "--"}</strong></span>
          <span>nos: <strong>${item.tamanho_caminho ?? "--"}</strong></span>
          <span>tempo: <strong>${timeValue(item.tempo_s)}</strong></span>
        </div>
        ${connectionFacts(item)}
        ${pathCards(item)}
      </article>
    `)
    .join("");

  const bfHtml = bellmanFord.map((item) => {
    const distancias = item.distancias
      ? Object.entries(item.distancias)
          .map(([node, value]) => `${attr(node)}: ${value}`)
          .join(", ")
      : "bloqueado por ciclo negativo";

    return `
      <article class="bf-card">
        <div>
          <span class="movie-label">dataset</span>
          <strong>${attr(fileName(item.dataset))}</strong>
          <p>fonte: ${attr(item.source)} | tempo: ${timeValue(item.tempo_s)}</p>
        </div>
        ${item.ciclo_negativo
        ? '<span class="status-danger">ciclo negativo</span>'
        : '<span class="status-ok">sem ciclo negativo</span>'}
        <p class="path-preview">${distancias}</p>
      </article>
    `;
  }).join("");

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
        <span>${timeValue(avgTime(items))}</span>
        <em>${maxVisited > 0 ? `${metricValue(maxVisited)} visitados` : "validacao curta"}</em>
      </article>
    `;
  }).join("");

  document.getElementById("results-grid").innerHTML = `
    <article class="result-panel result-panel-wide">
      <header>
        <h3>dijkstra</h3>
        <p>pares origem-destino com nome do filme, genero, custo, caminho e dados da conexao.</p>
      </header>
      <div class="route-list">${dijkstraHtml}</div>
    </article>

    <article class="result-panel">
      <header>
        <h3>bfs e dfs</h3>
        <p>fontes com nome do filme, genero, alcance e ciclos encontrados nas ilhas do grafo.</p>
      </header>
      <div class="search-result-list">${buscaHtml}</div>
    </article>

    <article class="result-panel">
      <header>
        <h3>bellman-ford</h3>
        <p>casos com peso negativo sem ciclo e com ciclo negativo detectado.</p>
      </header>
      <div class="bf-list">${bfHtml}</div>
    </article>

    <article class="result-panel result-panel-wide">
      <header>
        <h3>benchmark</h3>
        <p>media simples dos tempos registrados por familia de algoritmo.</p>
      </header>
      <div class="benchmark-list">${benchmarkHtml}</div>
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

function setupViews() {
  const triggers = [...document.querySelectorAll("[data-view]")];
  const tabs = [...document.querySelectorAll(".nav [data-view]")];
  const panels = [...document.querySelectorAll("[data-view-panel]")];
  const validViews = new Set(panels.map((panel) => panel.dataset.viewPanel));

  function showView(view) {
    const requestedView = view === "resultados" ? "algoritmos" : view;
    const nextView = validViews.has(requestedView) ? requestedView : "inicio";

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
  renderAlgorithms(state.summary);
  renderResults(state.summary);
  renderVisualizations(state.summary.visualizacoes);
  setupVizModal();
}

init().catch((err) => {
  console.error(err);
  document.body.classList.add("load-error");
});

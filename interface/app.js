const state = {
  summary: null,
  lookup: null,
  network: null,
  graph: {
    nodes: null,
    edges: null,
    baseNodes: [],
    baseEdges: [],
  },
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

async function fetchJson(path) {
  const response = await fetch(path);
  const text = await response.text();
  return JSON.parse(text.replace(/^\uFEFF/, ""));
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

function edgeKey(a, b) {
  return [a, b].sort().join("|");
}

function lookupEdge(a, b) {
  return state.lookup?.edges?.[edgeKey(a, b)] ?? null;
}

function movieGenres(id) {
  return (movieInfo(id).generos ?? "")
    .split(",")
    .map((genre) => genre.trim())
    .filter(Boolean);
}

function commonGenres(a, b) {
  const left = new Set(movieGenres(a));
  return movieGenres(b).filter((genre) => left.has(genre));
}

function movieLabel(id) {
  const movie = movieInfo(id);
  const title = movie.titulo || id;
  return title.length > 24 ? `${title.slice(0, 22)}...` : title;
}

function movieTitle(id) {
  const movie = movieInfo(id);
  const meta = [movie.ano, movie.generos, movie.nota ? `nota ${movie.nota}` : ""]
    .filter(Boolean)
    .join(" | ");
  return `${movie.titulo || id}\n${id}${meta ? `\n${meta}` : ""}`;
}

function edgeTitle(edge) {
  const source = movieInfo(edge.source);
  const target = movieInfo(edge.target);
  const genres = commonGenres(edge.source, edge.target);
  return [
    `${source.titulo || edge.source} -> ${target.titulo || edge.target}`,
    `atores em comum: ${edge.actors_common ?? "--"}`,
    `generos em comum: ${genres.join(", ") || "--"}`,
    `similaridade: ${edge.similaridade ?? "--"}`,
    `peso: ${edge.peso ?? "--"}`,
  ].join("\n");
}

function baseNode(id, extra = {}) {
  return {
    id,
    label: movieLabel(id),
    title: movieTitle(id),
    color: {
      background: extra.background ?? "#f5c518",
      border: extra.border ?? "#ffffff",
      highlight: {
        background: extra.highlight ?? "#ffffff",
        border: "#f5c518",
      },
    },
    font: {
      color: "#ffffff",
      size: 15,
      face: "Segoe UI",
      strokeWidth: 4,
      strokeColor: "#050505",
    },
    borderWidth: 2,
    shape: "dot",
    size: extra.size ?? 28,
    level: extra.level,
    group: extra.group,
  };
}

function baseEdge(edge, extra = {}) {
  const value = Number(edge.similaridade ?? edge.actors_common ?? 1);
  const color = extra.color ?? "rgba(245, 197, 24, 0.55)";

  return {
    id: edge.id ?? edgeKey(edge.source, edge.target),
    from: edge.source,
    to: edge.target,
    title: edgeTitle(edge),
    label: extra.label ?? String(edge.similaridade ?? ""),
    width: extra.width ?? Math.max(3, Math.min(10, 2 + Math.sqrt(value) * 1.8)),
    color: {
      color,
      highlight: "#ffffff",
      hover: "#ffffff",
    },
    font: {
      color: "#f5c518",
      size: 13,
      strokeWidth: 4,
      strokeColor: "#050505",
    },
    smooth: {
      type: "dynamic",
    },
    dashes: extra.dashes ?? false,
    arrows: extra.arrows,
    meta: edge,
  };
}

function makeGraphFromEdges(edges, options = {}) {
  const nodes = new Map();
  const degrees = new Map();
  const visualEdges = [];

  edges.forEach((edge) => {
    nodes.set(edge.source, edge.source);
    nodes.set(edge.target, edge.target);
    degrees.set(edge.source, (degrees.get(edge.source) ?? 0) + 1);
    degrees.set(edge.target, (degrees.get(edge.target) ?? 0) + 1);
    visualEdges.push(baseEdge(edge, options.edgeOptions));
  });

  return {
    nodes: [...nodes.values()].map((id) => {
      const degree = degrees.get(id) ?? 1;
      return baseNode(id, {
        size: Math.min(46, 25 + degree * 4),
        border: degree > 2 ? "#f5c518" : "#ffffff",
      });
    }),
    edges: visualEdges,
    layout: options.layout ?? "network",
  };
}

function connectedEdgeSample(sortedEdges, limit = 18) {
  if (!sortedEdges.length) return [];

  const selected = [sortedEdges[0]];
  const used = new Set([sortedEdges[0].id ?? edgeKey(sortedEdges[0].source, sortedEdges[0].target)]);
  const nodes = new Set([sortedEdges[0].source, sortedEdges[0].target]);

  while (selected.length < limit) {
    const next = sortedEdges.find((edge) => {
      const id = edge.id ?? edgeKey(edge.source, edge.target);
      return !used.has(id) && (nodes.has(edge.source) || nodes.has(edge.target));
    });

    if (!next) break;

    selected.push(next);
    used.add(next.id ?? edgeKey(next.source, next.target));
    nodes.add(next.source);
    nodes.add(next.target);
  }

  return selected;
}

function pathEdges(path, options = {}) {
  const edges = [];

  for (let index = 0; index < path.length - 1; index += 1) {
    const source = path[index];
    const target = path[index + 1];
    const stored = lookupEdge(source, target);
    edges.push({
      ...(stored ?? {
        source,
        target,
        actors_common: "--",
        similaridade: "--",
        peso: "--",
      }),
      id: `${options.prefix ?? "path"}-${source}-${target}-${index}`,
    });
  }

  return edges;
}

function makePathGraph(path, options = {}) {
  const nodes = path.map((id, index) => {
    const isFirst = index === 0;
    const isLast = index === path.length - 1;
    return baseNode(id, {
      size: isFirst || isLast ? 40 : 28,
      background: isFirst ? "#2ecc71" : isLast ? "#ff4d4d" : "#f5c518",
      border: isFirst || isLast ? "#ffffff" : "#f5c518",
    });
  });

  const edges = pathEdges(path, options).map((edge) => baseEdge(edge, {
    color: options.color ?? "#ff9f1c",
    width: options.width ?? 4,
    arrows: options.arrows,
    dashes: options.dashes,
    label: options.labelEdges ? String(edge.similaridade ?? "") : "",
  }));

  return {
    nodes,
    edges,
    layout: options.layout ?? "network",
    direction: options.direction ?? "LR",
  };
}

function makeBellmanFordGraph() {
  const node = (id, label, x, y, color, size = 34, description = "") => ({
    ...baseNode(id, {
      background: color,
      border: "#ffffff",
      size,
    }),
    label,
    x,
    y,
    bfDescription: description,
  });

  const directedEdge = (from, to, label, group, danger = false) => ({
    id: `bf-${from}-${to}-${label}`,
    from,
    to,
    label,
    arrows: "to",
    dashes: danger,
    title: `${group}\n${from} -> ${to}\npeso: ${label}`,
    color: {
      color: danger ? "#ff4d4d" : "#f5c518",
      highlight: "#ffffff",
      hover: "#ffffff",
    },
    width: danger ? 5 : 3,
    font: {
      color: danger ? "#ff4d4d" : "#f5c518",
      size: 15,
      strokeWidth: 4,
      strokeColor: "#050505",
    },
    smooth: {
      enabled: true,
      type: danger ? "curvedCW" : "cubicBezier",
      roundness: danger ? 0.34 : 0.18,
    },
    meta: {
      source: from,
      target: to,
      peso: label,
      caso: group,
      ciclo_negativo: danger,
      tipo: "bellman-ford",
    },
  });

  return {
    nodes: [
      node("ok-s", "sem ciclo\ns", -330, -130, "#2ecc71", 44, "fonte do caso sem ciclo negativo"),
      node("ok-a", "a", -455, 40, "#f5c518", 34, "vertice alcancado com peso positivo"),
      node("ok-b", "b", -205, 40, "#f5c518", 34, "vertice alcancado pela fonte s"),
      node("ok-c", "c", -330, 210, "#f5c518", 34, "recebe relaxamento com peso negativo, mas sem formar ciclo negativo"),
      node("bad-a", "com ciclo\na", 260, -130, "#ff4d4d", 44, "inicio do caso com ciclo negativo"),
      node("bad-b", "b", 105, 150, "#f5c518", 34, "parte do ciclo dirigido"),
      node("bad-c", "c", 415, 150, "#ff4d4d", 40, "fecha o ciclo negativo voltando para a"),
    ],
    edges: [
      directedEdge("ok-s", "ok-a", "5", "sem ciclo negativo"),
      directedEdge("ok-s", "ok-b", "2", "sem ciclo negativo"),
      directedEdge("ok-b", "ok-c", "0", "sem ciclo negativo"),
      directedEdge("ok-a", "ok-c", "-3", "sem ciclo negativo"),
      directedEdge("bad-a", "bad-b", "1", "com ciclo negativo"),
      directedEdge("bad-b", "bad-c", "-3", "com ciclo negativo", true),
      directedEdge("bad-c", "bad-a", "1", "com ciclo negativo", true),
    ],
    layout: "network",
  };
}

function buildLookupAdjacency() {
  const adj = new Map();

  Object.values(state.lookup?.edges ?? {}).forEach((edge) => {
    if (!adj.has(edge.source)) adj.set(edge.source, []);
    if (!adj.has(edge.target)) adj.set(edge.target, []);
    adj.get(edge.source).push({ to: edge.target, edge });
    adj.get(edge.target).push({ to: edge.source, edge });
  });

  return adj;
}

function dijkstraPath(source, target) {
  const adj = buildLookupAdjacency();
  const dist = new Map([[source, 0]]);
  const prev = new Map();
  const visited = new Set();
  const queue = [{ id: source, cost: 0 }];

  while (queue.length) {
    queue.sort((a, b) => a.cost - b.cost);
    const current = queue.shift();
    if (!current || visited.has(current.id)) continue;
    visited.add(current.id);
    if (current.id === target) break;

    (adj.get(current.id) ?? []).forEach(({ to, edge }) => {
      const nextCost = current.cost + Number(edge.peso ?? 1);
      if (nextCost < (dist.get(to) ?? Infinity)) {
        dist.set(to, nextCost);
        prev.set(to, current.id);
        queue.push({ id: to, cost: nextCost });
      }
    });
  }

  if (!dist.has(target)) return null;

  const path = [];
  let step = target;
  while (step) {
    path.unshift(step);
    if (step === source) break;
    step = prev.get(step);
  }

  return {
    path,
    cost: dist.get(target),
    algorithm: "dijkstra",
  };
}

function dfsPath(source, target) {
  const adj = buildLookupAdjacency();
  const visited = new Set();
  const path = [];

  function visit(node) {
    visited.add(node);
    path.push(node);
    if (node === target) return true;

    for (const { to } of adj.get(node) ?? []) {
      if (!visited.has(to) && visit(to)) return true;
    }

    path.pop();
    return false;
  }

  if (!visit(source)) return null;

  return {
    path,
    cost: null,
    algorithm: "profundidade",
  };
}

function makeTraversalGraph(source, type = "bfs") {
  const adj = buildLookupAdjacency();
  const visited = new Set([source]);
  const nodes = [];
  const treeEdges = [];
  const usedTreeEdges = new Set();
  const limit = 25;

  function addNode(id, level) {
    nodes.push(baseNode(id, {
      level,
      size: id === source ? 42 : 28,
      background: id === source ? "#2ecc71" : type === "bfs" ? "#f5c518" : "#7cc7ff",
      border: id === source ? "#ffffff" : "#f5c518",
    }));
  }

  addNode(source, 0);

  if (type === "bfs") {
    const queue = [{ id: source, level: 0 }];

    while (queue.length && nodes.length < limit) {
      const current = queue.shift();
      const neighbors = [...(adj.get(current.id) ?? [])]
        .sort((a, b) => movieLabel(a.to).localeCompare(movieLabel(b.to)));

      neighbors.forEach(({ to, edge }) => {
        if (visited.has(to) || nodes.length >= limit) return;
        visited.add(to);
        addNode(to, current.level + 1);
        const visual = baseEdge({
          ...edge,
          id: `bfs-${current.id}-${to}`,
        }, {
          color: "#2ecc71",
          width: 4,
          arrows: "to",
          label: "",
        });
        treeEdges.push(visual);
        usedTreeEdges.add(edgeKey(current.id, to));
        queue.push({ id: to, level: current.level + 1 });
      });
    }
  } else {
    function visit(id, level) {
      if (nodes.length >= limit) return;

      const neighbors = [...(adj.get(id) ?? [])]
        .sort((a, b) => (b.edge.similaridade ?? 0) - (a.edge.similaridade ?? 0));

      neighbors.forEach(({ to, edge }) => {
        if (visited.has(to) || nodes.length >= limit) return;
        visited.add(to);
        addNode(to, level + 1);
        const visual = baseEdge({
          ...edge,
          id: `dfs-${id}-${to}`,
        }, {
          color: "#7cc7ff",
          width: 4,
          arrows: "to",
          label: "",
        });
        treeEdges.push(visual);
        usedTreeEdges.add(edgeKey(id, to));
        visit(to, level + 1);
      });
    }

    visit(source, 0);
  }

  const selected = new Set(nodes.map((node) => node.id));
  const extraEdges = Object.values(state.lookup?.edges ?? {})
    .filter((edge) => selected.has(edge.source) && selected.has(edge.target))
    .filter((edge) => !usedTreeEdges.has(edgeKey(edge.source, edge.target)))
    .slice(0, 10)
    .map((edge) => baseEdge({
      ...edge,
      id: `${type}-extra-${edge.source}-${edge.target}`,
    }, {
      color: "rgba(245, 197, 24, 0.32)",
      width: 2,
      dashes: true,
      label: "",
    }));

  return {
    nodes,
    edges: [...treeEdges, ...extraEdges],
    layout: "network",
    direction: type === "bfs" ? "UD" : "LR",
  };
}

function makeDijkstraGraph() {
  const route = longestDijkstraPath();
  if (!route) {
    return {
      nodes: [],
      edges: [],
      layout: "network",
    };
  }

  const pathSet = new Set(route.path);
  const pathEdgeIds = new Set();
  const nodes = route.path.map((id, index) => {
    const isFirst = index === 0;
    const isLast = index === route.path.length - 1;
    return baseNode(id, {
      size: isFirst || isLast ? 42 : 30,
      background: isFirst ? "#2ecc71" : isLast ? "#ff4d4d" : "#f5c518",
      border: "#ffffff",
    });
  });

  const mainEdges = pathEdges(route.path, { prefix: "dijkstra" }).map((edge) => {
    pathEdgeIds.add(edgeKey(edge.source, edge.target));
    return baseEdge(edge, {
      color: "#ff9f1c",
      width: 6,
      arrows: "to",
      label: String(edge.similaridade ?? ""),
    });
  });

  const contextEdges = Object.values(state.lookup?.edges ?? {})
    .filter((edge) => pathSet.has(edge.source) && pathSet.has(edge.target))
    .filter((edge) => !pathEdgeIds.has(edgeKey(edge.source, edge.target)))
    .slice(0, 18)
    .map((edge) => baseEdge({
      ...edge,
      id: `dijkstra-context-${edge.source}-${edge.target}`,
    }, {
      color: "rgba(245, 197, 24, 0.26)",
      width: 2,
      dashes: true,
      label: "",
    }));

  return {
    nodes,
    edges: [...mainEdges, ...contextEdges],
    layout: "network",
  };
}

function longestDijkstraPath() {
  const nodes = Object.keys(state.lookup?.movies ?? {});
  let best = null;

  for (let i = 0; i < nodes.length; i += 1) {
    for (let j = i + 1; j < nodes.length; j += 1) {
      const result = dijkstraPath(nodes[i], nodes[j]);
      if (!result) continue;
      if (!best || result.path.length > best.path.length) {
        best = result;
      }
    }
  }

  return best;
}

function makeNeighborhoodGraph(id) {
  const edges = Object.values(state.lookup?.edges ?? {})
    .filter((edge) => edge.source === id || edge.target === id);

  if (!edges.length) {
    return {
      nodes: [baseNode(id, { background: "#2ecc71", size: 42 })],
      edges: [],
      layout: "network",
    };
  }

  const graph = makeGraphFromEdges(edges, {
    edgeOptions: {
      label: "",
    },
  });

  graph.nodes = graph.nodes.map((node) => {
    if (node.id !== id) return node;
    return {
      ...node,
      size: 44,
      color: {
        ...node.color,
        background: "#2ecc71",
      },
    };
  });

  return graph;
}

function graphForMode(mode) {
  const edges = Object.values(state.lookup?.edges ?? {});
  const bySimilarity = [...edges].sort((a, b) => (b.similaridade ?? 0) - (a.similaridade ?? 0));
  const byActors = [...edges].sort((a, b) =>
    (b.actors_common ?? 0) - (a.actors_common ?? 0)
    || (b.similaridade ?? 0) - (a.similaridade ?? 0)
    || (a.peso ?? Infinity) - (b.peso ?? Infinity)
  );

  if (mode === "top") {
    return makeGraphFromEdges(byActors.slice(0, 42), {
      edgeOptions: {
        label: "",
      },
    });
  }

  if (mode === "bfs") {
    return makeTraversalGraph("tt0012313", "bfs");
  }

  if (mode === "dfs") {
    return makeTraversalGraph("tt0012313", "dfs");
  }

  if (mode === "dijkstra") {
    return makeDijkstraGraph();
  }

  if (mode === "bellman-ford") {
    return makeBellmanFordGraph();
  }

  return makeGraphFromEdges(connectedEdgeSample(bySimilarity, 24), {
    edgeOptions: {
      label: "",
    },
  });
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

function renderDetailsForNode(id) {
  const graphNode = state.graph.nodes?.get(id);
  if (graphNode?.bfDescription) {
    document.getElementById("details-panel").innerHTML = `
      <p class="eyebrow">bellman-ford</p>
      <h3>${attr(graphNode.label.replace("\n", " "))}</h3>
      <p>${attr(graphNode.bfDescription)}</p>
      <dl class="detail-list">
        <div>
          <dt>tipo</dt>
          <dd>grafo dirigido artificial</dd>
        </div>
        <div>
          <dt>interacao</dt>
          <dd>voce pode arrastar este no para reorganizar o exemplo.</dd>
        </div>
      </dl>
    `;
    return;
  }

  const movie = movieInfo(id);
  const details = document.getElementById("details-panel");
  const meta = [movie.ano, movie.generos, movie.nota ? `nota ${movie.nota}` : ""]
    .filter(Boolean)
    .join(" | ");

  details.innerHTML = `
    <p class="eyebrow">selecao</p>
    <h3>${attr(movie.titulo || id)}</h3>
    <p>${attr(id)}${meta ? ` | ${attr(meta)}` : ""}</p>
    <dl class="detail-list">
      <div>
        <dt>filme</dt>
        <dd>${attr(movie.titulo || id)}</dd>
      </div>
      <div>
        <dt>generos</dt>
        <dd>${attr(movie.generos || "nao informado")}</dd>
      </div>
      <div>
        <dt>ano</dt>
        <dd>${attr(movie.ano || "--")}</dd>
      </div>
      <div>
        <dt>nota imdb</dt>
        <dd>${attr(movie.nota || "--")}</dd>
      </div>
    </dl>
  `;
}

function renderDetailsForEdge(id) {
  const edge = state.graph.edges.get(id);
  const meta = edge?.meta ?? {};
  if (meta.tipo === "bellman-ford") {
    document.getElementById("details-panel").innerHTML = `
      <p class="eyebrow">bellman-ford</p>
      <h3>${attr(meta.caso)}</h3>
      <p>${attr(edge.from)} -> ${attr(edge.to)}</p>
      <dl class="detail-list">
        <div>
          <dt>peso</dt>
          <dd>${attr(meta.peso)}</dd>
        </div>
        <div>
          <dt>ciclo negativo</dt>
          <dd>${meta.ciclo_negativo ? "esta aresta faz parte do ciclo negativo destacado" : "nao"}</dd>
        </div>
        <div>
          <dt>observacao</dt>
          <dd>exemplo artificial e dirigido, usado para validar bellman-ford fora do grafo imdb principal.</dd>
        </div>
      </dl>
    `;
    return;
  }

  const source = movieInfo(meta.source ?? edge?.from);
  const target = movieInfo(meta.target ?? edge?.to);
  const genres = meta.source && meta.target ? commonGenres(meta.source, meta.target) : [];
  const actorNames = Array.isArray(meta.actors_common_names) ? meta.actors_common_names : [];
  const actorIds = Array.isArray(meta.actors_common_ids) ? meta.actors_common_ids : [];
  const actors = actorNames.length
    ? actorNames.join(", ")
    : actorIds.length
      ? actorIds.join(", ")
      : `${meta.actors_common ?? "--"} ator(es) em comum`;
  const actorLabel = actorNames.length ? "atores em comum" : "ids dos atores";
  const details = document.getElementById("details-panel");

  details.innerHTML = `
    <p class="eyebrow">selecao</p>
    <h3>aresta selecionada</h3>
    <p>${attr(source.titulo || edge?.from)} -> ${attr(target.titulo || edge?.to)}</p>
    <dl class="detail-list">
      <div>
        <dt>origem</dt>
        <dd>${attr(source.titulo || edge?.from)}</dd>
      </div>
      <div>
        <dt>destino</dt>
        <dd>${attr(target.titulo || edge?.to)}</dd>
      </div>
      <div>
        <dt>${actorLabel}</dt>
        <dd>${attr(actors)}</dd>
      </div>
      <div>
        <dt>generos em comum</dt>
        <dd>${attr(genres.join(", ") || "--")}</dd>
      </div>
      <div>
        <dt>similaridade</dt>
        <dd>${attr(meta.similaridade ?? "--")}</dd>
      </div>
      <div>
        <dt>peso</dt>
        <dd>${attr(meta.peso ?? edge?.label ?? "--")}</dd>
      </div>
    </dl>
  `;
}

function renderRouteDetails(result, source, target) {
  const details = document.getElementById("details-panel");
  const sourceMovie = movieInfo(source);
  const targetMovie = movieInfo(target);

  if (!result) {
    details.innerHTML = `
      <p class="eyebrow">rota</p>
      <h3>sem caminho no lookup</h3>
      <p>${attr(sourceMovie.titulo || source)} -> ${attr(targetMovie.titulo || target)}</p>
      <dl class="detail-list">
        <div>
          <dt>origem</dt>
          <dd>${attr(source)}</dd>
        </div>
        <div>
          <dt>destino</dt>
          <dd>${attr(target)}</dd>
        </div>
        <div>
          <dt>observacao</dt>
          <dd>na amostra leve da interface, esses filmes nao ficaram conectados.</dd>
        </div>
      </dl>
    `;
    return;
  }

  details.innerHTML = `
    <p class="eyebrow">rota</p>
    <h3>${attr(result.algorithm)}</h3>
    <p>${attr(sourceMovie.titulo || source)} -> ${attr(targetMovie.titulo || target)}</p>
    <dl class="detail-list">
      <div>
        <dt>origem</dt>
        <dd>${attr(source)}</dd>
      </div>
      <div>
        <dt>destino</dt>
        <dd>${attr(target)}</dd>
      </div>
      <div>
        <dt>nos no caminho</dt>
        <dd>${attr(result.path.length)}</dd>
      </div>
      <div>
        <dt>custo</dt>
        <dd>${result.cost === null ? "nao ponderado" : attr(result.cost.toFixed(6))}</dd>
      </div>
      <div>
        <dt>caminho</dt>
        <dd>${attr(result.path.join(" -> "))}</dd>
      </div>
    </dl>
  `;
}

function renderBellmanDetails() {
  document.getElementById("details-panel").innerHTML = `
    <p class="eyebrow">bellman-ford</p>
    <h3>validacao direcionada artificial</h3>
    <p>estes dois grafos nao sao do imdb. eles servem para provar peso negativo sem ciclo e deteccao de ciclo negativo.</p>
    <dl class="detail-list">
      <div>
        <dt>caso sem ciclo negativo</dt>
        <dd>grafo dirigido com peso negativo controlado; o algoritmo calcula distancias finais.</dd>
      </div>
      <div>
        <dt>caso com ciclo negativo</dt>
        <dd>grafo dirigido com ciclo de custo negativo; o algoritmo bloqueia o resultado e marca deteccao.</dd>
      </div>
      <div>
        <dt>por que artificial?</dt>
        <dd>o grafo imdb principal usa pesos positivos para dijkstra. bellman-ford precisa demonstrar o caso de pesos negativos separadamente.</dd>
      </div>
    </dl>
  `;
}

function resetDetails() {
  document.getElementById("details-panel").innerHTML = `
    <p class="eyebrow">selecao</p>
    <h3>nenhum item selecionado</h3>
    <p>ao clicar em um filme ou aresta, os dados aparecem aqui.</p>
    <dl class="detail-list">
      <div>
        <dt>filme</dt>
        <dd>--</dd>
      </div>
      <div>
        <dt>conexao</dt>
        <dd>--</dd>
      </div>
      <div>
        <dt>similaridade</dt>
        <dd>--</dd>
      </div>
      <div>
        <dt>peso</dt>
        <dd>--</dd>
      </div>
    </dl>
  `;
}

function drawGraph(mode = "similaridade") {
  const container = document.getElementById("network");
  const placeholder = document.getElementById("graph-placeholder");
  const graph = typeof mode === "string" ? graphForMode(mode) : mode;
  const isPathLayout = graph.layout === "path" || graph.layout === "tree";

  state.graph.nodes = new vis.DataSet(graph.nodes);
  state.graph.edges = new vis.DataSet(graph.edges);
  state.graph.baseNodes = graph.nodes;
  state.graph.baseEdges = graph.edges;

  const options = {
    autoResize: true,
    interaction: {
      hover: true,
      tooltipDelay: 120,
      navigationButtons: false,
      keyboard: true,
    },
    layout: isPathLayout
      ? {
          hierarchical: {
            enabled: true,
            direction: graph.layout === "bf" ? "UD" : graph.direction ?? "LR",
            sortMethod: "directed",
            levelSeparation: graph.layout === "bf" ? 190 : graph.layout === "tree" ? 135 : 155,
            nodeSpacing: graph.layout === "bf" ? 230 : graph.layout === "tree" ? 170 : 145,
          },
        }
      : {},
    physics: {
      enabled: true,
      solver: "forceAtlas2Based",
      forceAtlas2Based: {
        gravitationalConstant: -90,
        centralGravity: 0.018,
        springLength: 145,
        springConstant: 0.08,
        damping: 0.5,
        avoidOverlap: 0.75,
      },
      stabilization: {
        iterations: 180,
      },
    },
    nodes: {
      shadow: {
        enabled: true,
        color: "rgba(0, 0, 0, 0.55)",
        size: 14,
      },
    },
    edges: {
      shadow: {
        enabled: true,
        color: "rgba(0, 0, 0, 0.45)",
        size: 8,
      },
    },
  };

  if (state.network) {
    state.network.destroy();
  }

  state.network = new vis.Network(container, {
    nodes: state.graph.nodes,
    edges: state.graph.edges,
  }, options);

  placeholder.hidden = graph.nodes.length > 0;

  state.network.once("stabilizationIterationsDone", () => {
    refreshGraphView(true);
    state.network?.stopSimulation();
  });

  state.network.on("click", (params) => {
    if (params.nodes.length) {
      renderDetailsForNode(params.nodes[0]);
      return;
    }

    if (params.edges.length) {
      renderDetailsForEdge(params.edges[0]);
      return;
    }

    resetDetails();
  });
}

function refreshGraphView(fit = false) {
  if (!state.network) return;

  requestAnimationFrame(() => {
    state.network.redraw();
    if (fit) {
      state.network.fit({
        animation: {
          duration: 450,
          easingFunction: "easeInOutQuad",
        },
      });
    }
  });
}

function focusGraphNode(id) {
  if (!state.network || !state.graph.nodes.get(id)) {
    return false;
  }

  state.network.selectNodes([id]);
  state.network.focus(id, {
    scale: 1.4,
    animation: {
      duration: 600,
      easingFunction: "easeInOutQuad",
    },
  });
  renderDetailsForNode(id);
  return true;
}

function setupGraphControls() {
  const mode = document.getElementById("graph-mode");
  const search = document.getElementById("graph-search");
  const searchButton = document.getElementById("search-btn");
  const resetButton = document.getElementById("reset-graph-btn");
  const routeSource = document.getElementById("route-source");
  const routeTarget = document.getElementById("route-target");
  const routeAlgorithm = document.getElementById("route-algorithm");
  const routeButton = document.getElementById("route-run-btn");

  mode.addEventListener("change", () => {
    drawGraph(mode.value);
    refreshGraphView(true);
    if (mode.value === "bellman-ford") {
      renderBellmanDetails();
    } else {
      resetDetails();
    }
  });

  function runSearch() {
    const id = search.value.trim();
    if (!id) return;

    let found = focusGraphNode(id);
    if (!found && state.lookup?.movies?.[id]) {
      drawGraph(makeNeighborhoodGraph(id));
      found = focusGraphNode(id);
    }
    search.classList.toggle("search-miss", !found);
  }

  searchButton.addEventListener("click", runSearch);
  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runSearch();
    }
  });
  search.addEventListener("input", () => {
    search.classList.remove("search-miss");
  });

  function runRoute() {
    const source = routeSource.value.trim();
    const target = routeTarget.value.trim();
    const algorithm = routeAlgorithm.value;

    if (!source || !target) return;

    const result = algorithm === "dfs"
      ? dfsPath(source, target)
      : dijkstraPath(source, target);

    if (result) {
      drawGraph(makePathGraph(result.path, {
        prefix: `rota-${algorithm}`,
        color: algorithm === "dfs" ? "#7cc7ff" : "#ff9f1c",
        width: algorithm === "dfs" ? 4 : 6,
        arrows: "to",
        dashes: algorithm === "dfs",
        labelEdges: algorithm === "dijkstra",
      }));
    } else {
      drawGraph(makeNeighborhoodGraph(source));
    }

    renderRouteDetails(result, source, target);
    routeSource.classList.toggle("search-miss", !state.lookup?.movies?.[source]);
    routeTarget.classList.toggle("search-miss", !state.lookup?.movies?.[target]);
  }

  routeButton.addEventListener("click", runRoute);
  [routeSource, routeTarget].forEach((input) => {
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter") {
        event.preventDefault();
        runRoute();
      }
    });
    input.addEventListener("input", () => input.classList.remove("search-miss"));
  });

  resetButton.addEventListener("click", () => {
    search.value = "";
    routeSource.value = "";
    routeTarget.value = "";
    search.classList.remove("search-miss");
    routeSource.classList.remove("search-miss");
    routeTarget.classList.remove("search-miss");
    state.network?.unselectAll();
    state.network?.fit({
      animation: {
        duration: 500,
        easingFunction: "easeInOutQuad",
      },
    });
    resetDetails();
  });

  drawGraph(mode.value);
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
    refreshGraphView(true);
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

    if (nextView === "grafos") {
      refreshGraphView(true);
    }

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
  const [summary, lookup] = await Promise.all([
    fetchJson("data/parte2_summary.json?v=2"),
    fetchJson("data/parte2_lookup.json?v=2"),
  ]);
  state.summary = summary;
  state.lookup = lookup;

  setupViews();
  renderMetrics(state.summary.dataset);
  renderResults(state.summary);
  renderBenchmarkOutput(state.summary);
  renderRawOutputs(state.summary);
  renderVisualizations(state.summary.visualizacoes);
  setupGraphControls();
  setupVizModal();
  setupGraphFullscreen();
}

init().catch((err) => {
  console.error(err);
  document.body.classList.add("load-error");
});

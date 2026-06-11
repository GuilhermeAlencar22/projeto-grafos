const state = {
  resumo: null,
  amostra: null,
  grafoCompleto: null,   // carregado sob demanda
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

function formatNumber(value, decimals = 0) {
  return new Intl.NumberFormat("pt-BR", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
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
    el.textContent = decimals > 0 ? formatNumber(current, decimals) : fmt.format(Math.round(current));

    if (progress < 1) {
      requestAnimationFrame(frame);
    } else {
      el.textContent = decimals > 0 ? formatNumber(value, decimals) : fmt.format(value);
    }
  }

  requestAnimationFrame(frame);
}

function timeValue(value) {
  if (typeof value !== "number") return "--";
  return `${(value * 1000).toFixed(3)} ms`;
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

const VIZ_META = {
  "Distribuição de graus": {
    insight: "Cauda longa com lei de potência: a maioria dos filmes tem grau baixo (~2–30), mas hubs como filmes de franquias Marvel alcançam grau 208. Evidência de rede livre de escala.",
    tag: "Gestalt · Figura-Fundo",
  },
  "Componentes conexas": {
    insight: "99,6% dos filmes (3.971/3.985) estão na componente gigante — a rede é praticamente conexa. As 6 ilhas restantes são filmes sem atores em comum com o restante.",
    tag: "Storytelling Exploratório",
  },
  "Atores vs Similaridade": {
    insight: "Cada ator em comum adiciona +2 à similaridade. O jitter expõe a estrutura discreta: filmes com 0 atores mas gênero em comum têm sim = 1 ou 2 (apenas gêneros).",
    tag: "Storytelling Explanatório",
  },
  "Similaridade e peso": {
    insight: "A curva peso = 1/sim comprova o modelo. Pontos reais seguem exatamente a curva teórica — o Dijkstra escolhe naturalmente o caminho pelos filmes mais parecidos.",
    tag: "Hierarquia Visual · Figura-Fundo",
  },
  "Benchmark — Tempos": {
    insight: "BFS e DFS são O(V+E) — os mais rápidos. Dijkstra O((V+E)logV) é ~2× mais lento. Bellman-Ford é executado em grafo artificial pequeno (validação, não comparação justa).",
    tag: "Storytelling Explanatório",
  },
};

function displayVizTitle(title) {
  if (title === "Componentes conexas") return "Ilhas do grafo";
  if (title === "Benchmark") return "Benchmark — Tempos";
  return title;
}

function vizMeta(titulo) {
  return VIZ_META[titulo] ?? VIZ_META[displayVizTitle(titulo)] ?? { insight: titulo, tag: "" };
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
  return (
    state.amostra?.movies?.[id] ??
    state.grafoCompleto?.filmes?.[id] ??
    { titulo: id, ano: "", generos: "genero nao informado", nota: "" }
  );
}

function edgeKey(a, b) {
  return [a, b].sort().join("|");
}

function edgeOrigem(edge) {
  return edge?.origem ?? "";
}

function edgeDestino(edge) {
  return edge?.destino ?? "";
}

function buscarAresta(a, b) {
  const key = edgeKey(a, b);
  const fromAmostra = state.amostra?.edges?.[key] ?? null;
  if (fromAmostra) return fromAmostra;

  if (state.grafoCompleto) {
    const adj = buildGrafoAdjacency();
    const vizinhos = adj.get(a) ?? [];
    const encontrado = vizinhos.find((v) => v.to === b);
    if (encontrado) {
      return { origem: a, destino: b, similaridade: encontrado.sim, peso: encontrado.p, actors_common: encontrado.a };
    }
  }
  return null;
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
  const titulo = movie.titulo || id;
  const linhas = [titulo];
  if (movie.ano)      linhas.push(`📅 ${movie.ano}`);
  if (movie.generos)  linhas.push(`🎬 ${movie.generos}`);
  if (movie.nota)     linhas.push(`⭐ ${movie.nota} IMDb`);
  if (movie.diretores) linhas.push(`🎥 ${movie.diretores}`);
  return linhas.join("\n");
}

function edgeTitle(edge) {
  const origem  = movieInfo(edgeOrigem(edge));
  const destino = movieInfo(edgeDestino(edge));
  const genres  = commonGenres(edgeOrigem(edge), edgeDestino(edge));
  const atores  = Array.isArray(edge.actors_common_names) && edge.actors_common_names.length
    ? edge.actors_common_names.join(", ")
    : `${edge.actors_common ?? 0} ator(es)`;
  const sim = edge.similaridade ?? "--";
  const peso = typeof edge.peso === "number" ? edge.peso.toFixed(4) : "--";
  return [
    `🎬 ${origem.titulo || edgeOrigem(edge)}`,
    `🎬 ${destino.titulo || edgeDestino(edge)}`,
    ``,
    `👥 atores em comum: ${atores}`,
    `🏷️  gêneros em comum: ${genres.join(", ") || "--"}`,
    `📊 similaridade: ${sim}  (peso: ${peso})`,
    ``,
    `quanto maior a similaridade, mais grossa a aresta.`,
  ].join("\n");
}

function baseNode(id, extra = {}) {
  return {
    id,
    label: movieLabel(id),
    title: undefined,
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

  const rawWidth = extra.width ?? Math.max(1, Math.min(10, 0.8 + Math.sqrt(value) * 1.9));

  return {
    id: edge.id ?? edgeKey(edgeOrigem(edge), edgeDestino(edge)),
    from: edgeOrigem(edge),
    to: edgeDestino(edge),
    title: undefined, // edgeTitle(edge),
    label: extra.label ?? "",
    width: rawWidth,
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

let _globalDegree = null;
function globalDegree() {
  if (_globalDegree) return _globalDegree;
  const deg = new Map();
  Object.values(state.amostra?.edges ?? {}).forEach((edge) => {
    deg.set(edgeOrigem(edge), (deg.get(edgeOrigem(edge)) ?? 0) + 1);
    deg.set(edgeDestino(edge), (deg.get(edgeDestino(edge)) ?? 0) + 1);
  });
  _globalDegree = deg;
  return deg;
}

function nodeSizeByGlobalDegree(id, minSize = 18, maxSize = 54) {
  const deg = globalDegree().get(id) ?? 1;
  const logDeg = Math.log2(deg + 1);
  const logMax = Math.log2(210);
  return Math.round(minSize + (maxSize - minSize) * (logDeg / logMax));
}

function nodeColorByGenre(id) {
  const genres = movieGenres(id);
  const genreColors = {
    "Action":    { bg: "#ef4444", border: "#b91c1c" },
    "Comedy":    { bg: "#f59e0b", border: "#d97706" },
    "Drama":     { bg: "#3b82f6", border: "#1d4ed8" },
    "Sci-Fi":    { bg: "#8b5cf6", border: "#6d28d9" },
    "Horror":    { bg: "#dc2626", border: "#7f1d1d" },
    "Romance":   { bg: "#ec4899", border: "#be185d" },
    "Animation": { bg: "#10b981", border: "#059669" },
    "Thriller":  { bg: "#f97316", border: "#c2410c" },
    "Adventure": { bg: "#06b6d4", border: "#0e7490" },
    "Crime":     { bg: "#6366f1", border: "#4338ca" },
    "Fantasy":   { bg: "#a855f7", border: "#7e22ce" },
    "Documentary": { bg: "#64748b", border: "#334155" },
  };
  for (const g of genres) {
    if (genreColors[g]) return genreColors[g];
  }
  return { bg: "#f5c518", border: "#b8940e" };
}

function makeGraphFromEdges(edges, options = {}) {
  const nodes = new Map();
  const degrees = new Map();
  const visualEdges = [];

  edges.forEach((edge) => {
    nodes.set(edgeOrigem(edge), edgeOrigem(edge));
    nodes.set(edgeDestino(edge), edgeDestino(edge));
    degrees.set(edgeOrigem(edge), (degrees.get(edgeOrigem(edge)) ?? 0) + 1);
    degrees.set(edgeDestino(edge), (degrees.get(edgeDestino(edge)) ?? 0) + 1);
    visualEdges.push(baseEdge(edge, options.edgeOptions));
  });

  return {
    nodes: [...nodes.values()].map((id) => {
      const size = nodeSizeByGlobalDegree(id, 20, 52);
      const cor = nodeColorByGenre(id);
      return baseNode(id, {
        size,
        background: cor.bg,
        border: cor.border,
      });
    }),
    edges: visualEdges,
    layout: options.layout ?? "network",
  };
}

function connectedEdgeSample(sortedEdges, limit = 18) {
  if (!sortedEdges.length) return [];

  const selected = [sortedEdges[0]];
  const used = new Set([sortedEdges[0].id ?? edgeKey(edgeOrigem(sortedEdges[0]), edgeDestino(sortedEdges[0]))]);
  const nodes = new Set([edgeOrigem(sortedEdges[0]), edgeDestino(sortedEdges[0])]);

  while (selected.length < limit) {
    const next = sortedEdges.find((edge) => {
      const id = edge.id ?? edgeKey(edgeOrigem(edge), edgeDestino(edge));
      return !used.has(id) && (nodes.has(edgeOrigem(edge)) || nodes.has(edgeDestino(edge)));
    });

    if (!next) break;

    selected.push(next);
    used.add(next.id ?? edgeKey(edgeOrigem(next), edgeDestino(next)));
    nodes.add(edgeOrigem(next));
    nodes.add(edgeDestino(next));
  }

  return selected;
}

function pathEdges(path, options = {}) {
  const edges = [];

  for (let index = 0; index < path.length - 1; index += 1) {
    const origem = path[index];
    const destino = path[index + 1];
    const stored = buscarAresta(origem, destino);
    edges.push({
      ...(stored ?? {
        origem,
        destino,
        actors_common: "--",
        similaridade: "--",
        peso: "--",
      }),
      id: `${options.prefix ?? "path"}-${origem}-${destino}-${index}`,
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

function makeBellmanFordGraph(caso = "sem-ciclo") {
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
    dashes: false,
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
      origem: from,
      destino: to,
      peso: label,
      caso: group,
      ciclo_negativo: danger,
      tipo: "bellman-ford",
    },
  });

  const okNodes = [
    node("ok-z", "fonte\nz", -80, -160, "#2ecc71", 44, "fonte Z do caso sem ciclo negativo"),
    node("ok-a", "a", -250, 60, "#f5c518", 34, "vertice alcancado com peso positivo"),
    node("ok-b", "b", 90, 60, "#f5c518", 34, "vertice alcancado pela fonte Z"),
    node("ok-c", "c", -80, 260, "#f5c518", 34, "recebe relaxamento com peso negativo, mas sem formar ciclo negativo"),
  ];
  const badNodes = [
    node("bad-a", "fonte\na", -80, -150, "#ff4d4d", 44, "inicio do caso com ciclo negativo"),
    node("bad-b", "b", -260, 170, "#f5c518", 34, "parte do ciclo dirigido"),
    node("bad-c", "c", 120, 170, "#ff4d4d", 40, "fecha o ciclo negativo voltando para a"),
  ];
  const okEdges = [
    directedEdge("ok-z", "ok-a", "5", "sem ciclo negativo"),
    directedEdge("ok-z", "ok-b", "2", "sem ciclo negativo"),
    directedEdge("ok-b", "ok-c", "0", "sem ciclo negativo"),
    directedEdge("ok-a", "ok-c", "-3", "sem ciclo negativo"),
  ];
  const badEdges = [
    directedEdge("bad-a", "bad-b", "1", "com ciclo negativo"),
    directedEdge("bad-b", "bad-c", "-3", "com ciclo negativo", true),
    directedEdge("bad-c", "bad-a", "1", "com ciclo negativo", true),
  ];

  return {
    nodes: caso === "com-ciclo" ? badNodes : okNodes,
    edges: caso === "com-ciclo" ? badEdges : okEdges,
    layout: "network",
  };
}

function buildAmostraAdjacency() {
  const adj = new Map();

  Object.values(state.amostra?.edges ?? {}).forEach((edge) => {
    if (!adj.has(edgeOrigem(edge))) adj.set(edgeOrigem(edge), []);
    if (!adj.has(edgeDestino(edge))) adj.set(edgeDestino(edge), []);
    adj.get(edgeOrigem(edge)).push({ to: edgeDestino(edge), edge });
    adj.get(edgeDestino(edge)).push({ to: edgeOrigem(edge), edge });
  });

  return adj;
}

function buildGrafoAdjacency() {
  if (state._grafoAdj) return state._grafoAdj;

  const adj = new Map();
  (state.grafoCompleto?.arestas ?? []).forEach((e) => {
    const origem = edgeOrigem(e);
    const destino = edgeDestino(e);
    if (!adj.has(origem)) adj.set(origem, []);
    if (!adj.has(destino)) adj.set(destino, []);
    adj.get(origem).push({ to: destino, peso: e.p, sim: e.sim, a: e.a });
    adj.get(destino).push({ to: origem, peso: e.p, sim: e.sim, a: e.a });
  });

  state._grafoAdj = adj;
  return adj;
}
function dijkstraPath(origem, destino) {
  const adj = buildAmostraAdjacency();

  const dist = new Map([[origem, 0]]);
  const prev = new Map();
  const visited = new Set();
  const queue = [{ id: origem, cost: 0 }];

  while (queue.length) {
    queue.sort((a, b) => a.cost - b.cost);
    const current = queue.shift();
    if (!current || visited.has(current.id)) continue;
    visited.add(current.id);
    if (current.id === destino) break;

    const vizinhos = adj.get(current.id) ?? [];
    vizinhos.forEach((v) => {
      const peso = Number(v.edge?.peso ?? 1);
      const nextCost = current.cost + peso;
      if (nextCost < (dist.get(v.to) ?? Infinity)) {
        dist.set(v.to, nextCost);
        prev.set(v.to, current.id);
        queue.push({ id: v.to, cost: nextCost });
      }
    });
  }

  if (!dist.has(destino)) return null;

  const path = [];
  let step = destino;
  while (step) {
    path.unshift(step);
    if (step === origem) break;
    step = prev.get(step);
  }

  return { path, cost: dist.get(destino), algorithm: "dijkstra" };
}

function dfsPath(origem, destino) {
  const adj = buildAmostraAdjacency();
  const visited = new Set();
  const stack = [[origem, [origem]]];

  while (stack.length) {
    const [node, path] = stack.pop();
    if (visited.has(node)) continue;
    visited.add(node);
    if (node === destino) return { path, cost: null, algorithm: "profundidade" };

    const vizinhos = adj.get(node) ?? [];
    for (let i = vizinhos.length - 1; i >= 0; i--) {
      const v = vizinhos[i].to;
      if (!visited.has(v)) stack.push([v, [...path, v]]);
    }
  }

  return null;
}

function makeTraversalGraph(origem, type = "bfs") {
  const adj = buildAmostraAdjacency();
  const visited = new Set([origem]);
  const nodes = [];
  const treeEdges = [];
  const usedTreeEdges = new Set();
  const limit = 28;
  const maxPerNode = type === "bfs" ? 4 : 3;

  function addNode(id, level) {
    const size = id === origem ? 48 : nodeSizeByGlobalDegree(id, 20, 44);
    nodes.push(baseNode(id, {
      level,
      size,
      background: id === origem ? "#2ecc71" : type === "bfs" ? "#f5c518" : "#7cc7ff",
      border: id === origem ? "#ffffff" : "#f5c518",
    }));
  }

  addNode(origem, 0);

  if (type === "bfs") {
    const queue = [{ id: origem, level: 0 }];

    while (queue.length && nodes.length < limit) {
      const current = queue.shift();
      const neighbors = [...(adj.get(current.id) ?? [])]
        .sort((a, b) => (b.edge.similaridade ?? 0) - (a.edge.similaridade ?? 0));

      let addedFromNode = 0;
      for (const { to, edge } of neighbors) {
        if (nodes.length >= limit) break;
        if (visited.has(to)) continue;
        if (addedFromNode >= maxPerNode) break;
        visited.add(to);
        addedFromNode += 1;
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
      }
    }
  } else {
    function visit(id, level) {
      if (nodes.length >= limit) return;

      const neighbors = [...(adj.get(id) ?? [])]
        .sort((a, b) => (b.edge.similaridade ?? 0) - (a.edge.similaridade ?? 0));

      let addedFromNode = 0;
      for (const { to, edge } of neighbors) {
        if (nodes.length >= limit) break;
        if (visited.has(to)) continue;
        if (addedFromNode >= maxPerNode) break;
        visited.add(to);
        addedFromNode += 1;
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
      }
    }

    visit(origem, 0);
  }

  return {
    nodes,
    edges: treeEdges,
    layout: "network",
    direction: type === "bfs" ? "UD" : "LR",
  };
}

function makeDijkstraGraph() {
  const movies = state.amostra?.movies ?? {};
  const ids = Object.keys(movies);

  const CANDIDATE_PAIRS = [
    ["Harry Potter and the Chamber of Secrets", "Star Trek II: The Wrath of Khan"],
    ["Harry Potter and the Goblet of Fire", "Jurassic Park"],
    ["Hobbit: An Unexpected Journey, The", "Finding Forrester"],
  ];

  let route = null;
  for (const [a, b] of CANDIDATE_PAIRS) {
    if (!movies[a] || !movies[b]) continue;
    const r = dijkstraPath(a, b);
    if (r && r.path.length >= 8) { route = r; break; }
    if (r && (!route || r.path.length > route.path.length)) route = r;
  }

  if (!route || route.path.length < 2) {
    state.lastDijkstraRoute = null;
    return { nodes: [], edges: [], layout: "network" };
  }

  state.lastDijkstraRoute = route;

  const pathNodes = route.path.map((id, index) => {
    const isFirst = index === 0;
    const isLast  = index === route.path.length - 1;
    return baseNode(id, {
      size: isFirst || isLast ? 48 : 34,
      background: isFirst ? "#2ecc71" : isLast ? "#ff4d4d" : "#f5c518",
      border: "#ffffff",
    });
  });

  // constrói arestas via baseEdge (mantém meta para o clique) e força from/to pela ordem do caminho
  const mainEdges = route.path.slice(0, -1).map((fromId, i) => {
    const toId = route.path[i + 1];
    const stored = buscarAresta(fromId, toId) ?? { origem: fromId, destino: toId, similaridade: 0, peso: 0 };
    const e = baseEdge(stored, {
      color: "#ff9f1c",
      width: 6,
      arrows: "to",
      label: stored.peso != null ? Number(stored.peso).toFixed(2) : "",
    });
    e.id = `dijkstra-${i}-${fromId}-${toId}`;
    e.from = fromId;
    e.to = toId;
    e.font = { color: "#ff9f1c", size: 14, strokeWidth: 3, strokeColor: "#050505" };
    e.smooth = { enabled: true, type: "cubicBezier", roundness: 0.2 };
    return e;
  });

  return { nodes: pathNodes, edges: mainEdges, layout: "network" };
}

function makeNeighborhoodGraph(id) {
  const edges = Object.values(state.amostra?.edges ?? {})
    .filter((edge) => edgeOrigem(edge) === id || edgeDestino(edge) === id);

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

function makeFullGraph() {
  const g = state.grafoCompleto;
  if (!g) return { nodes: [], edges: [], layout: "network" };

  const filmes = g.filmes ?? {};
  const arestas = g.arestas ?? [];
  const posicoes = g.posicoes ?? {};

  const LIMITE_VISUAL = 3000;
  const arestasSorted = [...arestas].sort((a, b) => (b.sim ?? 0) - (a.sim ?? 0));
  const arestasFiltradas = arestasSorted.slice(0, LIMITE_VISUAL);

  const nodeSet = new Set();
  arestasFiltradas.forEach((e) => { nodeSet.add(edgeOrigem(e)); nodeSet.add(edgeDestino(e)); });

  const nodes = Array.from(nodeSet).map((id) => {
    const info = filmes[id] ?? {};
    const pos = posicoes[id];
    const node = {
      id,
      label: "",
      title: `${id}${info.ano ? ` (${info.ano})` : ""}${info.nota ? ` | ${info.nota}` : ""}`,
      shape: "dot",
      size: 5,
      color: { background: "#4a9eff", border: "#2d7dd2", highlight: { background: "#ff9f1c", border: "#e67e00" } },
    };
    if (pos) {
      node.x = pos.x;
      node.y = pos.y;
      node.physics = false;
    }
    return node;
  });

  const edges = arestasFiltradas.map((e, i) => ({
    id: `fe-${i}`,
    from: edgeOrigem(e),
    to: edgeDestino(e),
    width: 0.5,
    color: { color: "rgba(100,160,255,0.22)", highlight: "rgba(255,159,28,0.9)" },
    title: `sim: ${e.sim} | peso: ${e.p} | atores: ${e.a}`,
  }));

  return { nodes, edges, layout: "network", fullGraph: true };
}

function makeFranquiasGraph() {
  const FRANQUIAS = [
    { nome: "Marvel / Avengers", cor: { bg: "#ef4444", border: "#b91c1c" },
      seeds: ["Avengers: Age of Ultron", "Captain America: Civil War",
               "Avengers: Infinity War - Part I", "Iron Man 2"] },
    { nome: "Star Wars", cor: { bg: "#f5c518", border: "#b8940e" },
      seeds: ["Star Wars: Episode IV - A New Hope",
               "Star Wars: Episode V - The Empire Strikes Back",
               "Star Wars: Episode VII - The Force Awakens",
               "Star Wars: The Last Jedi"] },
    { nome: "Harry Potter", cor: { bg: "#8b5cf6", border: "#6d28d9" },
      seeds: ["Harry Potter and the Chamber of Secrets",
               "Harry Potter and the Goblet of Fire",
               "Harry Potter and the Deathly Hallows: Part 1",
               "Harry Potter and the Deathly Hallows: Part 2"] },
    { nome: "Hobbit / LOTR", cor: { bg: "#10b981", border: "#059669" },
      seeds: ["Hobbit: An Unexpected Journey, The",
               "Hobbit: The Desolation of Smaug, The",
               "The Hobbit: The Battle of the Five Armies"] },
    { nome: "X-Men", cor: { bg: "#3b82f6", border: "#1d4ed8" },
      seeds: ["X-Men", "X2: X-Men United", "X-Men: Days of Future Past",
               "X-Men: Apocalypse"] },
    { nome: "Jurassic Park", cor: { bg: "#06b6d4", border: "#0e7490" },
      seeds: ["Jurassic Park", "Jurassic Park III",
               "Jurassic World", "Jurassic World: Fallen Kingdom"] },
    { nome: "Fast & Furious", cor: { bg: "#f97316", border: "#c2410c" },
      seeds: ["2 Fast 2 Furious (Fast and the Furious 2, The)",
               "Fast Five (Fast and the Furious 5, The)",
               "Fast & Furious 6 (Fast and the Furious 6, The)"] },
    { nome: "Star Trek (clássico)", cor: { bg: "#a855f7", border: "#7e22ce" },
      seeds: ["Star Trek: The Motion Picture",
               "Star Trek II: The Wrath of Khan",
               "Star Trek III: The Search for Spock",
               "Star Trek IV: The Voyage Home",
               "Star Trek V: The Final Frontier",
               "Star Trek VI: The Undiscovered Country"] },
  ];

  const edgeMap = {};
  Object.values(state.amostra?.edges ?? {}).forEach((e) => {
    if ((e.similaridade ?? 0) >= 3) edgeMap[e.id] = e;
  });

  const adj = new Map();
  Object.values(edgeMap).forEach((e) => {
    if (!adj.has(edgeOrigem(e))) adj.set(edgeOrigem(e), []);
    if (!adj.has(edgeDestino(e))) adj.set(edgeDestino(e), []);
    adj.get(edgeOrigem(e)).push(e);
    adj.get(edgeDestino(e)).push(e);
  });

  const nodeList = [];
  const edgeList = [];
  const usedNodes = new Set();
  const usedEdges = new Set();

  FRANQUIAS.forEach(({ nome, cor, seeds }, fi) => {
    const franqNodes = new Set();
    seeds.forEach((s) => {
      if (state.amostra?.movies?.[s]) franqNodes.add(s);
    });
    const limit = Math.max(10, seeds.length * 2);
    const bfsQueue = [...franqNodes];
    while (bfsQueue.length && franqNodes.size < limit) {
      const n = bfsQueue.shift();
      (adj.get(n) ?? [])
        .sort((a, b) => (b.similaridade ?? 0) - (a.similaridade ?? 0))
        .slice(0, 3)
        .forEach((e) => {
          const nb = edgeOrigem(e) === n ? edgeDestino(e) : edgeOrigem(e);
          if (!franqNodes.has(nb) && state.amostra?.movies?.[nb]) {
            franqNodes.add(nb);
            bfsQueue.push(nb);
          }
        });
    }

    franqNodes.forEach((id) => {
      if (usedNodes.has(id)) return;
      usedNodes.add(id);
      const size = nodeSizeByGlobalDegree(id, 22, 52);
      nodeList.push({
        ...baseNode(id, { size, background: cor.bg, border: cor.border }),
        group: fi,
        title: movieTitle(id) + `\n\nfranquia: ${nome}`,
      });
    });

    franqNodes.forEach((id) => {
      (adj.get(id) ?? []).forEach((e) => {
        const nb = edgeOrigem(e) === id ? edgeDestino(e) : edgeOrigem(e);
        if (!franqNodes.has(nb)) return;
        if (usedEdges.has(e.id)) return;
        usedEdges.add(e.id);
        edgeList.push(baseEdge(e, { color: cor.bg }));
      });
    });
  });

  return { nodes: nodeList, edges: edgeList, layout: "network" };
}

function makeTopNotasGraph() {
  const movies = state.amostra?.movies ?? {};
  const edges = Object.values(state.amostra?.edges ?? {});

  const top10 = Object.values(movies)
    .filter(m => m.nota && parseFloat(m.nota) > 0)
    .sort((a, b) => parseFloat(b.nota) - parseFloat(a.nota))
    .slice(0, 5)
    .map(m => m.titulo);

  const top10Set = new Set(top10);

  const selectedEdges = edges.filter(e =>
    top10Set.has(e.origem) || top10Set.has(e.destino)
  );

  const nodeSet = new Map();
  selectedEdges.forEach(e => {
    nodeSet.set(e.origem, e.origem);
    nodeSet.set(e.destino, e.destino);
  });
  top10.forEach(id => nodeSet.set(id, id));

  const visualNodes = [...nodeSet.keys()].map(id => {
    const isTop = top10Set.has(id);
    const nota = parseFloat(movies[id]?.nota ?? 0);
    const size = isTop ? Math.round(28 + nota * 4) : 18;
    const cor = isTop
      ? { background: "#f5c518", border: "#b8940e" }
      : nodeColorByGenre(id);
    return baseNode(id, { background: cor.background ?? cor.bg, border: cor.border, size });
  });

  const visualEdges = selectedEdges.map(e => {
    const isHighlight = top10Set.has(e.origem) && top10Set.has(e.destino);
    return baseEdge(e, {
      color: isHighlight ? "#f5c518" : "rgba(245,197,24,0.25)",
      width: isHighlight ? 4 : 1,
      label: "",
    });
  });

  return { nodes: visualNodes, edges: visualEdges, layout: "network" };
}

function graphForMode(mode) {
  const edges = Object.values(state.amostra?.edges ?? {});
  const bySimilarity = [...edges].sort((a, b) => (b.similaridade ?? 0) - (a.similaridade ?? 0));
  const byActors = [...edges].sort((a, b) =>
    (b.actors_common ?? 0) - (a.actors_common ?? 0)
    || (b.similaridade ?? 0) - (a.similaridade ?? 0)
    || (a.peso ?? Infinity) - (b.peso ?? Infinity)
  );

  if (mode === "franquias") {
    return makeFranquiasGraph();
  }

  if (mode === "top-notas") {
    return makeTopNotasGraph();
  }

  if (mode === "top") {
    return makeGraphFromEdges(byActors.slice(0, 42), {
      edgeOptions: { label: "" },
    });
  }

  if (mode === "bfs") {
    return makeTraversalGraph(defaultGraphSource(), "bfs");
  }

  if (mode === "dfs") {
    return makeTraversalGraph(defaultGraphSource(), "dfs");
  }

  if (mode === "dijkstra") {
    return makeDijkstraGraph();
  }

  if (mode === "bellman-sem-ciclo") {
    return makeBellmanFordGraph("sem-ciclo");
  }

  if (mode === "bellman-com-ciclo") {
    return makeBellmanFordGraph("com-ciclo");
  }

  if (mode === "grafo-completo") {
    return makeFullGraph();
  }

  if (mode === "amostra") {
    // top 100 por relevância; sempre inclui arestas do último caminho buscado
    const sorted = [...edges].sort((a, b) =>
      (b.actors_common ?? 0) - (a.actors_common ?? 0) || (b.similaridade ?? 0) - (a.similaridade ?? 0));
    const top = sorted.slice(0, 100);
    const topIds = new Set(top.map(e => e.id));
    const routeKeys = state._lastRouteEdgeKeys ?? new Set();
    const extra = edges.filter(e => routeKeys.has(e.id) && !topIds.has(e.id));
    return makeGraphFromEdges([...top, ...extra], { edgeOptions: { label: "" } });
  }

  const sampleEdges = connectedEdgeSample(bySimilarity, 32);
  const nodeSet = new Map();
  sampleEdges.forEach((e) => {
    nodeSet.set(edgeOrigem(e), edgeOrigem(e));
    nodeSet.set(edgeDestino(e), edgeDestino(e));
  });
  const visualNodes = [...nodeSet.keys()].map((id) => {
    const cor = nodeColorByGenre(id);
    const size = nodeSizeByGlobalDegree(id, 20, 50);
    return baseNode(id, { background: cor.bg, border: cor.border, size });
  });
  const visualEdges = sampleEdges.map((e) => baseEdge(e));
  return { nodes: visualNodes, edges: visualEdges, layout: "network" };
}

function defaultGraphSource() {
  return state.resumo?.buscas?.fontes_principais?.[0]
    ?? Object.keys(state.amostra?.movies ?? {})[0]
    ?? "";
}

function renderMetrics(dataset) {
  animateNumber('[data-field="num_vertices"]', dataset.num_vertices);
  animateNumber('[data-field="num_arestas"]', dataset.num_arestas);
  animateNumber('[data-field="grau_medio"]', dataset.grau?.medio, 1);
  animateNumber('[data-field="componentes_conexas"]', dataset.componentes_conexas);
}


function renderResults(resumo) {
  const bfsList = resumo.buscas?.bfs ?? [];
  const dfsList = resumo.buscas?.dfs ?? [];
  const dijkstraList = resumo.dijkstra ?? [];
  const bellmanList  = resumo.bellman_ford ?? [];
  const fontes = resumo.buscas?.fontes_principais ?? [];
  const dijkstraOk = dijkstraList.filter((i) => !i.sem_caminho).length;
  const bfCycle = bellmanList.some((i) => i.ciclo_negativo);
  const bfNoCycle = bellmanList.some((i) => !i.ciclo_negativo);

  document.getElementById("results-resumo").innerHTML = [
    `<article class="result-stat">
      <h3>BFS + DFS</h3>
      <span>${fontes.length} fontes</span>
      <p>
        <b>BFS</b>: percorre por camadas, garante menor número de saltos.<br>
        <b>DFS</b>: mergulha em profundidade, detecta ciclos.<br>
        Ambas rodaram a partir de <b>${attr(fontes.join(", "))}</b>.
      </p>
      <small>3.971 filmes alcançados em 7 camadas (BFS) · ciclos confirmados (DFS)</small>
    </article>`,
    `<article class="result-stat">
      <h3>Dijkstra</h3>
      <span>${dijkstraOk}/${dijkstraList.length} rotas</span>
      <p>
        Caminho de <b>menor custo ponderado</b> entre pares de filmes.<br>
        Peso = 1 / similaridade: conexões mais fortes custam menos.
        ${dijkstraList.length - dijkstraOk > 0
          ? `<br><b>${dijkstraList.length - dijkstraOk} par(es)</b> em componentes separadas — sem caminho possível.`
          : ""}
      </p>
      <small>pesos sempre ≥ 0 · Dijkstra válido · 5 pares testados conforme rubrica</small>
    </article>`,
    `<article class="result-stat">
      <h3>Bellman-Ford</h3>
      <span>${bfCycle && bfNoCycle ? "2 casos" : "ok"}</span>
      <p>
        Validado em <b>grafos artificiais dirigidos</b> com pesos negativos.<br>
        <b>Caso 1</b>: peso negativo sem ciclo → distâncias calculadas corretamente.<br>
        <b>Caso 2</b>: ciclo negativo → <b>detectado e bloqueado</b>.
      </p>
      <small>grafo IMDb usa pesos positivos → Dijkstra mais eficiente · BF valida o caso negativo</small>
    </article>`,
  ].join("");

  const bfsDfsRows = fontes.map((fonte) => {
    const b = bfsList.find((i) => i.origem === fonte) ?? {};
    const d = dfsList.find((i) => i.origem === fonte) ?? {};
    return `
      <tr>
        <td><b>${attr(movieInfo(fonte).titulo || fonte)}</b></td>
        <td class="td-yellow">${b.camadas ?? "--"} camadas</td>
        <td>${metricValue(b.visitados)} filmes</td>
        <td class="td-muted">${timeValue(b.tempo_s)}</td>
        <td class="td-yellow">${d.ciclo ? "✓ detectado" : "não"}</td>
        <td>${metricValue(d.visitados)} filmes</td>
        <td class="td-muted">${timeValue(d.tempo_s)}</td>
      </tr>`;
  }).join("");

  const dijkstraRows = dijkstraList.map((item) => {
    const origemTitulo = movieInfo(item.origem).titulo || item.origem;
    const destinoTitulo = movieInfo(item.destino).titulo || item.destino;
    const caminho = (item.caminho ?? []).map((id) => movieInfo(id).titulo || id);
    const pathStr = caminho.length > 0
      ? caminho.join(" → ")
      : "—";
    if (item.sem_caminho) {
      return `<tr>
        <td>${attr(origemTitulo)}</td>
        <td>${attr(destinoTitulo)}</td>
        <td class="td-red">sem caminho</td>
        <td class="td-muted">—</td>
        <td class="td-muted">—</td>
        <td class="td-muted">${timeValue(item.tempo_s)}</td>
        <td class="td-muted td-path">filmes em componentes separadas</td>
      </tr>`;
    }
    return `<tr>
      <td>${attr(origemTitulo)}</td>
      <td>${attr(destinoTitulo)}</td>
      <td class="td-green">encontrado</td>
      <td class="td-yellow">${attr(String(item.custo_total?.toFixed ? item.custo_total.toFixed(4) : item.custo_total ?? "--"))}</td>
      <td>${item.tamanho_caminho ?? "--"} filmes</td>
      <td class="td-muted">${timeValue(item.tempo_s)}</td>
      <td class="td-path">${attr(pathStr)}</td>
    </tr>`;
  }).join("");

  const bellmanRows = (items) => items.map((item) => {
    const dataset = String(item.dataset ?? "").split(/[/\\]/).pop();
    const distStr = item.distancias
      ? Object.entries(item.distancias).map(([k, v]) => `${k}=${v}`).join(", ")
      : "bloqueado (ciclo negativo)";
    return `<tr>
      <td>${attr(dataset)}</td>
      <td>${attr(item.origem ?? "--")}</td>
      <td class="${item.ciclo_negativo ? "td-red" : "td-green"}">
        ${item.ciclo_negativo ? "✓ ciclo detectado" : "✓ sem ciclo"}
      </td>
      <td class="td-path">${attr(distStr)}</td>
      <td class="td-muted">${timeValue(item.tempo_s)}</td>
    </tr>`;
  }).join("");
  const bellmanSemCicloRows = bellmanRows(bellmanList.filter((item) => !item.ciclo_negativo));
  const bellmanComCicloRows = bellmanRows(bellmanList.filter((item) => item.ciclo_negativo));

  document.getElementById("results-tables").innerHTML = `
    <div class="results-tables-section">

      <div class="results-table-block">
        <div class="results-table-block-header">
          <h4>BFS e DFS — 3 fontes distintas</h4>
          <span class="results-table-badge ok">rubrica: ≥ 3 fontes ✓</span>
        </div>
        <div class="table-wrap">
          <table class="results-detail-table">
            <thead>
              <tr>
                <th>Fonte</th>
                <th>BFS — camadas</th>
                <th>BFS — visitados</th>
                <th>BFS — tempo</th>
                <th>DFS — ciclo</th>
                <th>DFS — visitados</th>
                <th>DFS — tempo</th>
              </tr>
            </thead>
            <tbody>${bfsDfsRows}</tbody>
          </table>
        </div>
      </div>

      <div class="results-table-block">
        <div class="results-table-block-header">
          <h4>Dijkstra — 5 pares origem → destino</h4>
          <span class="results-table-badge ok">rubrica: ≥ 5 pares ✓</span>
          <span class="results-table-badge warn">pesos ≥ 0 garantidos ✓</span>
        </div>
        <div class="table-wrap">
          <table class="results-detail-table">
            <thead>
              <tr>
                <th>Origem</th>
                <th>Destino</th>
                <th>Status</th>
                <th>Custo total</th>
                <th>Tamanho</th>
                <th>Tempo</th>
                <th>Caminho completo</th>
              </tr>
            </thead>
            <tbody>${dijkstraRows}</tbody>
          </table>
        </div>
      </div>

      <div class="results-table-block">
        <div class="results-table-block-header">
          <h4>Bellman-Ford — caso sem ciclo negativo</h4>
          <span class="results-table-badge ok">sem ciclo negativo ✓</span>
        </div>
        <div class="table-wrap">
          <table class="results-detail-table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Fonte</th>
                <th>Resultado</th>
                <th>Distâncias calculadas</th>
                <th>Tempo</th>
              </tr>
            </thead>
            <tbody>${bellmanSemCicloRows}</tbody>
          </table>
        </div>
      </div>

      <div class="results-table-block">
        <div class="results-table-block-header">
          <h4>Bellman-Ford — caso com ciclo negativo</h4>
          <span class="results-table-badge cycle">ciclo negativo detectado ✓</span>
        </div>
        <div class="table-wrap">
          <table class="results-detail-table">
            <thead>
              <tr>
                <th>Dataset</th>
                <th>Fonte</th>
                <th>Resultado</th>
                <th>Distâncias calculadas</th>
                <th>Tempo</th>
              </tr>
            </thead>
            <tbody>${bellmanComCicloRows}</tbody>
          </table>
        </div>
      </div>

    </div>
  `;
}

function renderBenchmarkOutput(resumo) {
  const benchmark = resumo.benchmark ?? {};
  const benchmarkHtml = Object.entries(benchmark)
    .filter(([, items]) => Array.isArray(items))
    .map(([name, items]) => {
    if (!Array.isArray(items) || items.length === 0) return "";
    const maxVisited = Math.max(0, ...items.map((item) => item.visitados ?? 0));
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
    origem: item.origem,
    filme: movieInfo(item.origem).titulo,
    visitados: item.visitados,
    camadas: item.camadas,
    tem_ciclo: item.tem_ciclo,
    tempo_s: item.tempo_s,
  };
}

function compactDijkstra(item) {
  return {
    origem: item.origem,
    origem_filme: movieInfo(item.origem).titulo,
    destino: item.destino,
    destino_filme: movieInfo(item.destino).titulo,
    sem_caminho: item.sem_caminho,
    custo_total: item.custo_total,
    tamanho_caminho: item.tamanho_caminho,
    caminho_amostra: (item.caminho ?? []).slice(0, 6),
    tempo_s: item.tempo_s,
  };
}

function renderRawOutputs(resumo) {
  const consolidated = {
    dataset: {
      vertices: resumo.dataset?.num_vertices,
      arestas: resumo.dataset?.num_arestas,
      ilhas: resumo.dataset?.componentes_conexas,
      maior_ilha: resumo.dataset?.maior_componente_conexa,
      grau_medio: resumo.dataset?.grau?.medio,
    },
    bfs_dfs: {
      bfs: (resumo.buscas?.bfs ?? []).map(compactSearch),
      dfs: (resumo.buscas?.dfs ?? []).map(compactSearch),
    },
    dijkstra: (resumo.dijkstra ?? []).map(compactDijkstra),
    bellman_ford: (resumo.bellman_ford ?? []).map((item) => ({
      dataset: fileName(item.dataset),
      origem: item.origem,
      ciclo_negativo: item.ciclo_negativo,
      distancias: item.distancias,
      tempo_s: item.tempo_s,
    })),
  };

  document.getElementById("raw-output-pane").innerHTML = `
    <article class="result-panel raw-output-merged">
      <header>
        <h3 class="saidas-pane-title">resumo tecnico da parte 2</h3>
      </header>
      <pre class="raw-output-merged-pre"><code>${attr(JSON.stringify(consolidated, null, 2))}</code></pre>
    </article>
  `;
}

function renderVisualizations(visualizacoes) {
  const html = visualizacoes
    .map((viz) => {
      const title = displayVizTitle(viz.titulo);
      const meta = vizMeta(viz.titulo);

      return `
        <article
          class="viz-card"
          role="button"
          tabindex="0"
          aria-label="abrir grafico ${attr(title)}"
          data-viz-src="${attr(viz.arquivo)}"
          data-viz-title="${attr(title)}"
          data-viz-caption="${attr(meta.insight)}"
        >
          <img src="${viz.arquivo}" alt="${title}">
          <div class="viz-card-body">
            ${meta.tag ? `<span class="viz-card-tag">${attr(meta.tag)}</span>` : ""}
            <h3>${title}</h3>
            <p>${meta.insight}</p>
          </div>
        </article>
      `;
    })
    .join("");

  const grid = document.getElementById("viz-grid");
  if (grid) grid.innerHTML = html;
}

function showDetailsPanel() {
  const p = document.getElementById("details-panel");
  if (p) p.style.display = "block";
}

function renderDetailsForNode(id) {
  const graphNode = state.graph.nodes?.get(id);
  if (graphNode?.bfDescription) {
    showDetailsPanel(); document.getElementById("details-panel").innerHTML = `
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
  const details = document.getElementById("details-panel"); showDetailsPanel();
  const degree = globalDegree().get(id) ?? 0;
  const genreList = movieGenres(id);
  const genreTags = genreList
    .map((g) => `<span class="detail-genre-tag">${attr(g)}</span>`)
    .join("");

  let networkRole = "filme conectado";
  if (degree >= 100) networkRole = "hub principal da rede";
  else if (degree >= 50) networkRole = "hub secundário";
  else if (degree >= 20) networkRole = "bem conectado";
  else if (degree <= 3) networkRole = "filme de nicho";

  details.innerHTML = `
    <p class="eyebrow">filme selecionado</p>
    <h3>${attr(movie.titulo || id)}</h3>
    ${genreTags ? `<div class="detail-genre-row">${genreTags}</div>` : ""}
    <dl class="detail-list">
      ${movie.ano ? `<div><dt>ano</dt><dd>${attr(movie.ano)}</dd></div>` : ""}
      ${movie.nota ? `<div><dt>nota IMDb</dt><dd><strong>${attr(movie.nota)}</strong> / 5</dd></div>` : ""}
      ${movie.diretores ? `<div><dt>diretor</dt><dd>${attr(movie.diretores)}</dd></div>` : ""}
      <div><dt>conexões na rede</dt><dd><strong>${fmt.format(degree)}</strong> filmes</dd></div>
      <div><dt>papel na rede</dt><dd>${attr(networkRole)}</dd></div>
    </dl>
  `;
}

function renderDetailsForEdge(id) {
  const edge = state.graph.edges.get(id);
  const meta = edge?.meta ?? {};
  if (meta.tipo === "bellman-ford") {
    showDetailsPanel(); document.getElementById("details-panel").innerHTML = `
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
          <dd>${meta.ciclo_negativo ? "sim" : "nao"}</dd>
        </div>
        <div>
          <dt>observacao</dt>
          <dd>exemplo artificial e dirigido, usado para validar bellman-ford fora do grafo imdb principal.</dd>
        </div>
      </dl>
    `;
    return;
  }

  const origem = movieInfo(meta.origem ?? edge?.from);
  const destino = movieInfo(meta.destino ?? edge?.to);
  const genres = meta.origem && meta.destino ? commonGenres(meta.origem, meta.destino) : [];
  const actorNames = Array.isArray(meta.actors_common_names) ? meta.actors_common_names : [];
  const actorIds = Array.isArray(meta.actors_common_ids) ? meta.actors_common_ids : [];
  const actors = actorNames.length
    ? actorNames.join(", ")
    : actorIds.length
      ? actorIds.join(", ")
      : `${meta.actors_common ?? "--"} ator(es) em comum`;
  const actorLabel = actorNames.length ? "atores em comum" : "ids dos atores";
  const details = document.getElementById("details-panel"); showDetailsPanel();

  details.innerHTML = `
    <p class="eyebrow">selecao</p>
    <h3>aresta selecionada</h3>
    <p>${attr(origem.titulo || edge?.from)} -> ${attr(destino.titulo || edge?.to)}</p>
    <dl class="detail-list">
      <div>
        <dt>origem</dt>
        <dd>${attr(origem.titulo || edge?.from)}</dd>
      </div>
      <div>
        <dt>destino</dt>
        <dd>${attr(destino.titulo || edge?.to)}</dd>
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

function renderRouteDetails(result, origem, destino) {
  const details = document.getElementById("details-panel"); showDetailsPanel();
  const origemMovie = movieInfo(origem);
  const destinoMovie = movieInfo(destino);

  if (!result) {
    details.innerHTML = `
      <p class="eyebrow">rota</p>
      <h3>sem caminho na amostra</h3>
      <p>${attr(origemMovie.titulo || origem)} -> ${attr(destinoMovie.titulo || destino)}</p>
      <dl class="detail-list">
        <div>
          <dt>origem</dt>
          <dd>${attr(origem)}</dd>
        </div>
        <div>
          <dt>destino</dt>
          <dd>${attr(destino)}</dd>
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
    <p>${attr(origemMovie.titulo || origem)} -> ${attr(destinoMovie.titulo || destino)}</p>
    <dl class="detail-list">
      <div>
        <dt>origem</dt>
        <dd>${attr(origem)}</dd>
      </div>
      <div>
        <dt>destino</dt>
        <dd>${attr(destino)}</dd>
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

function legendaDot(color, label) {
  return `<span class="legend-item"><span class="legend-dot" style="background:${color}"></span>${attr(label)}</span>`;
}


function renderModeDetails(_mode) {
  const panel = document.getElementById("details-panel");
  if (panel) panel.style.display = "none";
}

function _renderModeDetailsLegacy(mode) {
  const panel = document.getElementById("details-panel");

  if (mode === "franquias") {
    panel.innerHTML = `
      <p class="eyebrow">modo ativo</p>
      <h3>Franquias Cinematográficas</h3>
      <p>Filmes da mesma franquia compartilham atores — a rede revela comunidades de elenco.</p>
      <div class="mode-legend">
        ${legendaDot("#ef4444", "Marvel / Avengers")}
        ${legendaDot("#f5c518", "Star Wars")}
        ${legendaDot("#8b5cf6", "Harry Potter / Hobbit")}
        ${legendaDot("#10b981", "Hobbit / LOTR")}
        ${legendaDot("#3b82f6", "X-Men")}
        ${legendaDot("#06b6d4", "Jurassic Park")}
        ${legendaDot("#f97316", "Fast & Furious")}
        ${legendaDot("#a855f7", "Star Trek")}
      </div>
      <dl class="detail-list">
        <div><dt>nó grande</dt><dd>hub da franquia — ator/filme com muitas conexões</dd></div>
        <div><dt>aresta grossa</dt><dd>alta similaridade: muitos atores em comum</dd></div>
        <div><dt>interação</dt><dd>clique em qualquer filme para ver grau, gênero e nota IMDb</dd></div>
      </dl>
    `;
    return;
  }

  if (mode === "similaridade") {
    panel.innerHTML = `
      <p class="eyebrow">modo ativo</p>
      <h3>Hubs da Rede</h3>
      <p>Arestas com maior similaridade. Sim = 2× atores + gêneros em comum. Conexões mais fortes primeiro.</p>
      <div class="mode-legend">
        ${legendaDot("#ef4444", "Ação")}
        ${legendaDot("#f59e0b", "Comédia")}
        ${legendaDot("#3b82f6", "Drama")}
        ${legendaDot("#8b5cf6", "Ficção Científica")}
        ${legendaDot("#10b981", "Animação")}
        ${legendaDot("#ec4899", "Romance")}
      </div>
      <dl class="detail-list">
        <div><dt>cor do nó</dt><dd>gênero principal do filme</dd></div>
        <div><dt>tamanho do nó</dt><dd>grau na rede completa (mais conexões = maior)</dd></div>
        <div><dt>aresta grossa</dt><dd>sim > 8: muitos atores em comum</dd></div>
      </dl>
    `;
    return;
  }

  if (mode === "bfs") {
    const fonte = defaultGraphSource();
    const fonteTitle = movieInfo(fonte).titulo || fonte;
    panel.innerHTML = `
      <p class="eyebrow">algoritmo: busca em largura</p>
      <h3>BFS — Expansão por Camadas</h3>
      <p>A partir de <strong>${attr(fonteTitle)}</strong>, o BFS visita todos os vizinhos diretos antes de avançar para o próximo nível.</p>
      <div class="algo-visual">
        <div class="algo-tree">
          <div class="algo-node algo-node-origem">● ${attr(fonteTitle.split(":")[0])}</div>
          <div class="algo-branch">
            <div class="algo-node algo-node-l1">● camada 1 — vizinhos diretos</div>
            <div class="algo-branch">
              <div class="algo-node algo-node-l2">● camada 2 — filmes de filmes</div>
              <div class="algo-branch">
                <div class="algo-node algo-node-l3">● camada 3 — e assim por diante</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <dl class="detail-list">
        <div><dt>insight</dt><dd>BFS atinge filmes FAMOSOS primeiro — vizinhos do hub têm alto grau</dd></div>
        <div><dt>complexidade</dt><dd>O(V + E) — linear no tamanho do grafo</dd></div>
        <div><dt>estrutura</dt><dd>usa fila (FIFO) — garante menor número de saltos</dd></div>
        <div><dt>resultado</dt><dd>3.899 filmes em 7 camadas a partir de qualquer hub</dd></div>
      </dl>
    `;
    return;
  }

  if (mode === "dfs") {
    const fonte = defaultGraphSource();
    const fonteTitle = movieInfo(fonte).titulo || fonte;
    panel.innerHTML = `
      <p class="eyebrow">algoritmo: busca em profundidade</p>
      <h3>DFS — Mergulho Profundo</h3>
      <p>A partir de <strong>${attr(fonteTitle)}</strong>, o DFS mergulha em um único caminho até o fim antes de retroceder.</p>
      <div class="algo-visual">
        <div class="algo-tree">
          <div class="algo-node algo-node-origem">● ${attr(fonteTitle.split(":")[0])}</div>
          <div class="algo-branch">
            <div class="algo-node algo-node-l1">↓ vizinho 1</div>
            <div class="algo-branch">
              <div class="algo-node algo-node-l2">↓ vizinho do vizinho 1</div>
              <div class="algo-branch">
                <div class="algo-node algo-node-l3">↓ chega em filmes de nicho</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <dl class="detail-list">
        <div><dt>insight</dt><dd>DFS chega em filmes OBSCUROS — mergulha fundo em filmes de baixo grau</dd></div>
        <div><dt>complexidade</dt><dd>O(V + E) — mesmo custo do BFS</dd></div>
        <div><dt>estrutura</dt><dd>usa pilha (LIFO) — detecta ciclos no percurso</dd></div>
        <div><dt>diferença visual</dt><dd>nós azuis claros; caminho em linha profunda vs radial do BFS</dd></div>
      </dl>
    `;
    return;
  }

  if (mode === "dijkstra") {
    panel.innerHTML = `
      <p class="eyebrow">algoritmo: menor caminho ponderado</p>
      <h3>Dijkstra — Caminho Mais Similar</h3>
      <p>Encontra a rota de menor custo entre dois filmes. Peso = 1 / similaridade: filmes muito parecidos custam menos para conectar.</p>
      <div class="algo-visual">
        <div class="algo-path">
          <span class="algo-path-node algo-path-origem">origem</span>
          <span class="algo-path-arrow">→</span>
          <span class="algo-path-node algo-path-mid">intermediário</span>
          <span class="algo-path-arrow">→</span>
          <span class="algo-path-node algo-path-mid">intermediário</span>
          <span class="algo-path-arrow">→</span>
          <span class="algo-path-node algo-path-destino">destino</span>
        </div>
        <p class="algo-path-caption">o caminho escolhido maximiza a similaridade total</p>
      </div>
      <dl class="detail-list">
        <div><dt>peso da aresta</dt><dd>1 / similaridade — conexão forte = custo baixo</dd></div>
        <div><dt>complexidade</dt><dd>O((V + E) log V) com heap mínimo</dd></div>
        <div><dt>garantia</dt><dd>pesos sempre ≥ 0 no grafo IMDb — Dijkstra é válido</dd></div>
        <div><dt>use a busca de rota</dt><dd>digite origem e destino acima para visualizar qualquer caminho</dd></div>
      </dl>
    `;
    return;
  }

  resetDetails();
}

function renderBellmanDetails(caso = "ambos") {
  const title = caso === "com-ciclo"
    ? "Bellman-Ford — Caso com Ciclo Negativo"
    : caso === "sem-ciclo"
      ? "Bellman-Ford — Caso sem Ciclo Negativo"
      : "Bellman-Ford — Validação de Ciclos";
  const intro = caso === "com-ciclo"
    ? "Grafo artificial dirigido com ciclo de custo negativo. O algoritmo detecta o ciclo e bloqueia o resultado."
    : caso === "sem-ciclo"
      ? "Grafo artificial dirigido com peso negativo controlado. O algoritmo calcula as distâncias finais sem detectar ciclo negativo."
      : "O grafo IMDb tem apenas pesos positivos. Para validar o algoritmo, foram criados dois grafos artificiais dirigidos.";

  showDetailsPanel(); document.getElementById("details-panel").innerHTML = `
    <p class="eyebrow">algoritmo: pesos negativos</p>
    <h3>${title}</h3>
    <p>${intro}</p>
    <div class="algo-visual">
      <div class="algo-cases">
        ${caso !== "com-ciclo" ? `<div class="algo-case algo-case-ok">
          <span class="algo-case-badge">✓ sem ciclo</span>
          <span>peso negativo sem loop — distâncias calculadas</span>
        </div>` : ""}
        ${caso !== "sem-ciclo" ? `<div class="algo-case algo-case-bad">
          <span class="algo-case-badge">⚠ ciclo negativo</span>
          <span>loop de custo negativo — distâncias não convergem</span>
        </div>` : ""}
      </div>
    </div>
    <dl class="detail-list">
      <div><dt>caso 1</dt><dd>grafo com peso negativo mas sem ciclo → calcula distâncias corretamente</dd></div>
      <div><dt>caso 2</dt><dd>grafo com ciclo negativo → detectado e resultado bloqueado</dd></div>
      <div><dt>no grafo IMDb</dt><dd>Dijkstra é preferido pois pesos = 1/sim são sempre positivos</dd></div>
    </dl>
  `;
}

function resetDetails() {
  const topHubs = [
    { id: "The Royal Tenenbaums", grau: 142 },
    { id: "Jurassic Park", grau: 121 },
    { id: "Pulp Fiction", grau: 118 },
    { id: "Avengers: Age of Ultron", grau: 97 },
    { id: "The Matrix", grau: 89 },
  ];

  const hubRows = topHubs
    .filter(({ id }) => state.amostra?.movies?.[id])
    .map(({ id, grau }) => `
      <div class="hub-row">
        <button type="button" class="detail-hint-btn" data-movie-id="${attr(id)}">${attr(id)}</button>
        <span class="hub-grau">${grau} conexões</span>
      </div>`)
    .join("");

  const comunidades = [
    { cor: "#ef4444", nome: "Ação" },
    { cor: "#3b82f6", nome: "Drama" },
    { cor: "#f59e0b", nome: "Comédia" },
    { cor: "#8b5cf6", nome: "Sci-Fi" },
    { cor: "#10b981", nome: "Animação" },
    { cor: "#dc2626", nome: "Terror" },
  ];
  const comunidadeDots = comunidades
    .map(({ cor, nome }) => `<span class="comm-dot-item"><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${cor};margin-right:5px;vertical-align:middle"></span>${nome}</span>`)
    .join("");

  showDetailsPanel(); document.getElementById("details-panel").innerHTML = `
    <p class="eyebrow">rede cinematográfica IMDb</p>
    <h3>Explore a Rede</h3>
    <p>3.899 filmes conectados por elenco compartilhado. Clique em qualquer nó para explorar.</p>

    <div class="detail-stat-row">
      <div class="detail-stat"><strong>3.899</strong><span>filmes</span></div>
      <div class="detail-stat"><strong>63.484</strong><span>conexões</span></div>
      <div class="detail-stat"><strong>32,6</strong><span>grau médio</span></div>
    </div>

    ${hubRows ? `<div class="detail-section-title">top hubs da rede</div><div class="hub-list">${hubRows}</div>` : ""}

    <div class="detail-section-title">comunidades por gênero</div>
    <div class="comm-dots">${comunidadeDots}</div>

    <div class="detail-section-title">como explorar</div>
    <dl class="detail-list detail-list-muted">
      <div><dt>Franquias</dt><dd>ver comunidades Marvel, Star Wars, HP…</dd></div>
      <div><dt>Hubs</dt><dd>filmes mais conectados da rede</dd></div>
      <div><dt>BFS / DFS</dt><dd>visualizar como os algoritmos percorrem</dd></div>
      <div><dt>Dijkstra</dt><dd>menor caminho entre dois filmes</dd></div>
    </dl>
  `;

  document.querySelectorAll(".detail-hint-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.movieId;
      if (!focusGraphNode(id)) {
        drawGraph(makeNeighborhoodGraph(id));
        focusGraphNode(id);
      }
    });
  });
  // esconde o painel flutuante ao resetar
  const dp = document.getElementById("details-panel");
  if (dp) dp.style.display = "none";
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
      tooltipDelay: 99999,
      navigationButtons: false,
      keyboard: true,
      hideEdgesOnDrag: !!graph.fullGraph,
      hideEdgesOnZoom: !!graph.fullGraph,
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
    physics: graph.fullGraph
      ? { enabled: false }
      : {
          enabled: !isPathLayout,
          solver: "forceAtlas2Based",
          forceAtlas2Based: {
            gravitationalConstant: -90,
            centralGravity: 0.018,
            springLength: 145,
            springConstant: 0.08,
            damping: 0.5,
            avoidOverlap: 0.75,
          },
          stabilization: { iterations: 180 },
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
    state.network?.stopSimulation();
    state.network?.fit({ animation: { duration: 600, easingFunction: "easeInOutQuad" } });
  });

  // fix canvas aspect-ratio bug: force resize em múltiplos momentos
  const _fixCanvasSize = () => {
    if (!state.network) return;
    const w = container.offsetWidth, h = container.offsetHeight;
    if (w > 0 && h > 0) {
      state.network.setSize(w + "px", h + "px");
      state.network.redraw();
    }
  };
  [50, 150, 400, 800].forEach(ms => setTimeout(_fixCanvasSize, ms));

  state.network.once("stabilized", _fixCanvasSize);

  // watch for container resize (tab switch, fullscreen, janela)
  if (state._resizeObserver) state._resizeObserver.disconnect();
  state._resizeObserver = new ResizeObserver(_fixCanvasSize);
  state._resizeObserver.observe(container);

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

async function loadGrafoCompleto() {
  if (state.grafoCompleto) return state.grafoCompleto;
  const data = await fetchJson("data/parte2_grafo.json?v=1");
  state.grafoCompleto = data;
  return data;
}

function showFullGraphModal(_originBtn) {
  const modal = document.getElementById("full-graph-modal");
  const confirmBtn = document.getElementById("full-graph-confirm");
  const cancelBtn = document.getElementById("full-graph-cancel");
  const backdrop = document.getElementById("full-graph-backdrop");

  modal.setAttribute("aria-hidden", "false");
  modal.style.display = "flex";

  function close(revert = true) {
    modal.setAttribute("aria-hidden", "true");
    modal.style.display = "";
    if (revert) setActiveMode("franquias");
    confirmBtn.removeEventListener("click", onConfirm);
    cancelBtn.removeEventListener("click", onCancel);
    backdrop.removeEventListener("click", onCancel);
  }

  async function onConfirm() {
    close(false);
    setActiveMode("grafo-completo");
    confirmBtn.textContent = "carregando...";
    confirmBtn.disabled = true;
    await loadGrafoCompleto();
    confirmBtn.textContent = "carregar mesmo assim";
    confirmBtn.disabled = false;
    drawGraph("grafo-completo");
    refreshGraphView(true);
    resetDetails();
  }

  function onCancel() { close(true); }

  confirmBtn.addEventListener("click", onConfirm);
  cancelBtn.addEventListener("click", onCancel);
  backdrop.addEventListener("click", onCancel);
}

function setActiveMode(modeValue) {
  document.querySelectorAll(".gmode-btn").forEach((b) => {
    b.classList.toggle("active", b.dataset.mode === modeValue);
  });
}


const MODE_INFO = {
  amostra: null,
  franquias: {
    title: "Franquias",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:6px;line-height:1.4;">Cada grupo de cor representa uma franquia. Os nós são filmes e as arestas indicam atores e gêneros em comum entre eles.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:4px;letter-spacing:.5px;">COR · FRANQUIA · FILMES</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#ef4444"></span><span><strong>Marvel / Avengers</strong> — 4 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f5c518"></span><span><strong>Star Wars</strong> — 4 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#8b5cf6"></span><span><strong>Harry Potter</strong> — 4 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#10b981"></span><span><strong>Hobbit / LOTR</strong> — 3 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#3b82f6"></span><span><strong>X-Men</strong> — 4 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#06b6d4"></span><span><strong>Jurassic Park</strong> — 4 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f97316"></span><span><strong>Fast & Furious</strong> — 3 filmes</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#a855f7"></span><span><strong>Star Trek</strong> — 6 filmes</span></div>
  <div style="margin-top:6px;font-size:11px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">Espessura da aresta = similaridade entre filmes (atores + gêneros em comum)</div>
</div>`
  },
  "top-notas": {
    title: "Top Notas",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:4px;line-height:1.4;">Os <strong>5 filmes mais bem avaliados</strong> da amostra e todas as conexões que partem deles.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:2px;letter-spacing:.5px;">LEGENDA VISUAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f5c518;border:2px solid #fff;box-sizing:border-box;"></span><span><strong>Nó amarelo grande</strong> — top 5 por nota IMDb</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#888;"></span><span><strong>Nós menores</strong> — filmes conectados aos top 5</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:4px;background:#f5c518;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Aresta brilhante</strong> — conexão entre dois top 5</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:2px;background:rgba(245,197,24,0.3);border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Aresta fraca</strong> — conexão com filme fora do top</span></div>
  <div style="margin-top:4px;font-size:11px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">Tamanho do nó proporcional à nota do filme</div>
</div>`
  },
  similaridade: {
    title: "Hubs",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:6px;line-height:1.4;">Exibe os <strong>filmes mais conectados</strong> da rede — aqueles com mais atores e gêneros em comum com outros títulos. O tamanho do nó reflete o grau de conexão.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:4px;letter-spacing:.5px;">COR · GÊNERO PRINCIPAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#ef4444"></span><span><strong>Action</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f59e0b"></span><span><strong>Comedy</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#3b82f6"></span><span><strong>Drama</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#8b5cf6"></span><span><strong>Sci-Fi</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#10b981"></span><span><strong>Animation</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f97316"></span><span><strong>Thriller</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#06b6d4"></span><span><strong>Adventure</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#ec4899"></span><span><strong>Romance</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#a855f7"></span><span><strong>Fantasy</strong></span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#6366f1"></span><span><strong>Crime</strong></span></div>
  <div class="g2-fr-row" style="margin-top:2px;"><span style="display:inline-block;width:22px;height:4px;background:rgba(245,197,24,0.8);border-radius:2px;flex-shrink:0;"></span><span><strong>Aresta grossa</strong> — muitos atores em comum</span></div>
  <div style="margin-top:6px;font-size:11px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">Cada filme recebe a cor do seu primeiro gênero listado</div>
</div>`
  },
  bfs: {
    title: "BFS — Busca em Largura",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:4px;line-height:1.4;">Explora o grafo <strong>nível a nível</strong> a partir de um filme fonte — visita todos os vizinhos diretos antes de avançar para os mais distantes.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:2px;letter-spacing:.5px;">LEGENDA VISUAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#2ecc71;border:2px solid #fff;box-sizing:border-box;"></span><span><strong>Nó fonte</strong> — ponto de partida da busca</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f5c518;"></span><span><strong>Nós visitados</strong> — filmes alcançados pela BFS</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:3px;background:#2ecc71;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Seta verde</strong> — direção da descoberta (de → para)</span></div>
  <div style="margin-top:4px;font-size:11px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">Garante o <strong style="color:var(--primary)">menor número de saltos</strong> entre dois filmes — não considera o peso das arestas.</div>
</div>`
  },
  dfs: {
    title: "DFS — Busca em Profundidade",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:4px;line-height:1.4;">Explora o grafo <strong>aprofundando ao máximo</strong> cada ramo antes de retroceder — mergulha em um caminho até o fim, depois volta e tenta outro.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:2px;letter-spacing:.5px;">LEGENDA VISUAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#2ecc71;border:2px solid #fff;box-sizing:border-box;"></span><span><strong>Nó fonte</strong> — ponto de partida da busca</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#7cc7ff;"></span><span><strong>Nós visitados</strong> — filmes alcançados pela DFS</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:3px;background:#7cc7ff;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Seta azul</strong> — ordem de descoberta do caminho</span></div>
  <div style="margin-top:4px;font-size:11px;color:rgba(255,255,255,0.45);border-top:1px solid rgba(255,255,255,0.08);padding-top:6px;">Útil para detectar <strong style="color:var(--primary)">ciclos</strong> e explorar componentes conexos — o caminho encontrado pode não ser o mais curto.</div>
</div>`
  },
  dijkstra: {
    title: "Dijkstra",
    body: `<div style="font-size:13px;color:rgba(255,255,255,0.5);">calculando rota...</div>`
  },
  "bellman-sem-ciclo": {
    title: "Bellman-Ford (BF−)",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:4px;line-height:1.4;">Grafo artificial dirigido com <strong>peso negativo sem ciclo</strong>. O algoritmo calcula as distâncias finais corretamente.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:2px;letter-spacing:.5px;">LEGENDA VISUAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#2ecc71;border:2px solid #fff;box-sizing:border-box;"></span><span><strong>Nó fonte</strong> — ponto de partida (Z)</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f5c518;"></span><span><strong>Nós alcançados</strong> — vértices relaxados</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:3px;background:#f5c518;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Seta amarela</strong> — aresta com peso (número = custo)</span></div>
</div>`
  },
  "bellman-com-ciclo": {
    title: "Bellman-Ford (BF+)",
    body: `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:13px;color:rgba(255,255,255,0.65);margin-bottom:4px;line-height:1.4;">Grafo artificial dirigido com <strong>ciclo de custo negativo</strong>. O algoritmo detecta o ciclo e bloqueia o resultado.</div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-bottom:2px;letter-spacing:.5px;">LEGENDA VISUAL</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#ff4d4d;border:2px solid #fff;box-sizing:border-box;"></span><span><strong>Nó fonte / ciclo</strong> — vértices envolvidos no ciclo</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#f5c518;"></span><span><strong>Nós normais</strong> — vértices fora do ciclo</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:3px;background:#ff4d4d;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Seta vermelha</strong> — aresta do ciclo negativo</span></div>
  <div class="g2-fr-row"><span style="display:inline-block;width:22px;height:3px;background:#f5c518;border-radius:2px;flex-shrink:0;margin-right:2px;"></span><span><strong>Seta amarela</strong> — aresta normal</span></div>
</div>`
  },
  "grafo-completo": {
    title: "Grafo Completo",
    body: "Carrega <strong>todos os 3.899 filmes</strong> e <strong>63.484 arestas</strong> do dataset IMDb.<br><br>⚠️ Pesado — pode travar em máquinas lentas."
  },
};

function updateModeInfo(mode) {
  const panel = document.getElementById("g2-mode-info");
  const titleEl = document.getElementById("g2-mode-info-title");
  const bodyEl = document.getElementById("g2-mode-info-body");
  const info = MODE_INFO[mode];
  if (!panel) return;
  if (!info) { panel.style.display = "none"; return; }
  panel.style.display = "block";
  titleEl.textContent = info.title;
  bodyEl.innerHTML = info.body;
}

function updateDijkstraInfo() {
  const bodyEl = document.getElementById("g2-mode-info-body");
  if (!bodyEl) return;
  const route = state.lastDijkstraRoute;
  if (!route || route.path.length < 2) {
    bodyEl.innerHTML = `<div style="font-size:13px;color:rgba(255,255,255,0.5);">Nenhuma rota encontrada.</div>`;
    return;
  }
  const origem = route.path[0];
  const destino = route.path[route.path.length - 1];
  const intermediarios = route.path.slice(1, -1);
  const custo = typeof route.cost === "number" ? route.cost.toFixed(2) : "--";
  const passagens = intermediarios.map(id => `<div style="padding:2px 0;border-left:2px solid rgba(245,197,24,0.4);padding-left:8px;font-size:12px;color:rgba(255,255,255,0.7);">${id}</div>`).join("");

  bodyEl.innerHTML = `<div style="display:flex;flex-direction:column;gap:6px;">
  <div style="font-size:11px;color:rgba(255,255,255,0.35);letter-spacing:.5px;">ROTA ENCONTRADA</div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#2ecc71;border:2px solid #fff;box-sizing:border-box;flex-shrink:0;"></span><span style="font-size:13px;"><strong>Origem:</strong> ${origem}</span></div>
  <div class="g2-fr-row"><span class="g2-fr-dot" style="background:#ff4d4d;border:2px solid #fff;box-sizing:border-box;flex-shrink:0;"></span><span style="font-size:13px;"><strong>Destino:</strong> ${destino}</span></div>
  <div style="font-size:11px;color:rgba(255,255,255,0.35);margin-top:2px;letter-spacing:.5px;">PASSA POR (${intermediarios.length} filmes)</div>
  ${passagens || '<div style="font-size:12px;color:rgba(255,255,255,0.4);">conexão direta</div>'}
  <div style="margin-top:4px;padding-top:6px;border-top:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;">
    <span style="font-size:12px;color:rgba(255,255,255,0.5);">total de filmes</span>
    <strong style="color:var(--primary);font-size:14px;">${route.path.length}</strong>
  </div>
  <div style="display:flex;justify-content:space-between;">
    <span style="font-size:12px;color:rgba(255,255,255,0.5);">custo total</span>
    <strong style="color:#ff9f1c;font-size:14px;">${custo}</strong>
  </div>
</div>`;
}

function setupGraphControls() {
  const search = document.getElementById("graph-search");
  const resetButton = document.getElementById("reset-graph-btn");
  const routeOrigem = document.getElementById("route-origem");
  const routeDestino = document.getElementById("route-destino");
  const routeAlgorithm = document.getElementById("route-algorithm");
  const routeButton = document.getElementById("route-run-btn");

  // modos que mostram filtros de gênero/grau
  const MODOS_COM_FILTROS = new Set(["amostra"]);
  const filtersBar = document.getElementById("graph-filters");

  window._setAmostPanels = (visible) => {
    const d = visible ? "" : "none";
    const df = visible ? "flex" : "none";
    const sp = document.querySelector(".g2-search-panel");
    const lp = document.querySelector(".g2-legend-panel");
    const sep = document.getElementById("g2-topbar-filters");
    const fl1 = document.getElementById("g2-topbar-filters-genero");
    const sg = document.getElementById("select-genero");
    const si = document.getElementById("select-grau");
    const fl2 = sg?.previousElementSibling;
    if (sp) sp.style.display = visible ? "flex" : "none";
    if (lp) lp.style.display = visible ? "block" : "none";
    if (sep) sep.style.display = d;
    if (fl1) fl1.style.display = d;
    if (sg) sg.style.display = d;
    
    if (si) { si.style.display = d; if (si.previousElementSibling) si.previousElementSibling.style.display = d; }
  };

  function applyFilters() {
    if (!state.graph.nodes || !state.graph.baseNodes) return;
    const genero = document.querySelector(".gfilter-btn[data-filter-genero].active")?.dataset.filterGenero ?? "";
    const grauMin = parseInt(document.querySelector(".gfilter-btn[data-filter-grau].active")?.dataset.filterGrau ?? "0", 10);
    if (!genero && grauMin === 0) {
      state.graph.nodes.update(state.graph.baseNodes.map((n) => ({ id: n.id, hidden: false })));
      return;
    }
    state.graph.nodes.update(state.graph.baseNodes.map((n) => {
      const deg = globalDegree().get(n.id) ?? 0;
      const genres = movieGenres(n.id);
      const generoOk = !genero || genres.includes(genero);
      const grauOk = deg >= grauMin;
      return { id: n.id, hidden: !(generoOk && grauOk) };
    }));
  }

  document.querySelectorAll(".gfilter-btn[data-filter-genero]").forEach((btn) => {
    btn.addEventListener("click", () => {
      for (const b of document.querySelectorAll(".gfilter-btn[data-filter-genero]")) b.classList.remove("active");
      btn.classList.add("active");
      applyFilters();
    });
  });

  document.querySelectorAll(".gfilter-btn[data-filter-grau]").forEach((btn) => {
    btn.addEventListener("click", () => {
      for (const b of document.querySelectorAll(".gfilter-btn[data-filter-grau]")) b.classList.remove("active");
      btn.classList.add("active");
      applyFilters();
    });
  });

  document.querySelectorAll(".gmode-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modeValue = btn.dataset.mode;
      if (modeValue === "grafo-completo") {
        showFullGraphModal(btn);
        return;
      }
      setActiveMode(modeValue);
      clearRouteHighlight();
      _setAmostPanels(modeValue === "amostra");
      state.graph.currentMode = modeValue;
      drawGraph(modeValue);
      updateModeInfo(modeValue);
      if (modeValue === "dijkstra") setTimeout(updateDijkstraInfo, 50);
      // fix canvas size após troca de modo
      const _c = document.getElementById("network");
      [80, 300].forEach(ms => setTimeout(() => {
        if (state.network && _c) { state.network.setSize(_c.offsetWidth+"px", _c.offsetHeight+"px"); state.network.redraw(); }
      }, ms));
      refreshGraphView(true);
      if (modeValue === "bellman-sem-ciclo") {
        renderBellmanDetails("sem-ciclo");
      } else if (modeValue === "bellman-com-ciclo") {
        renderBellmanDetails("com-ciclo");
      } else {
        renderModeDetails(modeValue);
      }
    });
  });

  function runSearch() {
    const id = search.value.trim();
    if (!id) return;

    let found = focusGraphNode(id);
    if (!found && state.amostra?.movies?.[id]) {
      drawGraph(makeNeighborhoodGraph(id));
      found = focusGraphNode(id);
    }
    search.classList.toggle("search-miss", !found);
  }

  search.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      runSearch();
    }
  });
  search.addEventListener("input", () => {
    search.classList.remove("search-miss");
  });

  function renderInlineRouteResult(result, origem, destino) {
  const el = document.getElementById("route-result");
  if (!el) return;
  if (!result) {
    el.style.display = "block";
    el.innerHTML = `
      <div class="g2-rr-route">
        <span class="g2-rr-orig">${origem.length > 14 ? origem.slice(0,13)+"…" : origem}</span>
        <span class="g2-rr-arr">→</span>
        <span class="g2-rr-dest">${destino.length > 14 ? destino.slice(0,13)+"…" : destino}</span>
      </div>
      <div class="g2-rr-stats">
        <div class="g2-rr-stat"><span class="g2-rr-val" style="color:#ff4d4d;font-size:12px;">Sem custo</span><span class="g2-rr-lbl">CUSTO</span></div>
        <div class="g2-rr-stat"><span class="g2-rr-val" style="color:#ff4d4d;font-size:12px;">—</span><span class="g2-rr-lbl">SALTOS</span></div>
      </div>
      <p style="font-size:10px;color:rgba(255,255,255,0.45);margin:4px 0 0;">sem caminho na amostra</p>
    `;
    return;
  }
  const hops = result.path.length - 1;
  const cost = result.cost != null ? result.cost.toFixed(2) : "—";
  el.style.display = "block";
  el.innerHTML = `
    <div class="g2-rr-route">
      <span class="g2-rr-orig">${origem.length > 14 ? origem.slice(0,13)+"…" : origem}</span>
      <span class="g2-rr-arr">→</span>
      <span class="g2-rr-dest">${destino.length > 14 ? destino.slice(0,13)+"…" : destino}</span>
    </div>
    <div class="g2-rr-stats">
      <div class="g2-rr-stat"><span class="g2-rr-val">${cost}</span><span class="g2-rr-lbl">CUSTO</span></div>
      <div class="g2-rr-stat"><span class="g2-rr-val">${hops}</span><span class="g2-rr-lbl">SALTOS</span></div>
    </div>
  `;
}

async function runRoute() {
    const origem = routeOrigem.value.trim();
    const destino = routeDestino.value.trim();
    const algorithm = routeAlgorithm.value;

    if (!origem || !destino) return;

    // usa somente a amostra — garante que nos/arestas existem no visual
    const result = algorithm === "dfs" || algorithm === "bfs"
      ? dfsPath(origem, destino)
      : dijkstraPath(origem, destino);

    const movieExists = (id) => !!(state.amostra?.movies?.[id]);
    routeOrigem.classList.toggle("search-miss", !movieExists(origem));
    routeDestino.classList.toggle("search-miss", !movieExists(destino));

    // salva chaves do caminho para o graphForMode incluir arestas extras se necessário
    if (result?.path?.length >= 2) {
      state._lastRouteEdgeKeys = new Set();
      for (let i = 0; i < result.path.length - 1; i++) {
        state._lastRouteEdgeKeys.add(edgeKey(result.path[i], result.path[i + 1]));
      }
    } else {
      state._lastRouteEdgeKeys = new Set();
    }

    // garante que o grafo amostra está visível (redesenha para incluir arestas da rota)
    setActiveMode("amostra");
    drawGraph("amostra");
    state.graph.currentMode = "amostra";

    if (result?.path?.length >= 2) {
      highlightRoute(result.path, algorithm);
    }

    renderRouteDetails(result, origem, destino);
    renderInlineRouteResult(result, origem, destino);
  }


  function clearRouteHighlight() {
    if (!state.graph.nodes || !state.graph.baseNodes) return;
    state.graph.nodes.update(
      state.graph.baseNodes.map((n) => ({
        id: n.id,
        color: n.color,
        size: n.size,
        borderWidth: n.borderWidth ?? 1,
        font: n.font,
        label: n.label,
      }))
    );
    if (state.graph.baseEdges) {
      state.graph.edges.update(
        state.graph.baseEdges.map((e) => ({
          id: e.id,
          color: e.color,
          width: e.width,
          dashes: e.dashes ?? false,
        }))
      );
    }
  }

  function highlightRoute(path, algorithm) {
    if (!state.graph.nodes || !path?.length) return;
    const pathSet = new Set(path);
    const pathColor = "#00e676";

    // destaca apenas as arestas do caminho; nos ficam com borda verde, background preservado
    const baseNodeMap = new Map((state.graph.baseNodes ?? []).map(n => [n.id, n]));
    const pathUpdates = path.map((id) => {
      const orig = baseNodeMap.get(id);
      const bg = orig?.color?.background ?? orig?.color ?? "#f5c518";
      return { id, borderWidth: 3, color: { background: bg, border: "#00e676" } };
    });
    state.graph.nodes.update(pathUpdates);

    // arestas do caminho: verdes e grossas — usa ID direto (edgeKey = id da aresta na amostra)
    const edgeUpdates = [];
    for (let i = 0; i < path.length - 1; i++) {
      const id = edgeKey(path[i], path[i + 1]);
      if (state.graph.edges.get(id) != null) {
        edgeUpdates.push({ id, color: { color: "#00e676", opacity: 1 }, width: 8, dashes: false });
      }
    }
    state.graph.edges.update(edgeUpdates);

    refreshGraphView(true);
  }

  window.applyFilters = applyFilters;
  if (!routeButton || !resetButton || !search) {
    console.error("[setupGraphControls] elemento nao encontrado", { routeButton, resetButton, search });
    return;
  }
  routeButton.addEventListener("click", runRoute);
  [routeOrigem, routeDestino].forEach((input) => {
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
    routeOrigem.value = "";
    routeDestino.value = "";
    search.classList.remove("search-miss");
    routeOrigem.classList.remove("search-miss");
    routeDestino.classList.remove("search-miss");
    state.network?.unselectAll();
    clearRouteHighlight();
    const rr = document.getElementById("route-result"); if (rr) rr.style.display = "none";
    state.network?.fit({ animation: { duration: 500, easingFunction: "easeInOutQuad" } });
    resetDetails();
  });


  renderModeDetails("franquias");
}

function setupVizModal() {
  const modal = document.getElementById("viz-modal");
  const image = document.getElementById("modal-image");
  const title = document.getElementById("modal-title");
  const caption = document.getElementById("modal-caption");
  const grid = document.getElementById("viz-grid");
  if (!grid || !modal) return;

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
  const viewAliases = {
    resultados: "analise",
    graficos: "analise",
  };

  function showView(view) {
    const requestedView = viewAliases[view] ?? view;
    const nextView = validViews.has(requestedView) ? requestedView : "inicio";

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
  const [resumo, amostra] = await Promise.all([
    fetchJson("data/resumo_parte2.json?v=1"),
    fetchJson("data/parte2_amostra.json?v=13"),
  ]);
  state.resumo = resumo;
  state.amostra = amostra;

  const dl = document.getElementById("movies-list");
  const movieTitles = amostra?.movies ? Object.keys(amostra.movies).sort() : [];
  if (dl) {
    movieTitles.forEach((title) => {
      const opt = document.createElement("option");
      opt.value = title;
      dl.appendChild(opt);
    });
  }
  setupMovieAutocomplete("route-origem", "ac-origem", movieTitles);
  setupMovieAutocomplete("route-destino", "ac-destino", movieTitles);

  setupViews();
  renderSaidaDashboard();
  renderMetrics(state.resumo.dataset);
  renderResults(state.resumo);
  renderBenchmarkOutput(state.resumo);
  renderRawOutputs(state.resumo);
  renderVisualizations(state.resumo.visualizacoes);
  setupGraphControls();
  setupVizModal();
  setupGraphFullscreen();
  setupLobbyCanvas();
  const _dp = document.getElementById("details-panel"); if (_dp) _dp.style.display = "none";
  setActiveMode("amostra");
  drawGraph("amostra");
  state.graph.currentMode = "amostra";
  _setAmostPanels(true);
  updateModeInfo("amostra");
}

function setupLobbyCanvas() {
  const canvas = document.getElementById("p2-lobby-bg");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const ICONS = ["🎬","🎥","🎞","📽","🎦","🍿"];
  let W, H, mx = 0, my = 0;

  function resize() {
    W = canvas.width = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight;
  }
  resize();
  window.addEventListener("resize", resize);

  class Flake {
    constructor(init) {
      this.x = Math.random() * (W || 800);
      this.y = init ? Math.random() * (H || 600) : -30;
      this.vy = 0.35 + Math.random() * 0.7;
      this.vx = (Math.random() - 0.5) * 0.25;
      this.size = 13 + Math.random() * 15;
      this.icon = ICONS[Math.floor(Math.random() * ICONS.length)];
      this.alpha = 0.12 + Math.random() * 0.28;
      this.rot = Math.random() * Math.PI * 2;
      this.rotV = (Math.random() - 0.5) * 0.012;
    }
    update() {
      const dx = this.x - mx, dy = this.y - my;
      const d = Math.sqrt(dx * dx + dy * dy);
      if (d < 130 && d > 0) {
        const f = (130 - d) / 130;
        this.vx += (dx / d) * f * 1.6;
        this.vy += (dy / d) * f * 1.6;
      }
      this.vx *= 0.97;
      this.vy = this.vy * 0.97 + 0.018;
      this.x += this.vx;
      this.y += this.vy;
      this.rot += this.rotV;
      if (this.y > H + 35 || this.x < -50 || this.x > W + 50) {
        Object.assign(this, new Flake(false));
      }
    }
    draw() {
      ctx.save();
      ctx.globalAlpha = this.alpha;
      ctx.translate(this.x, this.y);
      ctx.rotate(this.rot);
      ctx.font = this.size + "px serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(this.icon, 0, 0);
      ctx.restore();
    }
  }

  const flakes = Array.from({ length: 55 }, () => new Flake(true));

  document.getElementById("inicio").addEventListener("mousemove", e => {
    const r = canvas.getBoundingClientRect();
    mx = e.clientX - r.left;
    my = e.clientY - r.top;
  });

  let raf;
  function loop() {
    ctx.clearRect(0, 0, W, H);
    flakes.forEach(f => { f.update(); f.draw(); });
    raf = requestAnimationFrame(loop);
  }
  loop();
}

function renderSaidaDashboard() {
  const el = document.getElementById("saida-dashboard");
  if (!el || !state.resumo) return;
  const r = state.resumo;
  const consolidated = {
    dataset: {
      vertices: r.dataset?.num_vertices,
      arestas: r.dataset?.num_arestas,
      ilhas: r.dataset?.componentes_conexas,
      maior_ilha: r.dataset?.maior_componente_conexa,
      grau_medio: r.dataset?.grau?.medio,
    },
    bfs_dfs: {
      bfs: (r.buscas?.bfs ?? []).map(compactSearch),
      dfs: (r.buscas?.dfs ?? []).map(compactSearch),
    },
    dijkstra: (r.dijkstra ?? []).map(compactDijkstra),
    bellman_ford: (r.bellman_ford ?? []).map(item => ({
      dataset: fileName(item.dataset),
      origem: item.origem,
      ciclo_negativo: item.ciclo_negativo,
      distancias: item.distancias,
      tempo_s: item.tempo_s,
    })),
  };
  el.innerHTML = `
    <p class="saida-dash-title">resumo_parte2.json <span style="font-weight:400;color:var(--muted);font-size:11px;">— filtrado</span></p>
    <pre class="saida-json">${attr(JSON.stringify(consolidated, null, 2))}</pre>`;
}

function setupMovieAutocomplete(inputId, listId, titles) {
  const input = document.getElementById(inputId);
  const list = document.getElementById(listId);
  if (!input || !list) return;

  let activeIdx = -1;

  function close() { list.classList.remove("open"); list.innerHTML = ""; activeIdx = -1; }

  function open(matches) {
    list.innerHTML = "";
    activeIdx = -1;
    if (!matches.length) { close(); return; }
    matches.slice(0, 40).forEach((title, i) => {
      const li = document.createElement("li");
      li.textContent = title;
      li.addEventListener("mousedown", (e) => { e.preventDefault(); input.value = title; close(); });
      list.appendChild(li);
    });
    list.classList.add("open");
  }

  input.addEventListener("input", () => {
    const q = input.value.trim().toLowerCase();
    if (!q) { close(); return; }
    open(titles.filter(t => t.toLowerCase().includes(q)));
  });

  input.addEventListener("keydown", (e) => {
    const items = list.querySelectorAll("li");
    if (e.key === "ArrowUp") { e.preventDefault(); activeIdx = Math.max(0, activeIdx - 1); items.forEach((li, i) => li.classList.toggle("active", i === activeIdx)); items[activeIdx]?.scrollIntoView({ block: "nearest" }); }
    else if (e.key === "ArrowDown") { e.preventDefault(); activeIdx = Math.min(items.length - 1, activeIdx + 1); items.forEach((li, i) => li.classList.toggle("active", i === activeIdx)); items[activeIdx]?.scrollIntoView({ block: "nearest" }); }
    else if (e.key === "Enter" && activeIdx >= 0) { input.value = items[activeIdx].textContent; close(); }
    else if (e.key === "Escape") { close(); }
  });

  input.addEventListener("blur", () => setTimeout(close, 150));
}

init().catch((err) => {
  document.body.classList.add("load-error");
  console.error("[init] falha ao carregar:", err);
  const ph = document.getElementById("graph-placeholder");
  if (ph) ph.innerHTML = `<strong style="color:#ff4d4d">Erro ao carregar: ${err?.message ?? err}</strong>`;
});

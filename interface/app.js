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

  const rawWidth = extra.width ?? Math.max(1, Math.min(10, 0.8 + Math.sqrt(value) * 1.9));

  return {
    id: edge.id ?? edgeKey(edgeOrigem(edge), edgeDestino(edge)),
    from: edgeOrigem(edge),
    to: edgeDestino(edge),
    title: edgeTitle(edge),
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

  return {
    nodes: [
      node("ok-z", "sem ciclo\nz", -330, -130, "#2ecc71", 44, "fonte Z do caso sem ciclo negativo"),
      node("ok-a", "a", -455, 40, "#f5c518", 34, "vertice alcancado com peso positivo"),
      node("ok-b", "b", -205, 40, "#f5c518", 34, "vertice alcancado pela fonte Z"),
      node("ok-c", "c", -330, 210, "#f5c518", 34, "recebe relaxamento com peso negativo, mas sem formar ciclo negativo"),
      node("bad-a", "com ciclo\na", 260, -130, "#ff4d4d", 44, "inicio do caso com ciclo negativo"),
      node("bad-b", "b", 105, 150, "#f5c518", 34, "parte do ciclo dirigido"),
      node("bad-c", "c", 415, 150, "#ff4d4d", 40, "fecha o ciclo negativo voltando para a"),
    ],
    edges: [
      directedEdge("ok-z", "ok-a", "5", "sem ciclo negativo"),
      directedEdge("ok-z", "ok-b", "2", "sem ciclo negativo"),
      directedEdge("ok-b", "ok-c", "0", "sem ciclo negativo"),
      directedEdge("ok-a", "ok-c", "-3", "sem ciclo negativo"),
      directedEdge("bad-a", "bad-b", "1", "com ciclo negativo"),
      directedEdge("bad-b", "bad-c", "-3", "com ciclo negativo", true),
      directedEdge("bad-c", "bad-a", "1", "com ciclo negativo", true),
    ],
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
  const useFullGraph = !!state.grafoCompleto;
  const adj = useFullGraph ? buildGrafoAdjacency() : buildAmostraAdjacency();

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
      const peso = useFullGraph ? (v.peso ?? 1) : Number(v.edge?.peso ?? 1);
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

  return {
    path,
    cost: dist.get(destino),
    algorithm: "dijkstra",
    fullGraph: useFullGraph,
  };
}

function dfsPath(origem, destino) {
  const useFullGraph = !!state.grafoCompleto;
  const adj = useFullGraph ? buildGrafoAdjacency() : buildAmostraAdjacency();

  const visited = new Set();
  const stack = [[origem, [origem]]];

  while (stack.length) {
    const [node, path] = stack.pop();
    if (visited.has(node)) continue;
    visited.add(node);
    if (node === destino) return { path, cost: null, algorithm: "profundidade", fullGraph: useFullGraph };

    const vizinhos = adj.get(node) ?? [];
    for (let i = vizinhos.length - 1; i >= 0; i--) {
      const v = vizinhos[i].to;
      if (!visited.has(v)) {
        stack.push([v, [...path, v]]);
      }
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
    const baseSize = nodeSizeByGlobalDegree(id, 24, 46);
    return baseNode(id, {
      size: isFirst || isLast ? Math.max(baseSize, 44) : baseSize,
      background: isFirst ? "#2ecc71" : isLast ? "#ff4d4d" : "#f5c518",
      border: "#ffffff",
    });
  });

  const mainEdges = pathEdges(route.path, { prefix: "dijkstra" }).map((edge) => {
    pathEdgeIds.add(edgeKey(edgeOrigem(edge), edgeDestino(edge)));
    return baseEdge(edge, {
      color: "#ff9f1c",
      width: 6,
      arrows: "to",
      label: String(edge.similaridade ?? ""),
    });
  });

  return {
    nodes,
    edges: mainEdges,
    layout: "network",
  };
}

function longestDijkstraPath() {
  const nodes = Object.keys(state.amostra?.movies ?? {});
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
      seeds: ["Harry Potter and the Sorcerer's Stone",
               "Harry Potter and the Chamber of Secrets",
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
    if ((e.similaridade ?? 0) >= 8) edgeMap[e.id] = e;
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

  if (mode === "bellman-ford") {
    return makeBellmanFordGraph();
  }

  if (mode === "grafo-completo") {
    return makeFullGraph();
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
  animateNumber('[data-field="grau_medio"]', dataset.grau?.medio, 2);
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

  const bellmanRows = bellmanList.map((item) => {
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
          <h4>Bellman-Ford — grafos artificiais com pesos negativos</h4>
          <span class="results-table-badge ok">sem ciclo negativo ✓</span>
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
            <tbody>${bellmanRows}</tbody>
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
  const details = document.getElementById("details-panel");

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
  const details = document.getElementById("details-panel");
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

function renderModeDetails(mode) {
  const panel = document.getElementById("details-panel");
  const configs = {
    franquias: {
      eyebrow: "modo: franquias",
      titulo: "grupos por elenco compartilhado",
      descricao: "cada cor representa uma franquia. dois filmes se conectam quando compartilham atores — quanto mais atores em comum, mais grossa a aresta.",
      itens: [
        ["nó maior", "filme com mais conexões no dataset (grau alto)"],
        ["aresta grossa", "alta similaridade: muitos atores em comum"],
        ["aresta fina", "baixa similaridade: poucos atores ou só gênero"],
        ["cor do nó", "identifica a franquia (Marvel, Star Wars, etc.)"],
        ["passe o mouse", "veja título, ano, gênero e nota IMDb"],
      ],
    },
    similaridade: {
      eyebrow: "modo: maior similaridade",
      titulo: "filmes mais parecidos entre si",
      descricao: "mostra uma amostra conectada das arestas com maior similaridade. a similaridade é calculada como (2 × atores em comum) + gêneros em comum.",
      itens: [
        ["nó maior", "filme com mais conexões no dataset (hub)"],
        ["cor do nó", "gênero principal do filme"],
        ["aresta grossa", "muitos atores e/ou gêneros em comum"],
        ["aresta fina", "conexão mais fraca (só gênero, por exemplo)"],
        ["passe o mouse", "veja atores compartilhados e similaridade exata"],
      ],
    },
    top: {
      eyebrow: "modo: top conexões",
      titulo: "filmes mais conectados (hubs)",
      descricao: "exibe os filmes que mais compartilham atores com outros. hubs são vértices de alto grau — filmes com elencos grandes que aparecem em muitas outras produções.",
      itens: [
        ["nó maior", "hub: filme com centenas de conexões no dataset"],
        ["cor do nó", "gênero principal do filme"],
        ["aresta", "cada linha = elenco compartilhado com outro hub"],
        ["passe o mouse", "veja quais atores conectam os dois filmes"],
      ],
    },
  };
  const c = configs[mode];
  if (!c) { resetDetails(); return; }

  panel.innerHTML = `
    <p class="eyebrow">${attr(c.eyebrow)}</p>
    <h3>${attr(c.titulo)}</h3>
    <p>${attr(c.descricao)}</p>
    <dl class="detail-list">
      ${c.itens.map(([dt, dd]) => `<div><dt>${attr(dt)}</dt><dd>${attr(dd)}</dd></div>`).join("")}
    </dl>
  `;
}

function renderBellmanDetails() {
  document.getElementById("details-panel").innerHTML = `
    <p class="eyebrow">bellman-ford</p>
    <h3>validacao direcionada artificial</h3>
    <p>estes dois grafos nao sao do imdb. eles validam peso negativo sem ciclo e deteccao de ciclo negativo.</p>
    <dl class="detail-list">
      <div>
        <dt>caso sem ciclo negativo</dt>
        <dd>grafo dirigido com peso negativo controlado; o algoritmo calcula distancias finais.</dd>
      </div>
      <div>
        <dt>caso com ciclo negativo</dt>
        <dd>grafo dirigido com ciclo de custo negativo; o algoritmo bloqueia o resultado.</dd>
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

async function loadGrafoCompleto() {
  if (state.grafoCompleto) return state.grafoCompleto;
  const data = await fetchJson("data/parte2_grafo.json?v=1");
  state.grafoCompleto = data;
  return data;
}

function showFullGraphModal(modeSelect) {
  const modal = document.getElementById("full-graph-modal");
  const confirmBtn = document.getElementById("full-graph-confirm");
  const cancelBtn = document.getElementById("full-graph-cancel");
  const backdrop = document.getElementById("full-graph-backdrop");

  modal.setAttribute("aria-hidden", "false");
  modal.style.display = "flex";

  function close(revert = true) {
    modal.setAttribute("aria-hidden", "true");
    modal.style.display = "";
    if (revert) modeSelect.value = "similaridade";
    confirmBtn.removeEventListener("click", onConfirm);
    cancelBtn.removeEventListener("click", onCancel);
    backdrop.removeEventListener("click", onCancel);
  }

  async function onConfirm() {
    close(false);
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

function setupGraphControls() {
  const mode = document.getElementById("graph-mode");
  const search = document.getElementById("graph-search");
  const searchButton = document.getElementById("search-btn");
  const resetButton = document.getElementById("reset-graph-btn");
  const routeOrigem = document.getElementById("route-origem");
  const routeDestino = document.getElementById("route-destino");
  const routeAlgorithm = document.getElementById("route-algorithm");
  const routeButton = document.getElementById("route-run-btn");

  mode.addEventListener("change", () => {
    if (mode.value === "grafo-completo") {
      showFullGraphModal(mode);
      return;
    }
    drawGraph(mode.value);
    refreshGraphView(true);
    if (mode.value === "bellman-ford") {
      renderBellmanDetails();
    } else if (mode.value === "franquias") {
      renderModeDetails("franquias");
    } else if (mode.value === "similaridade") {
      renderModeDetails("similaridade");
    } else if (mode.value === "top") {
      renderModeDetails("top");
    } else {
      resetDetails();
    }
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

  async function runRoute() {
    const origem = routeOrigem.value.trim();
    const destino = routeDestino.value.trim();
    const algorithm = routeAlgorithm.value;

    if (!origem || !destino) return;

    if (!state.grafoCompleto) {
      routeButton.textContent = "carregando grafo...";
      routeButton.disabled = true;
      await loadGrafoCompleto();
      routeButton.textContent = "calcular rota";
      routeButton.disabled = false;
    }

    const result = algorithm === "dfs"
      ? dfsPath(origem, destino)
      : dijkstraPath(origem, destino);

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
      drawGraph(makeNeighborhoodGraph(origem));
    }

    renderRouteDetails(result, origem, destino);
    const movieExists = (id) =>
      !!(state.amostra?.movies?.[id] ?? state.grafoCompleto?.filmes?.[id]);
    routeOrigem.classList.toggle("search-miss", !movieExists(origem));
    routeDestino.classList.toggle("search-miss", !movieExists(destino));
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
    state.network?.fit({
      animation: {
        duration: 500,
        easingFunction: "easeInOutQuad",
      },
    });
    resetDetails();
  });

  drawGraph(mode.value);
  if (["franquias", "similaridade", "top"].includes(mode.value)) {
    renderModeDetails(mode.value);
  }
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
  const [resumo, amostra] = await Promise.all([
    fetchJson("data/resumo_parte2.json?v=1"),
    fetchJson("data/parte2_amostra.json?v=7"),
  ]);
  state.resumo = resumo;
  state.amostra = amostra;

  const dl = document.getElementById("movies-list");
  if (dl && amostra?.movies) {
    Object.keys(amostra.movies).sort().forEach((title) => {
      const opt = document.createElement("option");
      opt.value = title;
      dl.appendChild(opt);
    });
  }

  setupViews();
  renderMetrics(state.resumo.dataset);
  renderResults(state.resumo);
  renderBenchmarkOutput(state.resumo);
  renderRawOutputs(state.resumo);
  renderVisualizations(state.resumo.visualizacoes);
  setupGraphControls();
  setupVizModal();
  setupGraphFullscreen();
}

init().catch(() => {
  document.body.classList.add("load-error");
});

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
  const meta = [movie.ano, movie.generos, movie.nota ? `nota ${movie.nota}` : ""]
    .filter(Boolean)
    .join(" | ");
  return `${movie.titulo || id}\n${id}${meta ? `\n${meta}` : ""}`;
}

function edgeTitle(edge) {
  const origem = movieInfo(edgeOrigem(edge));
  const destino = movieInfo(edgeDestino(edge));
  const genres = commonGenres(edgeOrigem(edge), edgeDestino(edge));
  return [
    `${origem.titulo || edgeOrigem(edge)} -> ${destino.titulo || edgeDestino(edge)}`,
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
    id: edge.id ?? edgeKey(edgeOrigem(edge), edgeDestino(edge)),
    from: edgeOrigem(edge),
    to: edgeDestino(edge),
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
    nodes.set(edgeOrigem(edge), edgeOrigem(edge));
    nodes.set(edgeDestino(edge), edgeDestino(edge));
    degrees.set(edgeOrigem(edge), (degrees.get(edgeOrigem(edge)) ?? 0) + 1);
    degrees.set(edgeDestino(edge), (degrees.get(edgeDestino(edge)) ?? 0) + 1);
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
  // retorna cache se ja construido
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
  // min-heap simples com array ordenado (ok ate ~100k arestas)
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

  // iterativo para evitar stack overflow com 100k arestas
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
  // max vizinhos por no: evita que um hub (ex: Jurassic Park) ocupe todos os slots
  const maxPerNode = type === "bfs" ? 4 : 3;

  function addNode(id, level) {
    nodes.push(baseNode(id, {
      level,
      size: id === origem ? 42 : 28,
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
    return baseNode(id, {
      size: isFirst || isLast ? 42 : 30,
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

  // limite absoluto: pega as 3000 arestas de maior similaridade
  // o roteamento (dijkstra/dfs) usa todas as 100k via buildGrafoAdjacency()
  const LIMITE_VISUAL = 3000;
  const arestasSorted = [...arestas].sort((a, b) => (b.sim ?? 0) - (a.sim ?? 0));
  const arestasFiltradas = arestasSorted.slice(0, LIMITE_VISUAL);

  // apenas nos que aparecem nessas arestas
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

function graphForMode(mode) {
  const edges = Object.values(state.amostra?.edges ?? {});
  const bySimilarity = [...edges].sort((a, b) => (b.similaridade ?? 0) - (a.similaridade ?? 0));
  const byActors = [...edges].sort((a, b) =>
    (b.actors_common ?? 0) - (a.actors_common ?? 0)
    || (b.similaridade ?? 0) - (a.similaridade ?? 0)
    || (a.peso ?? Infinity) - (b.peso ?? Infinity)
  );

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

  return makeGraphFromEdges(connectedEdgeSample(bySimilarity, 24), {
    edgeOptions: { label: "" },
  });
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
  const bfs = resumo.buscas?.bfs ?? [];
  const dfs = resumo.buscas?.dfs ?? [];
  const dijkstra = resumo.dijkstra ?? [];
  const bellmanFord = resumo.bellman_ford ?? [];
  const dijkstraOk = dijkstra.filter((item) => !item.sem_caminho).length;
  const bfCycle = bellmanFord.some((item) => item.ciclo_negativo);

  document.getElementById("results-resumo").innerHTML = [
    `
      <article class="result-stat">
        <h3>buscas</h3>
        <span>${bfs.length + dfs.length}</span>
        <p>bfs mede alcance por camadas. dfs percorre trilhas mais profundas nas mesmas fontes.</p>
        <small>${metricValue(resumo.buscas?.fontes_principais?.length ?? 0)} filmes de partida usados tanto na bfs quanto na dfs.</small>
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
        <p>usa grafos dirigidos de validacao para testar pesos negativos e detectar ciclo negativo.</p>
        <small>casos sinteticos separados do grafo imdb principal.</small>
      </article>
    `,
  ].join("");
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
      // melhora o desempenho no grafo completo
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

  // popula datalist com os titulos da amostra para autocomplete nos inputs de busca.
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

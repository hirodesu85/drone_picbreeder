import * as THREE from "three";

// 定数
const FPS = 25;
const FRAME_DURATION = 1000 / FPS; // ミリ秒
const API_BASE = "http://localhost:8000";

// グローバル変数
let sessionId = null; // セッションID
let currentGeneration = -1;
let genomeIds = [];
let selectedIndices = new Set(); // 選択されたグリッドのインデックス
let gridSceneCleanups = []; // グリッドシーンのクリーンアップ関数

// Modal state
let modalOpen = false;
let modalScene = null;
let modalRenderer = null;
let modalCamera = null;
let modalAnimationId = null;
let modalResizeHandler = null;

// History modal state
let historyModalOpen = false;

// RGB値(0-255)をThree.jsの16進数カラーコード(0x000000-0xFFFFFF)に変換
function rgbToHex(r, g, b) {
  return (r << 16) | (g << 8) | b;
}

// API呼び出し関数
async function initializeEvolution() {
  const response = await fetch(`${API_BASE}/api/evolution/initialize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ num_drones: 50 }),
  });
  const data = await response.json();

  // セッションIDを保存
  sessionId = data.session_id;

  return data;
}

async function getGenomes() {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/genomes`, {
    headers: {
      "X-Session-ID": sessionId,
    },
  });

  if (!response.ok) {
    throw new Error(`ゲノム取得失敗: ${response.status}`);
  }

  return await response.json();
}

async function getPattern(genomeId, duration = 3.0) {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(
    `${API_BASE}/api/evolution/pattern/${genomeId}?duration=${duration}`,
    {
      headers: {
        "X-Session-ID": sessionId,
      },
    },
  );

  if (!response.ok) {
    throw new Error(`パターン取得失敗: ${response.status}`);
  }

  return await response.json();
}

async function assignFitness(genomeId, fitness) {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/fitness`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": sessionId,
    },
    body: JSON.stringify({ genome_id: genomeId, fitness: fitness }),
  });

  if (!response.ok) {
    throw new Error(`適応度割り当て失敗: ${genomeId}`);
  }

  return await response.json();
}

async function evolveGeneration() {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/evolve`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": sessionId,
    },
    body: JSON.stringify({ default_fitness: 0.0 }),
  });

  if (!response.ok) {
    throw new Error("進化失敗");
  }

  return await response.json();
}

async function getCPPNStructure(genomeId) {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/cppn/${genomeId}`, {
    headers: {
      "X-Session-ID": sessionId,
    },
  });

  if (!response.ok) {
    throw new Error(`CPPN構造取得失敗: ${response.status}`);
  }

  return await response.json();
}

async function getEvolutionHistory() {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/history`, {
    headers: {
      "X-Session-ID": sessionId,
    },
  });

  if (!response.ok) {
    throw new Error(`進化履歴取得失敗: ${response.status}`);
  }

  return await response.json();
}

async function checkConstraints() {
  if (!sessionId) {
    throw new Error("セッションが初期化されていません");
  }

  const response = await fetch(`${API_BASE}/api/evolution/constraints/check`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Session-ID": sessionId,
    },
  });

  if (!response.ok) {
    throw new Error(`制約チェック失敗: ${response.status}`);
  }

  return await response.json();
}

// 各グリッドセルにThree.jsシーンを作成（ドローンショー表示）
async function createScene(container, showData) {
  // シーン
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);

  // カメラ（俯瞰視点）
  const camera = new THREE.PerspectiveCamera(
    75,
    1, // aspect ratio (正方形)
    0.1,
    1000,
  );
  camera.position.set(13, 7, 13);
  camera.lookAt(0, 0, 0);

  // レンダラー
  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(renderer.domElement);

  // ライト
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  scene.add(ambientLight);

  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(5, 5, 5);
  scene.add(directionalLight);

  // ドローンの球体を作成
  const droneMeshes = [];
  const droneGeometry = new THREE.SphereGeometry(0.1, 16, 16);
  const numDrones = showData.frames[0].drones.length;

  for (let i = 0; i < numDrones; i++) {
    // 初期フレームから色情報を取得
    const initialDrone = showData.frames[0].drones[i];
    const r = initialDrone.r !== undefined ? initialDrone.r : 127;
    const g = initialDrone.g !== undefined ? initialDrone.g : 255;
    const b = initialDrone.b !== undefined ? initialDrone.b : 127;

    // RGB値からThree.jsの色を作成
    const material = new THREE.MeshPhongMaterial({
      color: rgbToHex(r, g, b),
      emissive: rgbToHex(
        Math.floor(r * 0.7),
        Math.floor(g * 0.7),
        Math.floor(b * 0.7),
      ),
    });
    const drone = new THREE.Mesh(droneGeometry, material);

    // 初期位置を設定
    drone.position.set(initialDrone.x, initialDrone.z, initialDrone.y);

    scene.add(drone);
    droneMeshes.push(drone);
  }

  // アニメーションループ
  let startTime = Date.now();
  let animationId = null;

  function animate() {
    animationId = requestAnimationFrame(animate);

    // 経過時間を計算
    const elapsed = Date.now() - startTime;
    const expectedFrameIndex = Math.floor(elapsed / FRAME_DURATION);

    // フレームをループ
    const currentFrameIndex = expectedFrameIndex % showData.frames.length;

    // ドローンの位置と色を更新
    const currentFrame = showData.frames[currentFrameIndex];
    for (let i = 0; i < droneMeshes.length; i++) {
      const drone = currentFrame.drones[i];

      // 位置を更新
      droneMeshes[i].position.set(drone.x, drone.z, drone.y);

      // 色を更新（RGB値が存在する場合）
      if (
        drone.r !== undefined &&
        drone.g !== undefined &&
        drone.b !== undefined
      ) {
        droneMeshes[i].material.color.setHex(
          rgbToHex(drone.r, drone.g, drone.b),
        );
        droneMeshes[i].material.emissive.setHex(
          rgbToHex(
            Math.floor(drone.r * 0.7),
            Math.floor(drone.g * 0.7),
            Math.floor(drone.b * 0.7),
          ),
        );
      }
    }

    renderer.render(scene, camera);
  }
  animate();

  // リサイズ対応
  const resizeObserver = new ResizeObserver(() => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    renderer.setSize(width, height);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
  });
  resizeObserver.observe(container);

  // クリーンアップ関数を返す
  return function cleanup() {
    // アニメーションループをキャンセル
    if (animationId) {
      cancelAnimationFrame(animationId);
      animationId = null;
    }

    // ResizeObserverを切断
    if (resizeObserver) {
      resizeObserver.disconnect();
    }

    // Three.jsリソースを破棄
    scene.traverse((object) => {
      if (object.geometry) object.geometry.dispose();
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach((m) => m.dispose());
        } else {
          object.material.dispose();
        }
      }
    });

    // レンダラーを破棄
    if (renderer) {
      renderer.dispose();
    }

    // canvasをDOMから削除（詳細ボタンは残す）
    const canvas = container.querySelector("canvas");
    if (canvas) {
      container.removeChild(canvas);
    }
  };
}

// パターンを読み込む
async function loadPatterns() {
  try {
    // 前のシーンをクリーンアップ
    gridSceneCleanups.forEach((cleanup) => cleanup());
    gridSceneCleanups = [];

    // 初期化（まだ初期化されていない場合）
    if (currentGeneration === -1) {
      await initializeEvolution();
    }

    // ゲノムリストを取得
    const data = await getGenomes();
    currentGeneration = data.generation;
    genomeIds = data.genome_ids; // 全て使う（sliceを削除）

    // 世代情報を更新
    document.getElementById("generation-info").textContent =
      `世代: ${currentGeneration}`;

    const gridItems = document.querySelectorAll(".grid-item");

    // パターンを並列で事前取得（パフォーマンス維持）
    const patternPromises = genomeIds.map((genomeId) => getPattern(genomeId));
    const patterns = await Promise.all(patternPromises);

    // シーン作成は順次実行（WebGLコンテキスト制限対策）
    for (let index = 0; index < genomeIds.length; index++) {
      const genomeId = genomeIds[index];
      const pattern = patterns[index];

      clearGrid(gridItems[index]);
      const cleanup = await createScene(gridItems[index], pattern);
      gridSceneCleanups.push(cleanup);

      // 詳細ボタンを追加（既存のコード）
      if (!gridItems[index].querySelector(".detail-btn")) {
        const detailBtn = document.createElement("button");
        detailBtn.className = "detail-btn";
        detailBtn.innerHTML = `
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round">
                        <circle cx="6.5" cy="6.5" r="4.5"/>
                        <line x1="10" y1="10" x2="14" y2="14"/>
                    </svg>
                `;
        detailBtn.title = "詳細表示";
        detailBtn.addEventListener("click", (e) => {
          e.stopPropagation();
          openModal(genomeId, index);
        });
        gridItems[index].appendChild(detailBtn);
      }
    }
  } catch (error) {
    alert("エラー: " + error.message);
    console.error(error);
  }
}

// ヘルパー関数
function showLoading(show) {
  document.getElementById("loading").style.display = show ? "block" : "none";
}

function clearGrid(container) {
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
}

// グリッドクリックハンドラー（イベント委譲用）
function handleGridClick(event) {
  // クリックされた要素から.grid-itemを探す
  // canvas要素をクリックした場合も親の.grid-itemを取得
  const gridItem = event.target.closest(".grid-item");
  if (!gridItem) return;

  // 全グリッドアイテムからインデックスを取得
  const gridItems = document.querySelectorAll(".grid-item");
  const index = Array.from(gridItems).indexOf(gridItem);

  if (index !== -1) {
    toggleSelection(index);
  }
}

// グリッド選択機能（イベント委譲パターン）
let isGridSelectionInitialized = false;

function setupGridSelection() {
  if (isGridSelectionInitialized) {
    return; // 既に初期化済みの場合は何もしない
  }

  const gridContainer = document.querySelector(".grid-container");
  gridContainer.addEventListener("click", handleGridClick);
  isGridSelectionInitialized = true;
}

function toggleSelection(index) {
  const gridItem = document.querySelectorAll(".grid-item")[index];

  if (selectedIndices.has(index)) {
    // 選択解除
    selectedIndices.delete(index);
    gridItem.classList.remove("selected");
  } else {
    // 選択
    selectedIndices.add(index);
    gridItem.classList.add("selected");
  }

  // 進化ボタンの有効/無効を更新
  updateEvolveButton();
}

function updateEvolveButton() {
  const evolveBtn = document.getElementById("evolve-btn");
  evolveBtn.disabled = selectedIndices.size === 0;
}

// モーダル制御関数
function openModal(genomeId, genomeIndex) {
  const modal = document.getElementById("detail-modal");
  modal.classList.add("active");
  modalOpen = true;

  document.getElementById("modal-title").textContent =
    `Animation ${genomeIndex + 1} - Genome ID: ${genomeId}`;

  loadModalAnimation(genomeId);
  loadCPPNGraph(genomeId);
}

function closeModal() {
  const modal = document.getElementById("detail-modal");
  modal.classList.remove("active");
  modalOpen = false;
  cleanupModalScene();
}

function cleanupModalScene() {
  if (modalAnimationId) {
    cancelAnimationFrame(modalAnimationId);
    modalAnimationId = null;
  }

  if (modalRenderer) {
    modalRenderer.dispose();
    modalRenderer = null;
  }

  if (modalScene) {
    modalScene.traverse((object) => {
      if (object.geometry) object.geometry.dispose();
      if (object.material) {
        if (Array.isArray(object.material)) {
          object.material.forEach((m) => m.dispose());
        } else {
          object.material.dispose();
        }
      }
    });
    modalScene = null;
  }

  if (modalResizeHandler) {
    window.removeEventListener("resize", modalResizeHandler);
    modalResizeHandler = null;
  }

  modalCamera = null;

  const container = document.getElementById("modal-scene-container");
  while (container.firstChild) {
    container.removeChild(container.firstChild);
  }
}

// モーダルシーンとアニメーション
async function loadModalAnimation(genomeId) {
  const container = document.getElementById("modal-scene-container");
  const pattern = await getPattern(genomeId, 3.0);

  // Scene
  modalScene = new THREE.Scene();
  modalScene.background = new THREE.Color(0x000000);

  // Camera
  modalCamera = new THREE.PerspectiveCamera(
    75,
    container.clientWidth / container.clientHeight,
    0.1,
    1000,
  );
  modalCamera.position.set(13, 7, 13);
  modalCamera.lookAt(0, 0, 0);

  // Renderer
  modalRenderer = new THREE.WebGLRenderer({ antialias: true });
  modalRenderer.setSize(container.clientWidth, container.clientHeight);
  modalRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(modalRenderer.domElement);

  // Lights
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.6);
  modalScene.add(ambientLight);
  const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
  directionalLight.position.set(5, 5, 5);
  modalScene.add(directionalLight);

  // Drones
  const droneMeshes = [];
  const droneGeometry = new THREE.SphereGeometry(0.1, 16, 16);
  const numDrones = pattern.frames[0].drones.length;

  for (let i = 0; i < numDrones; i++) {
    const initialDrone = pattern.frames[0].drones[i];
    const r = initialDrone.r !== undefined ? initialDrone.r : 127;
    const g = initialDrone.g !== undefined ? initialDrone.g : 127;
    const b = initialDrone.b !== undefined ? initialDrone.b : 255;

    const material = new THREE.MeshPhongMaterial({
      color: rgbToHex(r, g, b),
      emissive: rgbToHex(
        Math.floor(r * 0.7),
        Math.floor(g * 0.7),
        Math.floor(b * 0.7),
      ),
    });
    const drone = new THREE.Mesh(droneGeometry, material);
    drone.position.set(initialDrone.x, initialDrone.z, initialDrone.y);

    modalScene.add(drone);
    droneMeshes.push(drone);
  }

  // Animation loop
  let startTime = Date.now();

  function animate() {
    if (!modalOpen) return;

    modalAnimationId = requestAnimationFrame(animate);

    const elapsed = Date.now() - startTime;
    const expectedFrameIndex = Math.floor(elapsed / FRAME_DURATION);
    const currentFrameIndex = expectedFrameIndex % pattern.frames.length;
    const currentFrame = pattern.frames[currentFrameIndex];

    for (let i = 0; i < droneMeshes.length; i++) {
      const drone = currentFrame.drones[i];
      droneMeshes[i].position.set(drone.x, drone.z, drone.y);

      if (
        drone.r !== undefined &&
        drone.g !== undefined &&
        drone.b !== undefined
      ) {
        droneMeshes[i].material.color.setHex(
          rgbToHex(drone.r, drone.g, drone.b),
        );
        droneMeshes[i].material.emissive.setHex(
          rgbToHex(
            Math.floor(drone.r * 0.7),
            Math.floor(drone.g * 0.7),
            Math.floor(drone.b * 0.7),
          ),
        );
      }
    }

    modalRenderer.render(modalScene, modalCamera);
  }
  animate();

  // Resize handler
  modalResizeHandler = () => {
    if (!modalOpen || !modalCamera || !modalRenderer) return;
    const width = container.clientWidth;
    const height = container.clientHeight;
    modalCamera.aspect = width / height;
    modalCamera.updateProjectionMatrix();
    modalRenderer.setSize(width, height);
  };
  window.addEventListener("resize", modalResizeHandler);
}

// SVGグラフ描画
async function loadCPPNGraph(genomeId) {
  const svg = document.getElementById("cppn-svg");

  try {
    const cppnData = await getCPPNStructure(genomeId);

    // Clear previous content
    svg.innerHTML = "";

    // SVG dimensions
    const width = 360;
    const height = 430;
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);

    // Separate nodes by type
    const inputNodes = cppnData.nodes.filter((n) => n.type === "input");
    const outputNodes = cppnData.nodes.filter((n) => n.type === "output");
    const hiddenNodes = cppnData.nodes.filter((n) => n.type === "hidden");

    // Calculate layers (simple approach: input -> hidden -> output)
    const layers = [inputNodes, hiddenNodes, outputNodes].filter(
      (layer) => layer.length > 0,
    );
    const layerSpacing = width / (layers.length + 1);

    // Node positions
    const nodePositions = new Map();

    layers.forEach((layer, layerIndex) => {
      const x = layerSpacing * (layerIndex + 1);
      const nodeSpacing = height / (layer.length + 1);

      layer.forEach((node, nodeIndex) => {
        const y = nodeSpacing * (nodeIndex + 1);
        nodePositions.set(node.id, { x, y, node });
      });
    });

    // Draw connections first (so they appear behind nodes)
    const connectionsGroup = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "g",
    );
    connectionsGroup.setAttribute("class", "connections");

    cppnData.connections.forEach((conn) => {
      if (!conn.enabled) return; // Skip disabled connections

      const fromPos = nodePositions.get(conn.from);
      const toPos = nodePositions.get(conn.to);

      if (fromPos && toPos) {
        const line = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "line",
        );
        line.setAttribute("x1", fromPos.x);
        line.setAttribute("y1", fromPos.y);
        line.setAttribute("x2", toPos.x);
        line.setAttribute("y2", toPos.y);

        // Weight determines stroke width and opacity
        const absWeight = Math.abs(conn.weight);
        const strokeWidth = Math.max(0.5, Math.min(3, absWeight / 10));
        const opacity = Math.max(0.3, Math.min(0.9, absWeight / 30));

        // Positive weights = green, negative = red
        const color = conn.weight > 0 ? "#4CAF50" : "#f44336";

        line.setAttribute("stroke", color);
        line.setAttribute("stroke-width", strokeWidth);
        line.setAttribute("opacity", opacity);

        // Tooltip
        const title = document.createElementNS(
          "http://www.w3.org/2000/svg",
          "title",
        );
        title.textContent = `Weight: ${conn.weight.toFixed(3)}`;
        line.appendChild(title);

        connectionsGroup.appendChild(line);
      }
    });
    svg.appendChild(connectionsGroup);

    // Draw nodes
    const nodesGroup = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "g",
    );
    nodesGroup.setAttribute("class", "nodes");

    nodePositions.forEach(({ x, y, node }) => {
      // Node circle
      const circle = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle",
      );
      circle.setAttribute("cx", x);
      circle.setAttribute("cy", y);
      circle.setAttribute("r", 8);

      // Color by type
      let fillColor;
      if (node.type === "input") fillColor = "#2196F3";
      else if (node.type === "output") fillColor = "#FF5722";
      else fillColor = "#4CAF50";

      circle.setAttribute("fill", fillColor);
      circle.setAttribute("stroke", "white");
      circle.setAttribute("stroke-width", "1.5");

      // Tooltip
      const title = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "title",
      );
      title.textContent = `${node.label}\nActivation: ${node.activation}\nBias: ${node.bias.toFixed(3)}`;
      circle.appendChild(title);

      nodesGroup.appendChild(circle);

      // Node label
      const text = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text",
      );
      text.setAttribute("x", x);
      text.setAttribute("y", y + 20);
      text.setAttribute("text-anchor", "middle");
      text.setAttribute("fill", "white");
      text.setAttribute("font-size", "10");
      text.setAttribute("font-weight", "bold");
      text.textContent = node.label;

      nodesGroup.appendChild(text);
    });
    svg.appendChild(nodesGroup);

    // Add legend
    const legendGroup = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "g",
    );
    legendGroup.setAttribute("class", "legend");
    legendGroup.setAttribute("transform", "translate(10, 10)");

    const legendItems = [
      { label: "Input", color: "#2196F3" },
      { label: "Hidden", color: "#4CAF50" },
      { label: "Output", color: "#FF5722" },
    ];

    legendItems.forEach((item, i) => {
      const circle = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "circle",
      );
      circle.setAttribute("cx", 0);
      circle.setAttribute("cy", i * 18);
      circle.setAttribute("r", 5);
      circle.setAttribute("fill", item.color);
      legendGroup.appendChild(circle);

      const text = document.createElementNS(
        "http://www.w3.org/2000/svg",
        "text",
      );
      text.setAttribute("x", 10);
      text.setAttribute("y", i * 18 + 4);
      text.setAttribute("fill", "white");
      text.setAttribute("font-size", "11");
      text.textContent = item.label;
      legendGroup.appendChild(text);
    });

    svg.appendChild(legendGroup);
  } catch (error) {
    svg.innerHTML =
      '<text x="50%" y="50%" text-anchor="middle" fill="#ff6b6b" font-size="14">CPPN取得エラー</text>';
    console.error("CPPN構造の取得エラー:", error);
  }
}

// 進化処理
async function evolve() {
  const evolveBtn = document.getElementById("evolve-btn");
  const originalText = evolveBtn.textContent;

  try {
    // ローディング状態を設定
    evolveBtn.disabled = true;
    evolveBtn.textContent = "進化中...";

    // 全てのゲノムに適応度を割り当て
    const fitnessPromises = genomeIds.map(async (genomeId, index) => {
      const fitness = selectedIndices.has(index) ? 1.0 : 0.0;
      await assignFitness(genomeId, fitness);
    });
    await Promise.all(fitnessPromises);

    // 進化実行
    await evolveGeneration();

    // 選択状態をクリア
    selectedIndices.clear();
    document.querySelectorAll(".grid-item").forEach((item) => {
      item.classList.remove("selected");
    });

    // 新しい世代をロード
    await loadPatterns();
  } catch (error) {
    alert("進化エラー: " + error.message);
    console.error(error);
  } finally {
    // ボタンを元に戻す
    evolveBtn.textContent = originalText;
    updateEvolveButton();
  }
}

// History Modal Functions
async function openHistoryModal() {
  const modal = document.getElementById("history-modal");
  modal.classList.add("active");
  historyModalOpen = true;

  await loadHistoryTable();
}

function closeHistoryModal() {
  const modal = document.getElementById("history-modal");
  modal.classList.remove("active");
  historyModalOpen = false;
}

async function loadHistoryTable() {
  const tbody = document.getElementById("history-table-body");
  tbody.innerHTML = '<tr><td colspan="5">読み込み中...</td></tr>';

  try {
    const data = await getEvolutionHistory();
    tbody.innerHTML = "";

    // 世代ごとにデータを表示（新しい世代が上）
    const sortedHistory = [...data.history].sort(
      (a, b) => b.generation - a.generation,
    );

    for (const generation of sortedHistory) {
      // 世代ヘッダー行
      const headerRow = document.createElement("tr");
      headerRow.className = "generation-header";
      headerRow.innerHTML = `<td colspan="5">世代 ${generation.generation}</td>`;
      tbody.appendChild(headerRow);

      // ゲノムIDでソート
      const sortedGenomes = [...generation.genomes].sort(
        (a, b) => a.genome_id - b.genome_id,
      );

      for (const genome of sortedGenomes) {
        const row = document.createElement("tr");

        // 親の表示
        const parent1Display =
          genome.parent1 !== null
            ? genome.parent1
            : '<span class="parent-null">-</span>';
        const parent2Display =
          genome.parent2 !== null
            ? genome.parent2
            : '<span class="parent-null">-</span>';

        // 適応度の表示とクラス
        let fitnessDisplay, fitnessClass;
        if (genome.fitness === null) {
          fitnessDisplay = "-";
          fitnessClass = "fitness-none";
        } else if (genome.fitness >= 0.5) {
          fitnessDisplay = genome.fitness.toFixed(2);
          fitnessClass = "fitness-high";
        } else {
          fitnessDisplay = genome.fitness.toFixed(2);
          fitnessClass = "fitness-low";
        }

        row.innerHTML = `
                    <td>${generation.generation}</td>
                    <td>${genome.genome_id}</td>
                    <td>${parent1Display}</td>
                    <td>${parent2Display}</td>
                    <td class="${fitnessClass}">${fitnessDisplay}</td>
                `;

        tbody.appendChild(row);
      }
    }

    // データがない場合
    if (data.history.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5">履歴データがありません</td></tr>';
    }
  } catch (error) {
    tbody.innerHTML = `<tr><td colspan="5" style="color: #ff6b6b;">エラー: ${error.message}</td></tr>`;
    console.error("履歴取得エラー:", error);
  }
}

// メイン処理
async function main() {
  const gridContainer = document.querySelector(".grid-container");

  // 12個の空グリッドを作成
  for (let i = 0; i < 12; i++) {
    const gridItem = document.createElement("div");
    gridItem.className = "grid-item";
    gridContainer.appendChild(gridItem);
  }

  // グリッド選択機能を初期化（一度だけ）
  setupGridSelection();

  // ボタンイベント
  document.getElementById("evolve-btn").addEventListener("click", evolve);

  // Modal event listeners
  document.getElementById("modal-close").addEventListener("click", closeModal);
  document.getElementById("detail-modal").addEventListener("click", (e) => {
    if (e.target.id === "detail-modal") closeModal();
  });

  // History modal event listeners
  document
    .getElementById("history-btn")
    .addEventListener("click", openHistoryModal);
  document
    .getElementById("history-modal-close")
    .addEventListener("click", closeHistoryModal);
  document.getElementById("history-modal").addEventListener("click", (e) => {
    if (e.target.id === "history-modal") closeHistoryModal();
  });

  // Constraint check button
  document
    .getElementById("constraint-check-btn")
    .addEventListener("click", async () => {
      try {
        const result = await checkConstraints();
        alert(result.message);
      } catch (error) {
        alert("制約チェックエラー: " + error.message);
        console.error(error);
      }
    });

  // Escapeキーでモーダルを閉じる
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      if (modalOpen) closeModal();
      if (historyModalOpen) closeHistoryModal();
    }
  });

  // 自動的に世代0を読み込む
  await loadPatterns();
}

// 実行
main().catch(console.error);

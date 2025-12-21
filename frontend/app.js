import * as THREE from 'three';

// 定数
const FPS = 30;
const FRAME_DURATION = 1000 / FPS; // ミリ秒
const API_BASE = 'http://localhost:8000';

// グローバル変数
let currentGeneration = -1;
let genomeIds = [];
let selectedIndices = new Set(); // 選択されたグリッドのインデックス

// RGB値(0-255)をThree.jsの16進数カラーコード(0x000000-0xFFFFFF)に変換
function rgbToHex(r, g, b) {
    return (r << 16) | (g << 8) | b;
}

// API呼び出し関数
async function initializeEvolution() {
    const response = await fetch(`${API_BASE}/api/evolution/initialize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ num_drones: 5 })
    });
    return await response.json();
}

async function getGenomes() {
    const response = await fetch(`${API_BASE}/api/evolution/genomes`);
    return await response.json();
}

async function getPattern(genomeId, duration = 3.0) {
    const response = await fetch(
        `${API_BASE}/api/evolution/pattern/${genomeId}?duration=${duration}`
    );
    return await response.json();
}

async function assignFitness(genomeId, fitness) {
    const response = await fetch(`${API_BASE}/api/evolution/fitness`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ genome_id: genomeId, fitness: fitness })
    });
    if (!response.ok) {
        throw new Error(`適応度割り当て失敗: ${genomeId}`);
    }
    return await response.json();
}

async function evolveGeneration() {
    const response = await fetch(`${API_BASE}/api/evolution/evolve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ default_fitness: 0.0 })
    });
    if (!response.ok) {
        throw new Error('進化失敗');
    }
    return await response.json();
}

// 各グリッドセルにThree.jsシーンを作成（ドローンショー表示）
async function createScene(container, showData) {
    // シーン
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    // カメラ（俯瞰視点）
    const camera = new THREE.PerspectiveCamera(
        75,
        1, // aspect ratio (正方形)
        0.1,
        1000
    );
    camera.position.set(4, 4, 4);
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
                Math.floor(b * 0.7)
            )
        });
        const drone = new THREE.Mesh(droneGeometry, material);

        // 初期位置を設定
        drone.position.set(initialDrone.x, initialDrone.y, initialDrone.z);

        scene.add(drone);
        droneMeshes.push(drone);
    }

    // アニメーションループ
    let startTime = Date.now();

    function animate() {
        requestAnimationFrame(animate);

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
            droneMeshes[i].position.set(drone.x, drone.y, drone.z);

            // 色を更新（RGB値が存在する場合）
            if (drone.r !== undefined && drone.g !== undefined && drone.b !== undefined) {
                droneMeshes[i].material.color.setHex(rgbToHex(drone.r, drone.g, drone.b));
                droneMeshes[i].material.emissive.setHex(rgbToHex(
                    Math.floor(drone.r * 0.7),
                    Math.floor(drone.g * 0.7),
                    Math.floor(drone.b * 0.7)
                ));
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
}

// パターンを読み込む
async function loadPatterns() {
    showLoading(true);
    try {
        // 初期化（まだ初期化されていない場合）
        if (currentGeneration === -1) {
            await initializeEvolution();
        }

        // ゲノムリストを取得
        const data = await getGenomes();
        currentGeneration = data.generation;
        genomeIds = data.genome_ids.slice(0, 9); // 最初の9つ

        // 世代情報を更新
        document.getElementById('generation-info').textContent =
            `世代: ${currentGeneration}`;

        // 各グリッドにパターンを読み込み
        const gridItems = document.querySelectorAll('.grid-item');
        const promises = genomeIds.map(async (genomeId, index) => {
            const pattern = await getPattern(genomeId);
            clearGrid(gridItems[index]);
            await createScene(gridItems[index], pattern);
        });

        await Promise.all(promises);

    } catch (error) {
        alert('エラー: ' + error.message);
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// ヘルパー関数
function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'block' : 'none';
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
    const gridItem = event.target.closest('.grid-item');
    if (!gridItem) return;

    // 全グリッドアイテムからインデックスを取得
    const gridItems = document.querySelectorAll('.grid-item');
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

    const gridContainer = document.querySelector('.grid-container');
    gridContainer.addEventListener('click', handleGridClick);
    isGridSelectionInitialized = true;
}

function toggleSelection(index) {
    const gridItem = document.querySelectorAll('.grid-item')[index];

    if (selectedIndices.has(index)) {
        // 選択解除
        selectedIndices.delete(index);
        gridItem.classList.remove('selected');
    } else {
        // 選択
        selectedIndices.add(index);
        gridItem.classList.add('selected');
    }

    // 進化ボタンの有効/無効を更新
    updateEvolveButton();
}

function updateEvolveButton() {
    const evolveBtn = document.getElementById('evolve-btn');
    evolveBtn.disabled = selectedIndices.size === 0;
}

// 進化処理
async function evolve() {
    showLoading(true);
    try {
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
        document.querySelectorAll('.grid-item').forEach(item => {
            item.classList.remove('selected');
        });

        // 新しい世代をロード
        await loadPatterns();
    } catch (error) {
        alert('進化エラー: ' + error.message);
        console.error(error);
    } finally {
        showLoading(false);
    }
}

// メイン処理
async function main() {
    const gridContainer = document.querySelector('.grid-container');

    // 9つの空グリッドを作成
    for (let i = 0; i < 9; i++) {
        const gridItem = document.createElement('div');
        gridItem.className = 'grid-item';
        gridContainer.appendChild(gridItem);
    }

    // グリッド選択機能を初期化（一度だけ）
    setupGridSelection();

    // ボタンイベント
    document.getElementById('evolve-btn').addEventListener('click', evolve);

    // 自動的に世代0を読み込む
    await loadPatterns();
}

// 実行
main().catch(console.error);

import * as THREE from 'three';

// 定数
const FPS = 30;
const FRAME_DURATION = 1000 / FPS; // ミリ秒

// RGB値(0-255)をThree.jsの16進数カラーコード(0x000000-0xFFFFFF)に変換
function rgbToHex(r, g, b) {
    return (r << 16) | (g << 8) | b;
}

// JSONデータを読み込む
async function loadShowData() {
    const response = await fetch('mock_data/mock4.json');
    const data = await response.json();
    return data;
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

// メイン処理
async function main() {
    // データを読み込む
    const showData = await loadShowData();

    // 9つのグリッドセルを作成
    const gridContainer = document.querySelector('.grid-container');
    for (let i = 0; i < 9; i++) {
        const gridItem = document.createElement('div');
        gridItem.className = 'grid-item';
        gridContainer.appendChild(gridItem);

        // 各セルにシーンを作成（全て同じデータを表示）
        createScene(gridItem, showData);
    }
}

// 実行
main().catch(console.error);

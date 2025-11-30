import * as THREE from 'three';

// 定数
const FPS = 30;
const FRAME_DURATION = 1000 / FPS; // ミリ秒

// JSONデータを読み込む
async function loadShowData() {
    const response = await fetch('mock.json');
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
        const material = new THREE.MeshPhongMaterial({
            color: Math.random() * 0xffffff,
            emissive: Math.random() * 0x333333
        });
        const drone = new THREE.Mesh(droneGeometry, material);

        // 初期位置を設定
        const initialPos = showData.frames[0].drones[i];
        drone.position.set(initialPos.x, initialPos.y, initialPos.z);

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

        // ドローンの位置を更新
        const currentFrame = showData.frames[currentFrameIndex];
        for (let i = 0; i < droneMeshes.length; i++) {
            const pos = currentFrame.drones[i];
            droneMeshes[i].position.set(pos.x, pos.y, pos.z);
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

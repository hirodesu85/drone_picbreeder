import * as THREE from 'three';

// 各グリッドセルにThree.jsシーンを作成
function createScene(container) {
    // シーン
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);

    // カメラ
    const camera = new THREE.PerspectiveCamera(
        75,
        1, // aspect ratio (正方形)
        0.1,
        1000
    );
    camera.position.z = 3;

    // レンダラー
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);

    // ランダムカラーの立方体
    const geometry = new THREE.BoxGeometry(1, 1, 1);
    const material = new THREE.MeshPhongMaterial({
        color: Math.random() * 0xffffff
    });
    const cube = new THREE.Mesh(geometry, material);
    scene.add(cube);

    // ライト
    const ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
    scene.add(ambientLight);

    const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
    directionalLight.position.set(1, 1, 1);
    scene.add(directionalLight);

    // ランダムな回転速度
    const rotationSpeed = {
        x: 0.005 + Math.random() * 0.01,
        y: 0.005 + Math.random() * 0.01
    };

    // アニメーション
    function animate() {
        requestAnimationFrame(animate);
        cube.rotation.x += rotationSpeed.x;
        cube.rotation.y += rotationSpeed.y;
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

// 9つのグリッドセルを作成
const gridContainer = document.querySelector('.grid-container');
for (let i = 0; i < 9; i++) {
    const gridItem = document.createElement('div');
    gridItem.className = 'grid-item';
    gridContainer.appendChild(gridItem);

    createScene(gridItem);
}

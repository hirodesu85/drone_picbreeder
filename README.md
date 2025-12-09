# Drone Picbreeder

Picbreeder（インタラクティブな進化計算を用いたアート生成ツール）のドローンショー版です。ユーザーが好みのパターンを選択することで、ドローンの3D飛行軌道を進化的に生成します。

## 主な機能

- **インタラクティブ進化**: ユーザーが好みのパターンを選択しながら、ドローンショーのパターンを進化させる
- **3D軌道生成**: 進化計算により、ドローンの飛行経路を生成
- **リアルタイム可視化**: 生成されたパターンを3Dで確認可能

## 技術スタック

### フロントエンド
- **Three.js** - 3Dビジュアライゼーション

### バックエンド
- **Python** - メイン言語
- **FastAPI** - Web APIフレームワーク
- **NEAT (NeuroEvolution of Augmenting Topologies)** - 進化計算アルゴリズム
- **CPPN (Compositional Pattern Producing Networks)** - パターン生成ネットワーク

## 進化計算システムの設計

### CPPN仕様

**入力（4次元）**:
- `x, y, z`: ドローンの相対位置（原点からの座標）
- `d`: 原点からの距離 (d = √(x² + y² + z²))

**出力（6次元）**:
- `vx, vy, vz`: ドローンの速度ベクトル
- `r, g, b`: ドローンの色（RGB）

**その他の設定**:
- ドローン台数: 5台（固定）

シミュレーション設定の詳細（初期位置、空間制約、積分方法など）は実装時に追加します。

## ドローンショーデータ形式

ドローンショーのアニメーションデータはJSON形式で定義されます。

### データ構造

```json
{
  "id": 0,
  "frames": [
    {
      "t": 0.0,
      "drones": [
        { "x": 0.0, "y": 0.0, "z": 0.0 },
        ...
      ]
    },
    ...
  ]
}
```

### フィールド説明

- **id**: パターンの個体ID（進化計算で使用）
- **frames**: 時系列順のフレーム配列
  - **t**: フレームの時刻（秒）
  - **drones**: 各ドローンの3D座標配列
    - **x, y, z**: ドローンの3D空間上の位置

### アニメーション仕様

- **フレームレート**: 30fps（固定）
- **フレーム間隔**: 1/30秒 = 0.0333秒
- **座標系**: 3D直交座標系（中心が原点）

### サンプルデータ

現在のデモでは、5機のドローンが円形軌道で回転するパターンを使用しています（`frontend/mock.json`）。

## プロジェクト構造（予定）

```
drone_picbreeder/
├── frontend/     # Three.jsベースのフロントエンド
├── backend/      # FastAPIベースのバックエンド
└── README.md
```

## 開発環境のセットアップ

### バックエンド

1. backendディレクトリに移動
   ```bash
   cd backend
   ```

2. Pythonの仮想環境を作成
   ```bash
   python3 -m venv venv
   ```

3. 仮想環境を有効化
   ```bash
   source venv/bin/activate
   ```

4. 依存関係をインストール
   ```bash
   pip install -r requirements.txt
   ```

5. サーバーを起動
   ```bash
   python -m uvicorn main:app --reload
   ```

6. ブラウザでアクセス
   - API: http://localhost:8000/api/health
   - Swagger UI: http://localhost:8000/docs

### フロントエンド

静的HTMLファイルなので、`frontend/index.html` をブラウザで直接開くか、Live Serverなどを使用してください。

## 開発状況

現在はプロジェクトの初期段階です。実装が進むにつれて、このREADMEも更新していきます。

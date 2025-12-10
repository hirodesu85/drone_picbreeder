"""
Pattern Generation Test Script

PatternGeneratorクラスの動作を確認します：
1. ランダムなゲノムからCPPNを作成
2. CPPNから完全なアニメーションを生成
3. JSONファイルとして出力
"""

import os
import json
import neat
from neat_core.cppn import CPPN
from neat_core.pattern_generator import PatternGenerator


def main():
    print("=" * 60)
    print("Pattern Generation Test - ドローンPicbreeder")
    print("=" * 60)
    print()

    # Step 1: NEAT設定の読み込み
    local_dir = os.path.dirname(__file__)
    config_path = os.path.join(local_dir, '..', 'config', 'neat_config.txt')
    config_path = os.path.abspath(config_path)

    print(f"📁 設定ファイル: {config_path}")

    if not os.path.exists(config_path):
        print(f"❌ エラー: 設定ファイルが見つかりません: {config_path}")
        return

    print("\n" + "-" * 60)
    print("Step 1: NEAT設定の読み込み")
    print("-" * 60)

    try:
        config = neat.Config(
            neat.DefaultGenome,
            neat.DefaultReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path
        )
        print("✅ NEAT設定を正常に読み込みました")
    except Exception as e:
        print(f"❌ エラー: 設定の読み込みに失敗しました: {e}")
        return

    # Step 2: ランダムなゲノムとCPPNを作成
    print("\n" + "-" * 60)
    print("Step 2: ランダムなゲノムとCPPNを作成")
    print("-" * 60)

    genome_id = 1
    genome = config.genome_type(genome_id)
    genome.configure_new(config.genome_config)

    try:
        cppn = CPPN(genome, config)
        print(f"✅ ゲノムID {genome_id} のCPPNを作成しました")
    except Exception as e:
        print(f"❌ エラー: CPPNの作成に失敗しました: {e}")
        return

    # Step 3: PatternGeneratorを作成
    print("\n" + "-" * 60)
    print("Step 3: PatternGeneratorを作成")
    print("-" * 60)

    try:
        pattern_generator = PatternGenerator(cppn, genome_id, num_drones=5)
        print("✅ PatternGeneratorを作成しました")
        print(f"   ドローン数: {pattern_generator.num_drones}")
        print(f"   フレームレート: {pattern_generator.fps} fps")
        print(f"   タイムステップ: {pattern_generator.dt:.4f} 秒")
    except Exception as e:
        print(f"❌ エラー: PatternGeneratorの作成に失敗しました: {e}")
        return

    # Step 4: アニメーションを生成
    print("\n" + "-" * 60)
    print("Step 4: アニメーションを生成")
    print("-" * 60)

    duration = 3.0  # 3秒間
    print(f"   生成時間: {duration} 秒")

    try:
        animation = pattern_generator.generate_animation(duration=duration)
        print(f"✅ アニメーションを生成しました")
        print(f"   総フレーム数: {len(animation.frames)}")
        print(f"   ドローン数: {len(animation.frames[0].drones)}")
        print(f"   時間範囲: {animation.frames[0].t:.4f} ~ {animation.frames[-1].t:.4f} 秒")
    except Exception as e:
        print(f"❌ エラー: アニメーションの生成に失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 5: JSONファイルとして出力
    print("\n" + "-" * 60)
    print("Step 5: JSONファイルとして出力")
    print("-" * 60)

    output_dir = os.path.join(local_dir, '..', 'output')
    output_path = os.path.join(output_dir, 'test_pattern.json')
    output_path = os.path.abspath(output_path)

    # 出力ディレクトリの存在確認
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Pydantic modelをdict変換してJSONに出力
        # exclude_noneを使用してNone値を除外
        animation_dict = animation.model_dump(exclude_none=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(animation_dict, f, indent=2, ensure_ascii=False)

        print(f"✅ JSONファイルを出力しました")
        print(f"   出力パス: {output_path}")

        # ファイルサイズを確認
        file_size = os.path.getsize(output_path)
        print(f"   ファイルサイズ: {file_size:,} バイト ({file_size / 1024:.1f} KB)")

    except Exception as e:
        print(f"❌ エラー: JSONファイルの出力に失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 6: サンプルデータを表示
    print("\n" + "-" * 60)
    print("Step 6: サンプルデータを表示")
    print("-" * 60)

    # 最初のフレーム（t=0）を表示
    first_frame = animation.frames[0]
    print(f"\n   最初のフレーム (t={first_frame.t:.4f} 秒):")
    for i, drone in enumerate(first_frame.drones):
        print(f"     ドローン{i}: pos=({drone.x:+.3f}, {drone.y:+.3f}, {drone.z:+.3f}), "
              f"color=({drone.r}, {drone.g}, {drone.b})")

    # 最後のフレームを表示
    last_frame = animation.frames[-1]
    print(f"\n   最後のフレーム (t={last_frame.t:.4f} 秒):")
    for i, drone in enumerate(last_frame.drones):
        print(f"     ドローン{i}: pos=({drone.x:+.3f}, {drone.y:+.3f}, {drone.z:+.3f}), "
              f"color=({drone.r}, {drone.g}, {drone.b})")

    # まとめ
    print("\n" + "=" * 60)
    print("テスト完了！")
    print("=" * 60)
    print("\n次のステップ:")
    print("1. JSONファイルをフロントエンドで可視化できます：")
    print(f"   cp {output_path} ../frontend/mock.json")
    print("2. ブラウザでfrontend/index.htmlを開いてアニメーションを確認")
    print()


if __name__ == "__main__":
    main()

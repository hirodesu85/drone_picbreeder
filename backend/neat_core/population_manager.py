"""
Population Manager

NEAT集団の管理と進化を担当します。
集団の初期化、適応度の割り当て、世代の進化を実装します。
"""

import neat
from typing import List, Dict, Optional, Any
from neat_core.cppn import CPPN
from neat_core.pattern_generator import PatternGenerator
from neat_core.custom_reproduction import CustomReproduction
from models.animation import Animation


class PopulationManager:
    """
    NEAT集団を管理し、進化プロセスを制御するクラス

    インタラクティブ進化（Picbreeder）のために、
    外部からの適応度割り当てをサポートします。
    """

    def __init__(self, config_path: str, num_drones: int = 5):
        """
        PopulationManagerを初期化

        Args:
            config_path: NEAT設定ファイルのパス
            num_drones: ドローンの数（デフォルト: 5）
        """
        # NEAT設定を読み込む
        self.config = neat.Config(
            neat.DefaultGenome,
            CustomReproduction,
            neat.DefaultSpeciesSet,
            neat.DefaultStagnation,
            config_path
        )

        self.num_drones = num_drones

        # 集団を作成
        self.population = neat.Population(self.config)

        # 世代カウンター
        self.generation = 0

        # ゲノムIDからゲノムへのマッピング（現在の世代）
        self.current_genomes: Dict[int, neat.DefaultGenome] = {}

        # 進化履歴（世代ごとのゲノム情報）
        self.history: List[Dict[str, Any]] = []

        # 初期集団を取得
        self._update_current_genomes()

    def _update_current_genomes(self):
        """
        現在の世代のゲノムを更新

        population.populationは{genome_id: genome}の辞書
        """
        self.current_genomes = dict(self.population.population)
        self._record_generation_history()

    def _record_generation_history(self):
        """
        現在の世代のゲノム情報を履歴に記録
        """
        # population.reproduction.ancestors から親情報を取得
        ancestors = self.population.reproduction.ancestors

        generation_data = {
            "generation": self.generation,
            "genomes": []
        }

        for genome_id, genome in self.current_genomes.items():
            parent_info = ancestors.get(genome_id, ())

            genome_data = {
                "genome_id": genome_id,
                "parent1": parent_info[0] if len(parent_info) > 0 else None,
                "parent2": parent_info[1] if len(parent_info) > 1 else None,
                "fitness": genome.fitness
            }
            generation_data["genomes"].append(genome_data)

        # 既存の同じ世代のデータがあれば更新、なければ追加
        existing_idx = next(
            (i for i, h in enumerate(self.history) if h["generation"] == self.generation),
            None
        )
        if existing_idx is not None:
            self.history[existing_idx] = generation_data
        else:
            self.history.append(generation_data)

    def get_genome_ids(self) -> List[int]:
        """
        現在の世代の全ゲノムIDを取得

        Returns:
            List[int]: ゲノムIDのリスト
        """
        return list(self.current_genomes.keys())

    def get_genome(self, genome_id: int) -> Optional[neat.DefaultGenome]:
        """
        特定のゲノムを取得

        Args:
            genome_id: ゲノムID

        Returns:
            neat.DefaultGenome or None: ゲノム（存在しない場合はNone）
        """
        return self.current_genomes.get(genome_id)

    def generate_pattern(self, genome_id: int, duration: float = 3.0) -> Optional[Animation]:
        """
        特定のゲノムからアニメーションパターンを生成

        Args:
            genome_id: ゲノムID
            duration: アニメーションの長さ（秒）

        Returns:
            Animation or None: 生成されたアニメーション（ゲノムが存在しない場合はNone）
        """
        genome = self.get_genome(genome_id)
        if genome is None:
            return None

        # CPPNを作成
        cppn = CPPN(genome, self.config)

        # PatternGeneratorを作成してアニメーションを生成
        pattern_generator = PatternGenerator(cppn, genome_id, self.num_drones)
        animation = pattern_generator.generate_animation(duration)

        return animation

    def assign_fitness(self, genome_id: int, fitness: float) -> bool:
        """
        特定のゲノムに適応度を割り当て

        Args:
            genome_id: ゲノムID
            fitness: 適応度（0.0〜1.0を推奨）

        Returns:
            bool: 成功した場合True、ゲノムが存在しない場合False
        """
        genome = self.get_genome(genome_id)
        if genome is None:
            return False

        genome.fitness = fitness
        return True

    def assign_fitness_batch(self, fitness_map: Dict[int, float]):
        """
        複数のゲノムに一括で適応度を割り当て

        Args:
            fitness_map: {genome_id: fitness}の辞書
        """
        for genome_id, fitness in fitness_map.items():
            self.assign_fitness(genome_id, fitness)

    def get_fitness_status(self) -> Dict[str, any]:
        """
        適応度の割り当て状況を取得

        Returns:
            dict: 統計情報
                - total: 総ゲノム数
                - assigned: 適応度が割り当てられたゲノム数
                - unassigned: 適応度が割り当てられていないゲノム数
        """
        total = len(self.current_genomes)
        assigned = sum(1 for g in self.current_genomes.values() if g.fitness is not None)
        unassigned = total - assigned

        return {
            "total": total,
            "assigned": assigned,
            "unassigned": unassigned
        }

    def evolve(self, default_fitness: float = 0.0) -> bool:
        """
        次世代に進化

        適応度が割り当てられていないゲノムにはdefault_fitnessを使用します。
        ユーザーが選択した個体（fitness > 0）のみが親候補になるよう、
        survival_thresholdを動的に計算します。

        Args:
            default_fitness: デフォルト適応度（未割り当てゲノム用）

        Returns:
            bool: 進化に成功した場合True
        """
        # 選択された個体数をカウント（fitness > 0 の個体）
        selected_count = sum(
            1 for g in self.current_genomes.values()
            if g.fitness is not None and g.fitness > 0
        )

        # 動的にsurvival_thresholdとelitismを計算
        # 選択個体のみが親候補になり、全てそのまま次世代に残るよう設定
        if selected_count > 0:
            total = len(self.current_genomes)
            # NEAT-Pythonはceil()で切り上げるので、正確な比率を設定
            threshold = min(1.0, selected_count / total)
            self.config.reproduction_config.survival_threshold = threshold
            # 選択した個体全てをエリートとして残す
            self.config.reproduction_config.elitism = selected_count

        # 未割り当てのゲノムにデフォルト適応度を設定
        for genome in self.current_genomes.values():
            if genome.fitness is None:
                genome.fitness = default_fitness

        # NEAT進化を1世代実行
        # population.runは通常fitness_functionを受け取るが、
        # 既に適応度を割り当てているのでダミー関数を使用
        def dummy_fitness(genomes, config):
            # 何もしない（適応度は既に割り当て済み）
            pass

        # 1世代だけ進化
        self.population.run(dummy_fitness, 1)

        # 世代カウンターを更新
        self.generation += 1

        # 新しい世代のゲノムを取得
        self._update_current_genomes()

        return True

    def get_generation(self) -> int:
        """
        現在の世代番号を取得

        Returns:
            int: 世代番号（0から開始）
        """
        return self.generation

    def get_population_size(self) -> int:
        """
        集団サイズを取得

        Returns:
            int: 集団サイズ
        """
        return len(self.current_genomes)

    def get_best_genome(self) -> Optional[neat.DefaultGenome]:
        """
        現在の世代で最も適応度の高いゲノムを取得

        Returns:
            neat.DefaultGenome or None: 最良ゲノム（適応度が割り当てられていない場合はNone）
        """
        genomes_with_fitness = [
            g for g in self.current_genomes.values()
            if g.fitness is not None
        ]

        if not genomes_with_fitness:
            return None

        return max(genomes_with_fitness, key=lambda g: g.fitness)

    def get_evolution_history(self) -> List[Dict[str, Any]]:
        """
        全世代の進化履歴を取得

        Returns:
            List[Dict]: 世代ごとのゲノム情報リスト
        """
        # 現在の世代の適応度情報を履歴に反映
        self._update_current_generation_fitness()
        return self.history

    def _update_current_generation_fitness(self):
        """
        現在の世代のゲノムの適応度情報を履歴に反映
        """
        if not self.history:
            return

        current_gen_data = next(
            (h for h in self.history if h["generation"] == self.generation),
            None
        )

        if current_gen_data:
            for genome_data in current_gen_data["genomes"]:
                genome = self.current_genomes.get(genome_data["genome_id"])
                if genome:
                    genome_data["fitness"] = genome.fitness

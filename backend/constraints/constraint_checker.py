"""
Drone Constraint Checker
"""

import math
from dataclasses import dataclass
from typing import List
from models.animation import Animation


@dataclass
class ConstraintParams:
    """制約パラメータ"""
    x_min: float = -8.5
    x_max: float = 8.5
    y_min: float = -8.5
    y_max: float = 8.5
    z_min: float = -6.5
    z_max: float = 6.5
    max_horizontal_speed: float = 5.0  # m/s
    max_vertical_speed: float = 2.5    # m/s
    min_distance: float = 0.5          # m
    dt: float = 0.04                   # 25fps


@dataclass
class GenomeConstraintResult:
    """個体の制約チェック結果"""
    genome_id: int
    bounds_violations: int = 0
    max_bounds_violation: float = 0.0
    horizontal_speed_violations: int = 0
    vertical_speed_violations: int = 0
    distance_violations: int = 0
    min_distance_observed: float = float('inf')

    @property
    def passes_all(self) -> bool:
        return (self.bounds_violations == 0 and
                self.horizontal_speed_violations == 0 and
                self.vertical_speed_violations == 0 and
                self.distance_violations == 0)


class ConstraintChecker:
    def __init__(self, params: ConstraintParams):
        self.params = params

    def check_animation(self, animation: Animation) -> GenomeConstraintResult:
        result = GenomeConstraintResult(genome_id=animation.id)
        frames = animation.frames

        for frame_idx, frame in enumerate(frames):
            drones = frame.drones

            # 1. 飛行区域チェック
            for drone in drones:
                violation = self._check_bounds(drone.x, drone.y, drone.z)
                if violation > 0:
                    result.bounds_violations += 1
                    result.max_bounds_violation = max(result.max_bounds_violation, violation)

            # 2. 速度チェック
            if frame_idx > 0:
                prev_drones = frames[frame_idx - 1].drones
                for curr, prev in zip(drones, prev_drones):
                    h_speed, v_speed = self._calculate_speeds(prev, curr)
                    if h_speed > self.params.max_horizontal_speed:
                        result.horizontal_speed_violations += 1
                    if v_speed > self.params.max_vertical_speed:
                        result.vertical_speed_violations += 1

            # 3. ドローン間距離チェック
            for i in range(len(drones)):
                for j in range(i + 1, len(drones)):
                    dist = self._calculate_distance(drones[i], drones[j])
                    result.min_distance_observed = min(result.min_distance_observed, dist)
                    if dist < self.params.min_distance:
                        result.distance_violations += 1

        return result

    def _check_bounds(self, x: float, y: float, z: float) -> float:
        violations = [
            max(0, self.params.x_min - x),
            max(0, x - self.params.x_max),
            max(0, self.params.y_min - y),
            max(0, y - self.params.y_max),
            max(0, self.params.z_min - z),
            max(0, z - self.params.z_max),
        ]
        return max(violations)

    def _calculate_speeds(self, prev_drone, curr_drone) -> tuple:
        dx = curr_drone.x - prev_drone.x
        dy = curr_drone.y - prev_drone.y
        dz = curr_drone.z - prev_drone.z
        h_speed = math.sqrt(dx * dx + dy * dy) / self.params.dt
        v_speed = abs(dz) / self.params.dt
        return h_speed, v_speed

    def _calculate_distance(self, drone1, drone2) -> float:
        dx = drone2.x - drone1.x
        dy = drone2.y - drone1.y
        dz = drone2.z - drone1.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)


def check_all_genomes(animations: List[Animation], params: ConstraintParams) -> dict:
    checker = ConstraintChecker(params)
    results = [checker.check_animation(anim) for anim in animations]

    summary = {
        "total": len(results),
        "pass_bounds": sum(1 for r in results if r.bounds_violations == 0),
        "pass_h_speed": sum(1 for r in results if r.horizontal_speed_violations == 0),
        "pass_v_speed": sum(1 for r in results if r.vertical_speed_violations == 0),
        "pass_distance": sum(1 for r in results if r.distance_violations == 0),
        "pass_all": sum(1 for r in results if r.passes_all),
    }

    return {"results": results, "summary": summary, "params": params}

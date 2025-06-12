from typing import List, Dict, Tuple  
from logic.damage import calculate_adjusted_element, calculate_expected_physical

def calculate_combo_damage(
    combo_moves: List[str],
    motion_values: Dict[str, Dict],
    attack: float,
    element: float,
    sharpness: str = "白",
    element_zone: float = 100.0,
    affinity: float = 0.0,
    crit_element_lv: int = 0
) -> Tuple[float, float]:
    total_physical = 0.0
    total_element = 0.0

    expected_attack = calculate_expected_physical(attack, affinity)

    for move in combo_moves:
        if move not in motion_values:
            continue
        data = motion_values[move]
        motion_list = data.get("motion", [])
        element_list = data.get("element", [0.3] * len(motion_list))

        for i, mv in enumerate(motion_list):
            element_motion = element_list[i] if i < len(element_list) else 0.3
            total_physical += expected_attack * mv
            total_element += calculate_adjusted_element(
                base_element=element,
                sharpness=sharpness,
                motion_value=element_motion,
                element_zone=element_zone,
                affinity=affinity,
                crit_element_lv=crit_element_lv
            )

    return total_physical, total_element

def calculate_dps(physical: float, elemental: float, time: float) -> float:
    """
    DPS計算
    """
    if time <= 0:
        return 0.0
    return (physical + elemental) / time
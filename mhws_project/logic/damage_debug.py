# logic/damage_debug.py

import streamlit as st
from typing import Dict, List, Tuple

def apply_physical_sharpness(attack: float, sharpness: str) -> float:
    SHARPNESS_MODIFIERS = {
        "赤": 0.5, "橙": 0.75, "黄": 1.0,
        "緑": 1.05, "青": 1.2, "白": 1.32, "紫": 1.39
    }
    return attack * SHARPNESS_MODIFIERS.get(sharpness, 1.0)

def apply_elemental_sharpness(element: float, sharpness: str) -> float:
    SHARPNESS_MODIFIERS = {
        "赤": 0.25, "橙": 0.5, "黄": 0.75,
        "緑": 1.0, "青": 1.0625, "白": 1.15, "紫": 1.25
    }
    return element * SHARPNESS_MODIFIERS.get(sharpness, 1.0)

def calculate_expected_physical(attack: float, affinity: float, crit_mult: float = 1.25) -> float:
    affinity = max(min(affinity, 100), -100)
    if affinity >= 0:
        return attack * (1 + (affinity / 100.0) * (crit_mult - 1))
    else:
        return attack * (1 + (affinity / 100.0) * (0.75 - 1))

def calculate_elemental_crit_multiplier(affinity: float, skill_lv: int) -> float:
    crit_rate = max(min(affinity, 100), 0) / 100
    bonus_table = {0: 1.0, 1: 1.05, 2: 1.1, 3: 1.15}
    bonus = bonus_table.get(skill_lv, 1.0)
    return 1 + crit_rate * (bonus - 1)

def calculate_adjusted_element(
    base_element: float,
    sharpness: str,
    motion_value: float,
    element_zone: float,
    affinity: float,
    crit_element_lv: int
) -> float:
    element = base_element
    element = apply_elemental_sharpness(element, sharpness)
    element *= motion_value
    element *= (element_zone / 100.0)
    element *= calculate_elemental_crit_multiplier(affinity, crit_element_lv)
    return element

def apply_hitzone_modifier(attack: float, hitzone: float) -> float:
    return attack * (hitzone / 100.0)

def calculate_elemental_damage(element: float, element_zone: float) -> float:
    return element * (element_zone / 100.0)

def simulate_combo_damage(
    combo: Dict,
    motion_data: Dict,
    attack: float,
    element: float,
    affinity: float,
    sharpness: str,
    crit_element_lv: int,
    part_phys_mod: float,
    part_elem_mod: float
) -> Tuple[float, float, float]:
    total_phys = 0.0
    total_elem = 0.0

    sharp_attack = apply_physical_sharpness(attack, sharpness)
    exp_phys = calculate_expected_physical(sharp_attack, affinity)

    st.write("🔍 **[DEBUG] コンボ詳細出力**")
    for move in combo["moves"]:
        data = motion_data.get(move, {})
        motion_vals = data.get("motion", [0.0])
        element_vals = data.get("element", [0.3])

        motion_sum = sum(motion_vals)
        element_sum = sum(element_vals)

        phys_dmg = exp_phys * motion_sum * (part_phys_mod / 100.0)
        elem_dmg = calculate_adjusted_element(
            element, sharpness, element_sum, part_elem_mod, affinity, crit_element_lv
        )

        st.write(f"🪓 モーション名: {move}")
        st.write(f"  - motion: {motion_vals}, element: {element_vals}")
        st.write(f"  - 計算結果 → 物理: {phys_dmg:.2f}, 属性: {elem_dmg:.2f}")

        total_phys += phys_dmg
        total_elem += elem_dmg

    return total_phys, total_elem, combo["time"]
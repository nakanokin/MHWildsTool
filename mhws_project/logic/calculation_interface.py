# === calculation_interface.py（剛刃研磨対応） ===

import os
import json
import math
from logic.skill import apply_skill_modifiers
from logic.damage import (
    apply_physical_sharpness,
    apply_elemental_sharpness,
    calculate_expected_physical,
    apply_hitzone_modifier,
    calculate_elemental_damage
)
from logic.combo import calculate_combo_damage, calculate_dps
from utils.result_logger import log_result_to_csv, log_result_to_csv_readable

# def estimate_effective_sharpness_hits(base_hits, affinity, skills, skills_json):
#     if "匠" in skills:
#         lv, rate = skills["匠"]
#         skill_def = skills_json.get("匠", {}).get(f"Lv{lv}", {})
#         bonus = skill_def.get("sharpness_add", 0)
#         base_hits += int(bonus * rate)

#     if "業物" in skills:
#         lv, rate = skills["業物"]
#         skill_def = skills_json.get("業物", {}).get(f"Lv{lv}", {})
#         prob = skill_def.get("sharpness_reduction_prob", 0.0)
#         base_hits *= (1 + prob * rate)

#     if "達人芸" in skills:
#         _, rate = skills["達人芸"]
#         skill_def = skills_json.get("達人芸", {}).get("Lv1", {})
#         prob = skill_def.get("crit_sharpness_reduction_prob", 0.0)
#         crit = max(min(affinity, 100), 0) / 100
#         base_hits *= (1 + prob * crit * rate)

#     return int(base_hits)
def estimate_effective_sharpness_hits(base_hits, affinity, skills, skills_json):
    sharpness_consumption = 1.0  # 初期化を忘れずに

    # 匠：切れ味ゲージ自体が伸びる
    if "匠" in skills:
        lv, rate = skills["匠"]
        skill_def = skills_json.get("匠", {}).get(f"Lv{lv}", {})
        bonus = skill_def.get("sharpness_add", 0)
        base_hits += int(bonus * rate)

    # 業物：常時確率で消費無効
    if "業物" in skills:
        lv, rate = skills["業物"]
        skill_def = skills_json.get("業物", {}).get(f"Lv{lv}", {})
        prob = skill_def.get("sharpness_reduction_prob", 0.0)
        sharpness_consumption *= (1 - prob * rate)

    # 達人芸：会心時のみ確率で消費無効
    if "達人芸" in skills:
        _, rate = skills["達人芸"]
        skill_def = skills_json.get("達人芸", {}).get("Lv1", {})
        prob = skill_def.get("crit_sharpness_reduction_prob", 0.0)
        crit = max(min(affinity, 100), 0) / 100
        sharpness_consumption *= (1 - prob * crit * rate)

    if sharpness_consumption <= 0:
        sharpness_consumption = 0.01  # 安全策：ゼロ除算回避

    return int(base_hits / sharpness_consumption)

def run_full_dps_calculation(weapon_name, monster_name, part_name, combo_name, skill_input):
    BASE_DIR = os.path.dirname(__file__)
    DATA_DIR = os.path.join(BASE_DIR, "..", "data")

    def load_json(name):
        with open(os.path.join(DATA_DIR, name), "r", encoding="utf-8") as f:
            return json.load(f)

    skills_json = load_json("skills.json")
    weapons = load_json("weapons.json")
    monsters = load_json("monsters.json")
    motions = load_json("motion_values.json")
    combos = load_json("combos.json")

    weapon = weapons[weapon_name]
    monster = monsters[monster_name]

    DISPLAY_ATTACK = weapon["attack"]
    WEAPON_COEFFICIENT = 1.4
    base_attack = DISPLAY_ATTACK * WEAPON_COEFFICIENT

    attack, affinity, element = apply_skill_modifiers(
        base_attack=base_attack,
        base_affinity=weapon["affinity"],
        base_element=weapon["element"]["value"],
        skills=skill_input,
        skill_defs=skills_json
    )

    sharpness = weapon.get("sharpness", "白")
    attack = apply_physical_sharpness(attack, sharpness)
    element = apply_elemental_sharpness(element, sharpness)

    from logic.skill import get_crit_multiplier_from_skill

    crit_lv = skill_input.get("超会心", (0, 0.0))[0]
    crit_mult = get_crit_multiplier_from_skill("超会心", crit_lv)

    expected_attack = calculate_expected_physical(attack, affinity, crit_mult)

    hitzone = monster["parts"][part_name]["physical"]
    element_zone = monster["parts"][part_name]["element"].get(weapon["element"]["type"], 0)

    effective_attack = apply_hitzone_modifier(expected_attack, hitzone)
    effective_element = calculate_elemental_damage(element, element_zone)

    combo = combos[combo_name]
    combo_moves = combo["moves"]
    combo_time = combo["time"]

    total_physical, total_element = calculate_combo_damage(
        combo_moves, motions, effective_attack, effective_element,
        sharpness=sharpness,
        element_zone=element_zone,
        affinity=affinity,
        crit_element_lv=skill_input.get("会心撃【属性】", (0, 0.0))[0]
    )
    from logic.skill import get_crit_element_bonus
    # トータル属性補正として「会心撃【属性】」を適用
    crit_element_lv = skill_input.get("会心撃【属性】", (0, 0.0))[0]
    total_element *= get_crit_element_bonus("会心撃【属性】", crit_element_lv)

    phys_dps = total_physical / combo_time
    elem_dps = total_element / combo_time
    total_dps = phys_dps + elem_dps

    base_hits = weapon.get("sharpness_hits", 999)
    hits_per_combo = sum(len(motions.get(move, {}).get("motion", [1.0])) for move in combo_moves)
    effective_hits = estimate_effective_sharpness_hits(base_hits, affinity, skill_input, skills_json)
    # 平均ヒットあたりダメージと切れ味尽きるまでの総ダメージ
    if hits_per_combo:
        avg_hit_damage = (total_physical + total_element) / hits_per_combo
    else:
        avg_hit_damage = 0

    total_damage_until_sharpness_break = avg_hit_damage * effective_hits
    combo_count = math.floor(effective_hits / hits_per_combo) if hits_per_combo else 0
    total_duration = combo_count * combo_time

    # 剛刃研磨の無消費時間を追加
    if "剛刃研磨" in skill_input:
        lv, rate = skill_input["剛刃研磨"]
        def_ = skills_json.get("剛刃研磨", {}).get(f"Lv{lv}", {})
        goken_duration = def_.get("no_sharpness_time", 0) * rate
        total_duration += goken_duration

    result = {
        "武器": weapon_name,
        "モンスター": monster_name,
        "部位": part_name,
        "切れ味": sharpness,
        "スキル": skill_input,
        "コンボ": combo_name,
        "攻撃力": attack,
        "会心率": affinity,
        "属性値": element,
        "期待値攻撃力": expected_attack,
        "物理有効値": effective_attack,
        "属性有効値": effective_element,
        "物理合計": total_physical,
        "属性合計": total_element,
        "コンボ時間": combo_time,
        "物理DPS": phys_dps,
        "属性DPS": elem_dps,
        "DPS": total_dps,
        "切れ味Hit": base_hits,
        "実効Hit": effective_hits,
        "コンボ回数": combo_count,
        "維持秒数": total_duration,
        "平均Hitダメージ": avg_hit_damage,
        "合計ダメージ": total_damage_until_sharpness_break
    }

    # os.makedirs("results", exist_ok=True)
    RESULTS_DIR = os.path.join(BASE_DIR, "..", "results")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    log_result_to_csv(
        filepath=os.path.join(RESULTS_DIR, "dps_log.csv"),
        weapon=weapon_name,
        monster=monster_name,
        part=part_name,
        sharpness=sharpness,
        skills=skill_input,
        combo_name=combo_name,
        attack=attack,
        affinity=affinity,
        element=element,
        expected_attack=expected_attack,
        effective_attack=effective_attack,
        effective_element=effective_element,
        total_physical=total_physical,
        total_element=total_element,
        combo_time=combo_time,
        dps=total_dps,
        base_hits=base_hits,
        effective_hits=effective_hits,
        combo_count=combo_count,
        duration=total_duration
    )

    log_result_to_csv_readable(
        filepath=os.path.join(RESULTS_DIR, "dps_log_readable.csv"),
        weapon=weapon_name,
        monster=monster_name,
        part=part_name,
        sharpness=sharpness,
        skills=skill_input,
        combo_name=combo_name,
        attack=attack,
        affinity=affinity,
        element=element,
        expected_attack=expected_attack,
        effective_attack=effective_attack,
        effective_element=effective_element,
        total_physical=total_physical,
        total_element=total_element,
        combo_time=combo_time,
        dps=total_dps,
        base_hits=base_hits,
        effective_hits=effective_hits,
        combo_count=combo_count,
        duration=total_duration
    )

    return result

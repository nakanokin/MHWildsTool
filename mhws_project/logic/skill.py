
import json
import os
from typing import Dict, Tuple

# # skills.json を読み込む
# def load_skills(path="data/skills.json"):
#     with open(path, "r", encoding="utf-8") as f:
#         return json.load(f)

# skill.pyのある場所を基準に絶対パスを構築
# BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# DATA_PATH = os.path.join(BASE_DIR, "../../data/skills.json")
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))  # mhws_project/
DATA_PATH = os.path.join(BASE_DIR, "data", "skills.json")

def load_skills(path=DATA_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

SKILL_DATA = load_skills()

def apply_skill_modifiers(
    base_attack: float,
    base_affinity: float,
    base_element: float,
    skills: Dict[str, Tuple[int, float]],
    skill_defs: Dict = SKILL_DATA
) -> Tuple[float, float, float]:
    '''
    skills: {スキル名: (Lv, 発動率)}
    skill_defs: skills.jsonの辞書（省略時はデフォルトロード）
    出力: 補正後の attack, affinity, element
    '''
    atk_add = 0.0
    atk_mult = 1.0
    affinity = base_affinity
    elem_add = 0.0
    elem_mult = 1.0

    for name, (lv, rate) in skills.items():
        effect = skill_defs.get(name, {}).get(f"Lv{lv}", {})
        if not effect:
            continue

        atk_add += effect.get("add", 0) * rate
        atk_mult *= effect.get("mult", 1.0) ** rate
        affinity += effect.get("affinity", 0) * rate
        elem_add += effect.get("element_add", 0) * rate
        elem_mult *= effect.get("element_mult", 1.0) ** rate

    final_attack = base_attack * atk_mult + atk_add
    final_element = base_element * elem_mult + elem_add

    return final_attack, affinity, final_element

def get_crit_multiplier_from_skill(skill_name: str, level: int, skill_defs: Dict = SKILL_DATA) -> float:
    """クリティカル時の物理補正倍率（超会心など）"""
    data = skill_defs.get(skill_name, {}).get(f"Lv{level}", {})
    return data.get("crit_mult", 1.25)  # デフォルト1.25倍

def get_crit_element_bonus(skill_name: str, level: int, skill_defs: Dict = SKILL_DATA) -> float:
    """クリティカル時の属性補正倍率（会心撃【属性】）"""
    data = skill_defs.get(skill_name, {}).get(f"Lv{level}", {})
    return data.get("crit_element_bonus", 1.0)  # デフォルト補正なし
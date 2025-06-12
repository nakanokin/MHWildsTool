import csv
import os
from typing import Dict, Tuple

def rotate_csv(filepath: str, max_rows: int = 10):
    """
    CSVファイルを最大 max_rows 件にローテーションする（ヘッダー行は除く）。
    古い行を削除して最新 max_rows 件を残す。
    """
    if not os.path.exists(filepath):
        return
    with open(filepath, mode="r", newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)
    if len(rows) <= max_rows + 1:
        return
    header = rows[0]
    data = rows[1:]
    new_data = data[-max_rows:]
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(new_data)

def log_result_to_csv(
    filepath: str,
    weapon: str,
    monster: str,
    part: str,
    sharpness: str,
    skills: Dict[str, Tuple[int, float]],
    combo_name: str,
    attack: float,
    affinity: float,
    element: float,
    expected_attack: float,
    effective_attack: float,
    effective_element: float,
    total_physical: float,
    total_element: float,
    combo_time: float,
    dps: float,
    base_hits: int,
    effective_hits: int,
    combo_count: int,
    duration: float
):
    """
    構造化CSV出力（数値だけ、データ処理用）＋最新10件にローテーション
    """
    file_exists = os.path.exists(filepath)
    skill_str = "|".join([f"{name}Lv{lv}({int(rate*100)}%)" for name, (lv, rate) in skills.items()])

    with open(filepath, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow([
                "武器", "モンスター", "部位", "切れ味", "スキル構成", "コンボ名",
                "補正攻撃力", "会心率", "補正属性", "期待値攻撃", "物理肉質後", "属性肉質後",
                "物理合計", "属性合計", "コンボ時間", "DPS",
                "元切れ味Hit", "実効Hit", "コンボ回数", "切れ味持続秒"
            ])
        writer.writerow([
            weapon, monster, part, sharpness, skill_str, combo_name,
            f"{attack:.1f}", f"{affinity:.1f}", f"{element:.1f}", f"{expected_attack:.1f}",
            f"{effective_attack:.1f}", f"{effective_element:.1f}",
            f"{total_physical:.1f}", f"{total_element:.1f}", f"{combo_time:.2f}", f"{dps:.2f}",
            base_hits, effective_hits, combo_count, f"{duration:.1f}"
        ])

    # ローテーション
    rotate_csv(filepath, max_rows=10)

def log_result_to_csv_readable(
    filepath: str,
    weapon: str,
    monster: str,
    part: str,
    sharpness: str,
    skills: Dict[str, Tuple[int, float]],
    combo_name: str,
    attack: float,
    affinity: float,
    element: float,
    expected_attack: float,
    effective_attack: float,
    effective_element: float,
    total_physical: float,
    total_element: float,
    combo_time: float,
    dps: float,
    base_hits: int,
    effective_hits: int,
    combo_count: int,
    duration: float
):
    """
    人間読みやすいCSV出力（ラベル付き）＋最新10件にローテーション
    """
    file_exists = os.path.exists(filepath)
    skill_str = "|".join([f"{name}Lv{lv}({int(rate*100)}%)" for name, (lv, rate) in skills.items()])

    row = [
        f"武器: {weapon}", f"モンスター: {monster}", f"部位: {part}",
        f"切れ味: {sharpness}", f"スキル構成: {skill_str}", f"コンボ名: {combo_name}",
        f"攻撃力: {attack:.1f}", f"会心率: {affinity:.1f}%", f"属性値: {element:.1f}",
        f"期待値攻撃力: {expected_attack:.1f}", f"物理肉質後: {effective_attack:.1f}", f"属性肉質後: {effective_element:.1f}",
        f"物理合計: {total_physical:.1f}", f"属性合計: {total_element:.1f}", f"コンボ時間: {combo_time:.2f}",
        f"DPS: {dps:.2f}", f"切れ味ヒット数: {base_hits}", f"実効Hit: {effective_hits}",
        f"コンボ回数: {combo_count}", f"切れ味持続: {duration:.1f}秒"
    ]

    with open(filepath, mode="a", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(["結果概要"])
        writer.writerow(row)

    # ローテーション
    rotate_csv(filepath, max_rows=10)
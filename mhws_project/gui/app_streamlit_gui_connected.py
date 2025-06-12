import sys
import os
import streamlit as st
import json
import pandas as pd
import altair as alt

# === set_page_config は最初に呼ぶ必要あり ===
st.set_page_config(page_title="モンハン片手剣DPS計算ツール", layout="wide")

# # --- 初期化 ---
# st.title("モンハン片手剣DPSツール")

# logic/utils参照用パス設定
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logic.calculation_interface import run_full_dps_calculation
from gui import bookmarks  # bookmarks.py をインポート

# ── データ読み込み ──
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

def load_json(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

weapons = load_json("weapons.json")
monsters = load_json("monsters.json")
combos = load_json("combos.json")
skills_json = load_json("skills.json")
skill_names = sorted(skills_json.keys())
skills_category = load_json("skills_category.json")

# ── スキル自動分類 ──
all_skills = set(skills_json.keys())
categorized_skills = set(sum(skills_category.values(), []))
uncategorized_skills = sorted(list(all_skills - categorized_skills))

# ── タイトル ──
st.title("モンハンワイルズ DPS計算ツール（片手剣）")


# ── session_state 初期化 ──
if "weapon_name" not in st.session_state:
    st.session_state["weapon_name"] = list(weapons.keys())[0]
if "monster_name" not in st.session_state:
    st.session_state["monster_name"] = list(monsters.keys())[0]
if "part_name" not in st.session_state:
    st.session_state["part_name"] = list(monsters[st.session_state["monster_name"]]["parts"].keys())[0]
if "combo_name" not in st.session_state:
    st.session_state["combo_name"] = list(combos.keys())[0]

# ── pending_reflect があればスキルを強制表示に追加 ──
if "pending_reflect" in st.session_state:
    reflect_skills = st.session_state["pending_reflect"].get("skills", {})
    for skill_name in reflect_skills:
        if skill_name not in skills_json:
            skills_json[skill_name] = {}  # 存在しないスキルも追加
            uncategorized_skills.append(skill_name)

# ── pending_reflect を session_state に反映 ──
if "pending_reflect" in st.session_state:
    data = st.session_state.pop("pending_reflect")
    st.session_state["weapon_name"] = data["weapon_name"]
    st.session_state["monster_name"] = data["monster_name"]
    st.session_state["part_name"] = data["part_name"]
    st.session_state["combo_name"] = data["combo_name"]
    # すべてのスキルLv/発動率をリセット
    for skill in skills_json.keys():
        st.session_state[skill + "_lv"] = 0
        st.session_state[skill + "_rate"] = 1.0

    for skill, (lv, rate) in data.get("skills", {}).items():
        st.session_state[skill + "_lv"] = lv
        st.session_state[skill + "_rate"] = rate

# ── 入力 ──
st.sidebar.header("▼ 計算条件")
weapon_name = st.sidebar.selectbox("武器", list(weapons.keys()), key="weapon_name")
monster_name = st.sidebar.selectbox("モンスター", list(monsters.keys()), key="monster_name")
part_name = st.sidebar.selectbox("部位", list(monsters[monster_name]["parts"].keys()), key="part_name")
combo_name = st.sidebar.selectbox("コンボ", list(combos.keys()), key="combo_name")

# ── スキル入力 ──
st.sidebar.markdown("### スキル (Lv + 発動率)")
skills_input = {}

for category, skill_list in skills_category.items():
    with st.sidebar.expander(f"🟦 {category}"):
        for name in skill_list:
            if name in skills_json:
                lv = st.number_input(f"{name} Lv", 0, 7, 0, key=name+"_lv")
                rate = st.slider(f"{name} 発動率", 0.0, 1.0, 1.0, 0.05, key=name+"_rate")
                if lv > 0:
                    skills_input[name] = (lv, rate)

if uncategorized_skills:
    with st.sidebar.expander("🟪 その他スキル"):
        for name in uncategorized_skills:
            lv = st.number_input(f"{name} Lv", 0, 7, 0, key=name+"_lv")
            rate = st.slider(f"{name} 発動率", 0.0, 1.0, 1.0, 0.05, key=name+"_rate")
            if lv > 0:
                skills_input[name] = (lv, rate)

# ── 計算実行 ──
if st.sidebar.button("計算する"):
    with st.spinner("計算中..."):
        result = run_full_dps_calculation(
            weapon_name, monster_name, part_name, combo_name, skills_input
        )

    st.session_state["last_result"] = {
        "weapon": weapon_name,
        "monster": monster_name,
        "part": part_name,
        "combo": combo_name,
        "skills": skills_input,
        "dps": result["DPS"]
    }

    st.header("🟥 計算結果概要 🟥")
    st.write(f"DPS：**{result['DPS']:.2f}**（物理：{result['物理DPS']:.1f} / 属性：{result['属性DPS']:.1f}）")
    st.write(f"コンボ時間：{result['コンボ時間']:.2f}秒")

    st.subheader("補正後ステータス")
    st.write(f"攻撃力：{result['攻撃力']:.1f}")
    st.write(f"会心率：{result['会心率']:.1f}%")
    st.write(f"属性値：{result['属性値']:.1f}")
    st.write(f"期待値攻撃力：{result['期待値攻撃力']:.1f}")

    st.subheader("有効肉質補正後")
    st.write(f"物理有効値: {result['物理有効値']:.1f}")
    st.write(f"属性有効値: {result['属性有効値']:.1f}")

    st.subheader("✨ 切れ味持続評価 ✨")
    st.write(f"切れ味ヒット数: {result['切れ味Hit']}")
    st.write(f"実効ヒット数：{result['実効Hit']}")
    st.write(f"継続コンボ回数：{result['コンボ回数']}")
    st.write(f"維持可能時間：約{result['維持秒数']:.1f}秒")
    
    st.subheader("切れ味が尽きるまでのダメージ量")
    st.write(f"平均ヒットダメージ：{result['平均Hitダメージ']:.1f}")
    st.write(f"切れ味が続く間の合計ダメージ：**{result['合計ダメージ']:.1f}**")


# ── お気に入り登録 ──
st.divider()
st.subheader("⭐ お気に入り登録 ⭐")

bookmark_name = st.text_input("お気に入り名（任意）")
if st.button("お気に入りに追加"):
    if "last_result" not in st.session_state:
        st.warning("先に計算を実行してください。")
    else:
        bookmark_data = st.session_state["last_result"].copy()
        bookmark_data["name"] = bookmark_name or f"構成 {bookmark_data['weapon']} x {bookmark_data['monster']}"
        bookmarks.add_bookmark(bookmark_data)
        st.success(f"「{bookmark_data['name']}」をお気に入りに登録しました。")
        st.rerun()

# ── お気に入り一覧 ──
bookmark_list = bookmarks.load_bookmarks()
if bookmark_list:
    st.subheader("お気に入りリスト")
    selected_name = st.selectbox("お気に入りを選択", [b["name"] for b in bookmark_list])
    selected = next((b for b in bookmark_list if b["name"] == selected_name), None)

    if selected:
        with st.expander("📦 お気に入りの内容を表示／非表示", expanded=False):
            st.json(selected)

        if st.button("この構成を反映"):
            st.session_state["pending_reflect"] = {
                "weapon_name": selected["weapon"],
                "monster_name": selected["monster"],
                "part_name": selected["part"],
                "combo_name": selected["combo"],
                "skills": selected.get("skills", {})
            }
            st.rerun()

        if st.button("このお気に入りを削除"):
            bookmarks.delete_bookmark(selected_name)
            st.success("削除しました。")
            st.rerun()

    if st.button("すべてのお気に入りを削除"):
        bookmarks.clear_all_bookmarks()
        st.success("全て削除しました。")
        st.rerun()
else:
    st.info("お気に入りはまだありません。")

# ── グラフ ──
csv_path = os.path.join(os.path.dirname(__file__), "..", "results", "dps_log.csv")
colnames = [
    "武器","モンスター","部位","切れ味","スキル構成","コンボ名",
    "補正攻撃力","会心率","補正属性","期待値攻撃",
    "物理肉質後","属性肉質後","物理合計","属性合計",
    "コンボ時間","DPS","元切れ味Hit","実効Hit","コンボ回数","維持秒数"
]

if os.path.exists(csv_path):
    df_logs = pd.read_csv(csv_path, header=None)
    df_logs.columns = colnames

    max_n = min(5, len(df_logs))
    n = st.slider("表示する構成数（最新から）", 0, max_n, max_n)

    if n > 0:
        latest_n = df_logs.tail(n).iloc[::-1].reset_index(drop=True)
        labels = ["最新"] + [f"{i}つ前" for i in range(1, n)]
        latest_n["構成ラベル"] = labels

        # st.subheader("過去構成のDPS比較")
        # chart_dps = alt.Chart(latest_n).mark_bar().encode(
        #     x=alt.X("構成ラベル:N", title="構成", sort=labels),
        #     y=alt.Y("DPS:Q", title="DPS"),
        #     color=alt.value("red"),
        # )
        # st.altair_chart(chart_dps, use_container_width=True)

        # st.subheader("過去構成の切れ味長さ比較")
        # chart_len = alt.Chart(latest_n).mark_bar().encode(
        #     x=alt.X("構成ラベル:N", title="構成", sort=labels),
        #     y=alt.Y("実効Hit:Q", title="切れ味持続ヒット数"),
        #     color=alt.value("yellow"),
        # )
        # st.altair_chart(chart_len, use_container_width=True)

        # st.subheader("過去構成の切れ味持続時間比較")
        # chart_time = alt.Chart(latest_n).mark_bar().encode(
        #     x=alt.X("構成ラベル:N", title="構成", sort=labels),
        #     y=alt.Y("維持秒数:Q", title="切れ味持続時間 (秒)"),
        #     color=alt.value("lightgreen"),
        # )
        # st.altair_chart(chart_time, use_container_width=True)
        
        with st.expander("📊 過去構成のDPS・切れ味グラフ（クリックで表示）", expanded=False):
            st.subheader("過去構成のDPS比較")
            chart_dps = alt.Chart(latest_n).mark_bar().encode(
                x=alt.X("構成ラベル:N", title="構成", sort=labels),
                y=alt.Y("DPS:Q", title="DPS"),
                color=alt.value("red"),
            )
            st.altair_chart(chart_dps, use_container_width=True)

            st.subheader("過去構成の切れ味長さ比較")
            chart_len = alt.Chart(latest_n).mark_bar().encode(
                x=alt.X("構成ラベル:N", title="構成", sort=labels),
                y=alt.Y("実効Hit:Q", title="切れ味持続ヒット数"),
                color=alt.value("yellow"),
            )
            st.altair_chart(chart_len, use_container_width=True)

            st.subheader("過去構成の切れ味持続時間比較")
            chart_time = alt.Chart(latest_n).mark_bar().encode(
                x=alt.X("構成ラベル:N", title="構成", sort=labels),
                y=alt.Y("維持秒数:Q", title="切れ味持続時間 (秒)"),
                color=alt.value("lightgreen"),
            )
            st.altair_chart(chart_time, use_container_width=True)

else:
    st.write("ログファイルが見つかりません。")

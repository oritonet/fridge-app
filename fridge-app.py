import streamlit as st
import json
import os
from PIL import Image

# 定数
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")

# 初期データ
default_items = {
    "トマト": {"count": 2, "image": "tomato.png"},
    "卵": {"count": 6, "image": "egg.png"},
    "牛乳": {"count": 1, "image": "milk.png"}
}

# データ読み込み
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_items

# データ保存
def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# レシピ提案
def suggest_recipe(data):
    ingredients = data.keys()
    if "トマト" in ingredients and "卵" in ingredients:
        return "🍳 トマトオムレツ を作りましょう！"
    elif "牛乳" in ingredients and "卵" in ingredients:
        return "🍮 プリンはいかがですか？"
    elif "牛乳" in ingredients:
        return "🥣 ミルクスープをおすすめ！"
    else:
        return "🥲 材料が足りません..."

# セッション状態初期化
if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = load_data()

st.title("🧊 冷蔵庫在庫管理アプリ")

# アイテム表示関数
def display_items():
    for item, info in st.session_state.fridge_items.items():
        cols = st.columns([1, 4, 1, 1, 1])  # アイコン、名前＋数量、＋、－、削除

        # アイコン画像
        image_path = os.path.join(IMAGE_DIR, info["image"])
        try:
            img = Image.open(image_path).resize((40, 40))  # 小さめに調整
            cols[0].image(img)
        except:
            cols[0].text("画像なし")

        # 名前と数量
        cols[1].markdown(f"**{item}：{info['count']}個**")

        # ＋ボタン
        if cols[2].button("＋", key=f"add_{item}"):
            st.session_state.fridge_items[item]["count"] += 1
            save_data(st.session_state.fridge_items)
            st.rerun()

        # －ボタン
        if cols[3].button("－", key=f"sub_{item}"):
            st.session_state.fridge_items[item]["count"] = max(0, st.session_state.fridge_items[item]["count"] - 1)
            save_data(st.session_state.fridge_items)
            st.rerun()

        # 削除ボタン
        if cols[4].button("🗑", key=f"del_{item}"):
            del st.session_state.fridge_items[item]
            save_data(st.session_state.fridge_items)
            st.rerun()

display_items()

st.markdown("---")
st.subheader("🥕 食材を追加")

new_item = st.text_input("食材名を入力", key="new_item")
add_col1, add_col2 = st.columns([2, 1])
if add_col2.button("追加"):
    name = new_item.strip()
    if not name:
        st.warning("食材名を入力してください")
    elif name in st.session_state.fridge_items:
        st.info(f"{name} はすでに存在します")
    else:
        image_file = {
            "トマト": "tomato.png",
            "卵": "egg.png",
            "牛乳": "milk.png"
        }.get(name, "default.png")  # imagesフォルダにdefault.pngを用意しておくと良いです

        st.session_state.fridge_items[name] = {"count": 1, "image": image_file}
        save_data(st.session_state.fridge_items)
        st.success(f"{name} を追加しました")
        st.rerun()

st.markdown("---")
if st.button("🍳 おすすめレシピを表示"):
    st.info(suggest_recipe(st.session_state.fridge_items))

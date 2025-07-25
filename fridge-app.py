import streamlit as st
import json
import os
from PIL import Image
import base64
import requests

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

# 画像をbase64に変換
def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

# 安全に再実行（Streamlitのrerun）
def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

def display_items():
    for item, info in st.session_state.fridge_items.items():
        image_path = os.path.join(IMAGE_DIR, info["image"])
        if os.path.exists(image_path):
            image_base64 = get_image_base64(image_path)
            count = info["count"]

            html = f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                <div style="position: relative; width: 60px; height: 60px;">
                    <img src="data:image/png;base64,{image_base64}"
                         style="width: 60px; height: 60px; border-radius: 8px; object-fit: contain;" />
                    <div style="
                        position: absolute;
                        top: 50%;
                        left: 50%;
                        transform: translate(-50%, -50%);
                        background-color: rgba(0, 0, 0, 0.6);
                        color: white;
                        font-weight: bold;
                        border-radius: 50%;
                        width: 26px;
                        height: 26px;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        font-size: 16px;
                        user-select: none;
                    ">
                        {count}
                    </div>
                </div>
                <div style="flex-grow: 1;">
                    <h3 style="margin: 0 0 8px 0;">{item}</h3>
                </div>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,1,1])
            pressed_add = col1.button("＋", key=f"btn_add_{item}")
            pressed_sub = col2.button("−", key=f"btn_sub_{item}")
            pressed_del = col3.button("🗑️", key=f"btn_del_{item}")

            if pressed_add:
                st.session_state.fridge_items[item]["count"] += 1
                save_data(st.session_state.fridge_items)
                safe_rerun()
            if pressed_sub:
                current_count = st.session_state.fridge_items[item]["count"]
                st.session_state.fridge_items[item]["count"] = max(0, current_count - 1)
                save_data(st.session_state.fridge_items)
                safe_rerun()
            if pressed_del:
                del st.session_state.fridge_items[item]
                save_data(st.session_state.fridge_items)
                safe_rerun()

        else:
            st.text(f"{item}：画像なし, 個数: {info['count']}")

# セッション初期化
if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = load_data()

# CSS調整（ボタンを大きく）
st.markdown("""
    <style>
    .stButton > button {
        padding: 6px 12px !important;
        font-size: 18px !important;
        min-width: 48px !important;
        height: 38px !important;
        line-height: 1 !important;
    }
    </style>
""", unsafe_allow_html=True)

# タイトル
st.markdown("<h2 style='font-size:20px;'>🧊 冷蔵庫在庫管理アプリ</h2>", unsafe_allow_html=True)

# 在庫一覧表示
display_items()

# 新規追加セクション
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
        }.get(name, "default.png")

        st.session_state.fridge_items[name] = {"count": 1, "image": image_file}
        save_data(st.session_state.fridge_items)
        st.success(f"{name} を追加しました")
        safe_rerun()

# レシピ表示
st.markdown("---")
def suggest_recipe(data):
    ingredients = data.keys()
    if "トマト" in ingredients and "卵" in ingredients:
        return "🍳 トマトオムレツ を作りましょう！"
    elif "牛乳" in ingredients and "卵" in ingredients:
        return "🍮 プリンはいかが？"
    elif "牛乳" in ingredients:
        return "🥣 ミルクスープをおすすめ！"
    else:
        return "🥲 材料が足りません..."

if st.button("🍳 おすすめレシピを表示"):
    st.info(suggest_recipe(st.session_state.fridge_items))

RAKUTEN_APP_ID = "1077657241734895268"

def get_rakuten_recipes(ingredients):
    material_str = "、".join(list(ingredients)[:5])
    st.write(f"楽天レシピAPIに送信する材料パラメータ: {material_str}")
    url = "https://app.rakuten.co.jp/services/api/Recipe/RecipeMaterial/20170426"
    params = {
        "applicationId": RAKUTEN_APP_ID,
        "format": "json",
        "material": material_str
    }
    try:
        res = requests.get(url, params=params)
        res.raise_for_status()
        data = res.json()
        recipes = data.get("result", [])
        return recipes
    except Exception as e:
        st.error(f"楽天レシピAPIの取得に失敗しました: {e}")
        return []

st.markdown("---")
st.subheader("📝 楽天レシピから提案")

if st.button("楽天レシピで検索"):
    ingredients = list(st.session_state.fridge_items.keys())
    if not ingredients:
        st.info("食材がありません")
    else:
        recipes = get_rakuten_recipes(ingredients)
        if recipes:
            for recipe in recipes[:5]:
                st.markdown(f"**{recipe['recipeTitle']}**  \n[レシピを見る]({recipe['recipeUrl']})")
        else:
            st.info("該当するレシピが見つかりませんでした。")

import streamlit as st
import json
import os
import base64
import requests

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.json")
IMAGE_DIR = os.path.join(BASE_DIR, "images")

default_items = {
    "トマト": {"count": 2, "image": "tomato.png"},
    "卵": {"count": 6, "image": "egg.png"},
    "牛乳": {"count": 1, "image": "milk.png"}
}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_items

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_image_base64(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode()

if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = load_data()

if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = {}

for item in st.session_state.fridge_items:
    if item not in st.session_state.edit_mode:
        st.session_state.edit_mode[item] = False

def toggle_edit(item):
    # 全アイテムの編集モードをオフにし、対象アイテムはトグル切替
    current = st.session_state.edit_mode.get(item, False)
    for k in st.session_state.edit_mode.keys():
        st.session_state.edit_mode[k] = False
    st.session_state.edit_mode[item] = not current

def display_items():
    st.write("### 🧊 現在の食材一覧")
    cols = st.columns(3)

    for idx, (item, info) in enumerate(st.session_state.fridge_items.items()):
        image_path = os.path.join(IMAGE_DIR, info["image"])
        count = info["count"]

        if not os.path.exists(image_path):
            st.warning(f"{item} の画像が見つかりません")
            continue

        image_base64 = get_image_base64(image_path)
        col = cols[idx % 3]

        with col:
            # 画像表示
            st.markdown(f"""
            <div style="position: relative; width: 100px; height: 100px; margin: auto;">
                <img src="data:image/png;base64,{image_base64}"
                    style="width: 50px; height: 40px; border-radius: 8px; object-fit: cover;" />
                <div style="
                    position: absolute;
                    top: 50%;
                    left: 50%;
                    transform: translate(-50%, -50%);
                    background-color: rgba(0,0,0,0.6);
                    color: white;
                    font-weight: bold;
                    border-radius: 50%;
                    width: 36px;
                    height: 36px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 18px;
                    user-select: none;
                    pointer-events: none;
                ">
                    {count}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # 編集ボタン（ラベル切替あり）
            label = "閉じる" if st.session_state.edit_mode.get(item, False) else "編集"
            if st.button(label, key=f"edit_btn_{item}"):
                toggle_edit(item)
                st.rerun()

            # 編集モード：操作ボタン（＋/−/削除）表示（枠なし）
            if st.session_state.edit_mode.get(item, False):
                c1, c2, c3 = st.columns(3)
                if c1.button("＋", key=f"plus_{item}"):
                    st.session_state.fridge_items[item]["count"] += 1
                    save_data(st.session_state.fridge_items)
                    st.rerun()
                if c2.button("−", key=f"minus_{item}"):
                    st.session_state.fridge_items[item]["count"] = max(0, count - 1)
                    save_data(st.session_state.fridge_items)
                    st.rerun()
                if c3.button("🗑️", key=f"delete_{item}"):
                    del st.session_state.fridge_items[item]
                    save_data(st.session_state.fridge_items)
                    st.rerun()


                st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<h2 style='font-size:20px;'>🧊 冷蔵庫在庫管理アプリ</h2>", unsafe_allow_html=True)
display_items()

st.markdown("---")
st.subheader("🥕 食材を追加")

new_item = st.text_input("食材名を入力", key="new_item")
add_col1, add_col2 = st.columns([2,1])
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
        st.session_state.edit_mode[name] = False
        save_data(st.session_state.fridge_items)
        st.rerun()

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
        return data.get("result", [])
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

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

def safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        pass

def process_buttons():
    rerun_needed = False
    keys_to_delete = []

    for item in list(st.session_state.fridge_items.keys()):
        # 押下フラグを取得
        pressed_add = st.session_state.get(f"btn_add_{item}_clicked", False)
        pressed_sub = st.session_state.get(f"btn_sub_{item}_clicked", False)
        pressed_del = st.session_state.get(f"btn_del_{item}_clicked", False)

        if pressed_add:
            st.session_state.fridge_items[item]["count"] += 1
            rerun_needed = True
            st.session_state[f"btn_add_{item}_clicked"] = False  # フラグリセット
        if pressed_sub:
            st.session_state.fridge_items[item]["count"] = max(0, st.session_state.fridge_items[item]["count"] - 1)
            rerun_needed = True
            st.session_state[f"btn_sub_{item}_clicked"] = False
        if pressed_del:
            keys_to_delete.append(item)
            rerun_needed = True
            st.session_state[f"btn_del_{item}_clicked"] = False

    for key in keys_to_delete:
        del st.session_state.fridge_items[key]

    if rerun_needed:
        save_data(st.session_state.fridge_items)
        safe_rerun()

def display_items():
    for item, info in st.session_state.fridge_items.items():
        image_path = os.path.join(IMAGE_DIR, info["image"])
        count = info["count"]
        key_show = f"show_buttons_{item}"

        if key_show not in st.session_state:
            st.session_state[key_show] = False

        if os.path.exists(image_path):
            image_base64 = get_image_base64(image_path)

            # クリック可能な画像 + JSトリガー
            img_click_html = f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
                <div onclick="fetch('/_click_image_{item}', {{method: 'POST'}})"
                    style="position: relative; width: 60px; height: 60px; cursor: pointer;">
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

            # JavaScriptクリック→streamlitの値変更
            js = f"""
            <script>
                const imgDiv = document.querySelectorAll("div[onclick]");
                imgDiv.forEach(div => {{
                    div.addEventListener("click", () => {{
                        const event = new Event("input", {{ bubbles: true }});
                        const input = window.parent.document.querySelector("input[name='toggle_{item}']");
                        if (input) {{
                            input.checked = !input.checked;
                            input.dispatchEvent(event);
                        }}
                    }});
                }});
            </script>
            """
            # hidden input (トグルの代用)
            st.markdown(f"""
                <input type="checkbox" name="toggle_{item}" style="display:none"
                    {'checked' if st.session_state[key_show] else ''}>
            """, unsafe_allow_html=True)
            # 画像クリックUI
            st.markdown(img_click_html, unsafe_allow_html=True)
            st.markdown(js, unsafe_allow_html=True)

            # Python側でも toggle を管理
            toggle = st.checkbox(f"", key=f"toggle_checkbox_{item}", label_visibility="collapsed", value=st.session_state[key_show])
            st.session_state[key_show] = toggle

            if st.session_state[key_show]:
                col1, col2, col3 = st.columns([1, 1, 1])
                if col1.button("＋", key=f"btn_add_{item}"):
                    st.session_state.fridge_items[item]["count"] += 1
                    save_data(st.session_state.fridge_items)
                    st.session_state[key_show] = False
                    st.rerun()
                if col2.button("−", key=f"btn_sub_{item}"):
                    st.session_state.fridge_items[item]["count"] = max(0, count - 1)
                    save_data(st.session_state.fridge_items)
                    st.session_state[key_show] = False
                    st.rerun()
                if col3.button("🗑️", key=f"btn_del_{item}"):
                    del st.session_state.fridge_items[item]
                    save_data(st.session_state.fridge_items)
                    st.rerun()

        else:
            st.text(f"{item}：画像なし, 個数: {count}")

# セッション初期化
if "fridge_items" not in st.session_state:
    st.session_state.fridge_items = load_data()

# ボタン押下フラグ初期化（新アイテム追加時に対応）
for item in st.session_state.fridge_items.keys():
    for prefix in ["btn_add_", "btn_sub_", "btn_del_"]:
        key = f"{prefix}{item}_clicked"
        if key not in st.session_state:
            st.session_state[key] = False

process_buttons()  # ボタン押下の状態を処理・反映

st.markdown("<h2 style='font-size:20px;'>🧊 冷蔵庫在庫管理アプリ</h2>", unsafe_allow_html=True)

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
        }.get(name, "default.png")

        st.session_state.fridge_items[name] = {"count": 1, "image": image_file}
        # 追加したアイテムのボタン押下フラグも初期化
        for prefix in ["btn_add_", "btn_sub_", "btn_del_"]:
            st.session_state[f"{prefix}{name}_clicked"] = False
        save_data(st.session_state.fridge_items)
        st.success(f"{name} を追加しました")
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

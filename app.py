import streamlit as st
import requests
import base64
import io
from PIL import Image
import json

# --- 1. 設定 API 金鑰 ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except Exception:
    st.error("找不到 API Key，請在 Secrets 設定中填入 GOOGLE_API_KEY")
    st.stop()

def analyze_cabinet(image):
    """使用 REST API 直接呼叫 Gemini 2.5 Flash"""
    
    # 1. 將圖片轉為 Base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 2. 準備請求 (使用 Gemini 2.5 Flash)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    # --- 關鍵修改：更精確的提示詞 (Prompt) ---
    prompt_text = """
    【角色設定】
    你是一個嚴格的手機保管櫃檢查員。你的任務是找出哪些格子是「空的（缺交）」。

    【場景描述】
    1. 這是一個手機櫃，每個格子下方有藍色標籤與白色數字。
    2. 格子內部是「深色/黑色的防撞泡棉」。

    【判斷標準 - 請仔細閱讀】
    * **判定為「空 (缺交)」**：
        * 你可以清楚看到格子深處的「黑色泡棉質感」或「黑色陰影」。
        * 格子內沒有任何雜物。
    
    * **判定為「有手機 (已交)」**：
        * 格子內有「反光物體」、「彩色手機殼」或「螢幕」。
        * 原本深色的背景被物體擋住了。
        * 即使只看到手機的一角，也要算作「已交」。
    
    【思考步驟】
    1. 先辨識出圖片中所有的數字標籤。
    2. 對應每個標籤，往上看該格子的內容。
    3. 嚴格區分「黑色泡棉(空)」與「黑色手機(有物體)」。黑色手機通常會有光澤或邊框。

    【輸出格式】
    請直接列出「缺交」的號碼，用逗號分隔。
    例如: 03, 08, 12, 45
    (如果全部都交了，請回答：None)
    """
    
    payload = {
        "contents": [{
            "parts": [
                {"text": prompt_text},
                {
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": img_b64
                    }
                }
            ]
        }]
    }

    # 3. 發送請求
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 200:
            result = response.json()
            try:
                return result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return "AI 回傳了無法解析的資料，請再試一次。"
        elif response.status_code == 429:
             return "太頻繁了！請休息 1 分鐘後再試 (Google 免費版限制)。"
        else:
            return f"連線錯誤 (代碼 {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"發生錯誤: {e}"

# --- 3. 網頁介面 ---
st.set_page_config(page_title="手機櫃缺交偵測", page_icon="📱")
st.title("📱 手機櫃缺交偵測 (精準版)")

st.info("💡 拍照技巧：請盡量正面拍攝，避免反光太強，讓數字清晰可見。")

img_file_buffer = st.camera_input("📸 拍照")
uploaded_file = st.file_uploader("或上傳照片", type=["jpg", "jpeg", "png"])

image_to_process = None

if img_file_buffer:
    image_to_process = Image.open(img_file_buffer)
elif uploaded_file:
    image_to_process = Image.open(uploaded_file)

if image_to_process:
    st.image(image_to_process, caption="已讀取照片", use_container_width=True)
    
    if st.button("🔍 開始辨識", type="primary"):
        with st.spinner('AI 正在仔細檢查每一個格子...'):
            result = analyze_cabinet(image_to_process)
            
        if "錯誤" in result or "頻繁" in result:
            st.error(result)
        else:
            st.success("辨識完成！")
            st.subheader("⚠️ 缺交號碼：")
            st.markdown(f"### {result}")

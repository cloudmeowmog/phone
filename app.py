import streamlit as st
import requests
import base64
import io
from PIL import Image
import json

# --- 1. 設定 API 金鑰 ---
try:
    # 讀取並去除可能的多餘空白
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except Exception:
    st.error("找不到 API Key，請在 Secrets 設定中填入 GOOGLE_API_KEY")
    st.stop()

def analyze_cabinet(image):
    """使用 REST API 直接呼叫 Gemini 2.0"""
    
    # 1. 將圖片轉為 Base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 2. 準備請求 (改用您的帳號支援的 gemini-2.0-flash-exp)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    prompt_text = """
    這是一個由 01 到 48 號組成的與手機保管櫃。
    請仔細觀察圖片，找出哪些號碼的格子是「空的」（沒有放手機）。
    
    規則：
    1. 格子裡如果有手機（無論顏色），視為「已交」。
    2. 格子裡如果只有深色的防撞泡棉背景，視為「缺交（空）」。
    3. 格子下方的藍色標籤上有白色數字。
    4. 請忽略反光，專注辨識空格。
    
    請直接回傳缺交的號碼列表，用逗號分隔，不要有其他文字。
    例如: 03, 08, 12, 45
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
        else:
            return f"連線錯誤 (代碼 {response.status_code}): {response.text}"
            
    except Exception as e:
        return f"發生錯誤: {e}"

# --- 3. 網頁介面 ---
st.set_page_config(page_title="手機櫃缺交偵測", page_icon="📱")
st.title("📱 手機櫃缺交偵測")

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
        with st.spinner('正在使用最新的 Gemini 2.0 模型辨識中...'):
            result = analyze_cabinet(image_to_process)
            
        if "連線錯誤" in result:
            st.error(result)
        else:
            st.success("辨識完成！")
            st.subheader("⚠️ 缺交號碼：")
            st.markdown(f"### {result}")

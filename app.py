import streamlit as st
import requests
import base64
import io
from PIL import Image

# --- 1. 設定 API 金鑰 ---
try:
    # 使用 strip() 去除可能不小心複製到的空白鍵
    api_key = st.secrets["GOOGLE_API_KEY"].strip()
except Exception:
    st.error("找不到 API Key，請在 Secrets 設定中填入 GOOGLE_API_KEY")
    st.stop()

def get_available_models():
    """診斷功能：列出目前帳號可用的所有模型"""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            models = response.json().get('models', [])
            # 過濾出支援圖片 (vision) 的模型
            vision_models = [m['name'] for m in models if 'generateContent' in m['supportedGenerationMethods']]
            return vision_models
        else:
            return [f"無法取得清單: {response.text}"]
    except Exception as e:
        return [f"連線失敗: {e}"]

def analyze_cabinet(image):
    """使用 REST API 直接呼叫 Gemini"""
    
    # 1. 將圖片轉為 Base64
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_b64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # 2. 準備請求 (嘗試切換到 v1 正式版)
    # 如果 v1 也不行，我們等等會自動列出可用模型
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={api_key}"
    
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
    請直接回傳缺交的號碼列表，用逗號分隔，不要有其他文字。
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
                return True, result['candidates'][0]['content']['parts'][0]['text']
            except (KeyError, IndexError):
                return False, "AI 回傳了無法解析的資料。"
        elif response.status_code == 404:
            # 關鍵：如果是 404，啟動診斷模式
            return False, "MODEL_NOT_FOUND"
        else:
            return False, f"連線錯誤 (代碼 {response.status_code}): {response.text}"
            
    except Exception as e:
        return False, f"發生錯誤: {e}"

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
        with st.spinner('AI 正在辨識中...'):
            success, result = analyze_cabinet(image_to_process)
            
        if success:
            st.success("辨識完成！")
            st.subheader("⚠️ 缺交號碼：")
            st.markdown(f"### {result}")
        
        elif result == "MODEL_NOT_FOUND":
            # --- 自動診斷介面 ---
            st.error("⚠️ 找不到預設模型 (Gemini 1.5 Flash)")
            st.info("正在為您查詢帳號可用的模型清單...")
            
            available_models = get_available_models()
            st.write("您的 API Key 支援以下模型：")
            st.code(available_models)
            
            st.warning("請截圖這個畫面，我將為您調整程式碼！")
            
        else:
            st.error(f"發生錯誤：{result}")

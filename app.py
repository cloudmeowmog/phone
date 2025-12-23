import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. 設定 API ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("找不到 API Key，請在 Secrets 設定中填入 GOOGLE_API_KEY")
    st.stop()

# --- 2. 設定 AI 模型 ---
# 使用官方 SDK 呼叫 Gemini 1.5 Flash
model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_cabinet(image):
    """傳送圖片給 AI 進行分析"""
    prompt = """
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
    
    try:
        # 官方 SDK 支援直接傳送 PIL Image 物件
        response = model.generate_content([prompt, image])
        return response.text
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
        with st.spinner('AI 正在辨識中...'):
            result = analyze_cabinet(image_to_process)
            
        st.success("辨識完成！")
        st.subheader("⚠️ 缺交號碼：")
        st.markdown(f"### {result}")

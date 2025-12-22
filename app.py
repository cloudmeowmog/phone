import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 設定 ---
# 改成從 Streamlit 的 "Secrets" 讀取密碼，比較安全
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
    genai.configure(api_key=api_key)
except Exception:
    st.error("找不到 API Key，請在 Streamlit 設定中的 Secrets 填入 GOOGLE_API_KEY")
    st.stop()

model = genai.GenerativeModel('gemini-1.5-flash')

def analyze_cabinet(image):
    prompt = """
    這是一個由 01 到 48 號組成的與手機保管櫃。
    請仔細觀察圖片，找出哪些號碼的格子是「空的」（沒有放手機）。
    規則：
    1. 格子裡如果有手機（無論顏色），視為「已交」。
    2. 格子裡如果只有深色的防撞泡棉背景，視為「缺交（空）」。
    3. 格子下方的藍色標籤上有白色數字。
    請直接回傳缺交的號碼列表，用逗號分隔，不要有其他文字。
    """
    try:
        response = model.generate_content([prompt, image])
        return response.text
    except Exception as e:
        return f"錯誤: {e}"

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
    st.image(image_to_process, use_container_width=True)
    if st.button("🔍 開始辨識", type="primary"):
        with st.spinner('AI 正在檢查...'):
            result = analyze_cabinet(image_to_process)
        st.success("完成！")
        st.subheader("⚠️ 缺交號碼：")
        st.markdown(f"### {result}")
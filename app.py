import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from PIL import Image
import io
import base64

# --- 1. 設定 API ---
# 嘗試從 Streamlit Secrets 讀取 API Key
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except Exception:
    st.error("找不到 API Key，請在 Secrets 設定中填入 GOOGLE_API_KEY")
    st.stop()

# --- 2. 設定 AI 模型 ---
# 使用最穩定的版本號 001，解決找不到模型的問題
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash-001",
    google_api_key=api_key
)

def analyze_cabinet(image):
    """將圖片轉為 Base64 並傳送給 LangChain"""
    
    # 1. 圖片前處理：轉為 Base64 字串
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    # 2. 準備 Prompt (提示詞)
    prompt_text = """
    這是一個由 01 到 48 號組成的與手機保管櫃。
    請仔細觀察圖片，找出哪些號碼的格子是「空的」（沒有放手機）。
    
    規則：
    1. 格子裡如果有手機（無論顏色），視為「已交」。
    2. 格子裡如果只有深色的防撞泡棉背景，視為「缺交（空）」。
    3. 格子下方的藍色標籤上有白色數字。
    
    請直接回傳缺交的號碼列表，用逗號分隔，不要有其他文字。
    例如: 03, 08, 12, 45
    """

    # 3. 組合訊息 (文字 + 圖片)
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt_text},
            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{img_str}"}}
        ]
    )

    # 4. 發送請求
    try:
        response = llm.invoke([message])
        return response.content
    except Exception as e:
        return f"發生錯誤: {e}"

# --- 3. 網頁介面 ---
st.set_page_config(page_title="手機櫃缺交偵測", page_icon="📱")
st.title("📱 手機櫃缺交偵測")

# 讓手機可以選擇「拍照」或「上傳相簿」
img_file_buffer = st.camera_input("📸 拍照")
uploaded_file = st.file_uploader("或上傳照片", type=["jpg", "jpeg", "png"])

image_to_process = None

if img_file_buffer:
    image_to_process = Image.open(img_file_buffer)
elif uploaded_file:
    image_to_process = Image.open(uploaded_file)

if image_to_process:
    # 顯示預覽圖
    st.image(image_to_process, caption="已讀取照片", use_container_width=True)
    
    if st.button("🔍 開始辨識", type="primary"):
        with st.spinner('AI 正在辨識中...'):
            result = analyze_cabinet(image_to_process)
            
        st.success("辨識完成！")
        
        # 美化輸出結果
        st.subheader("⚠️ 缺交號碼：")
        st.markdown(f"### {result}")

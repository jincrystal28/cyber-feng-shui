import streamlit as st
import base64
from openai import OpenAI
import os
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 =================
st.set_page_config(page_title="赛博堪舆大师 | AI风水", page_icon="☯️", layout="centered")

# 图像转 Base64 的辅助函数 (大模型视觉接口需要)
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def main():
    st.title("☯️ 赛博堪舆：内外局全息诊断系统")
    st.markdown("---")

    # ================= 侧边栏：引擎配置 =================
    with st.sidebar:
        st.header("⚙️ 引擎配置 (Google Gemini版)")
        st.markdown("本项目由 Google Gemini 提供视觉算力支持。")
        
        # 输入 Google AI Studio 申请的 API Key
        api_key = st.text_input("Google API Key (AIza开头):", type="password")
        
        # 模型选择改为 Gemini 家族
        model_choice = st.selectbox(
            "选择推演大模型:", 
            [
                "gemini-1.5-flash", # 每天1500次免费，速度极快
                "gemini-1.5-pro"    # 每天50次免费，逻辑推理最深
            ]
        )
        st.caption("提示：Flash 适合快速测算，Pro 适合深度看图找细节。")

    # ================= 1. 获取外局 (GPS 寻龙) =================
    st.subheader("📍 第一步：外局寻龙 (GPS测位)")
    st.write("请允许浏览器获取位置，以探测周边的地脉气场。")
    
    location = streamlit_geolocation()
    geo_context = ""

    if location['latitude'] is not None and location['longitude'] is not None:
        lat = location['latitude']
        lon = location['longitude']
        st.success(f"✅ 天机锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"当前坐标为北纬 {lat}, 东经 {lon}。"

    supplementary_geo = st.text_input("您可以补充周边环境 (例如: 窗外正对高架桥, 楼下是十字路口):")
    if supplementary_geo:
        geo_context += f" 补充环境信息：{supplementary_geo}。"

    st.markdown("---")

    # ================= 2. 获取内局 (图像观形) =================
    st.subheader("📸 第二步：内局观形 (上传实景)")
    uploaded_file = st.file_uploader("请上传户型图或室内实景（卧室/办公桌）", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:
        st.image(uploaded_file, caption="已录入的内局影像", use_container_width=True)

    st.markdown("---")

    # ================= 3. 核心引擎 (大模型推理) =================
    if st.button("🔮 开始全息堪舆推演", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ 请在左侧侧边栏输入 Google API Key 以启动引擎！")
            return
        if uploaded_file is None:
            st.error("⚠️ 请先上传内局照片，否则大师无法观形！")
            return

        with st.spinner("天地交泰，大师正在运算气场，请稍候..."):
            try:
                # 核心魔法：使用 OpenAI 官方库，但把网址指向 Google 的服务器！
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )

                # 将图片转码
                base64_image = encode_image(uploaded_file)

                # 终极 Prompt
                master_prompt = f"""
                # Role: 首席环境地理学与全息堪舆宗师
                你精通形峦与理气，擅长结合地理坐标与室内实景进行“内外兼修”的风水诊断。

                # Input Data:
                1. 外局地理信息：{geo_context if geo_context else '未提供精确坐标，请主要依赖内局照片推演。'}

                # Task:
                请综合外局的地理因素与内局的空间布局照片，输出一份《内外局全息能量诊断报告》。

                # Output Format:
                1. 📜 【天地定势】：写一首四句七言诗，巧妙融合方位感与室内照片的核心特征。
                2. 🧭 【外局环境解析】：根据补充的周边环境，用现代科学+环境心理学解释其对运势的影响。
                3. 🔍 【内局实景勘验】：指出照片中最严重的1个风水煞气（如穿堂煞、尖角冲射、横梁压顶等），并说明具体位置。
                4. 🛠️ 【化煞爆改方案】：给出一个能同时化解内外局冲突的务实物理调整建议（如摆放何种绿植、调整工位朝向、灯光色温布置等）。
                """

                # 发送图文混合请求
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": master_prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ]
                )

                report = response.choices[0].message.content
                st.success("✅ 推演完成！")
                st.markdown("### 📜 您的专属堪舆诊断报告")
                st.markdown(report)

            except Exception as e:
                st.error(f"运算出错，灵力受到干扰：{str(e)}")

if __name__ == "__main__":
    main()

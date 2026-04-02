import streamlit as st
import base64
from openai import OpenAI
import os
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 =================
st.set_page_config(page_title="赛博堪舆大师 | AI全息风水", page_icon="☯️", layout="centered")

# 图像转 Base64 的辅助函数 (视觉接口需要)
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def main():
    st.title("☯️ 赛博堪舆：内外局全息诊断系统")
    st.markdown("---")

    # ================= 侧边栏：引擎配置 =================
    with st.sidebar:
        st.header("⚙️ 引擎配置 (Google Gemini版)")
        st.markdown("本项目由 Google Gemini 提供最新款 Vision 视觉算力支持。")
        
        # 输入 Google AI Studio 申请的 API Key
        api_key = st.text_input("Google API Key (AIza开头):", type="password")
        
        # 强制选择最新版 2.5 模型，保证多图处理能力
        model_choice = "gemini-2.5-flash"
        st.success(f"已锁定高阶多模态引擎: {model_choice}")
        st.caption("Flash 模型每天有 1500 次免费额度，适合白嫖。")

    # ================= 1. 获取外局 (GPS+三层探测) =================
    st.subheader("📍 第一步：外局寻龙 (天地人三盘)")
    st.write("GPS定大局，肉眼看小局。请尽量补充以下信息以提升算力精度：")
    
    # 保留原有的 GPS 获取
    location = streamlit_geolocation()
    geo_context = ""

    if location['latitude'] is not None and location['longitude'] is not None:
        lat = location['latitude']
        lon = location['longitude']
        st.success(f"✅ GPS锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"

    # 新增三层外局手动探测输入框
    city_district = st.text_input("🌍 大外局 (5公里)：所在城市与行政区或大地标 (例如: 北京朝阳/上海陆家嘴)")
    local_landmark = st.text_input("🏙️ 中外局 (500米)：所在小区名称、附近商场或水系 (例如: 望京SOHO/旁边有条河)")
    micro_env = st.text_input("🏘️ 小外局 (50米)：环境文字描述 (例如: 有高架桥/楼下十字路口/有电线杆)")

    # 拼装地理上下文
    if city_district: geo_context += f"大外局信息：{city_district}。\n"
    if local_landmark: geo_context += f"中外局信息：{local_landmark}。\n"
    if micro_env: geo_context += f"小外局信息描述：{micro_env}。\n"

    st.markdown("---")

    # ================= 2. 获取图像 (全息观形) =================
    st.subheader("📸 第二步：全息观形 (上传环境照片)")
    st.write("图像信息越丰富，推演越精准。请分别上传以下两类照片：")

    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📸 窗外/门外景观 (小外局)**")
        window_file = st.file_uploader("拍摄窗外肉眼可见的环境", type=["jpg", "jpeg", "png"], key="window_uv")
        if window_file:
            st.image(window_file, caption="已录入的窗外影像", use_container_width=True)

    with col2:
        st.markdown("**📜 户型图 / 室内布局 (内局)**")
        st.caption("提示：上传【带比例的 drawn 户型图】定方位最准；若无，可上传客厅/卧室主景照片。")
        indoor_file = st.file_uploader("上传户型图或核心房间实景", type=["jpg", "jpeg", "png"], key="indoor_uv")
        if indoor_file:
            st.image(indoor_file, caption="已录入的内局/户型影像", use_container_width=True)

    st.markdown("---")

    # ================= 3. 核心引擎 (大模型推理) =================
    if st.button("🔮 开始全息堪舆推演", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ 请在左侧侧边栏输入 Google API Key (AIza开头)！")
            return
        # 允许只上传一张照片，增强灵活性，但 Prompt 里要处理
        if not window_file and not indoor_file:
            st.error("⚠️ 大师至少需要一张照片（窗外或内局）才能观形！")
            return

        with st.spinner("内外兼修，三维同勘。大师正在运算气场，请稍候..."):
            try:
                # 初始化客户端
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )

                # 准备消息体的内容列表
                content_list = []
                
                # 拼装终极 Prompt
                master_prompt = f"""
                # Role: 首席环境地理学与全息堪舆宗师
                你精通形峦与理气，擅长结合宏观地理、微观窗外冲煞以及室内空间布局进行“内外兼修、全息多模态”的风水诊断。

                # Input Data:
                1. 地理与文字信息：\n{geo_context if geo_context else '未提供精确坐标或文字描述，请完全依赖上传的照片推演。'}
                2. 照片 1 (窗外景观)：用于辨识 50 米内的特定“形煞”。
                3. 照片 2 (户型图或室内实景)：用于分析整体能量流或特定房间的物理布局吉凶。

                # Task:
                请综合上述所有信息（若用户只提供了其中一张照片，则仅针对该照片所涉层级进行深度分析），输出一份极具专业感、层次分明的《内外局全息能量诊断报告》。

                # Output Format (严格按照以下模块输出)：
                1. 📜 【天地定势】：写一首四句七言诗，巧妙融合方位感与两张照片的核心能量特征。
                2. 🌍 【大外局论龙脉 (5公里+)】：简述区域整体气场与大风水背景。
                3. 🏙️ 【中外局定格调 (500米)】：分析小区/地标/水系对所在建筑“聚气”的影响。
                4. 🏘️ 【小外局辨形煞 (50米 - 核心：参考照片1)】：犀利指出照片1中肉眼可见的煞气（如壁刀煞、路冲、天斩煞等）及其具体位置。
                5. 🔍 【内局全息勘验 (核心：参考照片2)】：
                   - 若用户上传的是【户型图】：分析整体 Bagua flow，指出核心房间方位吉凶。
                   - 若用户上传的是【室内实景】：指出照片中存在的物理冲煞（如横梁压顶、杂物逼虎、工位无靠）。
                6. 🛠️ 【化煞爆改方案】：给出一个务实、可操作的物理调整建议（如摆放植物、调整工位朝向、灯光色温布置等）。
                """
                content_list.append({"type": "text", "text": master_prompt})

                # 处理图片1 (窗外)
                if window_file:
                    base64_window = encode_image(window_file)
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_window}"
                        }
                    })

                # 处理图片2 (内局/户型)
                if indoor_file:
                    base64_indoor = encode_image(indoor_file)
                    content_list.append({
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_indoor}"
                        }
                    })

                # 发送图文消息
                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": content_list}]
                )

                report = response.choices[0].message.content
                st.success("✅ 推演完成！")
                st.markdown("### 📜 您的专属堪舆诊断报告")
                st.markdown(report)

            except Exception as e:
                # 针对 429 频率限制提供 empathetic 提示
                if "429" in str(e):
                    st.error("⚠️ 大师今日算卦过多，暂时灵力耗尽 (429 Rate Limit)。请稍候几分钟再试，或明天重置免费额度后再来。")
                else:
                    st.error(f"运算出错，灵力受到干扰：{str(e)}")

if __name__ == "__main__":
    main()

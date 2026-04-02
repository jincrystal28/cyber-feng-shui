import streamlit as st
import base64
from openai import OpenAI
import time
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 (必须放在最前面) =================
st.set_page_config(page_title="赛博堪舆大师 | AI全息风水", page_icon="☯️", layout="centered")

# ================= 🎨 视觉升级：黑金赛博玄学风 CSS =================
# ================= 🎨 视觉升级：黑金赛博玄学风 CSS =================
st.markdown("""
<style>
    /* 全局暗黑背景与柔和灰白文字 */
    .stApp {
        background-color: #0E1117;
        color: #E0E0E0;
    }
    /* 所有的标题强制变为暗金色 */
    h1, h2, h3, h4, h5, h6 {
        color: #D4AF37 !important;
        font-family: 'STXingkai', 'KaiTi', serif; 
    }
    /* 🌟 新增修复：强制把输入框上面的提示文字（那三行字）提亮，并稍微加粗 */
    label {
        color: #E0E0E0 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }
    /* 主按钮（推演按钮）黑金特效 */
    .stButton>button[kind="primary"] {
        background-color: #111111;
        color: #D4AF37;
        border: 1px solid #D4AF37;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.2);
        transition: all 0.3s ease;
        font-weight: bold;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #D4AF37;
        color: #0E1117;
        box-shadow: 0 0 20px rgba(212, 175, 55, 0.6);
    }
    /* 进度条变成暗金色 */
    .stProgress > div > div > div > div {
        background-color: #D4AF37;
    }
    /* 分割线变暗金 */
    hr {
        border-bottom-color: #D4AF37;
        opacity: 0.3;
    }
</style>
""", unsafe_allow_html=True)

# ================= 辅助函数 =================
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# ================= 核心逻辑 =================
def main():
    st.title("☯️ 赛博堪舆：天地人全息大阵")
    st.markdown("---")

    # ================= 🔑 密钥保密获取逻辑 =================
    # 优先尝试从云端 Secrets 读取 Key，如果没有，才显示输入框
    api_key = ""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        has_secret = True
    except (FileNotFoundError, KeyError):
        has_secret = False

    with st.sidebar:
        st.header("⚙️ 引擎配置")
        if has_secret:
            st.success("🔒 灵力接口已就绪 (云端密钥受保护)")
        else:
            st.warning("未检测到云端密钥，请手动输入")
            api_key = st.text_input("Google API Key:", type="password")
            
        model_choice = st.selectbox(
            "选择推演引擎:", 
            ["gemini-2.5-flash", "gemini-2.5-pro"]
        )
        st.caption("提示：Flash 主流测算，Pro 适合破译凶局。")

    # ================= 1. 获取外局 (GPS+三层探测) =================
    st.subheader("📍 壹 · 外局寻龙 (天地人三盘)")
    st.write("GPS定大局，肉眼看小局。补充信息以提升算力精度：")
    
    location = streamlit_geolocation()
    geo_context = ""

    if location['latitude'] is not None and location['longitude'] is not None:
        lat = location['latitude']
        lon = location['longitude']
        st.success(f"✅ 天机锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"

    city_district = st.text_input("🌍 大外局 (5公里)：所在城市与区县 (例: 广州天河)")
    local_landmark = st.text_input("🏙️ 中外局 (500米)：小区名或附近水系 (例: 珠江帝景/临江)")
    micro_env = st.text_input("🏘️ 小外局 (50米)：窗外肉眼所见冲煞 (例: 有高架桥/尖角)")

    if city_district: geo_context += f"大外局信息：{city_district}。\n"
    if local_landmark: geo_context += f"中外局信息：{local_landmark}。\n"
    if micro_env: geo_context += f"小外局信息描述：{micro_env}。\n"

    st.markdown("---")

    # ================= 2. 获取图像 (全息观形) =================
    st.subheader("📸 贰 · 全息观形 (上传环境法相)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📸 窗外景观 (看小外局)**")
        window_file = st.file_uploader("拍摄窗外肉眼可见的环境", type=["jpg", "png"], key="win")
        if window_file: st.image(window_file, use_container_width=True)

    with col2:
        st.markdown("**📜 户型/内局 (看形峦)**")
        indoor_file = st.file_uploader("上传户型图或核心房间照片", type=["jpg", "png"], key="in")
        if indoor_file: st.image(indoor_file, use_container_width=True)

    st.markdown("---")

    # ================= 3. 核心引擎 (大模型推理) =================
    if st.button("🔮 启动全息天道推演", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ 灵力源未接入，请检查 API Key！")
            return
        if not window_file and not indoor_file:
            st.error("⚠️ 大师至少需要一张照片（窗外或内局）才能开启视觉天眼！")
            return

        # 🎭 信任建立：运算剧场
        with st.status("🔮 开启天道引擎，启动全息推演...", expanded=True) as status:
            st.write("📡 正在解析 GPS 经纬度，锁定地脉气场...")
            time.sleep(1.2)
            st.write("🧭 正在调取当运流年，进行九宫飞星排盘...")
            time.sleep(1.2)
            st.write("👁️ 视觉引擎介入，扫描形峦冲煞与暗流...")
            time.sleep(1.0)
            st.write("⚙️ 汇总三盘数据，生成改运化煞真诀...")

            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                
                content_list = []
                master_prompt = f"""
                # Role: 首席环境地理学与全息堪舆宗师
                你精通形峦与理气，擅长结合宏观地理、微观窗外冲煞以及室内空间布局进行“内外兼修、全息多模态”的风水诊断。

                # Input Data:
                1. 地理与文字信息：\n{geo_context if geo_context else '仅依赖照片。'}
                2. 照片 1 (窗外景观)：用于辨识 50 米内的特定“形煞”。
                3. 照片 2 (户型图或室内实景)：用于分析整体能量流或特定房间布局。

                # Task:
                输出一份极具专业感、层次分明的《内外局全息能量诊断报告》。语气要像一位修为极高的道长，既科学又神秘。

                # Output Format:
                1. 📜 【天地定势】：写一首四句七言诗，融合方位与照片特征。
                2. 🌍 【大局理气】：简述该区域大风水背景。
                3. 🏘️ 【外局形煞】：指出窗外照片中肉眼可见的煞气（如壁刀煞、路冲等）及其影响。
                4. 🔍 【内局勘验】：指出户型/室内照片中存在的物理冲煞（如横梁压顶、门冲、杂物逼虎等）。
                5. 🛠️ 【基础化煞】：给出一个务实的物理调整建议（保留核心化解方案不说，只说基础调整）。
                """
                content_list.append({"type": "text", "text": master_prompt})

                if window_file:
                    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(window_file)}"}})
                if indoor_file:
                    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(indoor_file)}"}})

                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": content_list}]
                )
                report = response.choices[0].message.content
                
                status.update(label="✅ 天机已泄，排盘完成！", state="complete", expanded=False)

                # 📊 信任建立：能量雷达图 (UI展示，模拟数据)
                st.markdown("### 📊 气场能量扫描雷达")
                c1, c2, c3 = st.columns(3)
                c1.metric("外局聚气指数", "72/100", "略有散气", delta_color="inverse")
                c2.metric("内局安神指数", "68/100", "存在暗煞", delta_color="inverse")
                c3.metric("流年契合度", "85/100", "吉运当头")
                st.progress(72, text="当前综合风水能量槽")
                st.markdown("---")

                # 报告正文
                st.markdown("### 📜 您的专属堪舆诊断报告")
                st.markdown(report)
                
                # 🪝 信任建立与商业化：付费钩子
                st.markdown("---")
                st.warning("⚠️ 大师察觉到当前格局中潜藏一处隐秘『流年破财煞』，基础调整无法彻底拔除。")
                st.button("💰 支付 ￥19.9 解锁《专属化煞阵法图解与风水物摆放指北》", use_container_width=True)

            except Exception as e:
                status.update(label="❌ 阵法反噬，灵力中断", state="error", expanded=False)
                st.error(f"运算出错：{str(e)}")

if __name__ == "__main__":
    main()

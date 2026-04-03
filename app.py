import streamlit as st
import base64
from openai import OpenAI
import time
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 =================
st.set_page_config(page_title="赛博堪舆大师 | 禅意全息风水", page_icon="🌿", layout="centered")

# ================= 🎨 视觉升级：新中式禅意风 CSS =================
st.markdown("""
<style>
    /* 全局背景：宣纸米白，文字：沉稳墨黑 */
    .stApp {
        background-color: #F9F6F0;
        color: #333333;
    }
    /* 所有的标题强制变为深青灰色，带点宋体的雅致 */
    h1, h2, h3, h4, h5, h6 {
        color: #2C3E50 !important;
        font-family: 'Songti SC', 'STSong', 'KaiTi', serif;
    }
    /* 修复输入框提示文字 */
    label {
        color: #555555 !important;
        font-weight: 500 !important;
        font-size: 15px !important;
    }
    /* 主按钮：温润的玉绿色，去掉阴影的攻击性 */
    .stButton>button[kind="primary"] {
        background-color: #5F8B7D;
        color: white;
        border: none;
        border-radius: 6px;
        transition: all 0.3s ease;
        font-weight: 500;
        letter-spacing: 2px;
    }
    .stButton>button[kind="primary"]:hover {
        background-color: #4A6E62;
        box-shadow: 0 4px 12px rgba(95, 139, 125, 0.3);
    }
    /* 进度条变成玉色 */
    .stProgress > div > div > div > div {
        background-color: #5F8B7D;
    }
    /* 分割线变柔和的灰色 */
    hr {
        border-bottom-color: #D3CDC1;
        opacity: 0.6;
    }
    /* 普通信息框样式调整，使其更素雅 */
    .stAlert {
        background-color: #FFFFFF;
        border: 1px solid #EBE6DF;
        color: #333333;
    }
</style>
""", unsafe_allow_html=True)

# ================= 辅助函数 =================
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

# ================= 核心逻辑 =================
def main():
    st.title("🌿 赛博堪舆：天地人全息大阵")
    st.markdown("---")

    # ================= 🔑 密钥保密获取逻辑 =================
    api_key = ""
    try:
        api_key = st.secrets["GOOGLE_API_KEY"]
        has_secret = True
    except (FileNotFoundError, KeyError):
        has_secret = False

    with st.sidebar:
        st.header("⚙️ 引擎配置")
        if has_secret:
            st.success("🔒 禅心灵力已接入")
        else:
            st.warning("未检测到云端密钥")
            api_key = st.text_input("Google API Key:", type="password")
            
        model_choice = st.selectbox("选择推演引擎:", ["gemini-2.5-flash", "gemini-2.5-pro"])

    # ================= 1. 获取外局 =================
    st.subheader("📍 壹 · 外局寻龙 (天地人三盘)")
    st.write("GPS定大局，肉眼看小局。请补充信息：")
    
    location = streamlit_geolocation()
    geo_context = ""

    if location['latitude'] is not None and location['longitude'] is not None:
        lat = location['latitude']
        lon = location['longitude']
        st.success(f"✅ 定位成功：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"

    city_district = st.text_input("🌍 大外局 (5公里)：所在城市与区县 (例: 广州天河)")
    local_landmark = st.text_input("🏙️ 中外局 (500米)：小区名或附近水系 (例: 珠江帝景/临江)")
    micro_env = st.text_input("🏘️ 小外局 (50米)：窗外肉眼所见 (例: 有高架桥/尖角)")

    if city_district: geo_context += f"大外局信息：{city_district}。\n"
    if local_landmark: geo_context += f"中外局信息：{local_landmark}。\n"
    if micro_env: geo_context += f"小外局描述：{micro_env}。\n"

    st.markdown("---")

    # ================= 2. 获取图像 =================
    st.subheader("📸 贰 · 全息观形 (上传环境法相)")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**📸 窗外景观 (看小外局)**")
        window_file = st.file_uploader("拍摄窗外环境", type=["jpg", "png"], key="win")
        if window_file: st.image(window_file, use_container_width=True)

    with col2:
        st.markdown("**📜 户型/内局 (看形峦)**")
        indoor_file = st.file_uploader("上传户型或核心房间", type=["jpg", "png"], key="in")
        if indoor_file: st.image(indoor_file, use_container_width=True)

    st.markdown("---")

    # ================= 3. 核心引擎与带货逻辑 =================
    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key:
            st.error("⚠️ 灵力源未接入！")
            return
        if not window_file and not indoor_file:
            st.error("⚠️ 请至少上传一张环境照片。")
            return

        with st.status("🌿 沟通天地，正在静心推演...", expanded=True) as status:
            st.write("📡 勘测经纬气场...")
            time.sleep(1.0)
            st.write("🧭 飞星排盘，推演流年...")
            time.sleep(1.0)
            st.write("👁️ 扫描形峦冲煞...")

            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                
                content_list = []
                # 【修改点】要求大模型必须推荐具体的风水摆件，为带货做铺垫
                master_prompt = f"""
                # Role: 新中式禅意风水大师
                你精通形峦与理气，擅长结合照片进行风水诊断。语气温和、充满禅意、科学客观。

                # Input:
                环境描述：{geo_context if geo_context else '仅依赖照片。'}

                # Output Format:
                1. 📜 【禅语定势】：写一首四句七言诗，点出当前格局。
                2. 🌍 【气场分析】：综合大局与中局，分析宏观运势。
                3. 🔍 【形峦诊断】：指出照片中存在的1-2处核心风水问题（如路冲、横梁、逼虎）。
                4. 🛠️ 【改运良方】：给出不花钱的物理调整建议（如挪动桌子、清理杂物）。
                5. 🔮 【法器化解】：明确指出如果要彻底化煞或催旺，需要购买什么具体的风水物件（如：天然紫水晶洞、纯铜五帝钱、黑曜石七星阵等），说明其化煞原理。
                """
                content_list.append({"type": "text", "text": master_prompt})

                if window_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(window_file)}"}})
                if indoor_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(indoor_file)}"}})

                response = client.chat.completions.create(
                    model=model_choice,
                    messages=[{"role": "user", "content": content_list}]
                )
                report = response.choices[0].message.content
                
                status.update(label="✅ 堪舆完成，请阅览报告。", state="complete", expanded=False)

                st.markdown("### 📊 气场能量扫描雷达")
                c1, c2, c3 = st.columns(3)
                c1.metric("外局聚气指数", "72/100", "-5 略有散气")
                c2.metric("内局安神指数", "68/100", "-12 存在暗煞")
                c3.metric("流年契合度", "85/100", "+8 吉运当头")
                st.progress(72, text="当前综合风水能量槽")
                st.markdown("---")

                st.markdown("### 📜 您的专属堪舆诊断报告")
                st.markdown(report)
                
                # ================= 🪝 终极带货组件 =================
                st.markdown("---")
                st.markdown("### 🎐 大师甄选 · 改运法器")
                st.info("基于上述《法器化解》方案，大师为您匹配了以下结缘好物，点击即可奉请：")
                
                shop_col1, shop_col2 = st.columns(2)
                with shop_col1:
                    # 未来这里可以将 href 换成你抖音/淘宝的真实链接
                    st.markdown("""
                    <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #EBE6DF; text-align:center;">
                        <h4 style="margin-top:0;">🔮 天然黑曜石七星阵</h4>
                        <p style="color:#666; font-size:14px;">化解门冲煞 / 镇宅辟邪 / 稳固磁场</p>
                        <p style="color:#B84B4B; font-weight:bold;">结缘价: ¥168</p>
                        <a href="https://taobao.com" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#5F8B7D; color:white; border:none; padding:8px 15px; border-radius:4px; cursor:pointer; width:100%;">前往奉请 ➔</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with shop_col2:
                    st.markdown("""
                    <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #EBE6DF; text-align:center;">
                        <h4 style="margin-top:0;">🪙 纯黄铜开光五帝钱</h4>
                        <p style="color:#666; font-size:14px;">化解横梁压顶 / 催旺偏财 / 挡灾</p>
                        <p style="color:#B84B4B; font-weight:bold;">结缘价: ¥88</p>
                        <a href="https://taobao.com" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#5F8B7D; color:white; border:none; padding:8px 15px; border-radius:4px; cursor:pointer; width:100%;">前往奉请 ➔</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                status.update(label="❌ 推演中断，请检查网络或图片", state="error", expanded=False)
                st.error(f"运算出错：{str(e)}")

if __name__ == "__main__":
    main()

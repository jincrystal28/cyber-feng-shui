import streamlit as st
import base64
from openai import OpenAI
import time
import requests
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 =================
st.set_page_config(page_title="赛博堪舆大师 | 禅意全息风水", page_icon="🌿", layout="centered")

# ================= 🎨 视觉升级：新中式禅意风 CSS =================
st.markdown("""
<style>
    .stApp { background-color: #F9F6F0; color: #333333; }
    h1, h2, h3, h4, h5, h6 { color: #2C3E50 !important; font-family: 'Songti SC', 'STSong', 'KaiTi', serif; }
    label { color: #555555 !important; font-weight: 500 !important; font-size: 15px !important; }
    .stButton>button[kind="primary"] { background-color: #5F8B7D; color: white; border: none; border-radius: 6px; transition: all 0.3s ease; font-weight: 500; letter-spacing: 2px; }
    .stButton>button[kind="primary"]:hover { background-color: #4A6E62; box-shadow: 0 4px 12px rgba(95, 139, 125, 0.3); }
    .stProgress > div > div > div > div { background-color: #5F8B7D; }
    hr { border-bottom-color: #D3CDC1; opacity: 0.6; }
</style>
""", unsafe_allow_html=True)

# ================= 辅助函数与地理雷达 =================
def encode_image(uploaded_file):
    return base64.b64encode(uploaded_file.getvalue()).decode('utf-8')

def scan_nearby_fengshui_pois(lat, lon, radius=500):
    """免费调用 OSM API，扫描方圆 500 米内的风水关键设施"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json];
    (
      node["amenity"~"hospital|clinic|police|bank|courthouse|marketplace"](around:{radius},{lat},{lon});
      node["waterway"](around:{radius},{lat},{lon});
      node["natural"~"water|wood"](around:{radius},{lat},{lon});
    );
    out center;
    """
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, timeout=5)
        data = response.json()
        
        pois = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', '未知设施')
            amenity = tags.get('amenity', '')
            waterway = tags.get('waterway', '')
            natural = tags.get('natural', '')
            
            if amenity in ['hospital', 'clinic']: pois.append(f"{name} (偏阴)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name} (极阳)")
            elif amenity == 'bank': pois.append(f"{name} (聚财)")
            elif amenity == 'marketplace': pois.append(f"{name} (动处聚气)")
            elif waterway or natural == 'water': pois.append(f"自然水系 (界水止气)")
            elif natural == 'wood': pois.append(f"公园林地 (生发生气)")
            
        return list(set(pois))[:8] # 最多返回8个关键点
    except Exception:
        return []

# ================= 核心逻辑 =================
def main():
    st.title("🌿 赛博堪舆：天地人全息大阵")
    st.markdown("---")

    # 密钥获取逻辑
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
            api_key = st.text_input("Google API Key:", type="password")
            st.warning("未检测到云端密钥")
        model_choice = st.selectbox("推演引擎:", ["gemini-2.5-flash", "gemini-2.5-pro"])

    # ================= 1. 获取外局 =================
    st.subheader("📍 壹 · 外局寻龙 (地理雷达)")
    st.write("点击定位，系统将自动检索周边 500 米地脉设施：")
    
    location = streamlit_geolocation()
    geo_context = ""

    if location['latitude'] is not None and location['longitude'] is not None:
        lat = location['latitude']
        lon = location['longitude']
        st.success(f"✅ 定位成功：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"
        
        # 触发雷达扫描
        with st.spinner("📡 正在启动玄学雷达，扫描方圆 500 米地脉..."):
            nearby_pois = scan_nearby_fengshui_pois(lat, lon)
            if nearby_pois:
                st.info("🗺️ **雷达探明周边气场节点：**\n" + "、".join(nearby_pois))
                geo_context += f"【系统自动探测中外局】：{', '.join(nearby_pois)}。\n"
            else:
                st.write("未能自动扫描到特殊气场节点。")

    st.write("如有遗漏，可手动补充：")
    micro_env = st.text_input("🏘️ 窗外肉眼所见 (例: 有高架桥/尖角/电线杆)")
    if micro_env: geo_context += f"小外局描述：{micro_env}。\n"

    st.markdown("---")

    # ================= 2. 获取图像 =================
    st.subheader("📸 贰 · 全息观形 (实景法相)")
    
    col1, col2 = st.columns(2)
    with col1:
        window_file = st.file_uploader("📸 拍摄窗外环境", type=["jpg", "png"], key="win")
        if window_file: st.image(window_file, use_container_width=True)
    with col2:
        indoor_file = st.file_uploader("📜 上传户型或房间内景", type=["jpg", "png"], key="in")
        if indoor_file: st.image(indoor_file, use_container_width=True)

    st.markdown("---")

    # ================= 3. 核心引擎与变现逻辑 =================
    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key: st.error("⚠️ 灵力源未接入！"); return
        if not window_file and not indoor_file: st.error("⚠️ 请至少上传一张环境照片。"); return

        with st.status("🌿 沟通天地，正在静心推演...", expanded=True) as status:
            st.write("📡 融合雷达数据，比对玄空飞星...")
            time.sleep(1.0)
            st.write("👁️ 扫描形峦冲煞，锁定能量漏点...")

            try:
                client = OpenAI(
                    api_key=api_key,
                    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
                )
                
                # 【修改点】要求大模型“留一手”，绝对不可以说出破解之法
                master_prompt = f"""
                # Role: 新中式禅意风水大师
                你精通形峦与理气。语气温和、充满禅意、科学客观。

                # Input:
                环境描述与雷达数据：{geo_context if geo_context else '无坐标数据，依赖照片。'}

                # Output Format:
                1. 📜 【禅语定势】：写一首四句七言诗，点出当前格局。
                2. 🌍 【气场分析】：结合雷达数据(如果有)或地理常识，分析宏观运势。
                3. 🔍 【形峦诊断】：指出照片中存在的核心风水隐患（如路冲、横梁、煞气）。
                4. ⚠️ 【天机预警】：**这是重点！** 严肃地指出该煞气如果不化解，可能对财运或健康产生什么具体的不良影响。然后说一句：“然天地有好生之德，万物皆有相生相克之理，若需破局，需辅以特定之法门。” —— **绝对不要在回答中给出任何化解方案或建议买什么东西！在此处停止。**
                """
                content_list = [{"type": "text", "text": master_prompt}]

                if window_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(window_file)}"}})
                if indoor_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(indoor_file)}"}})

                response = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": content_list}])
                report = response.choices[0].message.content
                
                status.update(label="✅ 堪舆完成，请阅览诊断。", state="complete", expanded=False)

                st.markdown("### 📜 专属堪舆诊断（免费基础版）")
                st.markdown(report)
                
                # ================= 🪝 知识付费钩子 (4.99元) =================
                st.markdown("---")
                st.warning("⚠️ 命理有云：知命而不改命，犹如无锚之舟。由于检测到核心煞气，需专属化解之法。")
                st.button("💰 支付 ￥4.99 解锁《专属化煞阵法与空间调理真诀》", use_container_width=True)
                
                # ================= 🛒 隐形平价带货 =================
                st.markdown("<br><br>", unsafe_allow_html=True)
                st.markdown("### 🎐 日常调理 · 平价风水小件")
                st.caption("大师建议：化煞不必铺张，大道至简。日常在办公桌或门后添置一些低调小件，亦能潜移默化改善磁场。")
                
                shop_col1, shop_col2 = st.columns(2)
                with shop_col1:
                    st.markdown("""
                    <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #EBE6DF; text-align:center;">
                        <h4 style="margin-top:0; color:#4A6E62;">🌱 桌面水培好养绿植</h4>
                        <p style="color:#666; font-size:13px;">木气生发 / 挡尖角煞 / 吸纳浊气</p>
                        <p style="color:#B84B4B; font-weight:bold;">结缘价: ¥9.90</p>
                        <a href="https://taobao.com" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#F0EBE1; color:#333; border:1px solid #D3CDC1; padding:6px 12px; border-radius:4px; cursor:pointer; width:100%;">查看详情</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                    
                with shop_col2:
                    st.markdown("""
                    <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #EBE6DF; text-align:center;">
                        <h4 style="margin-top:0; color:#4A6E62;">葫 小巧纯铜实心葫芦</h4>
                        <p style="color:#666; font-size:13px;">收邪化病 / 挂于门后 / 隐蔽不显眼</p>
                        <p style="color:#B84B4B; font-weight:bold;">结缘价: ¥12.80</p>
                        <a href="https://taobao.com" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#F0EBE1; color:#333; border:1px solid #D3CDC1; padding:6px 12px; border-radius:4px; cursor:pointer; width:100%;">查看详情</button>
                        </a>
                    </div>
                    """, unsafe_allow_html=True)

            except Exception as e:
                status.update(label="❌ 推演中断，请检查网络或图片", state="error", expanded=False)
                st.error(f"运算出错：{str(e)}")

if __name__ == "__main__":
    main()

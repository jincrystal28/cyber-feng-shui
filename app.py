import streamlit as st
import base64
from openai import OpenAI
import time
import requests
import random
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

# 【记忆魔法】：避免重复请求导致被封，记住坐标 1 小时
@st.cache_data(ttl=3600, show_spinner=False)
def scan_nearby_fengshui_pois(lat, lon, radius=1000):
    """全方位侦测：涵盖建筑、山、水、路、村落"""
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:20];
    (
      nwr["amenity"](around:{radius},{lat},{lon});
      nwr["building"~"."]["name"](around:{radius},{lat},{lon});
      nwr["highway"~"motorway|trunk|primary|secondary"](around:{radius},{lat},{lon});
      nwr["waterway"](around:{radius},{lat},{lon});
      nwr["natural"~"water|peak|hill|wood"](around:{radius},{lat},{lon});
      nwr["place"~"village|town|neighbourhood"](around:{radius},{lat},{lon});
    );
    out tags center;
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberFengShui/2.0'}
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=12)
        data = response.json()
        pois = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', '')
            amenity = tags.get('amenity', '')
            natural = tags.get('natural', '')
            highway = tags.get('highway', '')
            place = tags.get('place', '')
            
            if not name:
                if highway: name = "主干道/虚水"
                elif natural in ['peak', 'hill']: name = "地脉隆起(山)"
                elif place: name = "人丁聚落"
                else: continue
                
            if amenity in ['hospital', 'clinic']: pois.append(f"{name}(医疗/偏阴)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name}(官威/极阳)")
            elif amenity == 'bank': pois.append(f"{name}(金融/聚财)")
            elif amenity == 'school': pois.append(f"{name}(文昌/青少之气)")
            elif natural == 'water' or tags.get('waterway'): pois.append(f"{name}(真水/界气)")
            elif natural in ['peak', 'hill']: pois.append(f"{name}(实山/靠山)")
            elif highway: pois.append(f"{name}(虚水流转)")
            elif place: pois.append(f"{name}(聚气村落)")
            else: pois.append(f"{name}(地标建筑)")
            
        return list(set(pois))[:15]
    except Exception:
        return []

# ================= 核心逻辑 =================
def main():
    st.title("🌿 赛博堪舆：全息地脉推演系统")
    st.markdown("---")

    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    with st.sidebar:
        st.header("⚙️ 引擎配置")
        if not api_key:
            api_key = st.text_input("Google API Key:", type="password")
        else:
            st.success("🔒 禅心灵力已接入")
        model_choice = st.selectbox("推演引擎:", ["gemini-2.5-flash", "gemini-2.5-pro"])
        if st.button("🔄 刷新地脉雷达记忆"):
            st.cache_data.clear()
            st.rerun()

    # ================= 1. 获取外局 =================
    st.subheader("📍 壹 · 地脉寻龙")
    location = streamlit_geolocation()
    geo_context = ""
    radar_placeholder = st.empty()

    if location['latitude'] is not None and location['longitude'] is not None:
        lat, lon = location['latitude'], location['longitude']
        st.success(f"✅ 坐标锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：{lat}, {lon}。\n"
        
        nearby_pois = scan_nearby_fengshui_pois(lat, lon)
        if nearby_pois:
            radar_placeholder.info("🗺️ **雷达探明周边气场：**\n" + "、".join(nearby_pois))
            geo_context += f"【雷达探测1000米环境】：{', '.join(nearby_pois)}。\n"
        else:
            radar_placeholder.warning("⚠️ **雷达监控：** 未探测到显赫地标，此地气场较平淡。")

    micro_env = st.text_input("🏘️ 补充描述 (例: 窗外有高压线/正对丁字路口)")
    if micro_env: geo_context += f"小外局补充：{micro_env}。\n"

    st.markdown("---")
    
    # ================= 2. 获取图像 (多图上传) =================
    st.subheader("📸 贰 · 全息观形")
    col1, col2 = st.columns(2)
    with col1: win_files = st.file_uploader("📸 窗外景观 (多张)", accept_multiple_files=True, key="win")
    with col2: in_files = st.file_uploader("📜 室内多角 (多张)", accept_multiple_files=True, key="in")

    total_files = len(win_files) + len(in_files)
    st.markdown("---")

    # ================= 3. 推演逻辑 =================
    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key: st.error("请配置 API Key"); return
        if total_files == 0: st.error("大师需要法相照片"); return

        with st.status("🔮 正在开启全息风水阵...", expanded=True) as status:
            st.write("📡 融合地脉雷达数据...")
            time.sleep(1.0)
            st.write("👁️ 视觉天眼扫描形峦细节...")
            time.sleep(1.0)
            status.update(label="✅ 卦象已成，正在宣说...", state="complete", expanded=False)

        st.markdown("### 📜 专属堪舆诊断报告")
        report_placeholder = st.empty()
        full_report = ""

        try:
            client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            
            master_prompt = f"""
            # Role: 首席堪舆宗师 (结合环境心理学与断舍离)
            你必须极其客观、先扬后抑。严禁在文中出现“先扬”、“后抑”等程序化词汇。
            字数要求：不少于 1000 字，要求逻辑缜密、引经据典、充满人文关怀。

            # Input Context:
            {geo_context}

            # Output Structure:
            1. 📜 【禅语定势】：写一首具有画面感的七言诗。
            2. 🌟 【地脉优势勘验】：详细分析雷达数据中的道路、水系、建筑、山峦带来的吉利气场。告诉用户为什么这里的底色是好的。
            3. ⚠️ 【形峦隐患点拨】：犀利指出雷达数据或照片中的隐患（如铁龙脉震动、电线杆煞）。结合环境心理学，解释其如何导致焦虑、决策失误或健康损耗。
            4. 🧹 【大道至简 · 扫洒除尘】：
               - 必须针对用户照片中的具体细节（如乱线、灰尘、杂物、枯枝）。
               - 给出 1 个完全免费的整理建议。
               - 详细解释：为什么“窗明几净”能平复磁场。
            5. 🔮 【破局之机】：总结治本之道。预留法器化解的悬念，严禁说出具体物品。
            """
            
            content_list = [{"type": "text", "text": master_prompt}]
            for f in win_files + in_files:
                content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(f)}"}})

            response = client.chat.completions.create(
                model=model_choice, 
                messages=[{"role": "user", "content": content_list}],
                stream=True
            )
            
            for chunk in response:
                if chunk.choices[0].delta.content:
                    full_report += chunk.choices[0].delta.content
                    report_placeholder.markdown(full_report + "▌")
            report_placeholder.markdown(full_report)
            
            # ================= 4. 带货逻辑 (动态 2+1) =================
            st.markdown("---")
            st.warning("⚠️ 破解之道：知易行难。由于格局复杂，需精确法器引导气场。")
            st.button("💰 支付 ￥4.99 解锁《全息方位调理图解》", use_container_width=True)
            
            st.markdown("### 🏮 大师阵眼 · 灵药图鉴")
            mundane = [
                {"name": "🪨 天然溪水鹅卵石", "kw": "天然 鹅卵石 摆件", "place": "窗台或青龙位", "why": "土生金，镇定火煞。"},
                {"name": "☕ 纯白陶瓷水杯", "kw": "白色 陶瓷杯 简约", "place": "工位明堂", "why": "金水相生，平复燥气。"},
                {"name": "🌱 桌面开运小绿植", "kw": "水培 绿萝 桌面", "place": "电脑左侧", "why": "木气生发，化解电子死气。"},
                {"name": "📏 工业加厚金属尺", "kw": "不锈钢 直尺", "place": "杂物堆旁", "why": "庚金截流，快刀斩乱麻。"},
                {"name": "🏮 暖色调小台灯", "kw": "暖色 氛围灯", "place": "阴暗角落", "why": "离火补阳，驱散阴寒。"}
            ]
            pros = [
                {"name": "葫 纯铜实心小葫芦", "kw": "纯铜 葫芦 挂件", "place": "门把手或窗前", "why": "吸纳病气口舌。"},
                {"name": "🪙 仿古纯铜五帝钱", "kw": "五帝钱 挂件 纯铜", "place": "入户门下", "why": "极阳金气，挡路冲。"},
                {"name": "🦁 纯铜镇宅小貔貅", "kw": "纯铜 貔貅 摆件", "place": "头朝外窗角", "why": "瑞兽守财，挡尖角。"}
            ]
            
            final_items = random.sample(mundane, 2) + random.sample(pros, 1)
            random.shuffle(final_items)
            
            cols = st.columns(3)
            for idx, item in enumerate(final_items):
                with cols[idx]:
                    url = f"https://s.taobao.com/search?q={item['kw']}"
                    st.markdown(f"""
                    <div style="background-color:white; padding:12px; border-radius:8px; border:1px solid #EBE6DF; text-align:center; height:100%;">
                        <h5 style="margin:0; color:#5F8B7D;">{item['name']}</h5>
                        <p style="color:#666; font-size:12px; margin:5px 0;">📍{item['place']}<br>☯️{item['why']}</p>
                        <a href="{url}" target="_blank"><button style="background-color:#F9F6F0; color:#4A6E62; border:1px solid #5F8B7D; width:100%; border-radius:4px; cursor:pointer;">🔍 寻觅</button></a>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

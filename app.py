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

@st.cache_data(ttl=3600, show_spinner=False)
def scan_nearby_fengshui_pois(lat, lon, radius=1000):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:15];
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
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
        if not api_key: api_key = st.text_input("Google API Key:", type="password")
        else: st.success("🔒 禅心灵力已接入")
        model_choice = st.selectbox("推演引擎:", ["gemini-2.5-flash", "gemini-2.5-pro"])
        if st.button("🔄 刷新地脉雷达记忆"):
            st.cache_data.clear()
            st.rerun()

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
            geo_context += f"【雷达探测环境】：{', '.join(nearby_pois)}。\n"
        else:
            radar_placeholder.warning("⚠️ 未探测到显赫地标，此地气场较平淡。")

    micro_env = st.text_input("🏘️ 补充描述 (例: 窗外有高压线)")
    if micro_env: geo_context += f"小外局补充：{micro_env}。\n"

    st.markdown("---")
    st.subheader("📸 贰 · 全息观形 (支持多图与户型图)")
    col1, col2 = st.columns(2)
    with col1: win_files = st.file_uploader("📸 窗外景观 (可多张)", accept_multiple_files=True, key="win")
    with col2: in_files = st.file_uploader("📜 室内实景或户型图", accept_multiple_files=True, key="in")

    total_files = len(win_files) + len(in_files)
    st.markdown("---")

    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key: st.error("请配置 API Key"); return
        if total_files == 0: st.error("大师需要法相照片"); return

        with st.status("🔮 正在开启全息风水阵...", expanded=True) as status:
            st.write("📡 融合地脉雷达数据...")
            time.sleep(1.0)
            st.write("👁️ 识别实景与户型格局...")
            time.sleep(1.0)
            status.update(label="✅ 卦象已成，正在宣说...", state="complete", expanded=False)

        st.markdown("### 📜 专属堪舆诊断报告")
        report_placeholder = st.empty()
        full_report = ""

        try:
            client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            
            # 【重大升级】：户型图分流逻辑 + 顺势调理
            master_prompt = f"""
            # Role: 首席堪舆宗师 (精通户型风水、环境心理学)
            你的诊断必须中正客观，排版清晰。严禁在文中出现程序化提示词。

            # Input Context:
            1. 地脉雷达信息：\n{geo_context}
            2. 用户上传的照片（可能包含户型设计图，也可能是室内实景照片）。

            # Output Structure (总字数不少于1000字):
            1. 📜 【禅语定势】：写一首具有画面感的七言诗。
            2. 🌟 【地脉优势勘验】：详细分析雷达数据带来的吉利气场。
            3. ⚠️ 【形峦隐患点拨】：
               - 重点分流：仔细观察图片！如果是【户型平面图】，请必须指出布局硬伤（如：门对门、缺角、卫生间居中、穿堂煞等）；如果是【室内实景图】，指出形峦冲煞或压迫感。
               - 结合环境心理学解释其负面影响。
            4. 🛋️ 【大道至简 · 顺势调理】（免费化解法）：
               - 严禁一直建议打扫卫生！
               - 必须给出物理空间布局的调整建议：例如，建议调整床的朝向、把书桌移开窗户、在某处挂一个门帘挡煞、或者挪动某个遮挡光线的柜子。
               - 详细解释：这样物理挪动后，是如何改变了室内的气场流向（风道与光影）。
            5. 🔮 【治本之道 · 预警】：
               - 总结：物理布局调整能缓解表层冲撞。
               - 抛出诱饵：然若要彻底化解此局，需布下贫道推演的【专属阵法】。此阵需借金木水火土三位法器，分别镇守阵眼……（在此处停止，绝不说出具体法器，留下极强的付费悬念）。
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
            
            # ================= 变现钩子 =================
            st.markdown("---")
            st.warning("⚠️ 免费推演至此结束。破解之道，在乎法器引气布阵。")
            st.button("💰 支付 ￥4.99 解锁《治本之道：专属化煞聚气阵法》", use_container_width=True)
            
            # ================= 交付感拉满：阵法包装 =================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为模拟用户支付 4.99 元后解锁的【高级阵法界面】 ⬇️</p>", unsafe_allow_html=True)
            
            # 动态生成阵法名称
            array_names = ["紫气东来纳福阵", "五行斗转星移阵", "太极两仪化煞阵", "九宫飞星旺财阵", "八卦锁幽凝神阵"]
            selected_array = random.choice(array_names)
            
            st.markdown(f"### 🏆 治本之道：【{selected_array}】")
            st.markdown("""
            > **大师法旨**：此阵法专为您当前的格局所创。以主法器镇压核心凶位，辅以日常五行之物催化气场流转。三件物品缺一不可，请依图位悉心布置。
            """)
            
            mundane = [
                {"name": "🪨 天然溪水鹅卵石", "kw": "天然 鹅卵石 摆件", "role": "阵法催化", "place": "窗台或青龙位", "why": "土生金，吸收尖锐火煞。"},
                {"name": "☕ 纯白陶瓷水杯", "kw": "白色 陶瓷杯 简约", "role": "辅阵之眼", "place": "工位正前方明堂", "why": "金水相生，平复燥气。"},
                {"name": "🌱 桌面水培小绿植", "kw": "水培 绿萝 桌面", "role": "辅阵之眼", "place": "电脑左侧或财位", "why": "木气生发，盘活死气。"},
                {"name": "📏 工业加厚金属尺", "kw": "不锈钢 直尺", "role": "阵法催化", "place": "凌乱区域压阵", "why": "庚金截流，斩断杂乱木煞。"},
                {"name": "🏮 暖色调小台灯", "kw": "暖色 氛围灯", "place": "阴暗角落", "role": "辅阵之眼", "why": "离火补阳，驱散阴寒。"}
            ]
            pros = [
                {"name": "葫 纯铜实心小葫芦", "kw": "纯铜 葫芦 挂件", "role": "核心主阵眼", "place": "煞气直冲的门把手或窗前", "why": "泄土煞，强力吸纳病气与冲撞。"},
                {"name": "🪙 仿古纯铜五帝钱", "kw": "五帝钱 挂件 纯铜", "role": "核心主阵眼", "place": "入户门地垫下或横梁下方", "why": "前朝极阳金气，挡外来路冲。"},
                {"name": "🦁 纯铜镇宅小貔貅", "kw": "纯铜 貔貅 摆件", "role": "核心主阵眼", "place": "头朝窗外放置于煞气位", "why": "上古瑞兽，镇守财库，吞噬凶煞。"}
            ]
            
            # 选取 1个主阵眼 + 2个辅阵/催化
            main_core = random.sample(pros, 1)
            aux_cores = random.sample(mundane, 2)
            final_items = main_core + aux_cores
            
            cols = st.columns(3)
            for idx, item in enumerate(final_items):
                with cols[idx]:
                    url = f"https://s.taobao.com/search?q={item['kw']}"
                    # 用深浅不一的背景色区分主阵眼和辅阵眼，增加高级感
                    bg_color = "#EDF2F0" if item["role"] == "核心主阵眼" else "#FFFFFF"
                    border_color = "#4A6E62" if item["role"] == "核心主阵眼" else "#EBE6DF"
                    
                    st.markdown(f"""
                    <div style="background-color:{bg_color}; padding:15px; border-radius:8px; border:2px solid {border_color}; text-align:center; height:100%;">
                        <span style="background-color:#4A6E62; color:white; padding:2px 8px; border-radius:12px; font-size:11px;">{item['role']}</span>
                        <h4 style="margin:10px 0 5px 0; color:#2C3E50;">{item['name']}</h4>
                        <div style="text-align:left; background:rgba(255,255,255,0.6); padding:8px; border-radius:4px; margin-bottom:10px;">
                            <p style="color:#555; font-size:12px; margin:0 0 5px 0;"><b>📍 定位：</b>{item['place']}</p>
                            <p style="color:#884A4A; font-size:12px; margin:0;"><b>☯️ 效用：</b>{item['why']}</p>
                        </div>
                        <a href="{url}" target="_blank"><button style="background-color:#2C3E50; color:#D4AF37; border:none; width:100%; padding:8px; border-radius:4px; cursor:pointer; font-weight:bold;">奉请法器 ➔</button></a>
                    </div>
                    """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

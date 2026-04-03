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
def scan_nearby_fengshui_pois(lat, lon, radius=500):
    overpass_url = "http://overpass-api.de/api/interpreter"
    overpass_query = f"""
    [out:json][timeout:10];
    (
      nwr["amenity"~"hospital|clinic|police|bank|courthouse|marketplace|school|place_of_worship"](around:{radius},{lat},{lon});
      nwr["waterway"](around:{radius},{lat},{lon});
      nwr["natural"~"water|wood|peak|ridge|hill"](around:{radius},{lat},{lon});
      nwr["highway"~"motorway|trunk|primary|secondary|residential"](around:{radius},{lat},{lon});
      nwr["railway"](around:{radius},{lat},{lon});
      nwr["place"~"village|hamlet|neighbourhood"](around:{radius},{lat},{lon});
    );
    out center;
    """
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) CyberFengShui/1.0'}
    try:
        response = requests.get(overpass_url, params={'data': overpass_query}, headers=headers, timeout=8)
        data = response.json()
        pois = []
        for element in data.get('elements', []):
            tags = element.get('tags', {})
            name = tags.get('name', '')
            amenity = tags.get('amenity', '')
            waterway = tags.get('waterway', '')
            natural = tags.get('natural', '')
            highway = tags.get('highway', '')
            railway = tags.get('railway', '')
            place = tags.get('place', '')
            
            if not name:
                if highway in ['motorway', 'trunk']: name = "城市快速路"
                elif highway in ['primary', 'secondary']: name = "主干道"
                elif highway == 'residential': name = "内部道路"
                elif railway: name = "铁轨干线"
                elif natural in ['peak', 'hill']: name = "无名山丘"
                elif waterway: name = "无名河流"
                else: continue
                
            if amenity in ['hospital', 'clinic']: pois.append(f"{name} (偏阴/病气)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name} (极阳/孤煞)")
            elif amenity == 'bank': pois.append(f"{name} (金旺/聚财)")
            elif amenity == 'marketplace': pois.append(f"{name} (动处/聚气)")
            elif amenity == 'school': pois.append(f"{name} (文昌/阳气旺)")
            elif waterway or natural == 'water': pois.append(f"{name} (真水/界水)")
            elif natural == 'wood': pois.append(f"{name} (林地/生气)")
            elif natural in ['peak', 'ridge', 'hill']: pois.append(f"{name} (实山/靠山)")
            elif highway in ['motorway', 'trunk']: pois.append(f"{name} (大虚水/气流急)")
            elif highway in ['primary', 'secondary']: pois.append(f"{name} (虚水干流)")
            elif railway: pois.append(f"{name} (铁龙脉/震动气场)")
            elif place in ['village', 'hamlet']: pois.append(f"{name} (村落/聚气)")
            
        return list(set(pois))[:12]
    except Exception as e:
        return []

# ================= 核心逻辑 =================
def main():
    st.title("🌿 赛博堪舆：天地人全息大阵")
    st.markdown("---")

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
        model_choice = st.selectbox("推演引擎:", ["gemini-2.5-flash", "gemini-2.5-pro"])

    st.subheader("📍 壹 · 外局寻龙 (含雷达监控)")
    location = streamlit_geolocation()
    geo_context = ""
    radar_placeholder = st.empty()

    if location['latitude'] is not None and location['longitude'] is not None:
        lat, lon = location['latitude'], location['longitude']
        st.success(f"✅ 坐标锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"
        with st.spinner("📡 正在启动玄学雷达，探测方圆 500 米..."):
            nearby_pois = scan_nearby_fengshui_pois(lat, lon)
            if nearby_pois:
                radar_placeholder.info("🗺️ **雷达探明气场节点：**\n" + "、".join(nearby_pois))
                geo_context += f"【系统探测到周边500米设施】：{', '.join(nearby_pois)}。\n"
            else:
                radar_placeholder.warning("⚠️ **雷达监控：** 方圆 500 米内未抓取到特殊建筑或主要道路。")
                geo_context += "【系统探测周边500米】：无特殊明显气场建筑。\n"

    micro_env = st.text_input("🏘️ 若雷达有遗漏，可手动补充 (例: 楼下十字路口/对面有变压器)")
    if micro_env: geo_context += f"小外局手动描述：{micro_env}。\n"

    st.markdown("---")
    
    st.subheader("📸 贰 · 全息观形 (支持多图上传)")
    st.write("大师建议：提供多角度照片（大门、卧室、窗外等），排盘更精准。")
    
    col1, col2 = st.columns(2)
    with col1: window_files = st.file_uploader("📸 拍摄窗外环境 (可多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="win")
    with col2: indoor_files = st.file_uploader("📜 上传室内多角度照片 (可多张)", type=["jpg", "png", "jpeg"], accept_multiple_files=True, key="in")

    total_files = len(window_files) + len(indoor_files)
    if total_files > 0:
        st.success(f"✅ 已成功录入 {total_files} 张法相，准备开启全方位勘验。")

    st.markdown("---")

    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key: st.error("⚠️ 灵力源未接入！"); return
        if total_files == 0: st.error("⚠️ 请至少上传一张环境照片。"); return

        # 1. 过场动画：滚动显示状态，但不把结果包裹在里面
        with st.status("🌿 开启全息风水阵，沟通天地...", expanded=True) as status:
            st.write("📡 正在融合地脉雷达数据...")
            time.sleep(1.2)
            st.write("🧭 正在排布九宫飞星，定位吉凶方位...")
            time.sleep(1.2)
            st.write("👁️ 视觉天眼已开启，正在扫描形峦特征...")
            time.sleep(1.0)
            status.update(label="✅ 风水气场演算完毕，正在输出卦象...", state="complete", expanded=False)

        # 2. 核心输出区：实时打字机流式输出 (Streaming)
        st.markdown("### 📜 专属堪舆诊断")
        
        # 创建一个空容器，用于一字一字地填入内容
        report_placeholder = st.empty()
        full_report = ""

        try:
            client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            
            # 【修改点】彻底删除了“先扬”、“后抑”等字眼，用优雅的词汇替代
            master_prompt = f"""
            # Role: 首席环境地理学与堪舆宗师 (精通环境心理学与断舍离美学)
            你的诊断必须中正客观，将传统理气与现代心理学融合。
            注意：请直接输出内容，不要在文中暴露诸如“先扬”、“后抑”、“缺点”等粗俗或程序性提示词，用优雅国风的词汇（如“气场优势”、“形峦隐患”）作为小标题。

            # Input Data:
            1. 地脉雷达信息：\n{geo_context}
            2. 用户上传的多角度现场照片。

            # Output Format (排版清晰，总字数不少于800字)：
            1. 📜 【禅语定势】：写一首四句七言诗，概括此地气场。
            2. 🌟 【气场优势勘验】：详细分析雷达数据中的道路、水系、建筑带来的“生机与聚气”吉相。用优美的国学语言让用户感到安心。
            3. ⚠️ 【形峦隐患点拨】：指出雷达或照片中的核心隐患。不仅用风水解释，必须结合“环境心理学”说明其对潜意识的负面影响。
            4. 🧹 【大道至简 · 扫洒除尘】（免费化解法）：
               - 严禁套用固定模板！必须死死盯住用户上传的照片，找出照片中真实存在的某个具体细节（例如：某处堆积的纸箱、乱绕的电线、脏玻璃等）。
               - 给出 1 个针对该具体细节的“完全免费的收纳、整理或卫生清洁”化解方案。
               - 解释原因：向用户解释“窗明几净、物有其位”本身就是最好的风水调理，清理此处能瞬间平复磁场。
            5. 🔮 【天机预警与破局之机】：
               - 总结：扫洒除尘乃治本之基。然若要对冲流年深层大煞，仅靠日常整理尚显不足。
               - 留白：“需辅以特定属性之物，布于特定阵眼……”（在此处停止，绝不说买什么）。
            """
            
            content_list = [{"type": "text", "text": master_prompt}]
            
            if window_files:
                for f in window_files:
                    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(f)}"}})
            if indoor_files:
                for f in indoor_files:
                    content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(f)}"}})

            # 【修改点】开启 stream=True，让 API 像流水一样返回数据
            response = client.chat.completions.create(
                model=model_choice, 
                messages=[{"role": "user", "content": content_list}],
                stream=True  # 开启流式输出
            )
            
            # 【修改点】打字机特效循环：每次拿到几个字，就立刻显示在屏幕上
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    full_report += chunk.choices[0].delta.content
                    # 加上一个小方块"▌"模拟光标闪烁
                    report_placeholder.markdown(full_report + "▌")
            
            # 输出完毕，去掉小光标
            report_placeholder.markdown(full_report)
            
            # ================= 变现钩子与灵药库 =================
            st.markdown("---")
            st.warning("⚠️ 破解之道：知易行难。需精确法器引导气场。")
            st.button("💰 支付 ￥4.99 解锁《全息调理方位图解与避坑真诀》", use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("### 🏮 大师阵眼 · 灵药图鉴")
            
            mundane_items = [
                {"name": "🪨 天然溪水鹅卵石", "keyword": "天然 鹅卵石 摆件", "placement": "正对煞气的窗台边缘，或办公桌青龙位。", "principle": "土生金。以天然艮土之气，吸收尖锐火煞，镇定磁场。"},
                {"name": "☕ 纯白哑光陶瓷杯", "keyword": "简约 纯白 陶瓷杯", "placement": "工位正前方，需注入八分满清水，每周一换。", "principle": "白色属金，杯中蓄水，形成“土生金生水”化煞局，专解燥热。"},
                {"name": "📏 工业级金属直尺", "keyword": "不锈钢 直尺 加厚", "placement": "压在桌面凌乱文件下，或键盘上方。", "principle": "庚金之气。以冷硬金属切断纠缠不清的杂乱木煞，提升决断力。"},
                {"name": "🌱 桌面水培富贵竹", "keyword": "水培富贵竹 桌面", "placement": "显示器左侧，或进门斜对角财位。", "principle": "活水养绿植，化解电子产品死气，盘活停滞运势。"},
                {"name": "🏮 暖色调小夜灯", "keyword": "暖色 氛围灯 桌面", "placement": "房间阴暗角落，或正北方玄武位。", "principle": "人造离火。补充缺角或采光不足的阴气，驱散冷硬气场。"},
                {"name": "🥣 透明玻璃浅碗", "keyword": "透明 玻璃碗 浅口", "placement": "靠近房门的玄关柜上，碗内可放硬币。", "principle": "玻璃属金水相合，形似微型水口，能兜住流出之财气。"}
            ]

            pro_items = [
                {"name": "葫 纯铜实心小葫芦", "keyword": "纯铜 葫芦 挂件", "placement": "悬挂于卧室门内把手，或正对冲煞的窗户。", "principle": "铜能泄土煞，葫芦肚大口小，能强力吸纳病气与口舌。"},
                {"name": "🪙 仿古纯铜五帝钱", "keyword": "纯铜 五帝钱 挂件", "placement": "贴于横梁下方，或入户门地垫之下。", "principle": "汇聚前朝极阳金气，专破上压与外冲，镇宅挡灾。"},
                {"name": "🪨 原矿黑曜石七星阵", "keyword": "黑曜石七星阵 天然", "placement": "办公桌右侧白虎位，或床头柜。", "principle": "极阴之石吸附力极强，七星阵放大磁场，专吃小人与负面焦虑。"},
                {"name": "🦁 纯铜镇宅小貔貅", "keyword": "纯铜 貔貅 摆件", "placement": "头朝窗外或门外放置于桌角。", "principle": "瑞兽以金气铸造，专克对面尖角煞与反弓路，镇守财库。"},
                {"name": "🔮 天然紫水晶碎石", "keyword": "紫水晶碎石 消磁", "placement": "装在小陶罐中，放床头或抽屉内。", "principle": "高频能量源。柔化交战气场，提升睡眠，暗催贵人运。"},
                {"name": "🪞 纯铜八卦凸镜", "keyword": "纯铜 八卦镜 凸镜", "placement": "仅限挂于室外，正对对面尖角或直路。", "principle": "凸镜如盾，先天八卦调配阴阳，将烈煞反射打散。"}
            ]

            selected_mundane = random.sample(mundane_items, 2)
            selected_pro = random.sample(pro_items, 1)
            final_items = selected_mundane + selected_pro
            random.shuffle(final_items)

            for item in final_items:
                search_url = f"https://s.taobao.com/search?q={item['keyword']}"
                st.markdown(f"""
                <div style="background-color:white; padding:15px; border-radius:8px; border:1px solid #EBE6DF; margin-bottom: 12px; display:flex; align-items:center; justify-content:space-between;">
                    <div style="flex:1; padding-right:15px;">
                        <h5 style="margin:0 0 8px 0; color:#4A6E62; font-size:16px;">{item['name']}</h5>
                        <div style="background:#F4F1EA; padding:8px 12px; border-radius:4px; margin-bottom:8px;">
                            <p style="margin:0 0 4px 0; font-size:13px; color:#555;"><b>📍 摆放阵眼：</b>{item['placement']}</p>
                            <p style="margin:0; font-size:13px; color:#884A4A;"><b>☯️ 运转原理：</b>{item['principle']}</p>
                        </div>
                    </div>
                    <div style="width:120px; text-align:center;">
                        <a href="{search_url}" target="_blank" style="text-decoration:none;">
                            <button style="background-color:#5F8B7D; color:white; border:none; padding:8px 0; border-radius:6px; cursor:pointer; width:100%; font-size:13px; font-weight:bold;">
                                🔍 寻觅此物
                            </button>
                        </a>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        except Exception as e:
            status.update(label="❌ 运算出错", state="error", expanded=False)
            st.error(f"运算出错：{str(e)}")

if __name__ == "__main__":
    main()

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

def scan_nearby_fengshui_pois(lat, lon, radius=500):
    """
    免费调用 OSM API 进阶版：扫描建筑、山脉、水系、道路（虚水）、村落。
    """
    overpass_url = "http://overpass-api.de/api/interpreter"
    
    # 【核心升级】使用 nwr (node, way, relation) 抓取所有形态，并加入道路(highway)、山脉(peak)、村落(place)
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
            
            # 【细节处理】有些大马路、山头、村落没有名字，我们要给它强制命名，因为这是风水核心要素
            if not name:
                if highway in ['motorway', 'trunk']: name = "城市快速路"
                elif highway in ['primary', 'secondary']: name = "主干道"
                elif highway == 'residential': name = "小区/村镇内部路"
                elif railway: name = "铁轨干线"
                elif natural in ['peak', 'hill']: name = "无名山丘"
                elif waterway: name = "无名河流/水渠"
                else: continue # 既没名字又不是核心地形的，直接跳过
                
            # 【风水理论映射】将现代地理标签翻译为风水气场属性
            if amenity in ['hospital', 'clinic']: pois.append(f"{name} (偏阴/病气)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name} (极阳/孤煞)")
            elif amenity == 'bank': pois.append(f"{name} (金旺/聚财)")
            elif amenity == 'marketplace': pois.append(f"{name} (动处/聚气)")
            elif amenity == 'school': pois.append(f"{name} (文昌/阳气旺)")
            elif amenity == 'place_of_worship': pois.append(f"{name} (宗教香火/孤气)")
            
            elif waterway or natural == 'water': pois.append(f"{name} (真水/界气引财)")
            elif natural == 'wood': pois.append(f"{name} (公园林地/生发之木)")
            elif natural in ['peak', 'ridge', 'hill']: pois.append(f"{name} (实山龙脉/靠山)")
            
            elif highway in ['motorway', 'trunk']: pois.append(f"{name} (大虚水/气流急易割脚)")
            elif highway in ['primary', 'secondary']: pois.append(f"{name} (虚水干流/带动气场)")
            elif railway: pois.append(f"{name} (铁龙脉/震动气场易生燥)")
            
            elif place in ['village', 'hamlet']: pois.append(f"{name} (自然村落/人丁聚气)")

        # 去重，保留最多 12 个关键地形特征传给大模型
        unique_pois = list(set(pois))
        return unique_pois[:12]
        
    except Exception as e:
        return []
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
    
    # 增加一个占位符用于显示雷达抓取情况
    radar_placeholder = st.empty()

    if location['latitude'] is not None and location['longitude'] is not None:
        lat, lon = location['latitude'], location['longitude']
        st.success(f"✅ 坐标锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：北纬 {lat}, 东经 {lon}。\n"
        
        with st.spinner("📡 正在启动玄学雷达，探测方圆 500 米..."):
            nearby_pois = scan_nearby_fengshui_pois(lat, lon)
            if nearby_pois:
                radar_placeholder.info("🗺️ **雷达探明气场节点（传给AI的数据）：**\n" + "、".join(nearby_pois))
                geo_context += f"【系统探测到周边500米设施】：{', '.join(nearby_pois)}。\n"
            else:
                radar_placeholder.warning("⚠️ **雷达监控：** 方圆 500 米内未抓取到医院/银行/公园等特殊建筑。可能因电脑IP定位偏差，或地图数据不全。")
                geo_context += "【系统探测周边500米】：无特殊明显气场建筑。\n"

    st.write("若雷达未扫到核心建筑，请务必在此手动补充：")
    micro_env = st.text_input("🏘️ 窗外肉眼所见 (例: 楼下十字路口/对面有工商银行)")
    if micro_env: geo_context += f"小外局手动描述：{micro_env}。\n"

    st.markdown("---")
    st.subheader("📸 贰 · 全息观形 (实景法相)")
    col1, col2 = st.columns(2)
    with col1: window_file = st.file_uploader("📸 拍摄窗外环境", type=["jpg", "png"], key="win")
    with col2: indoor_file = st.file_uploader("📜 上传户型或房间内景", type=["jpg", "png"], key="in")

    st.markdown("---")

    if st.button("🔮 开启禅心风水推演", type="primary", use_container_width=True):
        if not api_key: st.error("⚠️ 灵力源未接入！"); return
        if not window_file and not indoor_file: st.error("⚠️ 请至少上传一张环境照片。"); return

        with st.status("🌿 沟通天地，正在静心推演...", expanded=True) as status:
            try:
                client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
                
               # 【环境心理学 + 传统理气 融合版 Prompt】
                master_prompt = f"""
                # Role: 首席环境地理学与堪舆宗师 (精通环境心理学与断舍离美学)
                你的诊断必须极其客观、中正。严禁一味恐吓。你必须秉持“先赞美其优势，再指出其隐患”的原则。你要将传统风水理论与现代环境心理学、生活收纳美学完美融合，让用户觉得风水不仅是玄学，更是提升正能量的生活方式。

                # Input Data:
                1. 地脉雷达信息：\n{geo_context}
                2. 现场照片（如有）。

                # Output Format (必须详尽，总字数不少于800字，排版清晰)：
                1. 📜 【禅语定势】：写一首四句七言诗，概括此地气场。
                2. 🌟 【地脉与气场优势 (先扬)】（必须有此段！）：
                   - 严厉要求：详细阅读雷达数据中的所有建筑、水系、道路，以及照片中的优点（如采光好、格局方正）。
                   - 深度赞美：详细阐述这些元素带来的“吉相”。例如，道路交汇带来勃勃生机与商业潜能；附近的学校/政府/绿地带来了文昌、正气或木气生发；室内阳光充足让人阳气充沛。用优美的国学语言让用户感到安心和喜悦。
                3. ⚠️ 【形峦隐患勘验 (后抑)】：
                   - 话锋一转：“然太极生两仪，有吉必有凶…”。指出雷达数据或照片中的1-2处核心隐患（如铁龙脉震动、电线杆火煞、室内杂乱逼虎等）。
                   - 原理剖析：不仅用风水解释，必须结合“环境心理学”。例如：杂乱的物品会导致视觉噪音，消耗潜意识能量；直冲的尖角会产生心理暗示，导致神经紧绷、工作效率受损。
                4. 🧹 【大道至简 · 扫洒除尘】（免费药引 - 极其重要！）：
                   - 给出 1 个完全免费的“收纳、整理或生活习惯”化解方案。
                   - 案例参考：若照片杂乱，建议清理柜顶以化解“泰山压顶”，释放压抑感；若有电线杆煞，建议理顺窗前网线并保持窗玻璃明净，以清澈之气化解杂乱火煞；若空间闭塞，建议每日清晨开窗通风15分钟，引入生旺之气。
                   - 解释原因：用“一室之不治，何以天下为”的哲理，向用户解释“窗明几净、物有其位”本身就是最好的风水调理，能瞬间平复磁场。
                5. 🔮 【天机预警与破局之机】：
                   - 总结：扫洒除尘乃治本之基，可保日常心神安宁。然若要对冲流年特定方位的深层大煞，或催旺特定的财运/事业局，仅靠日常整理尚显不足。
                   - 留白：“需辅以特定属性之物，布于阵眼……”（在此处停止，绝不说需要买什么）。
                """
                
                content_list = [{"type": "text", "text": master_prompt}]
                if window_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(window_file)}"}})
                if indoor_file: content_list.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encode_image(indoor_file)}"}})

                response = client.chat.completions.create(model=model_choice, messages=[{"role": "user", "content": content_list}])
                report = response.choices[0].message.content
                
                status.update(label="✅ 堪舆完成。", state="complete", expanded=False)
                st.markdown("### 📜 专属堪舆诊断")
                st.markdown(report)
                
                st.markdown("---")
                st.warning("⚠️ 破解之道：知易行难。需精确法器引导气场。")
                st.button("💰 支付 ￥4.99 解锁《全息调理方位图解与避坑真诀》", use_container_width=True)
                
                # ================= 🛒 灵药库 (附带摆放秘籍与原理解析) =================
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown("### 🏮 大师阵眼 · 灵药图鉴")
                st.caption("以下为系统推演出的三味辅器，已为您标注专属摆放方位与运转原理，可自行寻觅结缘：")

                # 平民灵药库 (带详细解说)
                mundane_items = [
                    {"name": "🪨 天然溪水鹅卵石", "keyword": "天然 鹅卵石 摆件", "placement": "正对煞气的窗台边缘，或办公桌左前方（青龙位）。", "principle": "土生金。以天然艮土之气，吸收尖锐火煞（如电线杆/壁刀），镇定漂浮不定的磁场。"},
                    {"name": "☕ 纯白哑光陶瓷杯", "keyword": "简约 纯白 陶瓷杯", "placement": "工位正前方（明堂），需注入八分满清水，每周一换。", "principle": "白色属金，陶瓷属土，杯中蓄水，形成“土生金、金生水”的连环化煞局，专解燥热火煞。"},
                    {"name": "📏 工业级金属直尺", "keyword": "不锈钢 直尺 加厚", "placement": "压在桌面凌乱文件之下，或横放于键盘与显示器之间。", "principle": "庚金之气。以冷硬的金属切断纠缠不清的木煞（杂乱网线、繁杂事务），提升决断力。"},
                    {"name": "🌱 桌面水培富贵竹", "keyword": "水培富贵竹 桌面", "placement": "电脑显示器左侧，或进门斜对角（财位）。", "principle": "坎水生巽木。活水养绿植，化解电子产品的死气与辐射煞，盘活停滞的财运波动。"},
                    {"name": "🏮 暖色调小夜灯", "keyword": "暖色 氛围灯 桌面", "placement": "房间内最阴暗的角落，或正北方（玄武位）。", "principle": "人造离火。补充户型缺角或采光不足带来的阴气，驱散导致心情抑郁的冷硬气场。"},
                    {"name": "🥣 透明玻璃浅碗", "keyword": "透明 玻璃碗 浅口", "placement": "靠近房门内侧的玄关柜上，碗内可放几枚硬币。", "principle": "界水止气。玻璃属金水相合，形似微型明堂水口，能兜住即将流出大门的财气。"}
                ]

                # 专业法器库 (带详细解说)
                pro_items = [
                    {"name": "葫 纯铜实心小葫芦", "keyword": "纯铜 葫芦 挂件", "placement": "悬挂于卧室门内把手，或正对冲煞的窗户上方。", "principle": "铜能泄土煞，葫芦形似太极（肚大口小），能强力吸纳外来的病气与口舌是非，只进不出。"},
                    {"name": "🪙 仿古纯铜五帝钱", "keyword": "纯铜 五帝钱 挂件", "placement": "用双面胶贴于横梁下方，或放在入户门地垫之下。", "principle": "汇聚前朝盛世之极阳金气，专破上压（横梁压顶）与外冲（路冲/门冲），镇宅挡灾。"},
                    {"name": "🪨 原矿黑曜石七星阵", "keyword": "黑曜石七星阵 天然", "placement": "办公桌右侧（白虎位），或卧室床头柜。", "principle": "极阴之石，拥有极致的吸附力。七星阵列能放大磁场，专吃小人暗算与自身产生的负面焦虑。"},
                    {"name": "🦁 纯铜镇宅小貔貅", "keyword": "纯铜 貔貅 摆件", "placement": "头朝窗外或门外放置于桌角。", "principle": "上古瑞兽，以金气铸造，专克对面楼宇的尖角煞与反弓路，且能镇守本源财库。"},
                    {"name": "🔮 天然紫水晶碎石", "keyword": "紫水晶碎石 消磁", "placement": "装在小陶罐中，放在床头或书桌抽屉内。", "principle": "高频能量源。能柔化金火交战的暴躁气场，提升睡眠质量，并暗中催旺贵人运势。"},
                    {"name": "🪞 纯铜八卦凸镜", "keyword": "纯铜 八卦镜 凸镜", "placement": "仅限挂于室外，正对对面大楼的尖角、变压器或直路。", "principle": "凸镜如盾，先天八卦调配天地阴阳，将直冲而来的烈煞强行反射打散，护卫家宅安宁。"}
                ]

                # 随机抽取 2 个平民灵药 + 1 个专业法器
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

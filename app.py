import streamlit as st
import base64
from openai import OpenAI
import time
import requests
import random
from streamlit_geolocation import streamlit_geolocation

# ================= 页面基础配置 =================
st.set_page_config(page_title="赛博堪舆大师 | 秘传全息风水", page_icon="☯️", layout="centered")

# ================= 🎨 视觉升级：玄微暗金风 CSS =================
st.markdown("""
<style>
    .stApp { background-color: #F9F6F0; color: #333333; }
    h1, h2, h3, h4, h5, h6 { color: #2C3E50 !important; font-family: 'Songti SC', 'STSong', 'KaiTi', serif; }
    label { color: #555555 !important; font-weight: 500 !important; font-size: 15px !important; }
    .stButton>button[kind="primary"] { background-color: #5F8B7D; color: white; border: none; border-radius: 6px; transition: all 0.3s ease; font-weight: 500; letter-spacing: 2px; }
    .stButton>button[kind="primary"]:hover { background-color: #4A6E62; box-shadow: 0 4px 12px rgba(95, 139, 125, 0.3); }
    .stProgress > div > div > div > div { background-color: #5F8B7D; }
    hr { border-bottom-color: #D3CDC1; opacity: 0.6; }
    .array-text { font-family: 'KaiTi', serif; line-height: 1.8; color: #333; font-size: 15px;}
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
                if highway: name = "虚水(道路)"
                elif natural in ['peak', 'hill']: name = "地脉(山丘)"
                elif place: name = "聚落"
                else: continue
                
            if amenity in ['hospital', 'clinic']: pois.append(f"{name}(独阴煞)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name}(孤阳煞)")
            elif amenity == 'bank': pois.append(f"{name}(财气眼)")
            elif amenity == 'school': pois.append(f"{name}(文昌地)")
            elif natural == 'water' or tags.get('waterway'): pois.append(f"{name}(界水)")
            elif natural in ['peak', 'hill']: pois.append(f"{name}(靠山)")
            elif highway: pois.append(f"{name}(引气虚水)")
            elif place: pois.append(f"{name}(人丁穴)")
            else: pois.append(f"{name}(阵场节点)")
            
        return list(set(pois))[:15]
    except Exception:
        return []

# ================= 核心逻辑 =================
def main():
    st.title("☯️ 赛博堪舆：玄微地脉推演系统")
    st.markdown("---")

    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    with st.sidebar:
        st.header("⚙️ 引擎配置")
        if not api_key: api_key = st.text_input("Google API Key:", type="password")
        else: st.success("🔒 灵力已接入")
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
            radar_placeholder.warning("⚠️ 未探测到显赫地标，此地气场深藏不露。")

    micro_env = st.text_input("🏘️ 补充描述 (例: 窗外有高压线)")
    if micro_env: geo_context += f"小外局补充：{micro_env}。\n"

    st.markdown("---")
    st.subheader("📸 贰 · 观形辨气 (多图与户型)")
    col1, col2 = st.columns(2)
    with col1: win_files = st.file_uploader("📸 窗外景观 (可多张)", accept_multiple_files=True, key="win")
    with col2: in_files = st.file_uploader("📜 室内实景或户型图", accept_multiple_files=True, key="in")

    total_files = len(win_files) + len(in_files)
    st.markdown("---")

    if st.button("🔮 开启天机排盘", type="primary", use_container_width=True):
        if not api_key: st.error("请配置 API Key"); return
        if total_files == 0: st.error("大师需要法相照片"); return

        with st.status("🔮 正在开启风水大阵...", expanded=True) as status:
            st.write("📡 勘测阴阳理气...")
            time.sleep(1.0)
            st.write("👁️ 识别形峦格局...")
            time.sleep(1.0)
            status.update(label="✅ 卦象已成，天机显露...", state="complete", expanded=False)

        st.markdown("### 📜 堪舆诊断批言")
        report_placeholder = st.empty()
        full_report = ""

        try:
            client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            
            # 【终极玄学版 Prompt】：彻底剔除科学/心理学，全用阴阳五行术语
            master_prompt = f"""
            # Role: 隐世堪舆宗师 (精通玄空飞星、八宅明镜、峦头理气)
            你的诊断必须充满深厚的传统国学玄学底蕴。严禁使用任何“环境心理学”、“科学”、“视觉噪音”等现代词汇。一切皆由气场、五行、阴阳、形峦来解释。排版清晰。

            # Input Context:
            1. 地脉雷达信息：\n{geo_context}
            2. 用户上传的照片。

            # Output Structure (不少于1000字):
            1. 📜 【禅语定势】：写一首玄妙的七言绝句，断定此局吉凶。
            2. 🌟 【峦头理气勘验】：详细分析雷达数据中的道路、水系、建筑。使用“青龙白虎”、“朱雀玄武”、“得水藏风”、“虚水引气”等纯正风水术语，论述此地天地之气的汇聚之势，点出其蕴含的福泽与财运机缘。
            3. ⚠️ 【形峦冲煞点拨】：
               - 重点分流：仔细观察图片！如果是【户型图】，必须指出风水硬伤（如：门冲煞、缺角漏财、中宫受压、穿堂煞等）；如果是【实景图】，指出尖角煞、火煞或逼虎煞。
               - 必须用“五行生克”（如金木交战、火炎土燥）或“气场淤滞”来解释其对居住者命理运势、财帛宫、疾厄宫的破坏。
            4. 🛋️ 【顺势化解 · 借力打力】（免费化解法）：
               - 严禁让用户打扫卫生！
               - 必须结合照片，给出物理空间布局的调整：例如，改变床的朝向避开暗箭煞、将桌子移至文昌位、利用屏风/窗帘遮挡门冲或路冲。
               - 用风水学解释：这样挪动是如何改变了室内的“气口”，实现了“斗转星移”之效。
            5. 🔮 【预警与阵法契机】：
               - 总结：物理移位仅能避一时之锐气，化解表象。
               - 抛出诱饵：若要彻底锁住明堂财气，镇压流年大煞，逆天改命，唯有布下天地阵法，以五行法器镇守阵眼……（在此处停止，绝不说出具体法器，留下极强的付费悬念）。
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
            
            # ================= 变现钩子与深度阵法秘籍 =================
            st.markdown("---")
            st.warning("⚠️ 天机至此，免费推演已尽。破解死局，在乎引气布阵。")
            st.button("💰 支付 ￥4.99 解锁《秘传化煞聚气阵法真诀》", use_container_width=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为用户支付后解锁的【专属阵法秘籍】 ⬇️</p>", unsafe_allow_html=True)
            
            array_names = ["九宫飞星聚财阵", "太极两仪化煞阵", "五行斗转星移阵", "乾坤八卦锁幽阵"]
            selected_array = random.choice(array_names)
            
            st.markdown(f"<h3 style='text-align:center; color:#2C3E50;'>📜 秘传真诀：【{selected_array}】</h3>", unsafe_allow_html=True)
            st.markdown("<p class='array-text'>贫道夜观星象，推演贵宅格局，察觉此处气机交锋，非凡物可镇。此阵乃夺天地造化之局，需依五行生克之理，借金木水火土三位法器，分主次镇守各方阵眼。阵法大成之日，方能聚气凝神，化煞生财。以下为布阵法器与落位口诀，请依言悉心布置。</p>", unsafe_allow_html=True)
            
            # 商品库（附带玄学原理长文）
            mundane = [
                {"name": "天然溪水鹅卵石", "title": "【艮土基石 / 辅阵】", "kw": "天然 鹅卵石 摆件", "place": "青龙位或近窗台处", "desc": "此物常年受溪水冲刷，内蕴极强的水土交融之气。风水云“土能生金”，将其安置于此，可稳固本局阵基，吸收外溢之火煞，令室内气场沉稳不散。"},
                {"name": "纯白陶瓷水杯", "title": "【坎水灵泉 / 催化】", "kw": "白色 陶瓷杯 简约", "place": "明堂正中（书桌/茶几前方）", "desc": "白瓷属金，内注清水即为坎水。金水相生，连环生息。只需注入八分满清水，置于明堂，便能化解空间内的暴躁之气，柔化锐煞，引财气绵延。"},
                {"name": "桌面水培富贵竹", "title": "【巽木生花 / 辅阵】", "kw": "水培 富贵竹 桌面", "place": "大门斜对角（明财位）", "desc": "木气主生发，水培乃活水。将此物置于财位，以水养木，生生不息。不仅能驱散周遭死滞之气，更可盘活财库，令运势如竹节般步步高升。"},
                {"name": "工业级金属直尺", "title": "【庚金断刃 / 催化】", "kw": "不锈钢 直尺 加厚", "place": "桌面或抽屉底层", "desc": "五行之中，庚金最为肃杀刚硬。此处木气繁杂，易生纠葛。以此金尺压阵，取“快刀斩乱麻”之意，斩断晦暗气机，助主人行事果决，避退小人。"}
            ]
            pros = [
                {"name": "纯铜实心小葫芦", "title": "【太极阵眼 / 核心】", "kw": "纯铜 葫芦 挂件", "place": "直冲之气口（门把手或窗户正上）", "desc": "葫芦形似太极，肚大口小，乃道家收邪化病之上品法器。纯铜材质属重金，专泄五黄二黑土煞。悬于此阵眼处，可强力吞噬侵入宅内的病气与凶煞，只进不出，镇守宅门安宁。"},
                {"name": "仿古纯铜五帝钱", "title": "【帝威阵眼 / 核心】", "kw": "五帝钱 挂件 纯铜", "place": "横梁下方或入户地垫底部", "desc": "五帝钱汇聚前朝盛世之天、地、人三才之气，至阳至刚。以此物为核心阵眼，可凭千古帝王之威，强力破除横梁压顶之上压，阻挡外来路冲之锐气，保家宅四平八稳。"},
                {"name": "纯铜镇宅小貔貅", "title": "【吞金阵眼 / 核心】", "kw": "纯铜 貔貅 摆件", "place": "阵局前方，头朝门外或窗外", "desc": "貔貅乃上古吞金瑞兽，以重铜铸其形，杀气隐现。将其置于此位，不仅能迎击并咬碎对面刺来的尖角煞，更能以阵眼之力大开财门，广纳八方明财暗财。"}
            ]
            
            # 随机选取阵法元素
            main_core = random.sample(pros, 1)[0]
            aux_cores = random.sample(mundane, 2)
            
            # 渲染核心法器 (图文并茂的深度报告模式)
            st.markdown("#### ⚔️ 第一步：定海神针，立主阵眼")
            st.markdown(f"""
            <div style="background-color:#F4F1EA; border-left:4px solid #4A6E62; padding:15px; margin-bottom:20px;">
                <h5 style="margin-top:0; color:#2C3E50;">{main_core['title']} - {main_core['name']}</h5>
                <p class='array-text'><b>【落位口诀】：</b>置于{main_core['place']}。<br><b>【堪舆妙用】：</b>{main_core['desc']}</p>
                <a href="https://s.taobao.com/search?q={main_core['kw']}" target="_blank" style="text-decoration:none;">
                    <button style="background-color:#4A6E62; color:#FFF; border:none; padding:8px 15px; border-radius:4px; cursor:pointer;">🔮 前往结缘法器</button>
                </a>
            </div>
            """, unsafe_allow_html=True)
            
            # 渲染辅阵元素
            st.markdown("#### 🌿 第二步：五行相济，布辅阵眼")
            st.markdown("<p class='array-text'>主阵眼虽威，亦需阴阳调和。请备齐以下两件辅器，方能令阵法生生不息：</p>", unsafe_allow_html=True)
            
            for item in aux_cores:
                st.markdown(f"""
                <div style="background-color:#FFFFFF; border:1px solid #D3CDC1; padding:15px; border-radius:6px; margin-bottom:15px;">
                    <h5 style="margin-top:0; color:#5F8B7D;">{item['title']} - {item['name']}</h5>
                    <p class='array-text'><b>【落位口诀】：</b>置于{item['place']}。<br><b>【堪舆妙用】：</b>{item['desc']}</p>
                    <a href="https://s.taobao.com/search?q={item['kw']}" target="_blank" style="text-decoration:none;">
                        <button style="background-color:#F9F6F0; color:#4A6E62; border:1px solid #5F8B7D; padding:6px 12px; border-radius:4px; cursor:pointer;">🔍 寻觅此物</button>
                    </a>
                </div>
                """, unsafe_allow_html=True)
                
            st.markdown("<p class='array-text' style='text-align:center; color:#B84B4B; margin-top:20px;'><b>谨记：三位法器归位之日，便是此局煞气消散、财运重聚之时。福生无量天尊。</b></p>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

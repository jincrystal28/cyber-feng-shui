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
    /* 长卷文字排版，增加行距和首行缩进，更像古籍 */
    .array-text { font-family: 'STSong', 'KaiTi', serif; line-height: 2.0; color: #222; font-size: 16px; text-indent: 2em; margin-bottom: 15px;}
    .array-title { font-weight: bold; color: #2C3E50; font-size: 18px; margin-top: 20px; display: block; text-indent: 0;}
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
            
            # 【修改点 1】：强制要求先扬后抑，洋洋洒洒，只用风水黑话
            master_prompt = f"""
            # Role: 隐世堪舆宗师 (精通玄空飞星、八宅明镜、峦头理气)
            你的诊断必须充满深厚的传统国学玄学底蕴，排版必须如古籍长卷般行云流水。切忌通篇贬低，必须“先扬后抑”，先断言其吉相，再点破其凶煞。严禁使用现代心理学或科学词汇。

            # Input Context:
            1. 地脉雷达信息：\n{geo_context}
            2. 用户上传的照片。

            # Output Structure (总字数不少于1200字，尽显宗师风范):
            1. 📜 【禅语定势】：写一首玄妙的七言绝句，点出此局之天地造化。
            2. 🌟 【藏风聚气 · 寻龙点穴】（先扬 - 必须详尽！）：必须先找出雷达数据或照片中的风水极佳之处。用“青龙蜿蜒、明堂开阔、得水藏风、玉带环腰”等纯正风水术语，大肆赞美此地的天地灵气、地脉福泽，让居住者心生欢喜与自豪。（不少于300字）。
            3. ⚠️ 【暗煞潜行 · 形峦点拨】（后抑）：话锋一转，指出照片或雷达数据中潜藏的风水硬伤（如门冲、穿堂煞、火煞、逼虎煞等）。用“五行相克”、“气场淤滞”详细解释其对命理运势的暗中损耗。
            4. 🛋️ 【顺势化解 · 拂拭明台】（免费化解法）：
               - 结合照片，给出空间物理布局的调整：如清理某处杂乱以释放青龙位，改变床/桌朝向避开暗箭煞。
               - 必须用风水学解释：这样挪动与清理是如何改变了室内的“气口”与“风道”，实现了斗转星移之效。
            5. 🔮 【天机预警】：
               - 详细描述如果不进一步布阵化煞，流年大运将如何受损。
               - 结尾抛出悬念：“然天无绝人之路，唯有布下夺天地造化之大阵，以五行法器镇守阵眼……”（戛然而止，绝不说出具体法器）。
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
            st.warning("⚠️ 天机至此，免费推演已尽。破解死局，在乎引气布阵。")
            st.button("💰 支付 ￥4.99 解锁《秘传阵法：全息布阵真诀与法器落位图》", use_container_width=True)
            
            # ================= 【修改点 2】：无痕融入长文的付费秘籍 =================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为模拟用户支付 4.99 元后解锁的【阵法长卷】 ⬇️</p>", unsafe_allow_html=True)
            
            array_names = ["九宫飞星聚财阵", "太极两仪化煞阵", "五行斗转星移阵", "乾坤八卦锁幽阵", "先天四象引气阵"]
            selected_array = random.choice(array_names)
            
            mundane = [
                {"name": "天然溪水鹅卵石", "kw": "天然 鹅卵石 摆件", "place": "青龙位或近窗台处", "desc": "此物常年受溪水冲刷，内蕴极强的水土交融之气。风水云“土能生金”，将其安置于此，可稳固本局阵基，吸收外溢之火煞，令室内气场沉稳不散。"},
                {"name": "纯白陶瓷水杯", "kw": "白色 陶瓷杯 简约", "place": "明堂正中（书桌/茶几前方）", "desc": "白瓷属金，内注清水即为坎水。金水相生，连环生息。只需注入八分满清水，置于明堂，便能化解空间内的暴躁之气，柔化锐煞，引财气绵延。"},
                {"name": "桌面水培富贵竹", "kw": "水培 富贵竹 桌面", "place": "大门斜对角（明财位）", "desc": "木气主生发，水培乃活水。将此物置于财位，以水养木，生生不息。不仅能驱散周遭死滞之气，更可盘活财库，令运势如竹节般步步高升。"},
                {"name": "工业级金属直尺", "kw": "不锈钢 直尺 加厚", "place": "桌面或抽屉底层", "desc": "五行之中，庚金最为肃杀刚硬。此处木气繁杂，易生纠葛。以此金尺压阵，取“快刀斩乱麻”之意，斩断晦暗气机，助主人行事果决，避退小人。"}
            ]
            pros = [
                {"name": "纯铜实心小葫芦", "kw": "纯铜 葫芦 挂件", "place": "直冲之气口（门把手或窗户正上）", "desc": "葫芦形似太极，肚大口小，乃道家收邪化病之上品法器。纯铜材质属重金，专泄五黄二黑土煞。悬于此阵眼处，可强力吞噬侵入宅内的病气与凶煞，只进不出，镇守宅门安宁。"},
                {"name": "仿古纯铜五帝钱", "kw": "五帝钱 挂件 纯铜", "place": "横梁下方或入户地垫底部", "desc": "五帝钱汇聚前朝盛世之天、地、人三才之气，至阳至刚。以此物为核心阵眼，可凭千古帝王之威，强力破除横梁压顶之上压，阻挡外来路冲之锐气，保家宅四平八稳。"},
                {"name": "纯铜镇宅小貔貅", "kw": "纯铜 貔貅 摆件", "place": "阵局前方，头朝门外或窗外", "desc": "貔貅乃上古吞金瑞兽，以重铜铸其形，杀气隐现。将其置于此位，不仅能迎击并咬碎对面刺来的尖角煞，更能以阵眼之力大开财门，广纳八方明财暗财。"}
            ]
            
            main_core = random.sample(pros, 1)[0]
            aux_cores = random.sample(mundane, 2)
            
            st.markdown(f"""
            <div style="background-color: #FAF8F2; padding: 30px; border: 1px solid #E3DBCB; border-radius: 4px; box-shadow: inset 0 0 20px rgba(0,0,0,0.02);">
                <h3 style='text-align:center; color:#2C3E50; margin-bottom: 30px; border-bottom: 1px solid #D4AF37; padding-bottom: 10px;'>📜 秘传真诀：【{selected_array}】</h3>
                
                <span class='array-title'>【阵理玄机】</span>
                <p class='array-text'>观贵宅之气运交锋，寻常之物已难承其重。此【{selected_array}】乃贫道结合天地地脉与室内理气，独家推演而出的无上法门。阵法之妙，在于“一主两辅，三才合一”。借特定法器之五行灵力，锁住明堂之财，化解暗处之煞。布下此阵，犹如为家宅披上一层无形之铠甲，外邪不入，内气不泄。</p>

                <span class='array-title'>⚔️ 第一步：定海神针，立主阵眼</span>
                <p class='array-text'>要破此局，首当其冲需镇压核心凶位。贫道推演，需以 <a href="https://s.taobao.com/search?q={main_core['kw']}" target="_blank" style="color:#B84B4B; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #B84B4B; padding-bottom: 2px;">{main_core['name']}</a> 作为本局之主阵眼。此物{main_core['desc']} 此阵眼之<b>【落位口诀】为：需端正安放于{main_core['place']}</b>，切勿偏倚。</p>
                
                <span class='array-title'>🌿 第二步：五行相济，布辅阵眼</span>
                <p class='array-text'>主阵既立，需以五行相生之物辅佐，方能令气场流转不息，生生不绝。其一，当寻一 <a href="https://s.taobao.com/search?q={aux_cores[0]['kw']}" target="_blank" style="color:#4A6E62; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #4A6E62; padding-bottom: 2px;">{aux_cores[0]['name']}</a>，落位于<b>{aux_cores[0]['place']}</b>，取其{aux_cores[0]['desc']}其二，需觅得 <a href="https://s.taobao.com/search?q={aux_cores[1]['kw']}" target="_blank" style="color:#4A6E62; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #4A6E62; padding-bottom: 2px;">{aux_cores[1]['name']}</a>，安置于<b>{aux_cores[1]['place']}</b>，以达阴阳调和之境。双辅齐下，生财化煞之功乃成。</p>

                <span class='array-title'>⏳ 第三步：破局断言</span>
                <p class='array-text'>请于吉日良辰，净手焚香，将这三件法器依阵位依次落下。归位之日起，三日至七日内，您必感室内气场澄澈，心神安宁。流年大煞自此冰消瓦解，贵人与财源将循清灵之气而至。顺天应人，福生无量天尊。</p>
            </div>
            """, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

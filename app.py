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
    .array-text { font-family: 'STSong', 'KaiTi', serif; line-height: 2.0; color: #222; font-size: 16px; text-indent: 2em; margin-bottom: 15px;}
    .array-title { font-weight: bold; color: #2C3E50; font-size: 18px; margin-top: 25px; display: block; text-indent: 0; border-left: 4px solid #D4AF37; padding-left: 10px;}
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

    # ================= 变现法器库预加载 =================
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
    
    # 随机分配：1个免费区带货，1个付费区主阵眼，1个付费区辅阵眼
    free_item = random.choice(mundane)
    remaining_mundane = [m for m in mundane if m['name'] != free_item['name']]
    paid_main = random.choice(pros)
    paid_aux = random.choice(remaining_mundane)
    
    array_names = ["九宫飞星聚财阵", "太极两仪化煞阵", "五行斗转星移阵", "乾坤八卦锁幽阵", "先天四象引气阵"]
    selected_array = random.choice(array_names)

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
            
            # 【修改点 1】：强迫大模型在免费区推荐指定的法器 (free_item)
            master_prompt = f"""
            # Role: 隐世堪舆宗师 (精通玄空飞星、八宅明镜、峦头理气)
            你的诊断必须充满深厚的传统国学玄学底蕴，排版如古籍长卷。必须“先扬后抑”。严禁使用现代心理学或科学词汇。

            # Input Context:
            1. 地脉雷达信息：\n{geo_context}
            2. 用户上传的照片。

            # Output Structure (总字数不少于1200字):
            1. 📜 【禅语定势】：写一首玄妙的七言绝句，点出此局之天地造化。
            2. 🌟 【藏风聚气 · 寻龙点穴】（先扬）：用纯正风水术语大肆赞美此地的天地灵气、地脉福泽，让居住者心生欢喜。
            3. ⚠️ 【暗煞潜行 · 形峦点拨】（后抑）：指出潜藏的风水硬伤。用“五行相克”、“气场淤滞”详细解释其对命理运势的暗中损耗。
            4. 🛋️ 【顺势化解 · 借力打力】（免费化解法）：
               - 结合照片，给出空间物理布局的调整。
               - 【强制任务】：你必须在这一段中，强烈建议用户在调整后的位置摆放一件寻常可见的灵物：【{free_item['name']}】。
               - 必须用风水学原理解释它（{free_item['desc']}）是如何改变了室内的“气口”与“风道”，实现了斗转星移之效。
            5. 🔮 【天机预警】：
               - 详细描述如果不进一步布阵，流年大运将如何受损。
               - 结尾抛出悬念：“然天无绝人之路，唯有布下夺天地造化之大阵，以重宝法器镇守阵眼……”（戛然而止，绝不说出具体法器）。
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
            
            # ================= 免费区无痕带货卡片 =================
            st.markdown(f"""
            <div style="background-color:#FFFFFF; border:1px solid #EBE6DF; padding:15px; border-radius:6px; margin:20px 0; display:flex; align-items:center; justify-content:space-between; box-shadow: 0 2px 8px rgba(0,0,0,0.03);">
                <div style="flex:1;">
                    <span style="font-size:12px; color:#888;">宗师点拨 · 顺势灵物</span>
                    <h4 style="margin:5px 0 0 0; color:#5F8B7D;">{free_item['name']}</h4>
                    <p style="margin:5px 0 0 0; font-size:13px; color:#666;">置于{free_item['place']}，以达化煞生息之效。</p>
                </div>
                <div>
                    <a href="https://s.taobao.com/search?q={free_item['kw']}" target="_blank" style="text-decoration:none;">
                        <button style="background-color:#F9F6F0; color:#4A6E62; border:1px solid #5F8B7D; padding:8px 16px; border-radius:4px; cursor:pointer; font-weight:bold;">🔍 寻觅此物</button>
                    </a>
                </div>
            </div>
            """, unsafe_allow_html=True)

            # ================= 变现钩子 =================
            st.markdown("---")
            st.warning("⚠️ 天机至此，免费推演已尽。若觉运势凝滞，求治本之法，在乎引气布阵。")
            st.button("💰 支付 ￥4.99 解锁《万字秘卷：全息布阵真诀与法器落位图》", use_container_width=True)
            
            # ================= 【修改点 2】：万字秘卷扩容版 (绝无空格缩进！) =================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为模拟用户支付 4.99 元后解锁的【阵法长卷】 ⬇️</p>", unsafe_allow_html=True)
            
            # HTML 代码块：必须顶格写！
            html_content = f"""
<div style="background-color: #FAF8F2; padding: 40px; border: 1px solid #E3DBCB; border-radius: 4px; box-shadow: inset 0 0 30px rgba(0,0,0,0.03);">
<h2 style='text-align:center; color:#2C3E50; margin-bottom: 40px; border-bottom: 2px solid #D4AF37; padding-bottom: 15px; font-family:"STSong", serif;'>📜 秘传真诀：【{selected_array}】</h2>

<span class='array-title'>☯️ 阵理玄机与天地同频</span>
<p class='array-text'>天地之道，损有余而补不足。观贵宅之气运交锋，明堂虽有生气，然暗煞环伺，寻常之物已难承其重。此【{selected_array}】乃贫道夜观星象，结合贵宅地脉与室内理气，耗费心血推演而出的无上法门。此阵之妙，不在于物之贵贱，而在于“一主一辅，阴阳交泰”。借特定法器之五行灵力，锁住明堂之财，化解暗处之煞。布下此阵，犹如为家宅披上一层无形之金钟罩，外邪不入，内气不泄，乃是逆天改命之基。</p>

<span class='array-title'>🧭 寻龙定穴：堪定气场中枢</span>
<p class='array-text'>布阵之首要，在于定穴。法器若错位寸分，则失之千里。请于正午时分，阳气最盛之时，立于宅内中心，手持罗盘或指南针，寻出正南离火与正北坎水之交汇线。此线乃家宅之“脊骨”。感受气流微动之处，便是我等即将落下阵眼的重中之重。若遇迷惘，只需谨记贫道下方赐予的落位口诀，依言照做，万无一失。</p>

<span class='array-title'>⚔️ 第一步：定海神针，立主阵眼</span>
<p class='array-text'>要破此局，首当其冲需以重宝镇压核心凶位。贫道推演，唯有以 <a href="https://s.taobao.com/search?q={paid_main['kw']}" target="_blank" style="color:#B84B4B; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #B84B4B; padding-bottom: 2px; font-size:18px;">{paid_main['name']}</a> 作为本局之主阵眼，方能镇伏群魔。此宝物非同小可，{paid_main['desc']} 此物一出，万邪辟易。此主阵眼之<b>【落位口诀】为：须端正安放于{paid_main['place']}</b>，切勿偏倚，使其正面迎向煞气来临之方。</p>

<span class='array-title'>🌿 第二步：五行相济，布辅阵眼</span>
<p class='array-text'>孤阳不生，独阴不长。主阵既立，气场刚烈，必以五行相生之物辅佐，方能令气场流转不息，化刚为柔，生生不绝。请务必寻得一 <a href="https://s.taobao.com/search?q={paid_aux['kw']}" target="_blank" style="color:#4A6E62; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #4A6E62; padding-bottom: 2px; font-size:18px;">{paid_aux['name']}</a>，作为辅阵之眼。此物之精妙在于：{paid_aux['desc']} 辅器之<b>【落位口诀】为：妥善安置于{paid_aux['place']}</b>。双器齐鸣，一主杀伐镇煞，一主生发生财，阴阳调和之境乃成。</p>

<span class='array-title'>🕯️ 阵眼加持：净手焚香仪轨</span>
<p class='array-text'>法器迎回，切勿草率摆放。凡灵物皆需认主。请择一晴朗之日，辰时（早7点至9点）最佳。先以清水净手，若有条件，可点燃一炷沉香或檀香，绕法器三周，以香火之气洗去其凡尘沾染之气。心中默念：“天地自然，秽气分散，八方威神，使我自然。阵起！”随后，双手捧起法器，依前文口诀稳稳落下，安放后三日内切勿轻易挪动。</p>

<span class='array-title'>⏳ 破局断言：吉相显露之期</span>
<p class='array-text'>依此秘卷布阵，阵成之日，天地气场必生感应。快则三日，慢则七七四十九日内，您必感室内气场澄澈，呼吸顺畅，夜晚睡眠深沉，心神不再无故焦躁。流年之大煞自此冰消瓦解，曾经阻滞之事业、财源，将循此清灵之气如活水般涌来。所谓顺天应人，尽力而为，余下皆是天意。福生无量天尊，贫道在此静候佳音。</p>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

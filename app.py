import streamlit as st
import base64
from openai import OpenAI
import time
import requests
import random
from streamlit_geolocation import streamlit_geolocation
from fengshui_core import CyberCompass

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
    with col2: in_files = st.file_uploader("📜 室内实景或户型平面图", accept_multiple_files=True, key="in")

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
        {"name": "纯铜实心小葫芦", "title": "【太极阵眼 / 核心】", "kw": "纯铜 葫芦 挂件", "place": "煞气直冲之气口（门把手或窗户上）", "desc": "葫芦形似太极，肚大口小，乃道家收邪化病之上品法器。纯铜材质属重金，专泄五黄二黑土煞。悬于此阵眼处，可强力吞噬病气与凶煞，只进不出，镇守安宁。"},
        {"name": "仿古纯铜五帝钱", "title": "【帝威阵眼 / 核心】", "kw": "五帝钱 挂件 纯铜", "place": "横梁下方或入户门地垫底部", "desc": "五帝钱汇聚前朝盛世之三才之气，至阳至刚。以此物为核心阵眼，可凭千古帝王之威，强力破除横梁压顶之上压，阻挡外来路冲之锐气，保家宅四平八稳。"},
        {"name": "纯铜镇宅小貔貅", "title": "【吞金阵眼 / 核心】", "kw": "纯铜 貔貅 摆件", "place": "阵局前方，头朝冲煞之门或窗外", "desc": "貔貅乃上古吞金瑞兽，以重铜铸其形，杀气隐现。将其置于此位，不仅能迎击并咬碎对面刺来的尖角煞，更能以阵眼之力大开财门，广纳八方明财暗财。"}
    ]
    
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
            st.write("📡 融合外围地脉与实境法相...")
            time.sleep(1.0)
            st.write("🧭 挂载九星引擎，辩证阴阳吉凶...")
            time.sleep(1.0)
            status.update(label="✅ 九宫飞星推演完毕，天机显露...", state="complete", expanded=False)

        st.markdown("### 📜 堪舆诊断批言")
        report_placeholder = st.empty()
        full_report = ""

        try:
            flying_stars_data = CyberCompass.calculate_flying_stars()
            stars_str = "\n".join([f"{k}: {v}" for k, v in flying_stars_data['stars'].items()])
            current_year = flying_stars_data['year']

            client = OpenAI(api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta/openai/")
            
            # 【终极去标签化 Prompt】：严禁程序化词汇，强行约束大模型采用行云流水的古文过渡
            master_prompt = f"""
            # Role: 隐世堪舆宗师 (精通峦头理气)
            你的诊断必须充满深厚的国学底蕴，排版如古籍长卷。你必须遵循万物皆有阴阳的“客观辩证”原则：宏观与微观皆需指出吉相与隐患。

            # 🛑 核心排版禁令（绝对服从）：
            严禁在输出文本中出现任何指导性、程序化的词汇或括号备注！绝对不要出现：“（雷达辩证）”、“（图片辩证）”、“（免费化解法）”、“第一张图片”、“吉相赞誉”、“隐患警示”、“先断吉”、“后断凶”等破坏意境的字眼。所有的过渡必须行云流水，使用传统的风水术语自然衔接。

            # 硬性算理数据:
            1. 地脉雷达信息：\n{geo_context}
            2. 【{current_year}年 九宫飞星盘】：\n{stars_str}

            # Output Structure (总字数不少于1200字):
            1. 📜 【禅语定势】：写一首玄妙的七言绝句，点出此局之吉凶交织。
            2. 🌍 【峦头理气 · 宏观大局】：
               - 结合雷达数据，用风水术语大肆赞美周边地脉带来的福泽（如得水藏风、文昌高照、虚水引气）。
               - 随后自然过渡，结合飞星盘，指出周遭潜藏的暗煞（如某方位的二黑五黄，或官威独阴之压迫）。
            3. 🔍 【微观法相 · 图内玄机】：
               - 请用“贫道观此户型格局...” 或 “观此室内陈设...” 等古文句式自然切入，点明你看到的是户型图还是实景。
               - 夸赞图中的吉相：若为户型图，夸格局方正或得气；若为实景，夸采光或明堂。
               - 再严厉点出图中的隐患：缺角、穿堂煞、门冲、杂物淤滞、横梁压顶、尖角冲射等。用“五行相克”解释其损耗。
            4. 🛋️ 【顺势化解 · 拂拭明台】：
               - 给出一个物理空间布局调整方案（如清理特定淤滞区域、避开冲射、调整朝向）。
               - 强烈建议在调整后的位置摆放寻常可见的【{free_item['name']}】，并用风水原理解释它（{free_item['desc']}）如何改变了气口。
            5. 🔮 【天机预警】：
               - 描述若不进一步化解，流年大运将受凶星反扑。
               - 结尾抛出悬念：“然天无绝人之路，唯有布下夺天地造化之大阵，以法器镇守阵眼……”（戛然而止，绝不说出具体法器）。
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
            st.button("💰 支付 ￥4.99 解锁《秘卷：全息布阵真诀与法器落位图》", use_container_width=True)
            
           # ================= 【修改点】：付费秘籍疯狂扩容版 (HTML 绝对顶格) =================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为模拟用户支付 4.99 元后解锁的【阵法长卷】 ⬇️</p>", unsafe_allow_html=True)
            
            html_content = f"""
<div style="background-color: #FAF8F2; padding: 40px; border: 1px solid #E3DBCB; border-radius: 4px; box-shadow: inset 0 0 30px rgba(0,0,0,0.03);">
<h2 style='text-align:center; color:#2C3E50; margin-bottom: 40px; border-bottom: 2px solid #D4AF37; padding-bottom: 15px; font-family:"STSong", serif;'>📜 秘卷专供：【{selected_array}】全局部署真诀</h2>

<span class='array-title'>☯️ 阵理玄机：天地同频，造化暗藏</span>
<p class='array-text'>风水之妙，贵在“乘气”。天地之道，损有余而补不足。观贵宅之气运交锋，明堂虽有生气，然暗煞环伺，若不加以引导，则财气易散，口舌易生。此【{selected_array}】乃贫道结合贵宅地脉与本流年理气，独家推演而出的化煞生财法门。此阵不尚奢华，而重在“一主一辅，阴阳交泰，气机牵引”。借特定法器之五行灵力，辅以地理落位，即可锁住明堂之财，化解暗处之煞。布下此阵，犹如为家宅披上一层无形之铠甲，外邪不入，内气不泄，乃是调和磁场、逆天改命之基石。</p>

<span class='array-title'>⚔️ 核心枢纽：定海神针，立主阵眼</span>
<p class='array-text'>要破此局，首当其冲需以重宝镇压核心凶位，扼住煞气之咽喉。贫道推演，需以 <a href="https://s.taobao.com/search?q={paid_main['kw']}" target="_blank" style="color:#B84B4B; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #B84B4B; padding-bottom: 2px; font-size:18px;">{paid_main['name']}</a> 作为本局之主阵眼。此宝物非同小可，{paid_main['desc']} 此主阵眼之<b>【落位口诀】极为严苛：须端正安放于{paid_main['place']}</b>。安放时切勿偏倚，务必使其正面迎向煞气来临之方。一物镇宅，犹如猛将当关，万邪辟易，护佑家宅安宁。</p>

<span class='array-title'>🌿 生生不息：五行相济，布辅阵眼</span>
<p class='array-text'>孤阳不生，独阴不长。主阵既立，气场刚烈，若无辅佐则易生过极之象。需以五行相生之物从旁策应，方能令气场流转不息，化刚为柔。请务必寻得一 <a href="https://s.taobao.com/search?q={paid_aux['kw']}" target="_blank" style="color:#4A6E62; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #4A6E62; padding-bottom: 2px; font-size:18px;">{paid_aux['name']}</a>，作为辅阵之眼。此物之精妙在于：{paid_aux['desc']} 辅器之<b>【落位口诀】为：妥善安置于{paid_aux['place']}</b>。双器齐鸣，一主杀伐镇煞，一主生发生财，一刚一柔，阴阳调和之大境乃成。</p>

<span class='array-title'>✨ 起阵心法：借取天时，清净明台</span>
<p class='array-text'>大道至简，无需繁缛的焚香念咒，然“借取天时与明台之净”不可或缺。请择一晴朗之日，于辰时或巳时（早7点至11点，日出东方，阳气上升之际）进行布阵。布阵前，务必用干净的湿布将法器落位之处擦拭得一尘不染，风水中谓之“清净明台”。安放法器时，需心平气和，心无杂念，依前文口诀将两件法器稳稳落下。一旦落位，气机即刻流转。</p>

<span class='array-title'>🛑 守阵禁忌：日常护持与避险之道</span>
<p class='array-text'>阵法既成，便与家宅气运紧密相连。日常起居需谨记三点守阵禁忌：其一，不可令外人（非同住亲属）随意把玩、抚摸法器，以免沾染外部杂气，乱了阵法磁场；其二，阵眼周边三尺之内需保持整洁，切忌堆放杂物或垃圾纸篓，以免秽气冲阵；其三，法器安放后，非大扫除切勿随意挪动其方位。若时间久远积落灰尘，可用干净的专属软布轻轻拂拭，切忌用水浸泡冲洗。</p>

<span class='array-title'>⏳ 破局断言：吉相显露之期</span>
<p class='array-text'>依此秘卷布阵，阵成之日，天地气场必生微妙感应。快则三五日，慢则一月之内，您必感室内气场澄澈，呼吸更为顺畅，夜晚睡眠深沉，白日心神不再无故焦躁。流年大煞自此冰消瓦解，曾经阻滞之事业、财源，将循此清灵之气如活水般涌来。顺天应人，积善成德，余下皆是天意。贫道在此静候佳音。</p>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

        except Exception as e:
            st.error(f"灵力中断：{str(e)}")

if __name__ == "__main__":
    main()

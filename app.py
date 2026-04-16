import streamlit as st
import base64
from openai import OpenAI
import time
import requests
import random
from streamlit_geolocation import streamlit_geolocation
from fengshui_core import CyberCompass  # 挂载底层算理引擎

# ================= 页面基础配置 =================
st.set_page_config(page_title="玄微空间 | 人居环境推演", page_icon="☯️", layout="centered")

# ================= 🎨 视觉升级：玄微暗金风 + 隐藏水印 =================
st.markdown("""
<style>
    /* 隐藏 Streamlit 右下角的水印和右上角的菜单 */
    footer {visibility: hidden;}
    #MainMenu {visibility: hidden;}
    
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
    overpass_url = "[http://overpass-api.de/api/interpreter](http://overpass-api.de/api/interpreter)"
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
                if highway: name = "动线交织之径(道路)"
                elif natural in ['peak', 'hill']: name = "形峦稳固之基(山丘)"
                elif place: name = "人居理气聚落"
                else: continue
                
            if amenity in ['hospital', 'clinic']: pois.append(f"{name}(气机沉郁之区)")
            elif amenity in ['police', 'courthouse']: pois.append(f"{name}(气势威压之地)")
            elif amenity == 'bank': pois.append(f"{name}(资源汇聚之眼)")
            elif amenity == 'school': pois.append(f"{name}(心智启迪之所)")
            elif natural == 'water' or tags.get('waterway'): pois.append(f"{name}(水气环抱之局)")
            elif natural in ['peak', 'hill']: pois.append(f"{name}(背靠稳固之屏)")
            elif highway: pois.append(f"{name}(气流冲射之带)")
            elif place: pois.append(f"{name}(生机盘桓之枢)")
            else: pois.append(f"{name}(空间理气节点)")
            
        return list(set(pois))[:15]
    except Exception:
        return []

# ================= 核心逻辑 =================
def main():
    st.title("☯️ 玄微空间：全息人居环境推演")
    st.markdown("---")

    api_key = st.secrets.get("GOOGLE_API_KEY", "")
    with st.sidebar:
        st.header("⚙️ 算力引擎配置")
        if not api_key: api_key = st.text_input("Google API Key:", type="password")
        else: st.success("🔒 算力已接入")
        model_choice = st.selectbox("推演模型:", ["gemini-2.5-flash", "gemini-2.5-pro"])
        if st.button("🔄 刷新空间基点缓存"):
            st.cache_data.clear()
            st.rerun()

    st.subheader("📍 壹 · 宏观势能锚定")
    location = streamlit_geolocation()
    geo_context = ""
    radar_placeholder = st.empty()

    if location['latitude'] is not None and location['longitude'] is not None:
        lat, lon = location['latitude'], location['longitude']
        st.success(f"✅ 坐标锁定：北纬 {lat:.4f}, 东经 {lon:.4f}")
        geo_context = f"GPS坐标：{lat}, {lon}。\n"
        
        nearby_pois = scan_nearby_fengshui_pois(lat, lon)
        if nearby_pois:
            radar_placeholder.info("🗺️ **雷达探明周边拓扑环境：**\n" + "、".join(nearby_pois))
            geo_context += f"【周边空间基点】：{', '.join(nearby_pois)}。\n"
        else:
            radar_placeholder.warning("⚠️ 未探测到显赫地标，此地气机平稳。")

    micro_env = st.text_input("🏘️ 补充空间描述 (例: 窗外有高压线塔)")
    if micro_env: geo_context += f"视觉盲区补充：{micro_env}。\n"

    st.markdown("---")
    st.subheader("📸 贰 · 微观理气勘测 (上传图纸或实景)")
    col1, col2 = st.columns(2)
    with col1: win_files = st.file_uploader("📸 视野朝向 (窗外景观)", accept_multiple_files=True, key="win")
    with col2: in_files = st.file_uploader("📜 内部理气 (户型或实景)", accept_multiple_files=True, key="in")

    total_files = len(win_files) + len(in_files)
    st.markdown("---")

    # ================= 变现法器库 (东方生态包装版) =================
    mundane = [
        {"name": "天然溪水鹅卵石", "title": "【厚土沉淀之基】", "kw": "天然 鹅卵石 摆件", "place": "空间采光口或视线尽头", "desc": "此物经流体长期冲刷，内蕴极强的水土和合之气。将其安置于此，可作为视觉与心理的‘沉淀锚点’，吸收空间内冗余的焦躁氛围，令气机沉稳。"},
        {"name": "纯白陶瓷水杯", "title": "【金水相生之枢】", "kw": "白色 陶瓷杯 简约", "place": "核心作业区（书桌/茶几前方）", "desc": "白瓷属性纯粹，内注清水即为流转之气。只需注入八分满清水置于此处，便能柔化周遭尖锐之形峦冲射，降低环境心理压迫，令心智澄明。"},
        {"name": "桌面水培富贵竹", "title": "【木气生发之源】", "kw": "水培 富贵竹 桌面", "place": "动线斜对角（滞塞盲区）", "desc": "植物乃天然之生机引流器。置于空间盲区，可以水气滋养生态活力，不仅能驱散周遭死滞之气机，更能盘活该区域之空间势能，破除郁结。"}
    ]
    pros = [
        {"name": "纯铜实心小葫芦", "title": "【太极化育中枢】", "kw": "纯铜 葫芦 挂件", "place": "气流对冲之节点（门窗直冲处）", "desc": "其形契合道家流体力学，材质属高密度精铜，专克滞塞浊气。悬于此气机中枢，可强力吸收并中和外来之视觉与心理逼压，稳固空间生态基底。"},
        {"name": "仿古纯铜五帝钱", "title": "【盛世理气稳压器】", "kw": "五帝钱 挂件 纯铜", "place": "顶端形体压迫处（横梁下或门槛）", "desc": "此介质汇聚极强之历史沉淀与正向势能，至刚至阳。以此物为核心阵眼，可强力柔化横梁带来之垂直空间压迫，阻挡外来锐角之形峦冲刺。"},
        {"name": "纯铜镇宅小貔貅", "title": "【势能内聚瑞兽】", "kw": "纯铜 貔貅 摆件", "place": "气运流失口，朝向外部", "desc": "此物造型具极强之视觉威慑张力，纯铜铸造。置于此处，不仅能在心理层面迎击外部刺来之尖角干扰，更能建立单向气机屏障，锁住内部之生机富集。"}
    ]
    
    free_item = random.choice(mundane)
    paid_main = random.choice(pros)
    remaining_mundane = [m for m in mundane if m['name'] != free_item['name']]
    paid_aux = random.choice(remaining_mundane)
    
    array_names = ["五行感官调平布局", "太极双轨理气方案", "九宫全息环境生态矩阵", "气机沉淀与空间重构案"]
    selected_array = random.choice(array_names)

    if st.button("🔮 开启环境理气演算", type="primary", use_container_width=True):
        if not api_key: st.error("请配置算力 API Key"); return
        if total_files == 0: st.error("需要提供环境图纸或图像资料"); return

        with st.status("🔮 正在推演空间经络...", expanded=True) as status:
            st.write("📡 扫描周边地脉与形峦基点...")
            time.sleep(1.0)
            st.write("🧭 叠算年度九维气机流转盘...")
            time.sleep(1.0)
            status.update(label="✅ 理气推演完毕，报告生成中...", state="complete", expanded=False)

        st.markdown("### 📜 空间理气智库研报")
        report_placeholder = st.empty()
        full_report = ""

        try:
            # 挂载算理外挂
            flying_stars_data = CyberCompass.calculate_flying_stars()
            stars_str = "\n".join([f"{k}: {v}" for k, v in flying_stars_data['stars'].items()])
            current_year = flying_stars_data['year']

            client = OpenAI(api_key=api_key, base_url="[https://generativelanguage.googleapis.com/v1beta/openai/](https://generativelanguage.googleapis.com/v1beta/openai/)")
            
            # 【终极防崩坏 Prompt】：东方理气 + 严格排版禁令 + 词汇限制
            master_prompt = f"""
            # Role: 隐世空间理气宗师 (深谙东方建筑生态、环境心理与气机流转，以古文自居)
            你必须呈现一种“东方高雅玄学”文风：句式为“半文半白”的古典国学风格，名词使用关于“环境、气象、理气、光影、形峦、心理”的合规词汇。

            # 🛑 核心红线禁令（绝对服从，关乎系统存亡）：
            1. 词汇替换：绝对不使用“风水、算命、堪舆、煞气、五鬼、明堂、文昌、量子、引力波”等封建迷信或西方物理词汇。
            2. 排版严禁：【绝对不要】使用Markdown代码块（即```）来包裹你的回复！【绝对不要】在段落或标题开头使用空格缩进！全部顶格书写，自然分段。
            3. 字眼限制：全篇输出中，“磁场”一词的出现次数【绝对不能超过 3 次】！多用“气机、理气、空间势能、环境生态、流转”来替代。

            # ☯️ 东方理气词汇矩阵（随机调用）：
            - 描述吉相：使用“气机环抱之局”、“前置舒朗之境”、“背靠稳固之基”、“心智澄明之枢纽”、“气流绵延之所”。
            - 描述隐患：使用“动线冲逼之径”、“形峦尖锐之冲射”、“气机流失之漏”、“顶端形体之压迫（横梁）”、“气机郁结之暗区”、“暴躁之源”。
            - 解析原理：使用“空间经络疏通”、“建筑生态调和”、“环境心理暗示”、“阴阳光影交泰”。

            # 硬性输入数据:
            1. 宏观基点：\n{geo_context}
            2. 【{current_year}年度 天地九维气机流转盘】：\n{stars_str}

            # Output Structure (自然顶格输出，不带代码块，不少于1200字):
            1. 📜 【环境理气定调】：写一首七言古诗，以光影、草木、气象等自然意象，隐喻此空间的居住底色。
            2. 🌍 【宏观形峦 · 气运流转】：
               - 结合宏观基点，用古风句式赞美周边环境设施带来的“气流绵延”与“生活气息之滋养”。
               - 结合年度九维盘，指出周边潜藏的“气机暴躁之源”或“势能郁结之向”。
            3. 🔍 【微观勘测 · 空间经络解析】：
               - 自然切入，点明看到的是平面布局图还是实景视野。
               - 先论其长：赞其物理框架之规整，或光影通透。
               - 犀利点破隐患：死盯布局中的硬伤。解释其（如直冲、杂乱、逼压）如何潜移默化造成居住者的“心理焦躁、睡眠浅薄、决断力迟滞”。
            4. 🛋️ 【生态调优 · 熵减方案】（免费方案）：
               - 给出一个免费的空间整理方案。
               - 强烈建议在核心位置引入介质：【{free_item['name']}】，解释它（{free_item['desc']}）如何作为“视觉与心理的定海神针”，实现气机的柔化与沉淀。
            5. 🔮 【气运推演预警】：
               - 描述若放任此“气机郁结”，在今年环境势能波动下，将如何引发长期的精神内耗。
               - 结尾悬念：“然空间理气皆可调和。唯有建立全息的【空间生态调和布局】，引入特定介质镇守中枢……”（戛然而止）。
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
                    <span style="font-size:12px; color:#888;">宗师点拨 · 顺势介质</span>
                    <h4 style="margin:5px 0 0 0; color:#5F8B7D;">{free_item['name']}</h4>
                    <p style="margin:5px 0 0 0; font-size:13px; color:#666;">置于{free_item['place']}，以达气机柔化之效。</p>
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
            st.warning("⚠️ 基础诊断至此结束。若觉近期决策受阻、身心凝滞，欲求深度气机重构之法，需建立全息生态理气阵列。")
            st.button("💰 支付 ￥4.99 解锁《全息空间生态重构方案与定心介质部署图》", use_container_width=True)
            
            # ================= 付费长卷区 =================
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("---")
            st.markdown("<p style='text-align:center; color:#888; font-size:12px;'>⬇️ 以下为模拟用户支付 4.99 元后解锁的【阵法长卷】 ⬇️</p>", unsafe_allow_html=True)
            
            html_content = f"""
<div style="background-color: #FAF8F2; padding: 40px; border: 1px solid #E3DBCB; border-radius: 4px; box-shadow: inset 0 0 30px rgba(0,0,0,0.03);">
<h2 style='text-align:center; color:#2C3E50; margin-bottom: 40px; border-bottom: 2px solid #D4AF37; padding-bottom: 15px; font-family:"STSong", serif;'>📜 深度智库：《{selected_array}》部署真诀</h2>

<span class='array-title'>☯️ 架构玄机：天地同频，造化暗藏</span>
<p class='array-text'>空间之妙，贵在“乘气”。天地物理，损有余而补不足。观贵宅之环境势能交锋，视野虽有生机，然暗处经络畸变，若不加以引导，则决策力易散，神经紧绷。此【{selected_array}】乃贫道结合地貌引力与本流年理气，独家推演而出的空间调平法门。此架构不尚奢华，重在“一主一辅，双极稳态，气机牵引”。借特定介质之五行物理属性，辅以精准拓扑落位，即可锁住正向反馈循环，化解高频冲射源。部署此系统，犹如为居所披上一层无形之生态屏障，外扰不入，内能不泄。</p>

<span class='array-title'>⚔️ 核心中枢：定海神针，立主能量锚点</span>
<p class='array-text'>要破此局，首需以高密度介质镇压核心高熵位，扼住畸变气流之咽喉。贫道推演，需以 <a href="https://s.taobao.com/search?q={paid_main['kw']}" target="_blank" style="color:#B84B4B; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #B84B4B; padding-bottom: 2px; font-size:18px;">{paid_main['name']}</a> 作为本局之主锚点。此物非同小可，{paid_main['desc']} 此主锚点之<b>【落位准则】极为严苛：须端正安放于{paid_main['place']}</b>。安放时切勿偏倚，务必使其正面迎向气流剪切来临之方。一物镇宅，犹如高频谐振器，护佑基底安宁。</p>

<span class='array-title'>🌿 生生不息：双极相济，布辅振中枢</span>
<p class='array-text'>孤阳不生，独阴不长。主节点既立，气机刚烈，若无辅佐则易生过极之象。需以相生波段之物从旁策应，方能令势能流转不息，化刚为柔。请务必寻得一 <a href="https://s.taobao.com/search?q={paid_aux['kw']}" target="_blank" style="color:#4A6E62; font-weight:bold; text-decoration:none; border-bottom: 1px dashed #4A6E62; padding-bottom: 2px; font-size:18px;">{paid_aux['name']}</a>，作为辅振之眼。此物之精妙在于：{paid_aux['desc']} 辅器之<b>【落位准则】为：妥善安置于{paid_aux['place']}</b>。双节点齐鸣，一主吸收降噪，一主生发引流，一刚一柔，双极生态稳态乃成。</p>

<span class='array-title'>✨ 启动心法：借取天时，清净明台</span>
<p class='array-text'>大道至简，无需繁缛仪式，然“借取天时与环境之净”不可或缺。请择一晴朗之日，于辰时或巳时（早7点至11点，阳气上升、心智活跃之际）进行部署。落位前，务必用净水将承载面擦拭得一尘不染，消除多余灰尘带来之微观漫反射，此谓之“清净明台”。安放介质时，需心平气和，依前文准则稳稳落下。一旦落位，气机即刻流转。</p>

<span class='array-title'>🛑 运行禁忌：日常护持与避噪之道</span>
<p class='array-text'>系统既成，便与居者心理暗影紧密相连。日常起居需谨记三点运行禁忌：其一，不可令外人随意把玩该介质，以免沾染外部杂散浊气，乱了核心经络；其二，节点周边三尺之内需保持极简，切忌堆放杂物纸篓，以免产生视觉噪点冲阵；其三，介质安放后，非深度清扫切勿随意挪动其坐标。若积落灰尘，可用专属软布轻轻拂拭，切忌用化学洗剂浸泡。</p>

<span class='array-title'>⏳ 破局断言：气运显露之期</span>
<p class='array-text'>依此秘卷完成部署，系统启动之日，微气候必生微妙感应。快则三五日，慢则一月之内，您必感室内光影柔和，呼吸更为顺畅，夜晚安眠规律，白日决策精神充沛。周期性焦虑自此冰消瓦解，曾经阻滞之事业灵感，将循此清灵气机如活水涌来。顺天应理，余下皆是自然之馈赠。贫道在此静候佳音。</p>
</div>
"""
            st.markdown(html_content, unsafe_allow_html=True)

        except Exception as e:
            error_msg = str(e)
            if "503" in error_msg or "high demand" in error_msg:
                status.update(label="⚠️ 天庭算力拥挤，请稍候...", state="error", expanded=False)
                st.warning("🏮 **【宗师提示】：** 此时求测者甚众，天机通道拥堵，算力传输受阻。请稍待片刻（约半分钟），再次点击【开启环境演算】即可重连。")
            elif "API_KEY" in error_msg or "401" in error_msg:
                status.update(label="❌ 算力密匙断绝", state="error", expanded=False)
                st.error("⚠️ 算力密匙（API Key）有误或已失效，请在侧边栏重新核对。")
            else:
                status.update(label="❌ 演算矩阵溃散", state="error", expanded=False)
                st.error(f"⚠️ 算力运转出现未知岔路，请重试。界外乱码：{error_msg}")

if __name__ == "__main__":
    main()

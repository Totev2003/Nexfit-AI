import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
import json
from pathlib import Path
import g4f
import re
import base64

st.set_page_config(
    page_title="NEXFIT AI",
    page_icon="⚡",
    layout="wide"
)

# ========================= ДАННИ =========================
DATA_FILE = Path("nexfit_data.json")

if "data" not in st.session_state:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            st.session_state.data = json.load(f)
    else:
        st.session_state.data = {}

if "current_weight" not in st.session_state:
    st.session_state.current_weight = 75.0
if "tracking_date" not in st.session_state:
    st.session_state.tracking_date = date.today()
if "ai_response" not in st.session_state:
    st.session_state.ai_response = None

# СЛЕДЕНЕ ДАЛИ ПОТРЕБИТЕЛЯТ Е НАТИСНАЛ БУТОНА "ЗАПОЧНИ"
if "app_started" not in st.session_state:
    st.session_state.app_started = False

# ИНИЦИАЛИЗАЦИЯ НА ПРОФИЛА В SESSION STATE
if 'prof_name' not in st.session_state: st.session_state.prof_name = "Цветомира"
if 'prof_gender' not in st.session_state: st.session_state.prof_gender = "Жена"
if 'prof_age' not in st.session_state: st.session_state.prof_age = 28
if 'prof_height' not in st.session_state: st.session_state.prof_height = 168
if 'prof_activity' not in st.session_state: st.session_state.prof_activity = "Умерена активност (3-5 тренировки/седмица)"
if 'prof_start_w' not in st.session_state: st.session_state.prof_start_w = 75.0
if 'prof_target_w' not in st.session_state: st.session_state.prof_target_w = 60.0
if 'avatar_data' not in st.session_state: st.session_state.avatar_data = None

# СЕСИОННИ ПРОМЕНЛИВИ ЗА БЪРЗОТО ДОБАВЯНЕ НА ХРАНИ
if 'selected_foods' not in st.session_state: st.session_state.selected_foods = []
if 'quick_calories' not in st.session_state: st.session_state.quick_calories = 0

# ========================= ФУНКЦИИ ЗА ИЗЧИСЛЕНИЯ =========================
def calculate_calories():
    w = float(st.session_state.current_weight)
    h = float(st.session_state.prof_height)
    a = float(st.session_state.prof_age)
    
    if st.session_state.prof_gender == "Мъж":
        bmr = 10 * w + 6.25 * h - 5 * a + 5
    else:
        bmr = 10 * w + 6.25 * h - 5 * a - 161
        
    activity_multipliers = {
        "Застоял живот (без тренировки)": 1.2,
        "Лека активност (1-3 тренировки/седмица)": 1.375,
        "Умерена активност (3-5 тренировки/седмица)": 1.55,
        "Висока активност (6-7 тренировки/седмица)": 1.725
    }
    multiplier = activity_multipliers.get(st.session_state.prof_activity, 1.2)
    tdee = bmr * multiplier
    target_calories = tdee * 0.85
    return int(target_calories)

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.data, f, ensure_ascii=False, indent=2)

def get_date_str(d):
    return d.strftime("%Y-%m-%d")

def extract_youtube_links(text):
    pattern = r'(https?://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s]+)'
    return re.findall(pattern, text)


# ========================= СВЕТЪЛ СТИЛ + АНИМАЦИИ =========================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
        color: #1e2937;
    }
    
    .main-header {
        font-size: 3.5rem !important;
        font-weight: 800;
        text-align: center;
        background: linear-gradient(90deg, #0ea5e9, #6366f1, #8b5cf6, #ec4899);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradientShift 8s ease infinite;
        background-size: 200% 200%;
    }
    
    @keyframes gradientShift {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 16px;
        padding: 12px 24px;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.12);
    }
    
    .stTabs [aria-selected="true"] {
        background: linear-gradient(90deg, #0ea5e9, #6366f1) !important;
        color: white !important;
        transform: scale(1.05);
    }

    /* ОСНОВЕН СТИЛ ЗА БУТОНИТЕ */
    .stButton>button {
        background: linear-gradient(90deg, #0ea5e9, #6366f1);
        color: white;
        font-weight: bold;
        border-radius: 16px;
        height: 52px;
        transition: all 0.3s ease;
        box-shadow: 0 8px 20px rgba(14, 165, 233, 0.3);
    }
    
    .stButton>button:hover {
        transform: translateY(-4px) scale(1.03);
        box-shadow: 0 15px 30px rgba(14, 165, 233, 0.4);
    }

    /* СПЕЦИАЛЕН СТИЛ ЗА БУТОНИТЕ ЗА БЪРЗО ДОБАВЯНЕ НА ХРАНИ */
    div[data-testid="stHorizontalBlock"] .food-btn button {
        background: linear-gradient(90deg, #0ea5e9, #6366f1) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        height: 45px !important;
        font-size: 0.88rem !important;
        border: none !important;
        box-shadow: 0 4px 10px rgba(99, 102, 241, 0.2) !important;
        transition: all 0.25s ease-in-out !important;
        margin-bottom: 8px !important;
        width: 100% !important;
    }
    
    div[data-testid="stHorizontalBlock"] .food-btn button:hover {
        transform: translateY(-3px) scale(1.02) !important;
        box-shadow: 0 8px 16px rgba(14, 165, 233, 0.35) !important;
        filter: brightness(1.1);
    }
</style>
""", unsafe_allow_html=True)

# =================================================================
# ЛОГИКА 1: ПОТРЕБИТЕЛЯТ ВСЕ ОЩЕ НЕ Е НАТИСНАЛ "ЗАПОЧНИ"
# =================================================================
if not st.session_state.app_started:
    
    # 1. Голямо и ярко заглавие НАД снимката
    st.markdown("""
    <div style="text-align: center; margin-top: 20px; margin-bottom: 30px;">
        <h1 style="font-size: 5.5rem !important; font-weight: 900; margin: 0; line-height: 1.1;
                   background: linear-gradient(90deg, #0ea5e9, #6366f1, #8b5cf6, #ec4899);
                   -webkit-background-clip: text;
                   -webkit-text-fill-color: transparent;
                   letter-spacing: 2px;">
            NEXFIT AI
        </h1>
        <p style="font-size: 2rem; font-weight: 600; color: #475569; margin-top: 15px; margin-bottom: 0;">
            Твоят личен AI треньор и нутриционист
        </p>
    </div>
    """, unsafe_allow_html=True)

    # 2. Чиста снимка (без текст върху нея) като банер
    st.markdown("""
    <div style="height: 380px; border-radius: 24px; overflow: hidden; margin-bottom: 40px; box-shadow: 0 15px 35px rgba(0,0,0,0.1);">
        <img src="https://images.unsplash.com/photo-1571019613454-1cb2f99b2d8b" 
             style="width: 100%; height: 100%; object-fit: cover;">
    </div>
    """, unsafe_allow_html=True)

    # 3. Трите колони с предимствата
    col1, col2, col3 = st.columns(3)
    with col1:
        st.image("https://images.unsplash.com/photo-1517838277536-f5f99be501cd", use_container_width=True)
        st.markdown("<h4 style='text-align:center;'>🏋️ Персонализирани тренировки</h4>", unsafe_allow_html=True)
        st.write("AI създава план според твоето ниво, оборудване и цели.")
    with col2:
        st.image("https://images.unsplash.com/photo-1490645935967-10de6ba17061", use_container_width=True)
        st.markdown("<h4 style='text-align:center;'>🥗 Интелигентно хранене</h4>", unsafe_allow_html=True)
        st.write("Точни препоръки за калории и макронутриенти всеки ден.")
    with col3:
        st.image("https://images.unsplash.com/photo-1571019614242-c5c5dee9f50b", use_container_width=True)
        st.markdown("<h4 style='text-align:center;'>📈 Проследяване на прогреса</h4>", unsafe_allow_html=True)
        st.write("Графики, статистики и мотивация всеки ден.")
    
    # 4. ЦЕНОВИ ПЛАНОВЕ
    st.markdown("---")
    st.markdown("<h2 style='text-align:center; margin-bottom: 30px;'>🎯 Избери своя план за промяна</h2>", unsafe_allow_html=True)
    
    price_col1, price_col2, price_col3 = st.columns(3)
    
    with price_col1:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e2e8f0; min-height: 290px;">
            <h3 style="margin: 0; color: #1e293b;">FREE TRIAL</h3>
            <h2 style="color: #0ea5e9; margin: 10px 0;">0.00 €</h2>
            <p style="color: #64748b; font-size: 0.95rem;">
                <b>5 дни безплатен тест</b><br>
                Изпробвай базовия AI анализ, проследявай теглото си и виж как работи системата.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🚀 Започни 5 дни тест", key="plan_free", use_container_width=True):
            st.session_state.app_started = True
            st.balloons()
            st.rerun()

    with price_col2:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #f8fafc 0%, #eef2f6 100%); padding: 25px; border-radius: 20px; box-shadow: 0 15px 30px rgba(99, 102, 241, 0.15); text-align: center; border: 2px solid #6366f1; min-height: 290px; position: relative;">
            <span style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #22c55e; color: white; padding: 2px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;">МОТИВАЦИЯ</span>
            <h3 style="margin-top: 10px; color: #1e293b;">MONTHLY PLAN</h3>
            <h2 style="color: #6366f1; margin: 10px 0;">4.99 € <span style="font-size: 1rem; color: #64748b;">/ месец</span></h2>
            <p style="color: #1e293b; font-size: 0.95rem; background: #dcfce7; padding: 8px; border-radius: 10px; margin-bottom: 10px; font-weight: 600;">
                🎁 При добри резултати получаваш 1 седмица БЕЗПЛАТНО!
            </p>
            <p style="color: #64748b; font-size: 0.85rem;">Пълен достъп до AI тренировки и детайлен хранителен навигатор.</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("👑 Абонирай се за 4.99 €", key="plan_monthly", type="primary", use_container_width=True):
            st.session_state.app_started = True
            st.balloons()
            st.rerun()

    with price_col3:
        st.markdown("""
        <div style="background: white; padding: 25px; border-radius: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.05); text-align: center; border: 1px solid #e2e8f0; min-height: 290px; position: relative;">
            <span style="position: absolute; top: -12px; left: 50%; transform: translateX(-50%); background: #8b5cf6; color: white; padding: 2px 12px; border-radius: 10px; font-size: 0.75rem; font-weight: bold; letter-spacing: 1px;">НАЙ-ИЗГОДНО</span>
            <h3 style="margin: 0; color: #1e293b;">6-MONTH PREMIUM</h3>
            <h2 style="color: #8b5cf6; margin: 10px 0;">19.99 €</h2>
            <p style="color: #64748b; font-size: 0.95rem;">
                <b>Спести над 30%!</b><br>
                Половин година пълен Премиум достъп без лимити, приоритетно AI генериране и разширени графики.
            </p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("🔥 Вземи 6 месеца за 19.99 €", key="plan_premium_6m", use_container_width=True):
            st.session_state.app_started = True
            st.balloons()
            st.rerun()
            
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 5. Статистики долу
    c_stat1, c_stat2, c_stat3 = st.columns(3)
    with c_stat1:
        st.markdown("<div style='text-align:center; font-size:1.1rem;'>🔥 <b>14 200+</b> активни потребители</div>", unsafe_allow_html=True)
    with c_stat2:
        st.markdown("<div style='text-align:center; font-size:1.1rem;'>🤖 <b>99.4%</b> точни AI анализи</div>", unsafe_allow_html=True)
    with c_stat3:
        st.markdown("<div style='text-align:center; font-size:1.1rem;'>🎯 <b>-4.2 кг</b> средно за месец</div>", unsafe_allow_html=True)

# =================================================================
# ЛОГИКА 2: ПРИЛОЖЕНИЕТО Е ОТКЛЮЧЕНО
# =================================================================
else:
    calorie_target = calculate_calories()

    # ========================= СТИЛИЗИРАН SIDEBAR =========================
    with st.sidebar:
        st.markdown("""
        <div style="text-align:center; margin-bottom:20px;">
            <h1 style="font-size:2rem; font-weight:800; background: linear-gradient(90deg,#0ea5e9,#6366f1); -webkit-background-clip:text; -webkit-text-fill-color:transparent; margin-bottom:5px;">
                👤 ПРОФИЛ
            </h1>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🏠 Върни Начална страница", use_container_width=True):
            st.session_state.app_started = False
            st.rerun()

        st.markdown("---")

        st.markdown("""
        <style>
            .stFileUploader section { padding: 0 !important; background-color: transparent !important; border: none !important; text-align: center !important; }
            .stFileUploader section > div:first-child { display: none !important; }
            .stFileUploader label { display: none !important; }
            .stFileUploader button { margin: 0 auto !important; display: block !important; padding: 4px 12px !important; font-size: 0.85rem !important; }
        </style>
        """, unsafe_allow_html=True)

        st.markdown('<div style="text-align:center; margin-bottom:10px;">', unsafe_allow_html=True)

        if st.session_state.avatar_data:
            base64_img = base64.b64encode(st.session_state.avatar_data).decode()
            st.markdown(f"""
            <div style="display:flex; justify-content:center; margin-bottom:10px;">
                <img src="data:image/png;base64,{base64_img}" style="width:110px; height:110px; border-radius:50%; object-fit:cover; border:4px solid white; box-shadow:0 8px 25px rgba(99,102,241,0.3);">
            </div>
            <h3 style="text-align:center; margin-top:5px; margin-bottom:5px; font-weight:700; color:#1e293b !important; font-size:1.3rem;">
                {st.session_state.prof_name if st.session_state.prof_name else "Потребител"}
            </h3>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="display:flex; justify-content:center; margin-bottom:15px;">
                <div style="width:110px; height:110px; border-radius:50%; background:#f1f5f9; display:flex; align-items:center; justify-content:center; border:3px solid #e2e8f0; color:#94a3b8; font-size:2.8rem; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
                    👤
                </div>
            </div>
            """, unsafe_allow_html=True)

        uploaded_avatar = st.file_uploader("", type=["png", "jpg", "jpeg"], key="sidebar_avatar")
        if uploaded_avatar:
            st.session_state.avatar_data = uploaded_avatar.getvalue()
            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

        st.text_input("Име", key="prof_name")
        c_sex, c_age = st.columns(2)
        with c_sex:
            g_index = 0 if st.session_state.prof_gender == "Жена" else 1
            st.selectbox("Пол", ["Жена", "Мъж"], index=g_index, key="prof_gender")
        with c_age:
            st.number_input("Години", 12, 100, key="prof_age")

        st.number_input("Ръст (см)", 100, 250, key="prof_height")
        st.selectbox("Активност", [
            "Застоял живот (без тренировки)",
            "Лека активност (1-3 тренировки/седмица)",
            "Умерена активност (3-5 тренировки/седмица)",
            "Висока активност (6-7 тренировки/седмица)"
        ], key="prof_activity")

        st.markdown("<p style='font-weight:600; margin-bottom:-5px; color:#475569;'>⚙️ Биометрични Цели</p>", unsafe_allow_html=True)
        st.number_input("Начално тегло (кг)", 30.0, 200.0, step=0.1, key="prof_start_w")
        st.number_input("Текущо тегло (кг)", 30.0, 200.0, step=0.1, key="current_weight")
        st.number_input("Целево тегло (кг)", 30.0, 200.0, step=0.1, key="prof_target_w")

        if st.button("💾 Запази промените", use_container_width=True):
            st.success("Профилът е обновен успешно!")
            st.rerun()

        st.markdown("---")
        diff = round(float(st.session_state.current_weight - st.session_state.prof_target_w), 1)
        if diff > 0:
            st.markdown(f"""
            <div style="background:rgba(239,68,68,0.1); border-left:5px solid #ef4444; padding:18px; border-radius:14px; margin:15px 0;">
                <span style="font-size:0.9rem; color:#b91c1c; font-weight:600;">ОСТАВА ДО ЦЕЛТА</span>
                <h3 style="margin:8px 0 0 0; color:#b91c1c; font-weight:800;">{diff} кг</h3>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div style="background:rgba(34,197,94,0.1); border-left:5px solid #22c55e; padding:18px; border-radius:14px; margin:15px 0; text-align:center;">
                <h4 style="margin:0; color:#15803d; font-weight:800;">🎉 Целта е постигната!</h4>
            </div>
            """, unsafe_allow_html=True)

        calorie_target = calculate_calories()
        st.markdown(f"""
        <div style="background:linear-gradient(135deg, #4f46e5, #06b6d4); padding:20px; border-radius:16px; text-align:center; color:white; margin:15px 0; box-shadow:0 8px 20px rgba(0,0,0,0.15);">
            <span style="font-size:0.9rem; opacity:0.9; font-weight:600;">ДНЕВЕН КАЛОРИЕН ТАРГЕТ</span>
            <h2 style="margin:8px 0 0 0; color:white; font-weight:800; font-size:2rem;">{calorie_target} kcal</h2>
            <span style="font-size:0.8rem; opacity:0.85;">Автоматично изчислен здравословен дефицит</span>
        </div>
        """, unsafe_allow_html=True)

    # ========================= ТАБОВЕ С ФУНКЦИИ =========================
    st.markdown("<h1 class='main-header'>NEXFIT AI</h1>", unsafe_allow_html=True)
    tab1, tab2, tab3, tab4 = st.tabs(["📥 Дневен Отчет", "📊 Прогрес", "🤖 AI Асистент", "📜 История"])
    
    # ====================== TAB 1: ДНЕВЕН ОТЧЕТ ======================
    with tab1:
        st.subheader(f"📅 Дневен Отчет — {st.session_state.tracking_date.strftime('%d.%m.%Y')}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            weight = st.number_input("Тегло (кг)", value=st.session_state.current_weight, step=0.1)
        with col2:
            water = st.number_input("Вода (литри)", value=2.0, step=0.25)
        with col3:
            sleep = st.slider("Сън (часове)", min_value=3.0, max_value=12.0, value=7.0, step=0.5)
        with col4:
            mood = st.select_slider("Настроение", ["Много лошо", "Лошо", "Средно", "Добро", "Отлично"])

        st.markdown("---")

        left_col, right_col = st.columns([2, 1.4])
        with left_col:
            st.markdown("**🍽️ Хранене за деня**")
            food = st.text_area(
                label="",
                height=320,
                placeholder="Опиши какво хапна днес...",
                value="\n".join(st.session_state.get('selected_foods', []))
            )

        with right_col:
            st.markdown("**⚡ Бързо добавяне на храни**")
            FOOD_CATEGORIES = {
                "🥩 Протеини": {
                    "Пилешко филе (200г)": 230,
                    "Сьомга (150г)": 300,
                    "Яйца (3 бр)": 210,
                    "Извара (200г)": 180
                },
                "🍚 Въглехидрати": {
                    "Ориз (150г)": 200,
                    "Овесени ядки (50г)": 190,
                    "Картофи (200г)": 180
                },
                "🥑 Мазнини": {
                    "Авокадо (1 бр)": 240,
                    "Ядки (30г)": 180,
                    "Зехтин (1 с.л.)": 120
                },
                "🍲 Готвени ястия": {
                    "Пиле с ориз": 420,
                    "Мусака (порция)": 450,
                    "Шопска салата": 220
                }
            }

            for category, foods in FOOD_CATEGORIES.items():
                with st.expander(category, expanded=False):
                    for food_name, kcal in foods.items():
                        if st.button(f"{food_name} (+{kcal} kcal)", use_container_width=True, key=f"food_{food_name}"):
                            if 'selected_foods' not in st.session_state:
                                st.session_state.selected_foods = []
                            st.session_state.selected_foods.append(f"{food_name} (~{kcal} kcal)")
                            st.rerun()

        st.markdown("---")
        activity = st.text_area("🏃 Движение / Тренировка", height=110, placeholder="Ходене, тренировка във фитнеса...")

        col_save1, col_save2 = st.columns([3, 1])
        with col_save2:
            if st.button("💾 Запази деня", type="primary", use_container_width=True):
                entry = {
                    "weight": float(weight),
                    "water": float(water),
                    "sleep": float(sleep),
                    "mood": mood,
                    "food": food,
                    "activity": activity,
                    "target_calories": calorie_target,
                    "consumed_calories": st.session_state.get('quick_calories', 0) # По подразбиране
                }
                today_str = get_date_str(st.session_state.tracking_date)
                st.session_state.data[today_str] = entry
                st.session_state.current_weight = weight
                st.session_state.tracking_date += timedelta(days=1)
                save_data()
                
                if 'selected_foods' in st.session_state:
                    st.session_state.selected_foods = []
                
                st.success(f"✅ Денят {today_str} беше записан успешно!")
                st.rerun()

    # ====================== TAB 2: ПРОГРЕС ======================
    with tab2:
        if st.session_state.data:
            df = pd.DataFrame.from_dict(st.session_state.data, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.plotly_chart(px.line(df, y="weight", title="📉 Прогрес на теглото", markers=True), use_container_width=True)
            with col_b:
                if "consumed_calories" in df.columns:
                    fig_cal = px.bar(df, y=["target_calories", "consumed_calories"], barmode="group", title="🔥 Калориен таргет vs Приети калории")
                    st.plotly_chart(fig_cal, use_container_width=True)
                else:
                    st.plotly_chart(px.bar(df, y="water", title="💧 Прием на вода (л)"), use_container_width=True)
                    
            st.plotly_chart(px.line(df, y="sleep", title="😴 Качество на съня"), use_container_width=True)
        else:
            st.info("Все още няма данни за изграждане на графики.")

    # ====================== TAB 3: AI Асистент ======================
    with tab3:
        st.subheader("🤖 AI Персонален Асистент")
        
        if st.session_state.data:
            last_date = max(st.session_state.data.keys())
            last_date_obj = date.fromisoformat(last_date)
            st.info(f"**Използваме данни от последно попълнения ден:** {last_date_obj.strftime('%d.%m.%Y')}")
            
            if st.button("🚀 Генерирай подробен AI фитнес и диетичен одит", type="primary", use_container_width=True):
                entry = st.session_state.data[last_date]
                
                prompt = f"""
                Ти си професионален фитнес треньор и нутриционист. 
                Направи задълбочен персонален фитнес одит на български език за утрешния ден на база следните точни биометрични данни:
                - Зададен научен калориен таргет: {entry.get('target_calories')} ккал
                - Приблизително приети калории: {entry.get('consumed_calories')} ккал
                - Текстово описание на храната днес: {entry['food']}
                - Тренировка/Активност днес: {entry['activity']}
                - Изпита вода: {entry['water']} литра
                - Сън: {entry['sleep']} часа
                - Настроение/Тонус: {entry['mood']}
                
                Структурирай отговора си професионално:
                1. Анализ на днешния ден (Къде потребителят се е справил добре и къде е сгрешил).
                2. Конкретно разпределение на макросите за утре (Протеин, Въглехидрати, Мазнини в грамове за утрешния таргет от {entry.get('target_calories')} ккал).
                3. Предложение за 3 конкретни ястия за утре.
                4. Предложение за утрешна физическа активност или тренировка.
                """

                with st.spinner("AI анализира и подготвя препоръки..."):
                    try:
                        response = g4f.ChatCompletion.create(
                            model=g4f.models.default,
                            messages=[{"role": "user", "content": prompt}]
                        )
                        st.session_state.ai_response = response
                        st.success("✅ Персоналният одит и макросите са готови!")
                    except:
                        st.error("Възникна временна грешка при връзката с AI сървъра. Моля, опитайте пак.")
        else:
            st.warning("Първо запиши поне един ден в Дневния отчет!")

        if st.session_state.get('ai_response'):
            st.markdown("### 📋 Интелигентни насоки от твоя AI Треньор")
            st.markdown(st.session_state.ai_response)

            links = extract_youtube_links(st.session_state.ai_response)
            if links:
                st.markdown("### 🎥 Видео демонстрации от AI")
                for i, link in enumerate(links):
                    with st.expander(f"▶️ AI Видео {i+1}", expanded=True):
                        try:
                            st.video(link.strip())
                        except:
                            st.markdown(f"[▶️ Отвори в YouTube]({link})")
            else:
                st.info("**AI-то не даде директни линкове в генерирания текст.** Ето твоята постоянна видео библиотека с упражнения:")

            st.markdown("### 🎯 Популярни упражнения с видео")
            fallback_videos = {
                "Клекове (Goblet Squat)": "https://www.youtube.com/watch?v=aclHkVaku9U",
                "Лицеви опори (Push-ups)": "https://www.youtube.com/watch?v=IODxDxX7oi4",
                "Коремни преси (Crunches)": "https://www.youtube.com/watch?v=1fbU_MkV7NE",
                "Бицепс сгъване": "https://www.youtube.com/watch?v=ykJmrZ5v0Oo",
                "Рамо преса (Overhead Press)": "https://www.youtube.com/watch?v=qEwKCR5JCog",
                "Планк": "https://www.youtube.com/watch?v=pSHjTRCQx7o",
                "Мъртва тяга (Romanian Deadlift)": "https://www.youtube.com/watch?v=ytGaGIn3Sj8"
            }

            cols = st.columns(3)
            for idx, (exercise, video_url) in enumerate(fallback_videos.items()):
                with cols[idx % 3]:
                    with st.expander(f"▶️ {exercise}", expanded=False):
                        try:
                            st.video(video_url)
                        except:
                            st.markdown(f"[▶️ Гледай {exercise}]({video_url})")

            st.markdown("---")
            st.subheader("💬 Обратна връзка към AI")
            feedback = st.text_area("Как се чувстваш спрямо този план? Искаш ли някаква промяна или модификация?", placeholder="Искам по-малко въглехидрати, повече коремни упражнения...", height=100)
            
            if st.button("✉️ Изпрати обратна връзка"):
                if feedback.strip():
                    with st.spinner("AI преработва и адаптира плана..."):
                        try:
                            fb_prompt = f"Предишният генериран план:\n{st.session_state.ai_response}\n\nПотребителска обратна връзка: {feedback}\n\nОтговори на потребителя и коригирай/адаптирай плана спрямо неговите изисквания."
                            new_response = g4f.ChatCompletion.create(
                                model=g4f.models.default,
                                messages=[{"role": "user", "content": fb_prompt}]
                            )
                            st.session_state.ai_response = st.session_state.ai_response + "\n\n---\n\n**🔄 Адаптиран план:**\n" + new_response
                            st.rerun()
                        except:
                            st.error("Грешка при преработването на плана.")
                else:
                    st.warning("Моля, напиши коментар в полето преди да изпратиш!")

            st.caption("⚠️ **Отказ от отговорност**: Това е AI генерирано съдържание за фитнес и хранене.")

    # ====================== TAB 4: ИСТОРИЯ ======================
    with tab4:
        st.subheader("📜 Пълна История на записите")
        if st.session_state.data:
            for day_str, info in sorted(st.session_state.data.items(), reverse=True):
                with st.expander(f"📅 Ден: {day_str} | Тегло: {info.get('weight')} кг"):
                    st.write(f"💧 **Вода:** {info.get('water')} л | 😴 **Сън:** {info.get('sleep')} часа | 🧠 **Тонус:** {info.get('mood')}")
                    st.write(f"🍽️ **Храна:** {info.get('food') if info.get('food') else 'Няма запис'}")
                    st.write(f"🏃 **Активност:** {info.get('activity') if info.get('activity') else 'Няма запис'}")
        else:
            st.info("Все още няма записана история.")
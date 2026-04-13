import streamlit as st
import pandas as pd
import random

st.set_page_config(page_title="Hasičský Trenažér", page_icon="🚒", layout="centered")

# --- JS SKRIPT PRO OVLÁDÁNÍ (ŠIPKY, ENTER, ČÍSLA) ---
def inject_control_logic():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        let currentIndex = 0;

        function getButtons() {
            // Najde všechna standardní tlačítka v hlavním bloku, která nejsou disabled
            return Array.from(doc.querySelectorAll('button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"]'))
                .filter(btn => !btn.disabled && !btn.innerText.includes('Restart'));
        }

        function highlight(btns) {
            btns.forEach((b, i) => {
                if (i === currentIndex) {
                    b.style.outline = '4px solid #FF4B4B';
                    b.style.outlineOffset = '2px';
                    b.style.backgroundColor = 'rgba(255, 75, 75, 0.1)';
                    b.focus();
                } else {
                    b.style.outline = 'none';
                    b.style.backgroundColor = '';
                }
            });
        }

        doc.onkeydown = function(e) {
            const btns = getButtons();
            if (btns.length === 0) return;

            // Pokud je tam tlačítko "Další otázka", Enter ho stiskne hned
            const nextBtn = btns.find(b => b.innerText.includes('Další otázka'));

            if (e.key === 'ArrowDown') {
                currentIndex = (currentIndex + 1) % btns.length;
                highlight(btns);
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                currentIndex = (currentIndex - 1 + btns.length) % btns.length;
                highlight(btns);
                e.preventDefault();
            } else if (e.key === 'Enter') {
                if (nextBtn) {
                    nextBtn.click();
                } else if (btns[currentIndex]) {
                    btns[currentIndex].click();
                }
                currentIndex = 0;
            } else if (['1', '2', '3'].includes(e.key)) {
                const idx = parseInt(e.key) - 1;
                if (btns[idx]) btns[idx].click();
            }
        };

        // Automatické zvýraznění prvního tlačítka při změně stránky
        const observer = new MutationObserver(() => {
            const btns = getButtons();
            if (btns.length > 0) highlight(btns);
        });
        observer.observe(doc.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

# --- CSS PRO VZHLED ---
st.markdown("""
    <style>
    .stSubheader p { color: #000000 !important; font-weight: bold !important; font-size: 1.2rem !important; }
    .stCaption { color: #1B1D23 !important; font-size: 0.9rem !important; }
    div[data-testid="stButton"] button { min-height: 3.5rem !important; border-radius: 10px !important; }
    #MainMenu, footer, header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

# --- 1. NAČTENÍ DAT ---
@st.cache_data
def load_data():
    try:
        df_raw = pd.read_excel("zop_200.xlsx", header=None)
        seznam = []
        for i in range(0, len(df_raw), 5):
            if i < len(df_raw) and pd.notna(df_raw.iloc[i, 1]):
                seznam.append({
                    "text": str(df_raw.iloc[i, 1]),
                    "spravna": str(df_raw.iloc[i+1, 1]),
                    "moznosti": [str(df_raw.iloc[i+1, 1]), str(df_raw.iloc[i+2, 1]), str(df_raw.iloc[i+3, 1])]
                })
        return seznam
    except: return []

# --- 2. SESSION STATE ---
if 'fronta' not in st.session_state:
    st.session_state.fronta = load_data()
    st.session_state.historie = []
    st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1) if st.session_state.fronta else 0
    st.session_state.odpovezeno = False

if 'mix' not in st.session_state and st.session_state.fronta:
    m = st.session_state.fronta[st.session_state.idx]["moznosti"][:]
    random.shuffle(m)
    st.session_state.mix = m

# --- 3. LOGIKA ---
def potvrdit():
    st.session_state.odpovezeno = True

def klik_dalsi():
    aktualni = st.session_state.fronta[st.session_state.idx]
    is_correct = (st.session_state.vyber == aktualni["spravna"])
    
    # Uložit do historie
    st.session_state.historie.insert(0, {
        "vysledek": "✅" if is_correct else "❌",
        "otazka": aktualni["text"],
        "spravna": aktualni["spravna"]
    })
    st.session_state.historie = st.session_state.historie[:5]

    # Pokud správně, vyřadit z fronty
    if is_correct:
        st.session_state.fronta.pop(st.session_state.idx)
    
    # Reset pro další kolo
    if st.session_state.fronta:
        st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1)
        st.session_state.odpovezeno = False
        if 'mix' in st.session_state: del st.session_state.mix

# --- 4. UI ---
st.title("🚒 Hasičský Trenažér")

if not st.session_state.fronta:
    st.success("🎉 Hotovo! Všechny otázky umíte.")
    if st.button("Začít znovu"):
        st.session_state.clear()
        st.rerun()
else:
    q = st.session_state.fronta[st.session_state.idx]
    
    st.progress(1 - (len(st.session_state.fronta) / 200))
    st.subheader(q["text"])

    # KLÍČOVÝ PRVEK: radio button lze ovládat šipkami (když na něj kliknete)
    st.radio(
        "Vyberte odpověď šipkami:",
        st.session_state.mix,
        key="vyber",
        disabled=st.session_state.odpovezeno,
        label_visibility="collapsed"
    )

    st.write("") # Mezera

    if not st.session_state.odpovezeno:
        st.button("Potvrdit (Enter)", on_click=potvrdit, type="primary", use_container_width=True)
    else:
        if st.session_state.vyber == q["spravna"]:
            st.success(f"✅ Správně!")
        else:
            st.error(f"❌ Chyba! Správná odpověď: {q['spravna']}")
        
        st.button("Další otázka (Enter)", on_click=klik_dalsi, type="primary", use_container_width=True)

    # Historie
    if st.session_state.historie:
        st.write("---")
        for h in st.session_state.historie:
            st.caption(f"{h['vysledek']} {h['otazka'][:80]}...")

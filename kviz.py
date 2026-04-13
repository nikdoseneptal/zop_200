import streamlit as st
import pandas as pd
import random
import streamlit.components.v1 as components

st.set_page_config(page_title="Hasičský Trenažér", page_icon="🚒", layout="centered")

# --- JS SKRIPT PRO OVLÁDÁNÍ ---
def inject_control_logic():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        let currentIndex = 0;

        function getButtons() {
            // Hledáme tlačítka odpovědí nebo tlačítko Další v hlavním kontejneru
            return Array.from(doc.querySelectorAll('button[data-testid="baseButton-secondary"], button[data-testid="baseButton-primary"]'))
                .filter(btn => !btn.disabled && (btn.innerText.length > 0) && !btn.innerText.includes('Restart'));
        }

        function highlight(btns) {
            btns.forEach((b, i) => {
                if (i === currentIndex) {
                    b.style.outline = '4px solid #FF4B4B';
                    b.style.outlineOffset = '2px';
                    b.focus();
                } else {
                    b.style.outline = 'none';
                }
            });
        }

        doc.onkeydown = function(e) {
            const btns = getButtons();
            if (btns.length === 0) return;

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
                    currentIndex = 0;
                } else if (btns[currentIndex]) {
                    btns[currentIndex].click();
                    currentIndex = 0;
                }
            } else if (['1', '2', '3'].includes(e.key)) {
                const idx = parseInt(e.key) - 1;
                if (btns[idx]) btns[idx].click();
            }
        };

        // Pozvolnější sledování změn (řeší mizení prvků při načítání)
        let timeout;
        const observer = new MutationObserver(() => {
            clearTimeout(timeout);
            timeout = setTimeout(() => {
                const btns = getButtons();
                if (btns.length > 0) highlight(btns);
            }, 100); 
        });
        observer.observe(doc.body, { childList: true, subtree: true });
        </script>
        """,
        height=0,
    )

# --- CSS PRO VZHLED ---
st.markdown("""
    <style>
    /* Oprava kontrastu */
    .stSubheader p { color: #000000 !important; font-weight: bold !important; font-size: 1.2rem !important; }
    .stCaption { color: #1B1D23 !important; font-size: 0.9rem !important; }
    
    /* Větší tlačítka */
    div[data-testid="stButton"] button { min-height: 3.5rem !important; border-radius: 10px !important; }

    /* MENU ZDE NECHÁVÁME VIDITELNÉ (smazáno visibility: hidden) */
    
    /* Větší prostor nahoře */
    .block-container { padding-top: 3rem !important; }
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
    except Exception as e:
        st.error(f"Chyba při načítání Excelu: {e}")
        return []

# --- 2. SESSION STATE ---
if 'fronta' not in st.session_state:
    st.session_state.fronta = load_data()
    st.session_state.historie = []
    st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1) if st.session_state.fronta else 0
    st.session_state.odpovezeno = False
    st.session_state.vysledek = None

if 'mix' not in st.session_state and st.session_state.fronta:
    m = st.session_state.fronta[st.session_state.idx]["moznosti"][:]
    random.shuffle(m)
    st.session_state.mix = m

# --- 3. LOGIKA ---
def klik_odpoved(volba):
    if not st.session_state.odpovezeno:
        aktualni = st.session_state.fronta[st.session_state.idx]
        st.session_state.odpovezeno = True
        is_correct = (volba == aktualni["spravna"])
        st.session_state.vysledek = "ok" if is_correct else "error"
        st.session_state.historie.insert(0, {
            "vysledek": "✅" if is_correct else "❌",
            "otazka": aktualni["text"],
            "spravna": aktualni["spravna"]
        })
        st.session_state.historie = st.session_state.historie[:5]

def klik_dalsi():
    if st.session_state.vysledek == "ok":
        st.session_state.fronta.pop(st.session_state.idx)
    if st.session_state.fronta:
        st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1)
        st.session_state.odpovezeno = False
        st.session_state.vysledek = None
        if 'mix' in st.session_state: del st.session_state.mix

# --- 4. UI ---
inject_control_logic()

if not st.session_state.fronta:
    st.success("🎉 Hotovo! Všechny otázky umíte.")
    if st.button("Začít znovu", type="primary"):
        st.session_state.clear()
        st.rerun()
else:
    zbiva = len(st.session_state.fronta)
    st.progress(1 - (zbiva / 200) if zbiva <= 200 else 0)
    
    q = st.session_state.fronta[st.session_state.idx]
    st.subheader(q["text"])

    for i, m in enumerate(st.session_state.mix):
        st.button(
            m, 
            key=f"b{i}", 
            on_click=klik_odpoved, 
            args=(m,),
            use_container_width=True, 
            disabled=st.session_state.odpovezeno
        )

    if st.session_state.odpovezeno:
        if st.session_state.vysledek == "ok":
            st.success("✅ Správně!")
        else:
            st.error(f"❌ Chyba! Správně: {q['spravna']}")
        
        st.button("Další otázka", key="btn_next", on_click=klik_dalsi, type="primary", use_container_width=True)

    if st.session_state.historie:
        st.write("---")
        for h in st.session_state.historie:
            st.caption(f"{h['vysledek']} {h['otazka'][:80]}... ({h['spravna']})")

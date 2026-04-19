import streamlit as st
import pandas as pd
import random
import streamlit.components.v1 as components

# --- KONFIGURACE STRÁNKY ---
st.set_page_config(page_title="Hasičský Trenažér", page_icon="🚒")

# --- JS SKRIPT PRO OVLÁDÁNÍ (ŠIPKY, ENTER, ČÍSLA) ---
def inject_control_logic():
    components.html(
        """
        <script>
        const doc = window.parent.document;
        let currentIndex = 0;
        const marks = ["\u200D ", "\u200D ", "\u200D "];

        function getButtons() {
            return Array.from(doc.querySelectorAll('button')).filter(btn => 
                btn.innerText.includes('\u200D') || btn.innerText.includes('Další otázka')
            );
        }

        doc.onkeydown = function(e) {
            const btns = getButtons();
            const nextBtn = btns.find(b => b.innerText.includes('Další otázka'));
            
            if (nextBtn) {
                if (e.key === 'Enter') nextBtn.click();
                return;
            }

            if (['1', '2', '3'].includes(e.key)) {
                const mark = marks[parseInt(e.key) - 1];
                const target = btns.find(b => b.innerText.includes(mark));
                if (target) target.click();
                return;
            }

            if (e.key === 'ArrowDown') {
                currentIndex = (currentIndex + 1) % 3;
                highlight(btns);
                e.preventDefault();
            } else if (e.key === 'ArrowUp') {
                currentIndex = (currentIndex - 1 + 3) % 3;
                highlight(btns);
                e.preventDefault();
            } else if (e.key === 'Enter') {
                if (btns[currentIndex]) btns[currentIndex].click();
            }
        };

        function highlight(btns) {
            btns.forEach((b, i) => {
                b.style.outline = (i === currentIndex) ? '4px solid #FF4B4B' : 'none';
                b.style.outlineOffset = '2px';
            });
        }
        </script>
        """,
        height=0,
    )

# --- CSS PRO VZHLED ---
st.markdown("""
    <style>
    .stSubheader p { color: #000000 !important; font-weight: bold !important; }
    .stCaption { color: #1B1D23 !important; font-size: 0.9rem !important; }
    div[data-testid="stButton"] button p { font-size: 1.1rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 1. NAČTENÍ DAT ---
@st.cache_data
def load_data():
    try:
        # Načtení Excelu - předpokládá soubor ve stejné složce
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
        st.error(f"Chyba při načítání souboru: {e}")
        return []

# --- 2. SESSION STATE (PAMĚŤ APLIKACE) ---
if 'fronta' not in st.session_state:
    st.session_state.fronta = load_data()
    st.session_state.historie = []
    st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1) if st.session_state.fronta else 0
    st.session_state.odpovezeno = False
    st.session_state.vysledek = None

# Míchání možností (aby nebyla správná vždy první)
if 'mix' not in st.session_state and st.session_state.fronta:
    m = st.session_state.fronta[st.session_state.idx]["moznosti"][:]
    random.shuffle(m)
    st.session_state.mix = m

# --- 3. LOGIKA OVLÁDÁNÍ ---
def klik_odpoved(volba):
    if not st.session_state.odpovezeno:
        aktualni = st.session_state.fronta[st.session_state.idx]
        st.session_state.odpovezeno = True
        is_correct = (volba == aktualni["spravna"])
        st.session_state.vysledek = "ok" if is_correct else "error"
        
        # Přidání do historie (posledních 5)
        st.session_state.historie.insert(0, {
            "vysledek": "✅" if is_correct else "❌",
            "otazka": aktualni["text"],
            "spravna": aktualni["spravna"]
        })
        st.session_state.historie = st.session_state.historie[:5]

def klik_dalsi():
    # Pokud byla odpověď správná, vyřadíme otázku z fronty
    if st.session_state.vysledek == "ok":
        st.session_state.fronta.pop(st.session_state.idx)
    
    if st.session_state.fronta:
        st.session_state.idx = random.randint(0, len(st.session_state.fronta)-1)
        st.session_state.odpovezeno = False
        st.session_state.vysledek = None
        if 'mix' in st.session_state:
            del st.session_state.mix

# --- 4. UI (UŽIVATELSKÉ ROZHRANÍ) ---
inject_control_logic()

if not st.session_state.fronta:
    st.success("🎉 Všechny otázky jsou hotovy!")
    if st.button("Restartovat test"):
        st.session_state.clear()
        st.rerun()
else:
    # Progress bar
    zbiva = len(st.session_state.fronta)
    st.progress(max(0.0, min(1.0, 1 - (zbiva / 200))))
    st.write(f"Zbývá otázek: {zbiva}")
    
    # Zobrazení otázky
    q = st.session_state.fronta[st.session_state.idx]
    st.subheader(q["text"])

    # Tlačítka s odpověďmi
    marks = ["\u200D ", "\u200D ", "\u200D "]
    for i, m in enumerate(st.session_state.mix):
        label = f"{marks[i]}{m}"
        st.button(
            label, 
            key=f"b{i}", 
            on_click=klik_odpoved, 
            args=(m,), 
            use_container_width=True, 
            disabled=st.session_state.odpovezeno
        )

    # Vyhodnocení po kliknutí
    if st.session_state.odpovezeno:
        if st.session_state.vysledek == "ok":
            st.success("✅ Správně!")
        else:
            st.error(f"❌ Chyba! Správně je: {q['spravna']}")
        
        st.button("Další otázka (Enter)", key="btn_next", on_click=klik_dalsi, type="primary", use_container_width=True)

    # Historie posledních pokusů
    if st.session_state.historie:
        st.write("---")
        st.write("Historie:")
        for h in st.session_state.historie:
            st.caption(f"{h['vysledek']} {h['otazka'][:80]}... (Správně: {h['spravna']})")

import streamlit as st
import io
import zipfile
import pyloudnorm as pyln
from pedalboard import Pedalboard, Compressor, Gain, Limiter, HighpassFilter
from pedalboard.io import AudioFile

st.set_page_config(page_title="Kelly AI Mastering PRO", layout="wide")

# ══════════════════════════════════════════════════════════
# 데이터
# ══════════════════════════════════════════════════════════
GENRE_CATEGORIES = [
    "Pop / R&B", "Hip-Hop / Urban", "Rock / Metal",
    "Electronic", "World Music", "Jazz / Acoustic"
]
GENRE_SUBS = [
    ["Pop", "Ballad", "K-Pop", "J-Pop", "R&B", "Soul", "Indie"],
    ["Hip-Hop", "Trap", "Boom Bap", "Lo-Fi", "R&B/Hip-Hop"],
    ["Rock", "Metal", "Punk", "Grunge", "Modern Rock"],
    ["EDM", "House", "Techno", "Ambient", "Future Bass"],
    ["Country", "Reggae", "Latin", "Afrobeats", "Disco"],
    ["Jazz", "Café Jazz", "Bossa Nova", "Classical", "Acoustic"],
]

FORMAT_OPTIONS = ["MP3 · 320kbps", "WAV · 16bit 44.1kHz", "WAV · 24bit 48kHz", "FLAC · 24bit 96kHz"]
LUFS_OPTIONS   = ["Auto (No Target)", "YouTube  –14", "Streaming  –13", "Standard  –11", "Loud  –9"]
COMP_OPTIONS   = ["🌙  Light", "⚡  Normal", "🔥  Strong"]

def build_genre_opts():
    opts = []
    for cat, subs in zip(GENRE_CATEGORIES, GENRE_SUBS):
        opts.append(f"§{cat}")
        for sub in subs:
            opts.append(sub)
    return opts

GENRE_OPTS      = build_genre_opts()
SELECTABLE_GENRE = [g for g in GENRE_OPTS if not g.startswith("§")]

# ══════════════════════════════════════════════════════════
# 언어
# ══════════════════════════════════════════════════════════
LANG = {
    "ko": {
        "title":        "켈리의 AI 마스터링 스튜디오",
        "badge":        "Kelly Studio Engine v1.0",
        "file_label":   "음악 파일",
        "genre_label":  "장르 프리셋",
        "format_label": "출력 형식",
        "lufs_label":   "LUFS 타겟",
        "comp_label":   "3밴드 압축 강도",
        "run_btn":      "AI 마스터링 시작",
        "processing":   "오디오 처리 중...",
        "step3":        "3단계 — 다운로드",
        "download_all": "⬇  전체 트랙 다운로드 (.zip)",
        "save":         "저장",
        "done":         "✓ 완료",
        "reset_btn":    "↩  새 작업 시작",
        "lang_other":   "English",
        "lang_switch":  "en",
        "file_count":   lambda n: f"✓  총 {n}개 파일 선택됨",
    },
    "en": {
        "title":        "Kelly's AI Mastering Studio",
        "badge":        "Kelly Studio Engine v1.0",
        "file_label":   "Music File",
        "genre_label":  "Genre Preset",
        "format_label": "Output Format",
        "lufs_label":   "LUFS Target",
        "comp_label":   "3-Band Compression",
        "run_btn":      "Start AI Mastering",
        "processing":   "Processing audio...",
        "step3":        "Step 03 — Download",
        "download_all": "⬇  Download All Tracks (.zip)",
        "save":         "Save",
        "done":         "✓ Done",
        "reset_btn":    "↩  New Session",
        "lang_other":   "한국어",
        "lang_switch":  "ko",
        "file_count":   lambda n: f"✓  {n} file{'s' if n>1 else ''} selected",
    }
}

# ══════════════════════════════════════════════════════════
# 세션
# ══════════════════════════════════════════════════════════
for k, v in [
    ("downloaded_files", set()),
    ("mastered_results", []),
    ("lang", "ko"),
    ("selected_genre", SELECTABLE_GENRE[0]),
    ("uploader_key", 0),
]:
    if k not in st.session_state:
        st.session_state[k] = v

params = st.query_params
if "lang" in params and params["lang"] in LANG:
    st.session_state.lang = params["lang"]
    st.query_params.clear()
    st.rerun()

t = LANG[st.session_state.lang]

# ══════════════════════════════════════════════════════════
# CSS — 우주선AI 스타일
# ══════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700&family=Inter:wght@400;500;600;700&display=swap');

:root {
    --bg:        #1a1a2e;
    --nav:       #12122a;
    --surface:   #16213e;
    --surface2:  #1f2b47;
    --border:    #2a3a5c;
    --border2:   #3a4a6c;
    --text:      #e8e8f0;
    --text2:     #a8b4cc;
    --text3:     #6a7a9a;
    --green:     #4ade80;
    --green-dim: #1a3828;
    --green-dark:#166534;
    --green-glow:rgba(74,222,128,0.2);
}
*, *::before, *::after { box-sizing: border-box; }

.stApp {
    background-color: var(--bg) !important;
    color: var(--text) !important;
    font-family: 'Noto Sans KR', 'Inter', sans-serif;
    padding-top: 58px !important;
    padding-bottom: 100px !important;
}
.block-container {
    max-width: 680px !important;
    padding: 2rem 1.5rem 3rem !important;
    margin: auto;
}

/* ── 네비바 ── */
.kms-nav {
    position: fixed;
    top: 0; left: 0; right: 0;
    height: 58px;
    background: var(--nav);
    border-bottom: 1px solid var(--border);
    z-index: 99999;
    display: flex;
    align-items: center;
    padding: 0 2rem;
    gap: 16px;
}
.kms-nav-logo {
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--text);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    font-family: 'Inter', sans-serif;
}
.kms-nav-divider { width:1px; height:18px; background:var(--border2); flex-shrink:0; }
.kms-nav-badge {
    display: flex;
    align-items: center;
    gap: 7px;
    font-size: 0.7rem;
    color: var(--green);
    font-family: 'Inter', monospace;
    flex: 1;
}
.kms-nav-badge::before {
    content: '';
    width: 6px; height: 6px;
    border-radius: 50%;
    background: var(--green);
    animation: blink 2s infinite;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0.2} }
.kms-lang-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: var(--surface2);
    border: 1px solid var(--border2);
    border-radius: 6px;
    padding: 5px 14px;
    font-size: 0.75rem;
    font-weight: 500;
    color: var(--text2) !important;
    text-decoration: none !important;
    white-space: nowrap;
    transition: all 0.15s;
}
.kms-lang-btn:hover { border-color: var(--green); color: var(--green) !important; }

/* ── 헤더 ── */
.kms-header {
    margin-bottom: 2rem;
    padding-bottom: 1.5rem;
    border-bottom: 1px solid var(--border);
}
.kms-header h2 {
    font-size: 1.5rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 4px 0;
}
.kms-header .sub {
    font-size: 0.72rem;
    color: var(--text3);
    font-family: 'Inter', monospace;
}

/* ── 섹션 레이블 ── */
.sec-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text2);
    margin-bottom: 8px;
    font-family: 'Noto Sans KR', sans-serif;
}

/* ── 파일 업로더 ── */
[data-testid="stFileUploader"] {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 1.2rem 1.5rem !important;
    transition: all 0.2s;
    margin-bottom: 1.2rem;
}
[data-testid="stFileUploader"]:hover {
    border-color: var(--green) !important;
}
[data-testid="stFileUploader"] > label { display: none !important; }
[data-testid="stFileUploaderDropzone"] { background: transparent !important; border: none !important; }
[data-testid="stFileUploaderDropzone"] p,
[data-testid="stFileUploaderDropzone"] span {
    color: var(--text2) !important;
    font-size: 0.92rem !important;
    font-weight: 500 !important;
}
[data-testid="stFileUploaderDropzone"] small { color: var(--text3) !important; }
[data-testid="stFileUploaderFileName"] { color: var(--text) !important; }
[data-testid="stFileUploaderDropzone"] button {
    background: var(--green) !important;
    border: none !important;
    color: #000 !important;
    border-radius: 7px !important;
    font-size: 0.83rem !important;
    font-weight: 700 !important;
    padding: 7px 18px !important;
}

/* ── 셀렉트박스 ── */
[data-testid="stSelectbox"] label,
[data-testid="stSelectbox"] label p {
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    color: var(--text2) !important;
    font-family: 'Noto Sans KR', sans-serif !important;
    margin-bottom: 6px !important;
    text-transform: none !important;
    letter-spacing: 0 !important;
}
[data-testid="stSelectbox"] > div > div {
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text) !important;
    font-size: 0.92rem !important;
    min-height: 48px !important;
    margin-bottom: 1rem;
}
[data-testid="stSelectbox"] > div > div:hover { border-color: var(--border2) !important; }
[data-testid="stSelectbox"] > div > div:focus-within { border-color: var(--green) !important; }
[data-testid="stSelectbox"] span { color: var(--text) !important; }

/* 드롭다운 목록 */
ul[role="listbox"] {
    background: #1a1f35 !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    box-shadow: 0 8px 32px rgba(0,0,0,0.6) !important;
    padding: 4px 0 !important;
}
li[role="option"] {
    background: transparent !important;
    color: var(--text2) !important;
    font-size: 0.9rem !important;
    padding: 9px 16px !important;
    border-radius: 0 !important;
    border: none !important;
    margin: 0 !important;
}
li[role="option"]:hover { background: var(--surface2) !important; color: var(--text) !important; }
li[role="option"][aria-selected="true"] { background: var(--green-dim) !important; color: var(--green) !important; font-weight: 600 !important; }
li[role="option"][aria-disabled="true"] { color: var(--green) !important; font-weight: 700 !important; font-size: 0.78rem !important; padding-top: 12px !important; }
ul[role="listbox"]::-webkit-scrollbar { width: 4px; }
ul[role="listbox"]::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 4px; }

/* ── 압축강도 라디오 (가로) ── */
[data-testid="stRadio"] > label { display: none !important; }
[data-testid="stRadio"] > div {
    display: flex !important;
    gap: 8px !important;
    flex-wrap: nowrap !important;
    margin-bottom: 1rem;
}
[data-testid="stRadio"] > div > label {
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex: 1 !important;
    background: var(--surface) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    padding: 10px 8px !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    font-size: 0.88rem !important;
    font-weight: 500 !important;
    color: var(--text2) !important;
    min-width: unset !important;
    width: unset !important;
}
[data-testid="stRadio"] > div > label:hover {
    border-color: var(--border2) !important;
    color: var(--text) !important;
}
[data-testid="stRadio"] > div > label:has(input:checked) {
    background: var(--green-dim) !important;
    border-color: var(--green) !important;
    color: var(--green) !important;
    font-weight: 600 !important;
}
[data-testid="stRadio"] > div > label > div:first-child { display: none !important; }
[data-testid="stRadio"] > div > label > div:last-child { font-size: 0.88rem !important; font-weight: 500 !important; }
[data-testid="stRadio"] > div > label:has(input:checked) > div:last-child { color: var(--green) !important; }

/* ── 섹션 박스 ── */
.section-box {
    background: var(--surface);
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 1rem 1.2rem 0.5rem;
    margin-bottom: 1rem;
}
.section-box-title {
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text2);
    margin-bottom: 0.8rem;
    font-family: 'Noto Sans KR', sans-serif;
}
.section-box-desc {
    font-size: 0.75rem;
    color: var(--text3);
    margin-top: 4px;
    margin-bottom: 0.5rem;
}

/* ── 하단 고정 버튼 영역 ── */
.kms-bottom {
    position: fixed;
    bottom: 0; left: 0; right: 0;
    background: var(--nav);
    border-top: 1px solid var(--border);
    padding: 12px 2rem;
    z-index: 9998;
    display: flex;
    justify-content: center;
}
.kms-bottom-inner {
    width: 100%;
    max-width: 680px;
}

/* ── RUN 버튼 ── */
.stButton > button {
    width: 100% !important;
    background: var(--green) !important;
    color: #000 !important;
    border: none !important;
    border-radius: 8px !important;
    height: 50px !important;
    font-size: 0.95rem !important;
    font-weight: 700 !important;
    font-family: 'Noto Sans KR', 'Inter', sans-serif !important;
    cursor: pointer !important;
    transition: all 0.15s !important;
    margin-top: 0 !important;
}
.stButton > button:hover {
    background: #22c55e !important;
    box-shadow: 0 4px 20px var(--green-glow) !important;
}
.stButton > button:disabled {
    background: var(--surface2) !important;
    color: var(--text3) !important;
    cursor: not-allowed !important;
    box-shadow: none !important;
}

/* ── 다운로드 버튼 ── */
.stDownloadButton > button {
    background: var(--surface) !important;
    color: var(--text) !important;
    border: 1.5px solid var(--border) !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 500 !important;
    height: 42px !important;
    transition: all 0.15s !important;
}
.stDownloadButton > button:hover { border-color: var(--green) !important; color: var(--green) !important; }
[data-testid="stDownloadButton"]:first-of-type > button {
    background: var(--green-dim) !important;
    border-color: rgba(74,222,128,0.4) !important;
    color: var(--green) !important;
    height: 50px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
}

/* ── 페이지네이션 ── */
[data-testid="stFileUploaderPagination"] p,
[data-testid="stFileUploaderPagination"] span { color: var(--text2) !important; font-size: 0.82rem !important; }

/* ── 기타 ── */
audio { height: 34px !important; filter: invert(0.85) sepia(0.5) saturate(1.5) hue-rotate(90deg); }
hr { border-color: var(--border) !important; margin: 1.5rem 0 !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton, [data-testid="stToolbar"] { display: none; }
[data-testid="stSpinner"] > div { border-top-color: var(--green) !important; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 네비바
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="kms-nav">
    <span class="kms-nav-logo">Kelly Mastering</span>
    <span class="kms-nav-divider"></span>
    <span class="kms-nav-badge">{t["badge"]}</span>
    <a class="kms-lang-btn" href="?lang={t['lang_switch']}" target="_self">
        🌐 {t["lang_other"]}
    </a>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 헤더
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="kms-header">
    <h2>{t["title"]}</h2>
    <div class="sub">{t["badge"]}</div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 음악 파일
# ══════════════════════════════════════════════════════════
st.markdown(f'<div class="sec-label">{t["file_label"]}</div>', unsafe_allow_html=True)
uploaded_files = st.file_uploader(
    "upload", type=["wav", "mp3"],
    accept_multiple_files=True,
    label_visibility="collapsed",
    key=f"uploader_{st.session_state.uploader_key}"
)
if uploaded_files:
    st.markdown(
        f"<div style='margin-top:-8px;margin-bottom:12px;font-size:0.8rem;color:#4ade80;'>{t['file_count'](len(uploaded_files))}</div>",
        unsafe_allow_html=True
    )

# ══════════════════════════════════════════════════════════
# 장르 프리셋
# ══════════════════════════════════════════════════════════
def genre_fmt(val):
    if val.startswith("§"):
        return f"── {val[1:]}"
    return f"   {val}"

chosen = st.selectbox(
    t["genre_label"],
    options=GENRE_OPTS,
    index=GENRE_OPTS.index(st.session_state.selected_genre),
    format_func=genre_fmt,
    key="genre_select"
)
if chosen.startswith("§"):
    next_g = next((g for g in GENRE_OPTS[GENRE_OPTS.index(chosen)+1:] if not g.startswith("§")), SELECTABLE_GENRE[0])
    st.session_state.selected_genre = next_g
    st.rerun()
else:
    st.session_state.selected_genre = chosen
selected_genre = chosen

# ══════════════════════════════════════════════════════════
# 출력 형식
# ══════════════════════════════════════════════════════════
format_choice = st.selectbox(t["format_label"], FORMAT_OPTIONS)
out_format_ext = "mp3" if "MP3" in format_choice else ("flac" if "FLAC" in format_choice else "wav")

# ══════════════════════════════════════════════════════════
# LUFS 타겟
# ══════════════════════════════════════════════════════════
lufs_choice = st.selectbox(t["lufs_label"], LUFS_OPTIONS)
if lufs_choice == LUFS_OPTIONS[0]:
    target_lufs = -14.0  # Auto → 기본 -14
else:
    target_lufs = -float(lufs_choice.split("–")[1])

# ══════════════════════════════════════════════════════════
# 압축 강도 (섹션 박스)
# ══════════════════════════════════════════════════════════
st.markdown(f"""
<div class="section-box">
    <div class="section-box-title">{t["comp_label"]}</div>
""", unsafe_allow_html=True)

comp_strength = st.radio(
    "comp", COMP_OPTIONS, index=1,
    horizontal=True, label_visibility="collapsed", key="comp_radio"
)
comp_db = {"Light": -18, "Normal": -22, "Strong": -26}[comp_strength.split()[-1]]

# 선택된 강도 설명
desc = {"Light": "균형 잡힌 자연스러운 사운드", "Normal": "균형 잡힌 밀도감", "Strong": "강한 압축, 임팩트 있는 사운드"}
st.markdown(f'<div class="section-box-desc">{desc[comp_strength.split()[-1]]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════
# 하단 고정 RUN 버튼
# ══════════════════════════════════════════════════════════
st.markdown("""
<div class="kms-bottom">
    <div class="kms-bottom-inner" id="run-btn-area"></div>
</div>
""", unsafe_allow_html=True)

run_clicked = st.button(
    t["run_btn"],
    disabled=not bool(uploaded_files),
    key="run_btn",
    use_container_width=True
)

# ══════════════════════════════════════════════════════════
# 마스터링 처리
# ══════════════════════════════════════════════════════════
if run_clicked and uploaded_files:
    with st.spinner(t["processing"]):
        temp_results = []
        for file in uploaded_files:
            input_io = io.BytesIO(file.read())
            with AudioFile(input_io) as f:
                audio = f.read(f.frames)
                board = Pedalboard([
                    HighpassFilter(30),
                    Compressor(threshold_db=comp_db),
                    Gain(target_lufs - pyln.Meter(f.samplerate).integrated_loudness(audio.T)),
                    Limiter(-0.1)
                ])
                processed = board(audio, f.samplerate)
                out_io = io.BytesIO()
                with AudioFile(out_io, 'w', f.samplerate, f.num_channels, format=out_format_ext) as o:
                    o.write(processed)
                temp_results.append({
                    "name": file.name,
                    "data": out_io.getvalue(),
                    "ext":  out_format_ext,
                    "id":   f"{file.name}_{out_format_ext}"
                })
        st.session_state.mastered_results = temp_results

# ══════════════════════════════════════════════════════════
# 결과 다운로드
# ══════════════════════════════════════════════════════════
if st.session_state.mastered_results:
    st.divider()
    st.markdown(f'<div class="sec-label">{t["step3"]}</div>', unsafe_allow_html=True)

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zf:
        for res in st.session_state.mastered_results:
            zf.writestr(f"Mastered_{res['name']}.{res['ext']}", res['data'])

    st.download_button(
        label=t["download_all"],
        data=zip_buffer.getvalue(),
        file_name="Mastered_Tracks.zip",
        use_container_width=True
    )
    st.write("")

    for idx, res in enumerate(st.session_state.mastered_results):
        ca, cb, cc = st.columns([4, 6, 2])
        with ca:
            st.markdown(
                f"<div style='padding:9px 0;font-size:0.85rem;color:#c8c8d8;font-weight:500;'>🎵 {res['name']}</div>",
                unsafe_allow_html=True
            )
        with cb:
            st.audio(res['data'], format=f"audio/{res['ext']}")
        with cc:
            is_done = res['id'] in st.session_state.downloaded_files
            st.download_button(
                label=t["done"] if is_done else f"{t['save']} {res['ext'].upper()}",
                data=res['data'],
                file_name=f"Mastered_{res['name']}.{res['ext']}",
                key=f"dl_{idx}",
                on_click=lambda id=res['id']: st.session_state.downloaded_files.add(id),
                use_container_width=True
            )

    # 새 작업 시작 버튼
    st.write("")
    st.divider()
    _, rc, _ = st.columns([1, 2, 1])
    with rc:
        if st.button(t["reset_btn"], key="reset_btn_v2", use_container_width=True):
            st.session_state.mastered_results = []
            st.session_state.downloaded_files = set()
            st.session_state.uploader_key += 1  # 파일 업로더 초기화
            st.rerun()

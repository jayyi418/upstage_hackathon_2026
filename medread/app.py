import os

import streamlit as st
from dotenv import load_dotenv

from sample_texts import SAMPLES
from services.document_parse import parse_document
from services.info_extract import extract_medical_info
from services.llm import assess_risk, chat_with_document, get_rich_translation

load_dotenv()

# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="MediRead — 진단서 번역기",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [class*="css"] { font-family: 'Noto Sans KR', sans-serif; }

/* ── 위험도 배지 ── */
.badge { display:inline-block; padding:3px 14px; border-radius:20px; font-weight:700; font-size:0.82rem; }
.badge-low    { background:#d4edda; color:#155724; }
.badge-medium { background:#fff3cd; color:#856404; }
.badge-high   { background:#f8d7da; color:#721c24; }

/* ── 진단 카드 ── */
.diag-card {
    background:white; border:1px solid #e0e0e0;
    border-radius:10px; padding:14px 18px; margin-bottom:10px;
    box-shadow:0 1px 4px rgba(0,0,0,0.06);
}

/* ── 원문 박스 ── */
.doc-box {
    background:#f8f9fa; padding:20px; border-radius:10px;
    height:520px; overflow-y:auto; font-size:0.85rem; line-height:1.75;
    border:1px solid #dee2e6; white-space:pre-wrap;
}

/* ── 요약 배너 ── */
.summary-banner {
    background:linear-gradient(135deg,#e8f4fd,#dbeafe);
    border-left:5px solid #3b82f6; border-radius:8px;
    padding:16px 20px; margin-bottom:18px;
    font-size:0.95rem; line-height:1.7; color:#1e3a5f;
}

/* ── 검사 결과 테이블 ── */
.result-table { width:100%; border-collapse:collapse; font-size:0.85rem; margin-bottom:18px; }
.result-table th {
    background:#f1f5f9; color:#475569; padding:8px 12px;
    text-align:left; font-weight:600; border-bottom:2px solid #cbd5e1;
}
.result-table td { padding:9px 12px; border-bottom:1px solid #f1f5f9; vertical-align:top; }
.row-high   { background:#fff5f5; }
.row-low    { background:#f0f5ff; }
.row-normal { background:#f0fdf4; }
.status-high   { color:#dc2626; font-weight:700; }
.status-low    { color:#2563eb; font-weight:700; }
.status-normal { color:#16a34a; font-weight:700; }
.orig-term { color:#94a3b8; font-size:0.78rem; }

/* ── 약물 카드 ── */
.med-grid { display:flex; flex-wrap:wrap; gap:10px; margin-bottom:18px; }
.med-card {
    background:white; border:1px solid #e2e8f0; border-radius:10px;
    padding:12px 16px; flex:1; min-width:180px; max-width:260px;
    box-shadow:0 1px 3px rgba(0,0,0,0.07);
}
.med-name { font-weight:700; color:#1e293b; font-size:0.88rem; margin-bottom:4px; }
.med-dose { color:#64748b; font-size:0.78rem; margin-bottom:6px; }
.med-purpose { color:#475569; font-size:0.82rem; background:#f8fafc; padding:5px 8px; border-radius:6px; }

/* ── 할 일 목록 ── */
.action-list { list-style:none; padding:0; margin:0 0 18px; }
.action-list li {
    display:flex; align-items:flex-start; gap:10px;
    padding:10px 14px; margin-bottom:8px;
    background:white; border:1px solid #e2e8f0; border-radius:8px;
    font-size:0.88rem; color:#1e293b;
    box-shadow:0 1px 3px rgba(0,0,0,0.05);
}
.action-check { color:#22c55e; font-size:1.1rem; flex-shrink:0; }

/* ── 섹션 제목 ── */
.section-title {
    font-size:0.8rem; font-weight:700; letter-spacing:0.08em;
    text-transform:uppercase; color:#64748b; margin:0 0 8px;
}

/* ── 면책 배너 ── */
.disclaimer {
    background:#fff8e1; border-left:4px solid #ffc107;
    padding:10px 16px; border-radius:6px;
    font-size:0.82rem; color:#6d5c00; margin-top:8px;
}
</style>
""", unsafe_allow_html=True)

# ── 세션 상태 ─────────────────────────────────────────────────────────────────
_DEFAULTS: dict = {
    "parsed_text": None,
    "rich_translation": None,   # dict from get_rich_translation()
    "extracted_info": None,
    "risk_assessments": None,
    "chat_messages": [],
    "processing_done": False,
    "demo_mode": False,
}
for k, v in _DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── 렌더링 헬퍼 ──────────────────────────────────────────────────────────────

_RISK_META = {
    "low":    ("🟢 경증",   "badge-low",    "일반적인 관리로 호전 가능"),
    "medium": ("🟡 중등증", "badge-medium", "정기 모니터링과 치료 필요"),
    "high":   ("🔴 중증",   "badge-high",   "즉각적인 의료 개입 권고"),
}
_STATUS_META = {
    "high":   ("🔴 높음", "status-high",   "row-high"),
    "low":    ("🔵 낮음", "status-low",    "row-low"),
    "normal": ("🟢 정상", "status-normal", "row-normal"),
}


def render_risk_section(risk_list: list):
    if not risk_list:
        return
    st.markdown("### 진단명 위험도 분석")
    cols = st.columns(min(len(risk_list), 3))
    for i, item in enumerate(risk_list):
        level = item.get("level", "low")
        label, css, default_reason = _RISK_META.get(level, _RISK_META["low"])
        with cols[i % len(cols)]:
            st.markdown(
                f'<div class="diag-card">'
                f'<span class="badge {css}">{label}</span><br>'
                f'<strong style="font-size:0.98rem">{item.get("diagnosis","")}</strong><br>'
                f'<span style="color:#666;font-size:0.8rem">{item.get("reason") or default_reason}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )


def render_rich_translation(rich: dict):
    """구조화된 번역 결과를 시각적으로 렌더링합니다."""

    # ① 요약 배너
    if summary := rich.get("summary"):
        st.markdown(
            f'<div class="summary-banner">💬 <strong>요약</strong><br>{summary}</div>',
            unsafe_allow_html=True,
        )

    # ② 검사 결과 컬러 테이블
    test_results = rich.get("test_results", [])
    if test_results:
        st.markdown('<div class="section-title">🧪 검사 결과</div>', unsafe_allow_html=True)
        rows_html = ""
        for tr in test_results:
            status = tr.get("status", "normal")
            s_label, s_class, row_class = _STATUS_META.get(status, _STATUS_META["normal"])
            orig = f'<br><span class="orig-term">{tr["original_term"]}</span>' if tr.get("original_term") else ""
            normal_range = tr.get("normal_range", "—")
            rows_html += (
                f'<tr class="{row_class}">'
                f'<td><strong>{tr["name"]}</strong>{orig}</td>'
                f'<td><strong>{tr["value"]}</strong> {tr.get("unit","")}</td>'
                f'<td style="color:#94a3b8">{normal_range}</td>'
                f'<td class="{s_class}">{s_label}</td>'
                f'<td style="color:#475569">{tr.get("plain_explanation","")}</td>'
                f'</tr>'
            )
        st.markdown(
            f'<table class="result-table">'
            f'<thead><tr>'
            f'<th>검사명</th><th>수치</th><th>정상 범위</th><th>상태</th><th>쉬운 설명</th>'
            f'</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            f'</table>',
            unsafe_allow_html=True,
        )

    # ③ 약물 카드 그리드
    medications = rich.get("medications", [])
    if medications:
        st.markdown('<div class="section-title">💊 처방 약물</div>', unsafe_allow_html=True)
        cards_html = '<div class="med-grid">'
        for med in medications:
            dose_html = f'<div class="med-dose">{med["dosage_instruction"]}</div>' if med.get("dosage_instruction") else ""
            cards_html += (
                f'<div class="med-card">'
                f'<div class="med-name">{med["name"]}</div>'
                f'{dose_html}'
                f'<div class="med-purpose">{med["purpose"]}</div>'
                f'</div>'
            )
        cards_html += "</div>"
        st.markdown(cards_html, unsafe_allow_html=True)

    # ④ 지금 해야 할 일
    action_items = rich.get("action_items", [])
    if action_items:
        st.markdown('<div class="section-title">✅ 지금 해야 할 일</div>', unsafe_allow_html=True)
        items_html = '<ul class="action-list">'
        for item in action_items:
            items_html += f'<li><span class="action-check">✓</span>{item}</li>'
        items_html += "</ul>"
        st.markdown(items_html, unsafe_allow_html=True)

    # ⑤ 전체 번역 (접기)
    if full := rich.get("full_explanation"):
        with st.expander("📄 전체 번역 자세히 보기"):
            st.markdown(full)


def reset_state():
    for k, v in _DEFAULTS.items():
        st.session_state[k] = v


# ── 처리 파이프라인 ───────────────────────────────────────────────────────────

def process_uploaded_file(file_bytes: bytes, filename: str):
    prog = st.progress(0, text="📄 문서 파싱 중...")
    try:
        st.session_state.parsed_text = parse_document(file_bytes, filename)
    except RuntimeError as e:
        st.error(f"문서 파싱 실패: {e}")
        return

    prog.progress(30, text="🔍 의학 정보 추출 중...")
    try:
        st.session_state.extracted_info = extract_medical_info(file_bytes, filename)
    except RuntimeError as e:
        st.warning(f"정보 추출 실패 (번역은 계속 진행합니다): {e}")
        st.session_state.extracted_info = {"diagnoses": []}

    diagnoses = st.session_state.extracted_info.get("diagnoses", [])
    prog.progress(50, text="⚕️ 위험도 평가 중...")
    try:
        st.session_state.risk_assessments = assess_risk(diagnoses)
    except Exception as e:
        st.warning(f"위험도 평가 실패: {e}")
        st.session_state.risk_assessments = []

    prog.progress(70, text="✍️ 구조화 번역 중...")
    try:
        st.session_state.rich_translation = get_rich_translation(st.session_state.parsed_text)
    except Exception as e:
        st.error(f"번역 실패: {e}")
        return

    prog.progress(100, text="✅ 완료!")
    st.session_state.processing_done = True
    st.session_state.demo_mode = False
    st.session_state.chat_messages = []


def process_sample(sample_key: str):
    sample = SAMPLES[sample_key]
    st.session_state.parsed_text = sample["parsed_text"]
    st.session_state.extracted_info = {"diagnoses": sample["diagnoses"]}

    prog = st.progress(0, text="⚕️ 위험도 평가 중...")
    try:
        st.session_state.risk_assessments = assess_risk(sample["diagnoses"])
    except Exception as e:
        st.warning(f"위험도 평가 실패: {e}")
        st.session_state.risk_assessments = []

    prog.progress(50, text="✍️ 구조화 번역 중...")
    try:
        st.session_state.rich_translation = get_rich_translation(sample["parsed_text"])
    except Exception as e:
        st.error(f"번역 실패: {e}")
        return

    prog.progress(100, text="✅ 완료!")
    st.session_state.processing_done = True
    st.session_state.demo_mode = True
    st.session_state.chat_messages = []


# ── 랜딩 페이지 ──────────────────────────────────────────────────────────────
if not st.session_state.processing_done:
    st.title("🏥 MediRead")
    st.subheader("진단서, 이제 진짜로 이해하세요")
    st.caption("의학 용어가 가득한 진단서를 누구나 이해할 수 있는 쉬운 한국어로 번역해드립니다.")
    st.markdown("---")

    col_upload, col_sample = st.columns([3, 2], gap="large")

    with col_upload:
        st.markdown("#### 📄 직접 업로드")
        uploaded = st.file_uploader(
            "진단서 또는 소견서 파일 (PDF, JPG, PNG)",
            type=["pdf", "jpg", "jpeg", "png"],
            label_visibility="collapsed",
        )
        if uploaded:
            st.success(f"파일 선택됨: **{uploaded.name}**")
            if st.button("🔍 분석 시작", type="primary", use_container_width=True):
                with st.spinner("분석 중..."):
                    process_uploaded_file(uploaded.getvalue(), uploaded.name)
                st.rerun()

    with col_sample:
        st.markdown("#### 🧪 샘플로 체험")
        st.caption("실제 파일 없이 즉시 데모 체험")
        for key, sample in SAMPLES.items():
            if st.button(sample["label"], use_container_width=True, key=f"sample_{key}"):
                with st.spinner("샘플 분석 중..."):
                    process_sample(key)
                st.rerun()

    st.markdown("---")
    st.markdown(
        '<div class="disclaimer">⚠️ 이 서비스는 의료 진단을 대체하지 않습니다. '
        '건강에 관한 중요한 결정은 반드시 의사와 상담하세요.</div>',
        unsafe_allow_html=True,
    )


# ── 결과 페이지 ──────────────────────────────────────────────────────────────
else:
    col_back, col_title = st.columns([1, 6])
    with col_back:
        if st.button("← 새 문서"):
            reset_state()
            st.rerun()
    with col_title:
        st.markdown("## 🏥 MediRead — 분석 결과")
        if st.session_state.demo_mode:
            st.caption("💡 샘플 문서로 체험 중")

    st.markdown("---")

    # 위험도 배지
    render_risk_section(st.session_state.risk_assessments or [])
    if st.session_state.risk_assessments:
        st.markdown("---")

    # 원문 / 번역 2단 레이아웃
    col_orig, col_trans = st.columns([1, 1], gap="large")

    with col_orig:
        st.markdown("#### 📋 원문 (파싱 결과)")
        st.markdown(
            f'<div class="doc-box">{st.session_state.parsed_text or ""}</div>',
            unsafe_allow_html=True,
        )

    with col_trans:
        st.markdown("#### ✅ 쉬운 한국어 번역")
        if st.session_state.rich_translation:
            render_rich_translation(st.session_state.rich_translation)
        else:
            st.info("번역 결과가 없습니다.")

    st.markdown("---")

    # Q&A 챗봇
    st.markdown("### 💬 궁금한 점을 물어보세요")
    st.caption("번역 결과를 바탕으로 질문에 답변드립니다")

    suggested = ["이 진단이 심각한 건가요?", "앞으로 어떤 치료를 받게 되나요?", "일상생활에서 주의할 점이 있나요?"]
    btn_cols = st.columns(len(suggested))
    for col, q in zip(btn_cols, suggested):
        with col:
            if st.button(q, use_container_width=True, key=f"suggest_{q}"):
                st.session_state.chat_messages.append({"role": "user", "content": q})
                rich = st.session_state.rich_translation or {}
                context = (
                    f"원문:\n{st.session_state.parsed_text}\n\n"
                    f"번역 요약:\n{rich.get('summary','')}\n\n"
                    f"상세 번역:\n{rich.get('full_explanation','')}"
                )
                reply = chat_with_document(st.session_state.chat_messages, context)
                st.session_state.chat_messages.append({"role": "assistant", "content": reply})
                st.rerun()

    for msg in st.session_state.chat_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if prompt := st.chat_input("질문을 입력하세요..."):
        st.session_state.chat_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        rich = st.session_state.rich_translation or {}
        context = (
            f"원문:\n{st.session_state.parsed_text}\n\n"
            f"번역 요약:\n{rich.get('summary','')}\n\n"
            f"상세 번역:\n{rich.get('full_explanation','')}"
        )
        with st.chat_message("assistant"):
            with st.spinner("답변 생성 중..."):
                reply = chat_with_document(st.session_state.chat_messages, context)
            st.markdown(reply)
        st.session_state.chat_messages.append({"role": "assistant", "content": reply})

    st.markdown("---")
    st.markdown(
        '<div class="disclaimer">⚠️ 이 서비스는 의료 진단을 대체하지 않습니다. '
        '건강에 관한 중요한 결정은 반드시 의사와 상담하세요.</div>',
        unsafe_allow_html=True,
    )

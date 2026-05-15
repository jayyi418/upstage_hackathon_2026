import json
import os

from openai import OpenAI


def _client() -> OpenAI:
    return OpenAI(api_key=os.environ["UPSTAGE_API_KEY"], base_url="https://api.upstage.ai/v1")


# ── 구조화 번역 ────────────────────────────────────────────────────────────────

_RICH_SYSTEM = """당신은 의학 전문 통역사입니다. 진단서/소견서를 분석하여 환자와 보호자가 이해할 수 있는 형태로 변환합니다.

번역 원칙:
1. 의학 용어는 반드시 일반인 표현으로 바꾸고, 원어는 괄호에 표기 (예: 폐에 물이 차는 증상(흉막 삼출))
2. 검사 수치는 정상 범위와 비교해 status를 normal / high / low 로 명확히 분류
3. 침착하고 사실에 기반하되, 불필요한 공포심을 주지 않게 작성
4. 약물은 복용 이유를 쉬운 말로 설명 (약 이름만 나열하지 말 것)
5. action_items는 환자가 오늘 당장 실행 가능한 구체적 행동으로"""

_RICH_SCHEMA = {
    "type": "object",
    "properties": {
        "summary": {
            "type": "string",
            "description": "전체 진단 핵심을 환자 눈높이로 2~3문장 요약. 가장 중요한 메시지를 먼저.",
        },
        "test_results": {
            "type": "array",
            "description": "문서에 등장하는 모든 검사 수치",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "검사명 쉬운 한국어 (예: 혈당(공복))"},
                    "original_term": {"type": "string", "description": "원래 의학 용어 (예: Fasting Glucose)"},
                    "value": {"type": "string", "description": "측정값 숫자"},
                    "unit": {"type": "string", "description": "단위 (예: mg/dL)"},
                    "normal_range": {"type": "string", "description": "정상 범위 (예: 70–99)"},
                    "status": {"type": "string", "enum": ["normal", "high", "low"]},
                    "plain_explanation": {"type": "string", "description": "이 수치의 의미 한 문장. 정상이면 안심 멘트."},
                },
                "required": ["name", "value", "unit", "status", "plain_explanation"],
            },
        },
        "medications": {
            "type": "array",
            "description": "처방된 약물 목록",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "약물 성분명 + 용량 (예: 메트포르민 500mg)"},
                    "dosage_instruction": {"type": "string", "description": "복용 방법 (예: 1일 2회 식후)"},
                    "purpose": {"type": "string", "description": "왜 먹는 약인지 쉬운 한국어 (예: 혈당을 낮추는 기본 약입니다)"},
                },
                "required": ["name", "purpose"],
            },
        },
        "action_items": {
            "type": "array",
            "items": {"type": "string"},
            "description": "환자가 지금 당장 해야 할 구체적 행동 (날짜·횟수 포함). 3~5개.",
        },
        "full_explanation": {
            "type": "string",
            "description": "진단서 전체를 쉬운 한국어로 상세히 번역한 마크다운 전문. 섹션 제목 활용.",
        },
    },
    "required": ["summary", "test_results", "medications", "action_items", "full_explanation"],
}


def get_rich_translation(parsed_text: str) -> dict:
    """Solar Pro 3로 진단서를 분석해 시각화용 구조화 JSON을 반환합니다.

    reasoning_effort="low": 의학 용어 해석 및 수치 분류 정확도 향상
    """
    response = _client().chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": _RICH_SYSTEM},
            {
                "role": "user",
                "content": (
                    "다음 진단서/소견서를 분석하여 지정된 JSON 형식으로 반환하세요.\n\n"
                    f"{parsed_text}"
                ),
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "rich_translation", "schema": _RICH_SCHEMA},
        },
        temperature=0.2,
        max_tokens=4000,
        reasoning_effort="low",
    )
    return json.loads(response.choices[0].message.content)


# ── 위험도 평가 ────────────────────────────────────────────────────────────────

_RISK_SCHEMA = {
    "type": "object",
    "properties": {
        "results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "diagnosis": {"type": "string"},
                    "level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "reason": {"type": "string"},
                },
                "required": ["diagnosis", "level", "reason"],
            },
        }
    },
    "required": ["results"],
}

_RISK_SYSTEM = """당신은 의학 전문가입니다. 진단명을 보고 위험도를 평가하세요.

위험도 기준:
- low (경증): 생활 관리로 호전 가능
- medium (중등증): 정기 모니터링과 치료 필요
- high (중증): 즉각적인 의료 개입 필요"""


def assess_risk(diagnoses: list) -> list:
    """진단명 목록을 받아 위험도를 평가합니다."""
    if not diagnoses:
        return []

    diagnoses_text = "\n".join(f"- {d}" for d in diagnoses)
    response = _client().chat.completions.create(
        model="solar-pro3",
        messages=[
            {"role": "system", "content": _RISK_SYSTEM},
            {"role": "user", "content": f"다음 진단명들의 위험도를 평가하세요:\n{diagnoses_text}"},
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {"name": "risk_assessments", "schema": _RISK_SCHEMA},
        },
        temperature=0.1,
    )
    data = json.loads(response.choices[0].message.content)
    return data.get("results", [])


# ── Q&A 챗봇 ──────────────────────────────────────────────────────────────────

def chat_with_document(messages: list, document_context: str) -> str:
    """번역된 문서를 컨텍스트로 Q&A 챗봇 응답을 생성합니다."""
    system_prompt = f"""당신은 친절한 의료 정보 도우미입니다. 아래 진단서 내용을 바탕으로 질문에 답변하세요.

진단서 내용:
{document_context}

안내사항:
- 이 서비스는 의료 진단을 대체하지 않습니다
- 심각한 증상이 있으면 반드시 의사와 상담하도록 안내하세요
- 일반적인 의학 정보를 쉽게 설명하되, 개인 진단이나 처방은 하지 마세요"""

    response = _client().chat.completions.create(
        model="solar-pro3",
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.5,
        max_tokens=1000,
    )
    return response.choices[0].message.content

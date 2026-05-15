import asyncio
import json
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

load_dotenv()

from sample_texts import SAMPLES
from services.document_parse import parse_document
from services.info_extract import extract_medical_info
from services.llm import assess_risk, chat_with_document, get_rich_translation

app = FastAPI(title="MediRead API", version="1.0")

# 로컬: localhost / 배포: ALLOWED_ORIGINS 환경변수로 주입
_raw_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
_origins = [o.strip() for o in _raw_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",  # Vercel 프리뷰 URL 자동 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _event(progress: int, message: str, **extra) -> str:
    return f"data: {json.dumps({'progress': progress, 'message': message, **extra}, ensure_ascii=False)}\n\n"


@app.post("/api/analyze")
async def analyze_document(file: UploadFile = File(...)):
    """파일 업로드 → Document Parse → Info Extract → 위험도 → 번역 (SSE 스트리밍)"""
    file_bytes = await file.read()
    filename = file.filename or "document"

    async def generate():
        try:
            yield _event(10, "📄 문서를 파싱하고 있습니다...")
            parsed = await asyncio.to_thread(parse_document, file_bytes, filename)

            yield _event(32, "🔍 의학 정보를 추출하고 있습니다...")
            info = await asyncio.to_thread(extract_medical_info, file_bytes, filename)

            yield _event(55, "⚕️ 위험도를 평가하고 있습니다...")
            risks = await asyncio.to_thread(assess_risk, info.get("diagnoses", []))

            yield _event(75, "✍️ 쉬운 한국어로 번역하고 있습니다...")
            rich = await asyncio.to_thread(get_rich_translation, parsed)

            yield _event(100, "✅ 완료!", done=True, data={
                "parsed_text": parsed,
                "rich_translation": rich,
                "risk_assessments": risks,
                "extracted_info": info,
            })
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/analyze-sample/{sample_key}")
async def analyze_sample(sample_key: str):
    """샘플 문서 → 위험도 → 번역 (SSE 스트리밍)"""
    if sample_key not in SAMPLES:
        raise HTTPException(status_code=404, detail="Sample not found")
    sample = SAMPLES[sample_key]

    async def generate():
        try:
            yield _event(20, "⚕️ 위험도를 평가하고 있습니다...")
            risks = await asyncio.to_thread(assess_risk, sample["diagnoses"])

            yield _event(60, "✍️ 쉬운 한국어로 번역하고 있습니다...")
            rich = await asyncio.to_thread(get_rich_translation, sample["parsed_text"])

            yield _event(100, "✅ 완료!", done=True, data={
                "parsed_text": sample["parsed_text"],
                "rich_translation": rich,
                "risk_assessments": risks,
                "extracted_info": {"diagnoses": sample["diagnoses"]},
            })
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/samples")
async def get_samples():
    return [{"key": k, "label": v["label"]} for k, v in SAMPLES.items()]


class ChatRequest(BaseModel):
    messages: list
    parsed_text: str
    rich_summary: str


@app.post("/api/chat")
async def chat(req: ChatRequest):
    context = f"원문:\n{req.parsed_text}\n\n번역 요약:\n{req.rich_summary}"
    reply = await asyncio.to_thread(chat_with_document, req.messages, context)
    return {"reply": reply}


@app.get("/api/health")
async def health():
    return {"status": "ok"}

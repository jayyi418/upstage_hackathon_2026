import os

import requests

_URL = "https://api.upstage.ai/v1/document-digitization"
_MIME = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}


def parse_document(file_bytes: bytes, filename: str) -> str:
    """Document Parse API로 파일을 파싱하여 마크다운 텍스트를 반환합니다.

    chart_recognition=true: 표/차트를 텍스트로 변환 (검사 수치 표 인식에 필수)
    output_formats=["markdown"]: 마크다운만 요청해 응답 크기 최소화
    """
    headers = {"Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}"}
    ext = filename.lower().rsplit(".", 1)[-1]
    mime = _MIME.get(ext, "application/octet-stream")

    files = {"document": (filename, file_bytes, mime)}
    data = {
        "model": "document-parse",
        "output_formats": '["markdown"]',
        "chart_recognition": "true",
    }

    resp = requests.post(_URL, headers=headers, files=files, data=data, timeout=120)
    _raise_for_status(resp)

    content = resp.json().get("content", {})
    return content.get("markdown") or content.get("text") or ""


def _raise_for_status(resp: requests.Response) -> None:
    """HTTP 에러를 사용자 친화적 메시지로 변환합니다."""
    if resp.status_code == 200:
        return
    code = resp.status_code
    if code == 401:
        raise RuntimeError("API 키가 올바르지 않습니다. .env 파일의 UPSTAGE_API_KEY를 확인하세요.")
    if code == 403:
        raise RuntimeError("API 크레딧이 부족합니다. Upstage 콘솔에서 크레딧을 확인하세요.")
    if code == 415:
        raise RuntimeError("지원하지 않는 파일 형식입니다. PDF, JPG, PNG 파일을 사용하세요.")
    if code == 429:
        raise RuntimeError("API 요청 한도에 도달했습니다 (1 RPS). 잠시 후 다시 시도하세요.")
    try:
        msg = resp.json().get("error", {}).get("message", resp.text)
    except Exception:
        msg = resp.text
    raise RuntimeError(f"Document Parse 오류 ({code}): {msg}")

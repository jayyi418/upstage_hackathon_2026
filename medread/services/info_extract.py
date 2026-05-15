import base64
import json
import os

import requests
from services.document_parse import _raise_for_status


_MEDICAL_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnoses": {
            "type": "array",
            "items": {"type": "string"},
            "description": "진단명 목록 (한국어로 표기)",
        },
        "patient_name": {"type": "string", "description": "환자 이름"},
        "hospital": {"type": "string", "description": "병원명"},
        "date": {"type": "string", "description": "진단 날짜"},
        "test_results": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "value": {"type": "string"},
                    "unit": {"type": "string"},
                },
            },
            "description": "검사 수치 결과",
        },
        "medications": {
            "type": "array",
            "items": {"type": "string"},
            "description": "처방된 약물 목록",
        },
    },
}


def extract_medical_info(file_bytes: bytes, filename: str) -> dict:
    """Information Extract API로 의학 정보를 구조화하여 반환합니다."""
    url = "https://api.upstage.ai/v1/information-extraction"
    headers = {
        "Authorization": f"Bearer {os.environ['UPSTAGE_API_KEY']}",
        "Content-Type": "application/json",
    }

    ext = filename.lower().rsplit(".", 1)[-1]
    mime_map = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    mime = mime_map.get(ext, "application/octet-stream")

    b64 = base64.b64encode(file_bytes).decode("utf-8")

    payload = {
        "model": "information-extract",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime};base64,{b64}"},
                    }
                ],
            }
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "medical_document",
                "schema": _MEDICAL_SCHEMA,
            },
        },
    }

    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    _raise_for_status(resp)

    result = resp.json()
    content = result["choices"][0]["message"]["content"]
    return json.loads(content)

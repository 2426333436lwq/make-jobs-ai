from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlmodel import Session, select

from app.db import get_session, utc_now
from app.models import ResumeProfileRecord
from app.schemas import ResumeProfileInput, ResumeProfileView, ResumeUploadParseResponse
from app.services.claude_service import ClaudeService
from app.services.container import get_claude_service
from app.services.resume_file_parser import ResumeFileParserService
from app.services.resume_profile_parser import infer_resume_profile_from_text
from app.services.serializers import resume_record_to_view

router = APIRouter(prefix="/resume-profile", tags=["resume-profile"])
file_parser_service = ResumeFileParserService()


def _get_claude():
    return get_claude_service()


@router.get("", response_model=Optional[ResumeProfileView])
def get_resume_profile(session: Session = Depends(get_session)) -> Optional[ResumeProfileView]:
    record = session.exec(select(ResumeProfileRecord).order_by(ResumeProfileRecord.id.desc())).first()
    if not record:
        return None
    return resume_record_to_view(record)


@router.put("", response_model=ResumeProfileView)
def upsert_resume_profile(payload: ResumeProfileInput, session: Session = Depends(get_session)) -> ResumeProfileView:
    record = session.exec(select(ResumeProfileRecord).order_by(ResumeProfileRecord.id.desc())).first()
    profile_json = json.dumps(payload.model_dump(), ensure_ascii=False)
    if not record:
        record = ResumeProfileRecord(
            full_name=payload.personal_info.full_name,
            profile_json=profile_json,
            updated_at=utc_now(),
        )
        session.add(record)
    else:
        record.full_name = payload.personal_info.full_name
        record.profile_json = profile_json
        record.updated_at = utc_now()
    session.commit()
    session.refresh(record)
    return resume_record_to_view(record)


@router.post("/upload", response_model=ResumeUploadParseResponse)
async def upload_resume(file: UploadFile = File(...), use_ai: bool = False) -> ResumeUploadParseResponse:
    """
    上传简历并解析。

    - 有 API Key 时默认用 AI 解析（15s 超时），失败回退本地
    - 无 API Key 或 use_ai=false 时用本地规则解析
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Resume file name is required")
    MAX_SIZE = 10 * 1024 * 1024  # 10MB
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=400, detail="文件大小不能超过 10MB")
    try:
        raw_text = file_parser_service.extract_text(file.filename, content)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    import asyncio
    import logging
    logger = logging.getLogger(__name__)

    profile = None

    # 有 API Key 时优先用 AI 解析（准确率高）
    if _get_claude().enabled:
        try:
            ai_profile = await asyncio.wait_for(
                asyncio.to_thread(_get_claude().parse_resume_profile, raw_text),
                timeout=15,
            )
            profile = ai_profile
            logger.info("AI resume parse succeeded for %s", file.filename)
        except asyncio.TimeoutError:
            logger.warning("AI resume parse timed out, using heuristic")
        except Exception as exc:
            logger.warning("AI resume parse failed (%s), using heuristic", exc)

    # AI 失败或未配置时，使用本地规则解析
    if profile is None:
        profile = infer_resume_profile_from_text(raw_text)

    excerpt = raw_text[:1200]
    return ResumeUploadParseResponse(
        file_name=file.filename,
        parsed_text_excerpt=excerpt,
        profile=profile,
    )


@router.post("/generate/beautified")
def generate_beautified_resume(session: Session = Depends(get_session)):
    record = session.exec(select(ResumeProfileRecord).order_by(ResumeProfileRecord.id.desc())).first()
    if not record:
        raise HTTPException(status_code=400, detail="请先保存简历资料")
    profile = resume_record_to_view(record)
    if not _get_claude().enabled:
        raise HTTPException(status_code=400, detail="请先配置 API 密钥")
    try:
        markdown = _get_claude().generate_beautified_resume(profile)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="生成失败：{}".format(exc))
    return {"markdown": markdown}


@router.post("/generate/market")
def generate_market_resume(session: Session = Depends(get_session)):
    record = session.exec(select(ResumeProfileRecord).order_by(ResumeProfileRecord.id.desc())).first()
    if not record:
        raise HTTPException(status_code=400, detail="请先保存简历资料")
    profile = resume_record_to_view(record)
    if not _get_claude().enabled:
        raise HTTPException(status_code=400, detail="请先配置 API 密钥")
    try:
        markdown = _get_claude().generate_market_resume(profile)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="生成失败：{}".format(exc))
    return {"markdown": markdown}


@router.get("/{profile_id}", response_model=ResumeProfileView)
def get_resume_profile_by_id(profile_id: int, session: Session = Depends(get_session)) -> ResumeProfileView:
    record = session.get(ResumeProfileRecord, profile_id)
    if not record:
        raise HTTPException(status_code=404, detail="Resume profile not found")
    return resume_record_to_view(record)

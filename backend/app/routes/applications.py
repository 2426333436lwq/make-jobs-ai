from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, desc, func, select

from app.db import get_session, utc_now
from app.models import ApplicationRecord
from app.schemas import ApplicationView
from app.services.pagination import PaginatedResponse
from app.services.serializers import application_record_to_view

router = APIRouter(prefix="/applications", tags=["applications"])


@router.get("", response_model=PaginatedResponse[ApplicationView])
def list_applications(
    offset: int = Query(0, ge=0, description="偏移量"),
    limit: int = Query(20, ge=1, le=100, description="每页数量"),
    session: Session = Depends(get_session),
) -> PaginatedResponse[ApplicationView]:
    """获取投递记录列表（支持分页）。"""
    # 获取总数
    total = session.exec(select(func.count()).select_from(ApplicationRecord)).one()

    # 查询分页数据
    records = session.exec(
        select(ApplicationRecord).order_by(desc(ApplicationRecord.id)).offset(offset).limit(limit)
    ).all()

    items = [application_record_to_view(record) for record in records]
    has_more = offset + limit < total

    return PaginatedResponse(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=has_more,
    )


@router.get("/{application_id}", response_model=ApplicationView)
def get_application(application_id: int, session: Session = Depends(get_session)) -> ApplicationView:
    record = session.get(ApplicationRecord, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    return application_record_to_view(record)


@router.post("/{application_id}/confirm", response_model=ApplicationView)
def confirm_application(application_id: int, session: Session = Depends(get_session)) -> ApplicationView:
    record = session.get(ApplicationRecord, application_id)
    if not record:
        raise HTTPException(status_code=404, detail="Application not found")
    record.status = "confirmed"
    record.confirmed_at = utc_now()
    session.add(record)
    session.commit()
    session.refresh(record)
    return application_record_to_view(record)

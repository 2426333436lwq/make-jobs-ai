"""
分页工具模块。
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


@dataclass
class PaginationParams:
    """分页参数。"""
    offset: int = 0
    limit: int = 20

    def __post_init__(self):
        self.offset = max(0, self.offset)
        self.limit = max(1, min(100, self.limit))  # 限制最大每页 100 条


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应模型。"""
    items: List[T]
    total: int
    offset: int
    limit: int
    has_more: bool


def paginate_query(query, session, offset: int = 0, limit: int = 20) -> tuple[List, int]:
    """
    执行分页查询。

    Args:
        query: SQLModel 查询对象
        session: 数据库会话
        offset: 偏移量
        limit: 每页数量

    Returns:
        (items, total) 元组
    """
    # 获取总数
    from sqlmodel import func, select
    count_query = select(func.count()).select_from(query.subquery())
    total = session.exec(count_query).one()

    # 执行分页查询
    items = session.exec(query.offset(offset).limit(limit)).all()

    return items, total

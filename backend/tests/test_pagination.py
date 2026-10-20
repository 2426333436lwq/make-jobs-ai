"""
分页服务测试。
"""
from __future__ import annotations

import pytest

from app.services.pagination import PaginationParams, PaginatedResponse


class TestPaginationParams:
    def test_default_values(self):
        """测试默认值。"""
        params = PaginationParams()
        assert params.offset == 0
        assert params.limit == 20

    def test_custom_values(self):
        """测试自定义值。"""
        params = PaginationParams(offset=10, limit=50)
        assert params.offset == 10
        assert params.limit == 50

    def test_negative_offset_becomes_zero(self):
        """测试负偏移量变为 0。"""
        params = PaginationParams(offset=-10)
        assert params.offset == 0

    def test_limit_capped_at_100(self):
        """测试限制最大为 100。"""
        params = PaginationParams(limit=200)
        assert params.limit == 100

    def test_limit_minimum_is_1(self):
        """测试最小限制为 1。"""
        params = PaginationParams(limit=0)
        assert params.limit == 1


class TestPaginatedResponse:
    def test_has_more_true(self):
        """测试 has_more 为 True 的情况。"""
        response = PaginatedResponse(
            items=[1, 2, 3],
            total=10,
            offset=0,
            limit=3,
            has_more=True,
        )
        assert response.has_more is True
        assert response.total == 10
        assert len(response.items) == 3

    def test_has_more_false(self):
        """测试 has_more 为 False 的情况。"""
        response = PaginatedResponse(
            items=[1, 2, 3],
            total=3,
            offset=0,
            limit=10,
            has_more=False,
        )
        assert response.has_more is False
        assert response.total == 3

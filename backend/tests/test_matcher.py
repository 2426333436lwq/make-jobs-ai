"""
匹配服务测试。
"""
from __future__ import annotations

import pytest

from app.schemas import MatchAnalysis, ResumeProfileView
from app.services.matcher import MatcherService


@pytest.fixture
def matcher():
    return MatcherService()


@pytest.fixture
def sample_profile():
    return ResumeProfileView(
        id=1,
        full_name="测试用户",
        personal_info={"full_name": "测试用户", "job_intention": "Python 开发"},
        self_evaluation={"content": "测试用户"},
        education_background=[],
        internship_experiences=[],
        project_experiences=[],
        campus_experiences=[],
        honors_and_certificates=[],
        training_experiences=[],
        skills_and_other={"skills": ["Python", "FastAPI", "SQL"], "other": ""},
    )


class TestMatcherService:
    def test_analyze_heuristic_all_skills_match(self, matcher, sample_profile):
        """测试所有技能都匹配的情况。"""
        job_skills = ["Python", "FastAPI", "SQL"]
        responsibilities = ["负责后端开发"]

        result = matcher.analyze(
            profile=sample_profile,
            job_skills=job_skills,
            responsibilities=responsibilities,
            use_api=False,
        )

        assert isinstance(result, MatchAnalysis)
        assert result.match_score > 70
        assert len(result.matched_skills) == 3
        assert len(result.missing_skills) == 0
        assert "Python" in result.matched_skills

    def test_analyze_heuristic_no_skills_match(self, matcher, sample_profile):
        """测试没有技能匹配的情况。"""
        job_skills = ["Java", "Spring", "React"]
        responsibilities = ["负责前端开发"]

        result = matcher.analyze(
            profile=sample_profile,
            job_skills=job_skills,
            responsibilities=responsibilities,
            use_api=False,
        )

        assert isinstance(result, MatchAnalysis)
        assert result.match_score < 50
        assert len(result.matched_skills) == 0
        assert len(result.missing_skills) == 3

    def test_analyze_heuristic_partial_skills_match(self, matcher, sample_profile):
        """测试部分技能匹配的情况。"""
        job_skills = ["Python", "Java", "React"]
        responsibilities = ["负责全栈开发"]

        result = matcher.analyze(
            profile=sample_profile,
            job_skills=job_skills,
            responsibilities=responsibilities,
            use_api=False,
        )

        assert isinstance(result, MatchAnalysis)
        assert 30 < result.match_score < 80
        assert len(result.matched_skills) == 1
        assert len(result.missing_skills) == 2

    def test_analyze_heuristic_empty_job_skills(self, matcher, sample_profile):
        """测试空职位技能列表。"""
        result = matcher.analyze(
            profile=sample_profile,
            job_skills=[],
            responsibilities=[],
            use_api=False,
        )

        assert isinstance(result, MatchAnalysis)
        assert result.match_score >= 0
        assert len(result.matched_skills) == 0

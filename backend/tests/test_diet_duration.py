import pytest

from app.logic.diet_duration import (
    DEFAULT_PLAN_DURATION_DAYS,
    DurationParseError,
    QUICK_PLAN_DURATION_DAYS,
    apply_plan_duration_metadata,
    duration_from_existing_plan,
    optional_plan_duration_days,
    parse_duration_text,
    validate_duration_days,
)


def test_validate_duration_multiples_of_7():
    assert validate_duration_days(7) == 7
    assert validate_duration_days(28) == 28
    with pytest.raises(ValueError):
        validate_duration_days(8)
    with pytest.raises(ValueError):
        validate_duration_days(5)


def test_parse_duration_text():
    assert parse_duration_text("7") == 7
    assert parse_duration_text("una semana") == 7
    assert parse_duration_text("3 semanas") == 21
    assert parse_duration_text("14") == 14
    with pytest.raises(DurationParseError):
        parse_duration_text("xyz")


def test_apply_plan_duration_metadata():
    plan = apply_plan_duration_metadata({"title": "x"}, 14)
    assert plan["plan_duration_days"] == 14
    assert plan["plan_cycle_days"] == 7
    assert plan["plan_duration_weeks"] == 2
    assert "14 días" in plan["plan_repeat_instruction_es"]


def test_duration_from_existing_plan():
    assert duration_from_existing_plan(None) == DEFAULT_PLAN_DURATION_DAYS
    assert duration_from_existing_plan({}) == DEFAULT_PLAN_DURATION_DAYS
    assert duration_from_existing_plan({"plan_duration_days": 28}) == 28
    assert duration_from_existing_plan({"plan_duration_days": 364}) == 364
    assert duration_from_existing_plan({"plan_duration_days": 8}) == DEFAULT_PLAN_DURATION_DAYS


def test_optional_plan_duration_days():
    assert optional_plan_duration_days(None) is None
    assert optional_plan_duration_days({}) is None
    assert optional_plan_duration_days({"plan_duration_days": 21}) == 21
    assert optional_plan_duration_days({"plan_duration_days": 8}) is None


def test_quick_plan_duration_days_are_valid():
    assert len(QUICK_PLAN_DURATION_DAYS) >= 4
    for d in QUICK_PLAN_DURATION_DAYS:
        assert validate_duration_days(d) == d

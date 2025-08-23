import pytest
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.services.vehicle_event_processor_service import (
    _parse_coord_string,
    _calculate_distance,
    _calculate_bearing,
)


def test_parse_coord_string_valid():
    assert _parse_coord_string("N10.12345") == pytest.approx(10.12345)
    assert _parse_coord_string("W074.12345") == pytest.approx(-74.12345)


def test_parse_coord_string_invalid():
    assert _parse_coord_string(None) is None
    assert _parse_coord_string("") is None
    assert _parse_coord_string("NABC") is None


def test_calculate_distance():
    # Distance between two points about 111 km apart along equator
    dist = _calculate_distance(0, 0, 0, 1)
    assert dist == pytest.approx(111195, rel=1e-3)


def test_calculate_bearing():
    # Bearing from origin to point directly north should be 0 degrees
    bearing = _calculate_bearing(0, 0, 1, 0)
    assert bearing == 0

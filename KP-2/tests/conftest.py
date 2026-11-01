import pytest
from src.api_key import APIAdapter
from typing import List,Dict,Any


@pytest.fixture
def sample_data() -> List[Dict[str, Any]]:
    """Фикстура: 5 самолётов над Канадой"""
    return [
        {"callsign": "CFTAB", "origin_country": "Canada", "velocity": 132.27, "baro_altitude": 1310.64},
        {"callsign": "WJA793", "origin_country": "Canada", "velocity": 111.3, "baro_altitude": 1226.82},
        {"callsign": "CJT566", "origin_country": "Canada", "velocity": 86.43, "baro_altitude": 1165.86},
        {"callsign": "ACA840", "origin_country": "Canada", "velocity": 85.12, "baro_altitude": 1463.04},
        {"callsign": "ANT773", "origin_country": "Canada", "velocity": 67.91, "baro_altitude": 1196.34},
    ]


@pytest.fixture
def adapter() -> APIAdapter:
    """Фикстура: экземпляр APIAdapter"""
    return APIAdapter()


@pytest.fixture
def nominatim_response() -> list:
    """Фикстура: ответ от Nominatim"""
    return [
        {
            "place_id": "123456",
            "display_name": "Canada",
            "boundingbox": ["41.67598", "83.11386", "-141.00187", "-52.61785"],
            "lat": "60.0",
            "lon": "-100.0",
        }
    ]

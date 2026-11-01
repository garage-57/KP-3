import pytest
import json
import os
from unittest.mock import patch, Mock, mock_open
from typing import List, Dict, Any
import logger

from src.aeroplanes import (
    Aeroplane,
    JSONSaver,
    filter_aeroplanes,
    get_aeroplanes_by_altitude,
    sort_aeroplanes,
    get_top_aeroplanes,
)
from src.api_key import BaseAPIClient,APIAdapter



class TestBaseAPIClient:
    """Тесты абстрактного класса BaseAPIClient"""

    def test_is_abstract(self):
        """BaseAPIClient — абстрактный класс"""
        from abc import ABC
        assert issubclass(BaseAPIClient, ABC)

    def test_cannot_instantiate(self):
        """Нельзя создать экземпляр BaseAPIClient"""
        with pytest.raises(TypeError):
            BaseAPIClient("https://example.com")

    def test_has_abstract_methods(self):
        """Есть абстрактные методы"""
        assert hasattr(BaseAPIClient, 'get_info')
        assert hasattr(BaseAPIClient, 'connect')
        assert BaseAPIClient.get_info.__isabstractmethod__
        assert BaseAPIClient.connect.__isabstractmethod__


class TestCastToObjectList:
    """Тесты преобразования JSON в объекты Aeroplane"""

    def test_cast_all(self, sample_data):
        """Преобразование всех 5 самолётов"""
        result = Aeroplane.cast_to_object_list(sample_data)
        assert len(result) == 5

    def test_cast_callsigns(self, sample_data):
        """Проверка позывных"""
        result = Aeroplane.cast_to_object_list(sample_data)
        callsigns = [p.callsign for p in result]
        assert callsigns == ["CFTAB", "WJA793", "CJT566", "ACA840", "ANT773"]

    def test_cast_countries(self, sample_data):
        result = Aeroplane.cast_to_object_list(sample_data)
        assert all(p.origin_country == "Canada" for p in result)

    def test_cast_velocities(self, sample_data):
        """Проверка скоростей"""
        result = Aeroplane.cast_to_object_list(sample_data)
        velocities = [p.velocity for p in result]
        assert velocities == [132.27, 111.3, 86.43, 85.12, 67.91]

    def test_cast_altitudes(self, sample_data):
        """Проверка высот"""
        result = Aeroplane.cast_to_object_list(sample_data)
        altitudes = [p.baro_altitude for p in result]
        assert altitudes == [1310.64, 1226.82, 1165.86, 1463.04, 1196.34]

    def test_cast_returns_aeroplane_instances(self, sample_data):
        """Возвращаются объекты Aeroplane"""
        result = Aeroplane.cast_to_object_list(sample_data)
        assert all(isinstance(p, Aeroplane) for p in result)

    def test_first_plane_details(self, sample_data):
        """Данные первого самолёта"""
        result = Aeroplane.cast_to_object_list(sample_data)
        first = result[0]
        assert first.callsign == "CFTAB"
        assert first.origin_country == "Canada"
        assert first.velocity == 132.27
        assert first.baro_altitude == 1310.64


class TestSortingWithRealData:
    """Тесты сортировки на реальных данных"""

    def test_sort_descending(self, sample_data):
        """Сортировка по убыванию скорости"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        sorted_planes = sort_aeroplanes(planes, reverse=True)
        velocities = [p.velocity for p in sorted_planes]
        assert velocities == [132.27, 111.3, 86.43, 85.12, 67.91]

    def test_sort_ascending(self, sample_data):
        """Сортировка по возрастанию скорости"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        sorted_planes = sort_aeroplanes(planes, reverse=False)
        velocities = [p.velocity for p in sorted_planes]
        assert velocities == [67.91, 85.12, 86.43, 111.3, 132.27]

    def test_top_3(self, sample_data):
        """Топ-3 самых быстрых"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        sorted_planes = sort_aeroplanes(planes, reverse=True)
        top3 = get_top_aeroplanes(sorted_planes, 3)
        callsigns = [p.callsign for p in top3]
        assert callsigns == ["CFTAB", "WJA793", "CJT566"]


class TestFilteringWithRealData:
    """Тесты фильтрации на реальных данных"""

    def test_filter_canada(self, sample_data):
        """Фильтр по Канаде — все 5"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        filtered = filter_aeroplanes(planes, ["Canada"])
        assert len(filtered) == 5

    def test_filter_not_found(self, sample_data):
        """Тест 12: Фильтр по несуществующей стране"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        filtered = filter_aeroplanes(planes, ["France"])
        assert filtered == []


class TestAltitudeWithRealData:
    """Тесты фильтрации по высоте"""

    def test_altitude_range(self, sample_data):
        """Диапазон 1100 - 1300"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        filtered = get_aeroplanes_by_altitude(planes, "1100 - 1300")
        callsigns = [p.callsign for p in filtered]
        # WJA793 (1226), CJT566 (1165), ANT773 (1196)
        assert len(filtered) == 3
        assert "WJA793" in callsigns
        assert "CJT566" in callsigns
        assert "ANT773" in callsigns

    def test_altitude_narrow(self, sample_data):
        """Узкий диапазон"""
        planes = Aeroplane.cast_to_object_list(sample_data)
        filtered = get_aeroplanes_by_altitude(planes, "1300 - 1500")
        callsigns = [p.callsign for p in filtered]
        # CFTAB (1310), ACA840 (1463)
        assert len(filtered) == 2
        assert "CFTAB" in callsigns
        assert "ACA840" in callsigns


class TestJSONSaverWithRealData:
    """Тесты JSONSaver на реальных данных"""

    def test_save_and_load(self, sample_data, tmp_path):
        """Сохранение и загрузка"""
        planes = Aeroplane.cast_to_object_list(sample_data)

        file_path = tmp_path / "response.json"
        saver = JSONSaver(str(file_path))

        for plane in planes:
            saver.add_aeroplane(plane)

        loaded = saver.get_aeroplanes()
        assert len(loaded) == 5
        assert loaded[0].callsign == "CFTAB"
        assert loaded[4].callsign == "ANT773"


import json
import os
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logger
from src.api_key import APIAdapter
from typing import List, Dict, Any


class Aeroplane(APIAdapter):
    """Класс для представления самолёта"""

    def __init__(
        self,
        callsign: str,
        origin_country: str,
        velocity: float,
        baro_altitude: float,
    ):
        if not callsign:
            raise ValueError("Позывной не может быть пустым")
        if not origin_country:
            raise ValueError("Страна регистрации обязательна")
        if velocity is not None and velocity < 0:
            raise ValueError("Скорость не может быть отрицательной")
        if baro_altitude is not None and baro_altitude < 0:
            raise ValueError("Высота не может быть отрицательной")

        self.callsign = callsign.strip()
        self.origin_country = origin_country
        self.velocity = velocity or 0.0
        self.baro_altitude = baro_altitude or 0.0

    def __repr__(self) -> str:
        return (
            f"Aeroplane({self.callsign}, {self.origin_country}, "
            f"{self.velocity} м/с, {self.baro_altitude} м)"
        )

    def __str__(self) -> str:
        return (
            f"{self.callsign} | {self.origin_country} | "
            f"Скорость: {self.velocity:.1f} м/с | "
            f"Высота: {self.baro_altitude:.0f} м"
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.velocity == other.velocity

    def __gt__(self, other) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.velocity > other.velocity

    def __lt__(self, other) -> bool:
        if not isinstance(other, Aeroplane):
            return NotImplemented
        return self.velocity < other.velocity

    @classmethod
    def cast_to_object_list(cls, data: List[Dict[str, Any]]) -> List["Aeroplane"]:
        """Преобразует список словарей OpenSky в список объектов"""
        result = []

        for item in data:
            try:
                if isinstance(item, list):
                    # Формат OpenSky state vector
                    plane = cls(
                        callsign=item[1].strip() if item[1] else "UNKNOWN",
                        origin_country=item[2] or "Unknown",
                        velocity=item[9] or 0.0,
                        baro_altitude=item[7] or 0.0,
                    )
                else:
                    # Формат словаря
                    plane = cls(
                        callsign=item.get("callsign") or "UNKNOWN",
                        origin_country=item.get("origin_country") or "Unknown",
                        velocity=item.get("velocity") or 0.0,
                        baro_altitude=item.get("baro_altitude") or 0.0,
                    )
                result.append(plane)
            except (ValueError, IndexError, TypeError):
                continue

        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "callsign": self.callsign,
            "origin_country": self.origin_country,
            "velocity": self.velocity,
            "baro_altitude": self.baro_altitude,
        }


def filter_aeroplanes(
    aeroplanes: List[Aeroplane], filter_words: List[str]
) -> List[Aeroplane]:
    """
    Фильтрует самолёты по стране регистрации.
    """
    if not filter_words:
        return aeroplanes

    result = []
    for plane in aeroplanes:
        for word in filter_words:
            if word.lower() in plane.origin_country.lower():
                result.append(plane)
                break

    return result


def get_aeroplanes_by_altitude(
    aeroplanes: List[Aeroplane], altitude_range: str
) -> List[Aeroplane]:
    """
    Фильтрует самолёты по диапазону высот.

    Args:
        aeroplanes: Список самолётов
        altitude_range: Диапазон в формате "1000 - 5000"

    Returns:
        Отфильтрованный список
    """
    if not altitude_range:
        return aeroplanes

    try:
        parts = altitude_range.replace("-", " ").split()
        if len(parts) < 2:
            return aeroplanes

        min_alt = float(parts[0])
        max_alt = float(parts[1])

        return [p for p in aeroplanes if min_alt <= p.baro_altitude <= max_alt]
    except (ValueError, IndexError):
        print(f"Неверный формат диапазона: {altitude_range}")
        return aeroplanes


def sort_aeroplanes(
    aeroplanes: List[Aeroplane], reverse: bool = True
) -> List[Aeroplane]:
    """
    Сортирует самолёты по скорости.

    Args:
        aeroplanes: Список самолётов
        reverse: True — по убыванию, False — по возрастанию

    Returns:
        Отсортированный список
    """
    return sorted(aeroplanes, key=lambda p: p.velocity, reverse=reverse)


def get_top_aeroplanes(aeroplanes: List[Aeroplane], top_n: int) -> List[Aeroplane]:
    return aeroplanes[:top_n]


def print_aeroplanes(aeroplanes: List[Aeroplane]) -> None:

    print(f"Найдены самолеты: {len(aeroplanes)}")

    if not aeroplanes:
        print("Самолёты не найдены")
        return

    for i, plane in enumerate(aeroplanes, 1):
        print(f"\n{i}. {plane.callsign}")
        print(f"Страна: {plane.origin_country}")
        print(f"Скорость: {plane.velocity:.2f} м/с")
        print(f"Высота: {plane.baro_altitude:.2f} м")


class BaseSaver(ABC):
    """Абстрактный класс для хранилища"""

    @abstractmethod
    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        pass

    @abstractmethod
    def get_aeroplanes(self, **criteria) -> List[Aeroplane]:
        pass

    @abstractmethod
    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        pass


class JSONSaver(BaseSaver):
    """Класс для сохранения самолётов в JSON"""

    def __init__(self, filename: str = "response.json"):
        self.filename = filename
        self._ensure_file_exists()

    def _ensure_file_exists(self):
        if not os.path.exists(self.filename):
            with open(self.filename, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read_data(self) -> List[Dict]:
        try:
            with open(self.filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []

    def _write_data(self, data: List[Dict]) -> None:
        with open(self.filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def add_aeroplane(self, aeroplane: Aeroplane) -> None:
        if not isinstance(aeroplane, Aeroplane):
            raise TypeError("Можно добавлять только объекты Aeroplane")

        data = self._read_data()
        data.append(aeroplane.to_dict())
        self._write_data(data)

    def get_aeroplanes(self, **criteria) -> List[Aeroplane]:
        data = self._read_data()
        result = []

        for item in data:
            if all(item.get(k) == v for k, v in criteria.items()):
                try:
                    result.append(
                        Aeroplane(
                            callsign=item["callsign"],
                            origin_country=item["origin_country"],
                            velocity=item["velocity"],
                            baro_altitude=item["baro_altitude"],
                        )
                    )
                except (ValueError, KeyError):
                    continue

        return result

    def delete_aeroplane(self, aeroplane: Aeroplane) -> None:
        data = self._read_data()
        target = aeroplane.to_dict()
        new_data = [item for item in data if item != target]
        self._write_data(new_data)

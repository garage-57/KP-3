from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import logging
import os
import sys
import requests


def setup_logging(log_file: str = "logs/response.log", level: str = "INFO"):
    os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger(__name__)


logger = setup_logging("logs/response.log")


class BaseAPIClient(ABC):
    """Абстрактный класс для работы с API"""

    def __init__(self, base_url: str, timeout: int = 15):
        self._base_url = base_url.rstrip('/')
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({'User-Agent': 'Aircraft-Client/1.0'})

    def _make_request(self, url: str, params: Optional[Dict] = None) -> Optional[Any]:
        try:
            logger.info(f"GET {url}")
            response = self._session.get(url, params=params, timeout=self._timeout)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.Timeout:
            logger.error("Таймаут запроса")
            return None
        except requests.exceptions.ConnectionError:
            logger.error("Ошибка соединения")
            return None
        except Exception as e:
            logger.error(f"Ошибка: {e}")
            return None

    @abstractmethod
    def get_info(self, **kwargs) -> Any:
        pass

    @abstractmethod
    def connect(self) -> bool:
        pass

    @abstractmethod
    def get_aeroplanes(self, country: str) -> None:
        """Получить самолёты по стране"""
        pass

    @abstractmethod
    def get_info(self) -> List[Dict[str, Any]]:
        """Получить информацию о самолётах"""
        pass



class APIAdapter(BaseAPIClient):
    def __init__(self, timeout: int = 15):
        super().__init__(
            base_url="https://opensky-network.org/api",
            timeout=timeout)

    def connect(self) -> bool:
        """Проверка соединения с API"""
        data = self._make_request(f"{self._base_url}/states/all")
        return data is not None

    def get_info(self, **kwargs) -> Any:
        """Алиас для get_aeroplanes"""
        return self.get_aeroplanes(kwargs.get('country', ''))

    def get_aeroplanes(self, country: str) -> List[Dict[str, Any]]:

        logger.info(f"Поиск самолётов над страной: {country}")

        data = self._make_request(f"{self._base_url}/states/all")

        if not data or 'states' not in data:
            logger.warning("Нет данных от OpenSky")
            return []

        states = data.get('states', [])
        result = []

        for state in states:
            try:
                # Проверяем страну
                origin_country = state[2] if len(state) > 2 else None

                if origin_country and country.lower() in origin_country.lower():
                    result.append({
                        'icao24': state[0],
                        'callsign': state[1].strip() if state[1] else None,
                        'origin_country': state[2],
                        'time_position': state[3],
                        'last_contact': state[4],
                        'longitude': state[5],
                        'latitude': state[6],
                        'baro_altitude': state[7],
                        'on_ground': state[8],
                        'velocity': state[9],
                        'true_track': state[10],
                        'vertical_rate': state[11],
                        'sensors': state[12],
                        'geo_altitude': state[13],
                        'squawk': state[14],
                        'spi': state[15],
                        'position_source': state[16]
                    })
            except (IndexError, TypeError) as e:
                logger.warning(f"Ошибка парсинга state vector: {e}")
                continue

        logger.info(f"Найдено {len(result)} самолётов над {country}")
        return result




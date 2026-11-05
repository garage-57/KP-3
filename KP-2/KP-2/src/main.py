from src.aeroplanes import (
    Aeroplane,
    JSONSaver,
    filter_aeroplanes,
    print_aeroplanes,
    sort_aeroplanes,
    get_top_aeroplanes, get_aeroplanes_by_altitude
)
from src.api_key import APIAdapter
import psycopg2

def user_interaction():
    """Функция для взаимодействия с пользователем"""

    # Создание экземпляра класса для работы с API
    api = APIAdapter()
    api.get_aeroplanes('Canada')
    print(f"Самолётов: {len(api.get_info())}")

    # Ввод данных
    country = input("\nВведите название страны (например, Canada): ").strip()

    if not country:
        print("Страна не указана")
        return

    # Получение информации о самолётах
    print(f" Поиск самолётов над {country}...")
    aeroplanes_data = api.get_aeroplanes(country)

    if not aeroplanes_data:
        print(f"Самолёты над {country} не найдены")
        return

    # Преобразование набора данных в список объектов
    aeroplanes = Aeroplane.cast_to_object_list(aeroplanes_data)
    print(f"Преобразовано {len(aeroplanes)} объектов")

    if not aeroplanes:
        print("Не удалось преобразовать данные")
        return

    print(f"Найдено {len(aeroplanes)} самолётов")

    # Ввод параметров фильтрации
    try:
        top_n = int(input("\nВведите количество самолётов для вывода в топ N: "))
    except ValueError:
        top_n = 5
        print(f"Неверный ввод, использую {top_n}")

    filter_words = input("Введите страны для фильтрации (через пробел): ").split()

    altitude_range = input(
        "Введите диапазон высот (например, 100000 - 150000): "
    ).strip()

    # Фильтрация по стране
    filtered_aeroplanes = filter_aeroplanes(aeroplanes, filter_words)

    # Фильтрация по высоте
    ranged_aeroplanes = get_aeroplanes_by_altitude(filtered_aeroplanes, altitude_range)

    # Сортировка по скорости
    sorted_aeroplanes = sort_aeroplanes(ranged_aeroplanes)

    # Топ-N
    top_aeroplanes = get_top_aeroplanes(sorted_aeroplanes, top_n)

    # Вывод
    print_aeroplanes(top_aeroplanes)

    # Сохранение в файл
    if top_aeroplanes:
        json_saver = JSONSaver("response.json")
        for plane in top_aeroplanes:
            json_saver.add_aeroplane(plane)
        print(f"\nСохранено {len(top_aeroplanes)} самолётов в response.json")


user_interaction()

from db_api import LocationDatabase

def create_route_prompt(user_tags, max_points=5):
    db = LocationDatabase()
    
    # Получаем отфильтрованные места
    filtered_places = db.get_filtered_places(user_tags)
    place_names = [place['name'] for place in filtered_places]
    
    # Получаем матрицы только для отфильтрованных мест
    matrices = db.get_filtered_matrices(place_names)
    
    # Создаем сжатое представление матриц
    compressed_matrices = {
        mode: {
            f"{from_p}->{to_p}": f"{data['distance']:.1f}km, {data['duration']:.0f}min" 
            for from_p, tos in matrix.items() 
            for to_p, data in tos.items()
        }
        for mode, matrix in matrices.items()
    }
    
    prompt = f"""Ты - опытный турагент-планировщик маршрутов. Составь оптимальный туристический маршрут по Калининградской области.

ПРАВИЛА:
1. Используй только предоставленные места и данные о расстояниях/времени
2. Маршрут должен быть логичным, круговым (начало = конец) и удобным
3. Учитывай разные способы передвижения: пешком, велосипед, автомобиль, автобус
4. Количество точек: от 3 до {max_points}
5. Учитывай интересы туриста (теги: {', '.join(user_tags)})
6. Маршрут должен быть выполним за день

МЕСТА:
{[f"{p['name']}: {p['description']}..." for p in filtered_places]}

МАТРИЦЫ РАССТОЯНИЙ/ВРЕМЕНИ:
{compressed_matrices}

ФОРМАТ ОТВЕТА:
1. Краткое описание маршрута с обоснованием выбора
2. Структурированные данные:
route_output: [точка1, точка2 (способ), точка3, ...], общая_дистанция_км, общее_время_часов

Составь оптимальный маршрут, учитывая все требования."""

    return prompt

# Пример использования
user_tags = ["история", "природа"]
prompt = create_route_prompt(user_tags)
print(prompt)
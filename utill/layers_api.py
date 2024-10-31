from utill.db_api import LocationDatabase

class Layer1():
    def __init__(self):
        self.promt="""
            Ты профессиональный сборщик информации. Твоя задача - собрать информацию о поездке в Калининградскую область:

            1. Длительность поездки (только целое положительное число дней от 1 до 30)

            2. Способ передвижения (СТРОГО из списка):
            - машина
            - автобус  
            - велосипед
            - пешком

            3. Интересы (СТРОГО из списка):
            - история
            - природа 
            - наука
            - архитектура
            - искусство
            - спорт

            4. Пожелания пользователя (любые)

            После получения всей информации НЕМЕДЛЕННО отправь сообщение СТРОГО по шаблону:
            chat next (ЧИСЛО_ДНЕЙ; СПОСОБ1, СПОСОБ2...; ИНТЕРЕС1, ИНТЕРЕС2...; ПОЖЕЛАНИЯ)

            Не добавляй кавычек, не изменяй формат. Не общайся после отправки шаблона.

            При получении некорректных данных - запроси корректные.
        """

    def get_promt(self):
        return self.promt

    def validate_input(self, days, transport, interests):
        valid_transport = ['машина', 'автобус', 'велосипед', 'пешая прогулка']
        valid_interests = ['история', 'природа', 'наука', 'архитектура', 'искусство', 'спорт']
        
        try:
            days = int(days)
            if days < 1 or days > 30:
                return False
        except:
            return False
        
        if transport == []:
            return "Пользователь не указал транспорт"
        for t in transport:
            if t not in valid_transport:
                return "Неправильный транспорт"
                
        if interests == []:
            return("Пользователь не указал интересы")
        #for i in interests:
        #    if i not in valid_interests:
        #        return "Неправельные интересы"

        return True

class Layer2():
    def __init__(self):
        pass

    def create_route_prompt(self, days, transport, user_tags, wish, max_points=3):
        db = LocationDatabase()

        if not isinstance(user_tags, list):
            raise TypeError("user_tags должен быть списком")

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
        
        json_format = '''[
        {
            "day": int,
            "route": [
            {"place_id": "int", "place_name": "string", "description": "string"},
            ...
            ],
            "total_distance_km": float,
            "total_time_hours": float,
            "transport": "string"
        },
        ...
        ]'''

        prompt = f"""Ты - опытный турагент-планировщик маршрутов. Составь оптимальный туристический маршрут по Калининградской области на {days} дней.

        ПРАВИЛА:
        1. Используй только предоставленные места и данные о расстояниях/времени
        2. Маршрут должен быть логичным и удобным, охватывающим все дни пребывания
        3. Учитывай только следующие способы передвижения: {', '.join(transport)}
        4. Количество точек в день: от 1 до {max_points}
        5. Учитывай интересы туриста (теги: {', '.join(user_tags)}) и особое пожелание ({wish})
        6. Распредели места посещения равномерно на все {days} дней
        7. Маршрут может быть не круговым, так как охватывает несколько дней

        ПОЖЕЛАНИЯ К МАРШРУТУ:
        {wish}

        МЕСТА:
        {[f"{{'place_id': {i}, 'place_name': '{p['name']}', 'description': '{p['description']}...'}}" for i, p in enumerate(filtered_places)]}

        МАТРИЦЫ РАССТОЯНИЙ/ВРЕМЕНИ:
        {compressed_matrices}

        ФОРМАТ ОТВЕТА:
        Предоставь массив с JSON-массивами, содержащими маршрут на {days} дней в следующем формате в трёх вариациях:
        [  
            {json_format},
            {json_format},
            {json_format}
        ]

        Убедись, что:
        1. Все расчеты расстояний и времени выполнены точно и математически корректно, используя предоставленные матрицы.
        2. Каждый день имеет свои собственные значения total_distance_km и total_time_hours.
        3. Для каждого дня указан подходящий вид транспорта из списка: {', '.join(transport)}.
        4. Маршрут построен с учётом необходимости возвращения домой и отдыха не перегружай день

        Представь что этот массив ты отправляешь в компьютер, поэтому выдай только JSON-массив без дополнительных пояснений, примечаний, или текста."""

        return prompt

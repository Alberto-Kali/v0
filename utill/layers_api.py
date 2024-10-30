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

            После получения всей информации НЕМЕДЛЕННО отправь сообщение СТРОГО по шаблону:
            chat next (ЧИСЛО_ДНЕЙ; СПОСОБ1, СПОСОБ2...; ИНТЕРЕС1, ИНТЕРЕС2...)

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
        for i in interests:
            if i not in valid_interests:
                return "Неправельные интересы"

        return True

class Layer2():
    def __init__(self):
        self.promt="""
            Ты профессиональный составитель маршрутов
        """

    def get_promt(self):
        return self.promt

from utill.giga_api import GigaAPI
from utill.layers_api import Layer1, Layer2, Layer3
from utill.db_api import LocationDatabase
import json


api = GigaAPI()
db = LocationDatabase()



class Traveler():
    def __init__(self):
        self.characters = [

        ]
        self.collectorOUT = ""
        self.routerOUT = ()
        self.correctorOUT = {}
        self.finalRoute = {}
    
    def collector(self, user_id, input_queue, output_queue):
        layer = Layer1()
        prompt = layer.get_promt()
        history = [
            {
                "role": "system",
                "content": prompt
            },
        ]
        while True:
            user_message = input_queue.get()
            history.append({"role": "user", "content": user_message})
            response = api.get_simple_answer(history)
            assistant_message = response['choices'][0]["message"]['content']
            if "chat" in assistant_message:
                output_queue.put("Рассчитываю ваше расписание, это займёт примерно 4 минуты...")
                out = assistant_message.strip().split('chat')[1]
                out = out[7:-1].strip().split(";")
                out = [x.strip().split(',') for x in out]
                out[2] = [x.strip() for x in out[2]]
                valid = layer.validate_input(int(out[0][0]), out[1], out[2])
                if valid == True:
                    break
                else:
                    history = [
                        {
                        "role": "system",
                        "content": prompt
                        },
                    ]
                    history.append({"role": "system","content": f"Процесс сбора информации был перезапущен, причина: {valid}"})
            else:
                if len(history) < 10:
                    output_queue.put(assistant_message)
                else:
                    history = [
                        {
                        "role": "system",
                        "content": prompt
                        },
                    ]
                    history.append({"role": "system","content": f"Процесс сбора информации был перезапущен, причина: Возникло непонимание"})
        
        self.collectorOUT = out
        return out

    def router(self, user_id, input_queue, output_queue):
        layer = Layer2()
        out = self.collectorOUT
        prompt = layer.create_route_prompt(out[0], out[1], out[2], out[3])
        counter = 0
        while counter < 10:
            history = [{"role": "system", "content": prompt}]
            response = api.get_simple_answer(history)
            assistant_message = response['choices'][0]["message"]['content']
            try:
                data = json.loads(assistant_message)
                
                # Проверяем формат данных и приводим к единому виду
                if isinstance(data, list) and all(isinstance(day, dict) for day in data):
                    # Если data уже список словарей, оборачиваем его в список
                    data = [data]
                elif not isinstance(data, list):
                    raise ValueError("Неверный формат данных")
                
                days = db.find_places_from_names(data[0])  # Теперь всегда берем первый элемент
                
                z = ""
                for day_info in data[0]:  # Итерируемся по первому элементу
                    z += (f"День {day_info['day']}:\n")
                    for place in day_info['route']:
                        z += (f"- {place['place_name']} \n")
                    z += (f"Общее расстояние: {day_info['total_distance_km']} км\n")
                    z += ("\n")
                break
            except Exception as e:
                print(f"Ошибка при обработке ответа: {str(e)}")
                counter += 1
                continue
                
        if data and days:
            self.routerOUT = (data[0], days)  # Сохраняем первый элемент
            return (data[0], days)
        else:
            return "Не удалось построить маршруты"

    import json

    def corrector(self, user_id, wish, input_queue, output_queue):
        character_type = "local_enthusiast"
        layer = Layer3()
        data, days = self.routerOUT
        similar_places_by_tags = {}
        for day_data in days:
            day_number = day_data['day']
            tags = []
            for place in day_data['route']:
                place_tags = place.get('tags', [])
                tags.extend(place_tags)
            try:
                if tags:
                    similar_places = db.get_filtered_places(tags)
                    similar_places_by_tags[f"day_{day_number}"] = similar_places
                else:
                    similar_places_by_tags[f"day_{day_number}"] = []
            except Exception as e:
                #output_queue.put(f"Ошибка при поиске похожих мест для дня {day_number}: {str(e)}")
                similar_places_by_tags[f"day_{day_number}"] = []

        try:
            prompt = layer.create_route_optimization_prompt(days, similar_places_by_tags, wish, character_type)
            history = [{"role": "system", "content": prompt}]
            response = api.get_simple_answer(history)

            while True:
                assistant_message = response['choices'][0]["message"]['content']
                history.append({"role": "assistant", "content": assistant_message})
                
                if "chat done" in assistant_message.lower():
                    self.finalRoute = assistant_message
                    #print(assistant_message)
                    #try:
                    #    # Находим начало JSON в сообщении
                    #    json_start = assistant_message.find('[')
                    #    if json_start == -1:
                    #        raise ValueError("JSON не найден в ответе")
                    #    
                    #    json_str = assistant_message[json_start:]
                    #    data = json.loads(json_str)
                    #    
                    #    # Проверяем формат данных
                    #    if not isinstance(data, list) or not all(isinstance(day, dict) for day in data):
                    #        raise ValueError("Неверный формат данных")
                    #    
                    #    z = ""
                    #    for day_info in data:
                    #        z += f"День {day_info['day']}:\n"
                    #        for place in day_info['route']:
                    #            z += f"- {place['place_name']} \n"
                    #        z += f"Общее расстояние: {day_info['total_distance_km']} км\n\n"

                    #except json.JSONDecodeError as e:
                    #    print(f"Ошибка при разборе JSON: {str(e)}")
                    #    output_queue.put("К сожалению пока что наш код может распознать не все выводы нейросети, но скоро мы это исправим :)")
                    #except Exception as e:
                    #    print(f"Ошибка при обработке ответа: {str(e)}")
                    #    output_queue.put("К сожалению пока что наш код может распознать не все выводы нейросети, но скоро мы это исправим :)")
                    #else:
                        #output_queue.put("Ваш маршрут: \n" + z)
                    output_queue.put("Маршрут завершен.")
                    break
                
                output_queue.put(assistant_message)
                user_input = input_queue.get()
                history.append({"role": "user", "content": user_input})
                
                response = api.get_simple_answer(history)
        except Exception as e:
            output_queue.put(f"Произошла ошибка, уже работаем над исправлением :)")

        output_queue.put("Спасибо!")
    
    def process_all_layers(self, user_id, input_queue, output_queue):
        self.collector(user_id, input_queue, output_queue)
        self.router(user_id, input_queue, output_queue)
        self.corrector(user_id, input_queue, output_queue)
    
    def process_only_collector(self, user_id, input_queue, output_queue):
        self.collector(user_id, input_queue, output_queue)
        return self.collectorOUT

    def process_only_router(self, collectorOUT, user_id, input_queue, output_queue):
        self.collectorOUT = collectorOUT
        self.router(user_id, input_queue, output_queue)
        return self.routerOUT

    def process_only_corrector(self, routerOUT, user_id, wish, input_queue, output_queue):
        self.routerOUT = routerOUT
        self.corrector(user_id, wish, input_queue, output_queue)
        return self.correctorOUT

from utill.giga_api import GigaAPI
from utill.layers_api import Layer1, Layer2, Layer3
from utill.db_api import LocationDatabase
import json

api = GigaAPI()
db = LocationDatabase()

#------------Слой1

layer1 = Layer1()
promt1 = layer1.get_promt()

history = [
    {
      "role": "system",
      "content": promt1
    },
]

while True:
    # ВВоД
    user_message = input("> ")

    #Составление ответа
    history.append({"role": "user", "content": user_message})
    data = {
        "mode": "instruction",
        "messages": history
    }

    #Получение ответа
    response = api.get_simple_answer(history)


    #print(history)
    #print(response)

    
    assistant_message = response['choices'][0]["message"]['content']
    history.append({"role": "assistant", "content": assistant_message})
    print(assistant_message)
    if assistant_message[0:4] == "chat":
        out = assistant_message[11:-1].split(";")
        out = [x.strip().split(',') for x in out]
        out[2] = [x.strip() for x in out[2]]
        valid = layer1.validate_input(int(out[0][0]), out[1], out[2])
        if valid == True:
            break
        else:
            history = [
                {
                "role": "system",
                "content": promt1
                },
            ]
            history.append({"role": "assistant","content": valid})
            


#-------------Слой2

layer2 = Layer2()
days = out[0]
transport = out[1]
user_tags = out[2]
wish = out[3]
promt2 = layer2.create_route_prompt(days, transport, user_tags, wish)
#print(promt2)

history = [
    {
      "role": "system",
      "content": promt2
    },
]

response = api.get_simple_answer(history)
assistant_message = response['choices'][0]["message"]['content']

# Парсим JSON в Python-объект
data = json.loads(assistant_message)

# Теперь data - это список словарей Python
# Можно обращаться к элементам, например:
for day_info in data:
    print(f"День {day_info['day']}:")
    for place in day_info['route']:
        print(f"- {place['place_name']}")
    print(f"Общее расстояние: {day_info['total_distance_km']} км")
    print()

print(db.find_places_from_names(data))



#--------------Слой3

layer3 = Layer3()

# Выбор персонажа может быть основан на предпочтениях пользователя
character_type = "local_enthusiast"  # или "historian", "adventure_guide", "friendly_guide"

for day in days:
    current_places_tags = [tag for place in day['route'] for tag in place.get('tags', [])]
    similar_places = db.get_filtered_places(current_places_tags)
        
    while True:
        prompt = create_daily_schedule_prompt(day, similar_places, character_type)
        response = send_to_model(prompt)
        print(response)
            
        user_input = input("Ваш ответ: ")
            
        if "chat next 1" in response.lower():
            break
            
        prompt += f"\nПользователь: {user_input}\n"

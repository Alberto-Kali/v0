from utill.giga_api import GigaAPI
from utill.layers_api import Layer0, Layer1, Layer2

api = GigaAPI()


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
        valid = layer1.validate_input(int(out[0]), out[1], out[2])
        if valid == True:
            break
        else:
            history.append({"role": "system","content": valid})


#-------------Слой2

layer2 = Layer2()
promt2 = layer2.get_promt()

history = [
    {
      "role": "system",
      "content": promt2
    },
]


import telebot
from telebot import types
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from threading import Thread
import queue
import time
from utill.processor import Traveler

traveler = Traveler()
bot = telebot.TeleBot('7631980240:AAGri9lZHMVuyCCqFKaBh14zsSCDrFqfDbk')

user_processes = {}
user_data = {}
user_messages = {}

@bot.message_handler(commands=['start'])
def handle_start_command(message):
    if isinstance(message, dict):
        chat_id = message['chat']['id']
    else:
        chat_id = message.chat.id
    
    bot.send_chat_action(chat_id, 'typing')
    user_name = bot.get_chat(chat_id).first_name
    welcome_text = f"""
    Привет, {user_name}! 👋 Я твой AI-гид по Калининградской области.
    Я могу помочь тебе составить тур по Калининграду и области на основе твоих предпочтений.
    """
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Составить тур", callback_data="start_survey"))
    markup.add(types.InlineKeyboardButton("Настройки", callback_data="settings"))
    
    try:
        photo = open('prev.jpg', 'rb')
        bot.send_photo(chat_id, photo, caption=welcome_text, reply_markup=markup)
    except Exception as e:
        print(f"Ошибка при отправке изображения: {str(e)}")
        bot.send_message(chat_id, welcome_text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    bot.send_chat_action(call.message.chat.id, 'typing')
    user_id = call.message.chat.id
    try:
        if call.data == "start_survey":
            markup = types.InlineKeyboardMarkup()
            markup.add(
                types.InlineKeyboardButton("Да", callback_data="local_yes"),
                types.InlineKeyboardButton("Нет", callback_data="local_no")
            )
            survey_message = bot.send_message(
                call.message.chat.id,
                "Вы являетесь местным жителем?",
                reply_markup=markup
            )
            user_data[user_id] = {
                'survey_message_id': survey_message.message_id,
                'step': 'local_check'
            }

        elif call.data in ["local_yes", "local_no"]:
            user_data[user_id]['is_local'] = (call.data == "local_yes")
            
            markup = types.InlineKeyboardMarkup(row_width=5)
            buttons = [types.InlineKeyboardButton(str(i), callback_data=f"duration_{i}") 
                      for i in range(1, 6)]
            markup.add(*buttons)
            
            bot.edit_message_text(
                "Укажите длительность поездки (выберите количество дней):",
                call.message.chat.id,
                user_data[user_id]['survey_message_id'],
                reply_markup=markup
            )
            user_data[user_id]['step'] = 'duration'

        elif call.data == "settings":
            bot.answer_callback_query(call.id, "Настройки пока недоступны")

        elif call.data.startswith("duration_"):
            duration = int(call.data.split('_')[1])
            user_data[user_id].update({
                'duration': duration,
                'transport': [],
                'step': 'transport'
            })
            
            markup = types.InlineKeyboardMarkup()
            transport_options = ["Машина", "Автобус", "Велосипед", "Пешком"]
            for option in transport_options:
                markup.add(types.InlineKeyboardButton(
                    option,
                    callback_data=f"transport_{option.lower()}"
                ))
            markup.add(types.InlineKeyboardButton("Это всё", callback_data="transport_done"))
            
            bot.edit_message_text(
                "Выберите способы передвижения:",
                call.message.chat.id,
                user_data[user_id]['survey_message_id'],
                reply_markup=markup
            )

        elif call.data.startswith("transport_"):
            if call.data == "transport_done":
                if not user_data[user_id]['transport']:
                    bot.answer_callback_query(call.id, "Выберите хотя бы один способ передвижения")
                    return
                    
                user_data[user_id]['step'] = 'interests'
                user_data[user_id]['interests'] = []
                
                markup = types.InlineKeyboardMarkup()
                interest_options = ["История", "Природа", "Наука", "Архитектура", "Искусство", "Спорт"]
                for option in interest_options:
                    markup.add(types.InlineKeyboardButton(
                        option,
                        callback_data=f"interests_{option.lower()}"
                    ))
                markup.add(types.InlineKeyboardButton("Это всё", callback_data="interests_done"))
                
                bot.edit_message_text(
                    "Выберите ваши интересы:",
                    call.message.chat.id,
                    user_data[user_id]['survey_message_id'],
                    reply_markup=markup
                )
            else:
                transport = call.data.split('_')[1]
                if transport in user_data[user_id]['transport']:
                    user_data[user_id]['transport'].remove(transport)
                else:
                    user_data[user_id]['transport'].append(transport)
                
                markup = types.InlineKeyboardMarkup()
                transport_options = ["Машина", "Автобус", "Велосипед", "Пешком"]
                for option in transport_options:
                    markup.add(types.InlineKeyboardButton(
                        f"✓ {option}" if option.lower() in user_data[user_id]['transport'] else option,
                        callback_data=f"transport_{option.lower()}"
                    ))
                markup.add(types.InlineKeyboardButton("Это всё", callback_data="transport_done"))
                
                bot.edit_message_text(
                    "Выберите способы передвижения:",
                    call.message.chat.id,
                    user_data[user_id]['survey_message_id'],
                    reply_markup=markup
                )

        elif call.data.startswith("interests_"):
            if call.data == "interests_done":
                if not user_data[user_id]['interests']:
                    bot.answer_callback_query(call.id, "Выберите хотя бы один интерес")
                    return
                    
                bot.edit_message_text(
                    "Опишите ваши дополнительные пожелания:",
                    call.message.chat.id,
                    user_data[user_id]['survey_message_id']
                )
                user_data[user_id]['step'] = 'wishes'
            else:
                interest = call.data.split('_')[1]
                if interest in user_data[user_id]['interests']:
                    user_data[user_id]['interests'].remove(interest)
                else:
                    user_data[user_id]['interests'].append(interest)
                
                markup = types.InlineKeyboardMarkup()
                interest_options = ["История", "Природа", "Наука", "Архитектура", " Искусство", "Спорт"]
                for option in interest_options:
                    markup.add(types.InlineKeyboardButton(
                        f"✓ {option}" if option.lower() in user_data[user_id]['interests'] else option,
                        callback_data=f"interests_{option.lower()}"
                    ))
                markup.add(types.InlineKeyboardButton("Это всё", callback_data="interests_done"))
                
                bot.edit_message_text(
                    "Выберите ваши интересы:",
                    call.message.chat.id,
                    user_data[user_id]['survey_message_id'],
                    reply_markup=markup
                )

    except Exception as e:
        print(f"Ошибка в обработке колбека: {str(e)}")
        bot.answer_callback_query(call.id, "Произошла ошибка. Попробуйте еще раз.")
    
    finally:
        bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_id = message.chat.id
    if user_id in user_data:
        if user_data[user_id]['step'] == 'wishes':
            user_data[user_id]['wishes'] = message.text
            
            summary = f"📋 Результаты опроса:\n\n" \
                     f"🕒 Длительность: {user_data[user_id]['duration']} дней\n" \
                     f"🚗 Транспорт: {', '.join(user_data[user_id]['transport'])}\n" \
                     f"🎯 Интересы: {', '.join(user_data[user_id]['interests'])}\n" \
                     f"📝 Пожелания: {user_data[user_id]['wishes']}"
            
            bot.edit_message_text(
                summary,
                message.chat.id,
                user_data[user_id]['survey_message_id']
            )
            
            processing_message = bot.send_message(
                message.chat.id,
                "⏳ Ваш запрос обрабатывается...\nЭто может занять несколько минут."
            )
            
            out = [
                user_data[user_id]['duration'],
                user_data[user_id]['transport'],
                user_data[user_id]['interests'],
                user_data[user_id]['wishes']
            ]
            
            try:
                print(out)
                start_neuro_process(message, out)
                user_data[user_id]['step'] = 'chat'
                markup = ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(KeyboardButton("Время для финального ответа"))
                markup.add(KeyboardButton("Перезапуск"))
                #bot.send_message(message.chat.id, "Используйте кнопки для управления:", reply_markup=markup)
            except Exception as e:
                bot.send_message(message.chat.id, f"Произошла ошибка при составлении тура: {str(e)}")
        
        elif user_data[user_id]['step'] == 'chat':
            if message.text == "Перезапуск":
                if user_id in user_processes:
                    user_processes[user_id]['active'] = False
                if user_id in user_data:
                    del user_data[user_id]
                bot.send_message(message.chat.id, "Перезапуск бота...", reply_markup=ReplyKeyboardRemove())
                handle_start_command(message)
            elif message.text == "Время для финального ответа":
                if user_id in user_processes and user_processes[user_id]['active']:
                    user_processes[user_id]['input_queue'].put("Время для финального ответа")
            elif user_id in user_processes and user_processes[user_id]['active']:
                user_processes[user_id]['input_queue'].put(message.text)
            else:
                bot.reply_to(message, "Извините, ваш процесс больше не активен. Пожалуйста, начните заново.")
                handle_start_command(message)
    
    elif message.text == "Составить тур":
        start_survey(message)
    else:
        bot.reply_to(message, "Используйте кнопки для взаимодействия с ботом")

def start_neuro_process(message, out):
    user_id = message.chat.id
    
    if user_id in user_processes:
        user_processes[user_id]['active'] = False
    
    input_queue = queue.Queue()
    output_queue = queue.Queue()
    
    def run_process():
        try:
            traveler.process_only_corrector(traveler.process_only_router(out, user_id, input_queue, output_queue), user_id, input_queue, output_queue)
        except Exception as e:
            bot.send_message(user_id, f"Произошла ошибка: {str(e)}")
        finally:
            if user_id in user_processes:
                user_processes[user_id]['active'] = False

    process_thread = Thread(target=run_process)
    process_thread.start()
    
    user_processes[user_id] = {
        'thread': process_thread,
        'input_queue': input_queue,
        'output_queue': output_queue,  # Исправлено здесь
        'active': True
    }
    
    Thread(target=handle_output, args=(user_id,)).start()

def handle_output(user_id):
    while user_id in user_processes and user_processes[user_id]['active']:
        try:
            output = user_processes[user_id]['output_queue'].get(timeout=1)
            bot.send_message(user_id, output)
            
            if "Спасибо!" in output or "Маршрут завершен." in output:
                if user_id in user_processes:
                    user_processes[user_id]['active'] = False
                if user_id in user_data:
                    del user_data[user_id]
                bot.send_message(user_id, "Перезапуск бота...", reply_markup=ReplyKeyboardRemove())
                bot.send_message(user_id, "Для начала нового тура нажмите /start")
                break
                
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Ошибка при отправке сообщения: {str(e)}")
            user_processes[user_id]['active'] = False
            bot.send_message(user_id, "Извините, произошла ошибка. Пожалуйста, начните заново.", 
                           reply_markup=ReplyKeyboardRemove())
            bot.send_message(user_id, "Для начала нового тура нажмите /start")
            break

def run_bot():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(f"Произошла ошибка при работе бота: {str(e)}")
            print("Перезапуск бота через 3 секунд...")
            time.sleep(3)

if __name__ == '__main__':
    run_bot()
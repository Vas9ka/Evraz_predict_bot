import telebot
import os
import user
import model
import catboost
from telebot import types
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
from flask import Flask, request
predict_model = catboost.CatBoostRegressor().load_model('saved_model')
TOKEN = '1630197252:AAHRN0xbUGeLA-WnFnWvor1j-gGUyWUkr6g'
bot = telebot.TeleBot(TOKEN)
server = Flask(__name__) 
users = {}
markup = types.ReplyKeyboardMarkup(row_width=1)
itembtn1 = types.KeyboardButton('Отправить документ')
markup.add(itembtn1)

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привет! Этот бот умеет предсказывать значение сыпучей извести по данным!', reply_markup=markup)

@bot.message_handler(commands=['mode'])
def help_message(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    keyboard.row(
        telebot.types.InlineKeyboardButton('csv', callback_data='get-csv'),
        telebot.types.InlineKeyboardButton('текст', callback_data='get-текст')
    )
    bot.send_message(message.chat.id, 'При помощи этой команды ты можешь сменить формат получаемого предсказания. '
                                      'Нажми на кнопку "текст", чтобы получать предсказания в виде сообщений от бота. '
                                      'Нажми на кнопку "csv", чтобы получать предсказания в виде файла формата .csv ',reply_markup=keyboard)
@bot.callback_query_handler(func=lambda call: True)
def iq_callback(query):
   data = query.data
   if data.startswith('get-'):
       get_ex_callback(query)

def get_ex_callback(query):
    bot.answer_callback_query(query.id)
    if query.data[4:] == 'csv':
        users[query.message.chat.id].mode = 'csv'
        bot.send_message(query.message.chat.id, "Был успешно выбран режим csv")
    else:
        users[query.message.chat.id].mode = 'текст'
        bot.send_message(query.message.chat.id, "Был успешно выбран режим текст")

@bot.message_handler(content_types = ['text'])
def handle_text(message):
    if not users.get(message.chat.id):
        user_ = user.User()
        users[message.chat.id] = user_
    else:
        if(message.text == "Отправить документ"):
            users[message.chat.id].is_document = True
            bot.send_message(message.chat.id, "Пожалуйста, пришли документ")

@bot.message_handler(content_types= ['document'])
def handle_document(message):
    global users
    if users.get(message.chat.id):
        if os.path.exists(f'predict{message.chat.id}.csv'):
            os.remove(f'predict{message.chat.id}.csv')
        if users[message.chat.id].is_document:
            id = message.document.file_id
            document_URL = bot.get_file_url(id)
            users[message.chat.id].document_url = document_URL
            users[message.chat.id].is_document = False

        if users[message.chat.id].document_url != '':
            bot.send_message(message.chat.id, "Данные получены, теперь надо немного потерпеть...")

            
            result = model.read_document(users[message.chat.id].document_url,message.chat.id)
            if users[message.chat.id].mode == 'csv':
                model.get_predict(predict_model, result,'csv',message.chat.id)
                predict = open(f'predict{message.chat.id}.csv','rb')
                bot.send_document(message.chat.id,predict)
            else:
                predict = model.get_predict(predict_model,result,'текст',message.chat.id)
                if len(predict) > 30:
                    bot.send_message(message.chat.id, "Слишком много данных, посылаю первые 30 предсказаний")
                    for value in predict[:30]:
                        bot.send_message(message.chat.id,value)
                else:
                    for value in predict:
                        bot.send_message(message.chat.id,value)


@server.route('/' + TOKEN, methods=['POST'])
def getMessage():
    bot.process_new_updates([telebot.types.Update.de_json(request.stream.read().decode("utf-8"))])

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url='https://styletransferbott.herokuapp.com/' + TOKEN)
    return "!", 200

if __name__ == '__main__':
    #server.debug = True
    #server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
    bot.polling(none_stop=True, interval=0)

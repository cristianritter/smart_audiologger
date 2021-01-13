from telegram.ext import Updater, MessageHandler, Filters
import os
import parse_config
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, TELEGRAM')

NAME = configs['FILES']['name']

updater = Updater(token='1424747599:AAFyyZqM7PZ61BJjoL77MK2mh2i2m8DjOng', use_context=True)


ids_file = os.path.join(ROOT_DIR,'chat_id.txt')
def adiciona_chat_id(chat_id):
    try:
        f = open(ids_file, 'a')
        f.write(str(chat_id)+"\n")
        f.close()
    except Exception as err:
        print("ERRO: ", err)

def remove_chat_id(chat_id):
    try:
        f = open(ids_file, 'r')
        ids_list = f.readlines()
        print(ids_list)
        if str(chat_id) in ids_list:
            ids_list.remove(chat_id)
        elif str(chat_id)+'\n' in ids_list:
            ids_list.remove(str(chat_id)+'\n')
        f.close()
        f = open(ids_file, 'w')
        f.writelines(ids_list)
        f.close()
    except Exception as err:
        print("ERRO: ", err)

def get_chat_ids():
    try:
        f = open(ids_file, 'r')
        ids_list = f.readlines()
    #    print(ids_list)
        clean_ids = []
        for item in ids_list:
            if item.find('\n') > 0:
                clean_ids.append(item[:item.find('\n')])
            else:
                clean_ids.append(item)
        f.close()
    except Exception as err:
        print("ERRO: ", err)
    return clean_ids

def send_message(texto, to='all'):
    ids = get_chat_ids()
    global updater
    if to == 'all':
        for item in ids:
            updater.bot.send_message(chat_id=item, text=texto)
    else:
        updater.bot.send_message(chat_id=to, text=texto)
                                   

def receive_msg(update, context):
    print("Mensagem Recebida via Telegram.")
    if NAME.upper() in update.message.text.upper() and 'CADASTRAR' in str(update.message.text).upper():
        adiciona_chat_id(update.effective_chat.id)
        send_message("Você foi cadastrado para receber alertas de {}.".format(NAME.upper()), update.effective_chat.id)
    elif NAME.upper() in update.message.text.upper() and 'SAIR' in str(update.message.text).upper():
        remove_chat_id(update.effective_chat.id)
        send_message("Você foi não vai mais receber alertas de {}.".format(NAME.upper()), update.effective_chat.id)
  
#  to get chat id https://api.telegram.org/bot1424747599:AAFyyZqM7PZ61BJjoL77MK2mh2i2m8DjOng/getUpdates

echo_handler = MessageHandler(Filters.text & (~Filters.command), receive_msg)
updater.dispatcher.add_handler(echo_handler)

if str(configs['TELEGRAM']['server_enabled']).upper() == 'TRUE': 
    updater.start_polling()

                                 


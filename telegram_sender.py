from telegram.ext import Updater, MessageHandler, Filters
import os
import parse_config
import time

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES')

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
        print(ids_list)
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

def send_message(texto):
    ids = get_chat_ids()
    global updater
    for item in ids:
        updater.bot.send_message(chat_id=item, text=texto)
                                 #noc 978496789

def receive_msg(update, context):
    #print('chegou')
    if NAME.upper() in update.message.text.upper() and 'CADASTRAR' in str(update.message.text).upper():
        #print("adicionou")
        adiciona_chat_id(update.effective_chat.id)
    elif NAME.upper() in update.message.text.upper() and 'SAIR' in str(update.message.text).upper():
        remove_chat_id(update.effective_chat.id)
    #print(update)
    #print(context)
    #print(update.message.text)
    #print(update.effective_chat.id)
    #pass

#  to get chat id https://api.telegram.org/bot1424747599:AAFyyZqM7PZ61BJjoL77MK2mh2i2m8DjOng/getUpdates

echo_handler = MessageHandler(Filters.text & (~Filters.command), receive_msg)
updater.dispatcher.add_handler(echo_handler)
#get_chat_ids()

updater.start_polling()

                                 


from telegram.ext import Updater, MessageHandler, Filters
import os
import parse_config

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('TELEGRAM_CLIENTS_FOLDERS, TELEGRAM_SERVER')

TOKEN = configs['TELEGRAM_SERVER']['token']

NAMES = configs['TELEGRAM_CLIENTS_FOLDERS']

updater = Updater(token=TOKEN, use_context=True)


def adiciona_chat_id(chat_id, DIR):
    ids_file = os.path.join(DIR,'chat_id.txt')
    try:
        f = open(ids_file, 'a')
        f.write(str(chat_id)+"\n")
        f.close()
    except Exception as err:
        print("ERRO: ", err)

def remove_chat_id(chat_id, DIR):
    ids_file = os.path.join(DIR,'chat_id.txt')
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
    ids_file = os.path.join(ROOT_DIR,'chat_id.txt')
    try:
        f = open(ids_file, 'r')
        ids_list = f.readlines()
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
    for name in NAMES:
        if name.lower() in str(update.message.text).lower():   
            if 'CADASTRAR' in str(update.message.text).upper():
                adiciona_chat_id(update.effective_chat.id, configs['TELEGRAM_CLIENTS_FOLDERS'][name])
                send_message("Você foi cadastrado para receber alertas de {}.".format(name.upper()), update.effective_chat.id)
                return
            elif 'SAIR' in str(update.message.text).upper():
                remove_chat_id(update.effective_chat.id, configs['TELEGRAM_CLIENTS_FOLDERS'][name])
                send_message("Você não receberá mais alertas de {}.".format(name.upper()), update.effective_chat.id)
                return
            else:
                send_message("Não consegui entender, tente novamente.", update.effective_chat.id)
                return
    send_message("Nome não encontrado.", update.effective_chat.id)
            
         
    
        
  
#  to get chat id https://api.telegram.org/bot1424747599:AAFyyZqM7PZ61BJjoL77MK2mh2i2m8DjOng/getUpdates

echo_handler = MessageHandler(Filters.text & (~Filters.command), receive_msg)
updater.dispatcher.add_handler(echo_handler)

if str(configs['TELEGRAM_SERVER']['enabled']).upper() == 'TRUE': 
    updater.start_polling()

                                 


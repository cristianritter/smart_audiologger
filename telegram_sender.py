from telegram.ext import Updater, MessageHandler, Filters
import os
import parse_config

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
configuration = parse_config.ConfPacket()
configs = configuration.load_config('TELEGRAM_CLIENTS_FOLDERS, TELEGRAM_SERVER')

TOKEN = configs['TELEGRAM_SERVER']['token']

TELEGRAM_CLIENTS_FOLDERS = configs['TELEGRAM_CLIENTS_FOLDERS']

updater = Updater(token=TOKEN, use_context=True)

for item in TELEGRAM_CLIENTS_FOLDERS:
    folder = configs['TELEGRAM_CLIENTS_FOLDERS'][item]
    filepath = os.path.join(folder, 'chat_id.txt')
    if not os.path.exists(filepath):
        f = open(filepath, 'a')
        f.write("\n")
        f.close()
       
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

def get_chat_ids(ids_file):
    try:
        f = open(ids_file, 'r')
        ids_list = f.readlines()
        clean_ids = []
        for item in ids_list:
            if item.find('\n') > 0:
                clean_ids.append(item[:item.find('\n')])
            elif item.find('\n') == 0:
                continue
            else:
                clean_ids.append(item)
        f.close()
    except Exception as err:
        print("ERRO: ", err)
    return clean_ids

def send_message(texto, to='all'):
    global updater
    if to == 'all':
        for name in TELEGRAM_CLIENTS_FOLDERS:
            if name.upper() in texto.upper():
                file = os.path.join(configs['TELEGRAM_CLIENTS_FOLDERS'][name], 'chat_id.txt')
        if not os.path.exists(file):
            print("Arquivo de chats do telegram não encontrado, verifique configuração TELEGRAM_CLIENTS_FOLDERS")
        ids = get_chat_ids(file)
        for item in ids:
            updater.bot.send_message(chat_id=item, text=texto)
    else:
        updater.bot.send_message(chat_id=to, text=texto)
                                   

def receive_msg(update, context):
    print("Mensagem Recebida via Telegram.")
    for name in TELEGRAM_CLIENTS_FOLDERS:
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
                send_message("Parece que algo não está funcionando como deveria...", update.effective_chat.id)
                return
    send_message("Tente utilizar [CADASTRAR] ou [SAIR] + [NOME DA CONFIGURAÇÃO].", update.effective_chat.id)
            
         
    
        
  
#  to get chat id https://api.telegram.org/bot1424747599:AAFyyZqM7PZ61BJjoL77MK2mh2i2m8DjOng/getUpdates

echo_handler = MessageHandler(Filters.text & (~Filters.command), receive_msg)
updater.dispatcher.add_handler(echo_handler)

if str(configs['TELEGRAM_SERVER']['enabled']).upper() == 'TRUE': 
    updater.start_polling()

                                 


from datetime import date, datetime, timedelta
import parse_config
from time import sleep
import os
configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES')
definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
log_folder = os.path.join(definitive_folder, "logs")
if (not os.path.exists(log_folder)):
    os.path.mkdir(log_folder)
try:
    def adiciona_linha_log(texto, time_offset=0):
            dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
            mes_ano = (datetime.now()+timedelta(seconds=time_offset)).strftime('_%Y%m')
            try:
                filename = 'log'+mes_ano+'.txt'
                logfilepath = os.path.join(log_folder, filename)
                f = open(logfilepath, 'a')
                f.write(dataFormatada + " " + str(texto) +"\n")
                f.close()
            except Exception as err:
                print(dataFormatada, "ERRO ao adicionar linha log: ", err)
                adiciona_linha_log(str(err))
except Exception as ERR:
    print(ERR)
    sleep(50)
    
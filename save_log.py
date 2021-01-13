from datetime import date, datetime, timedelta
import parse_config
configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES')

def adiciona_linha_log(texto, time_offset=0):
        dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
        mes_ano = (datetime.now()+timedelta(seconds=time_offset)).strftime('_%Y%m')
        try:
            logfilename = configs['FILES']['log_folder']+'log'+mes_ano+'.txt'
            f = open(logfilename, 'a')
            f.write(dataFormatada + " " + texto +"\n")
            f.close()
        except Exception as err:
            print(dataFormatada, "ERRO ao adicionar linha log: ", err)
            adiciona_linha_log(err)

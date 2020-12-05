import subprocess
import audiorecorder
from datetime import date, datetime
import shutil
import os
import time
from threading import Thread
from pyzabbix import ZabbixMetric, ZabbixSender
import sys

#its better to create a ramdisk to use because rw disk stressfull

class Waiter(Thread):
    def run(self):
        while 1:
            time.sleep(int(audiorecorder.configs['ZABBIX']['send_metrics_interval']))
            global metric
            send_status_metric(metric)
    
    def stop(self):
        sys.exit()
         
def calculate_fingerprints(filename):
    fpcalc_out = subprocess.check_output('fpcalc -raw -length 5 %s'
                                    % (filename)).decode()
    lista_fp = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
    lista_fp[len(lista_fp)-1]=lista_fp[len(lista_fp)-1][:9]
    return lista_fp

def adiciona_linha_log(texto):
    dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    print(dataFormatada, texto)
    try:
        f = open(audiorecorder.configs['FILES']['log_file'], "a")
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, err)

def send_status_metric(value):
    packet = [
        ZabbixMetric(audiorecorder.configs['ZABBIX']['hostname'], audiorecorder.configs['ZABBIX']['key'], value)
    ]
    ZabbixSender(zabbix_server=audiorecorder.configs['ZABBIX']['zabbix_server'], zabbix_port=int(audiorecorder.configs['ZABBIX']['port'])).send(packet)

def convert_to_mp3(wav_file, mp3_file):
    cmd = 'lame %s %s --silent' % (wav_file,mp3_file)
    subprocess.call(cmd, shell=True)


tt = audiorecorder.AudioRec()

Waiter().start()

metric = 3
double_test = 0
double_time = ""


while (1):
    try:
        tt.listen()
        finger1 = calculate_fingerprints(os.path.join(audiorecorder.parse_config.ROOT_DIR, audiorecorder.configs['FILES']['sample_file']))
        temp_file = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'temp.wav')
        temp_doubt = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'doubt.wav')
        finger2 = calculate_fingerprints(temp_file)
        soma = 0
        for idx, item in enumerate(finger1):
            cont = (bin(int(finger1[idx]) ^ int(finger2[idx])).count("1"))
            soma += cont
        soma /= len(finger1)
        dataFormatada = datetime.now().strftime('%d%m%Y_%H%M%S.mp3')
         
        if (tt.amplitude < float(audiorecorder.configs['DETECTION_PARAM']['silence_offset'])):
            print("silence")
            if (metric != 1):
                adiciona_linha_log("Amplitude: {}, Similaridade: {} - Silencio".format(tt.amplitude, soma))
                metric = 1
                send_status_metric(metric)
        
        elif (soma < float(audiorecorder.configs['DETECTION_PARAM']['similarity_tolerance'])):
            if (metric != 2 and double_test == 0):
                print("Apeears be noise, testing again")
                shutil.copy(temp_file, temp_doubt)
                double_name = dataFormatada
                double_test = 1
            elif (double_test == 1):
                print("Problema de sintonia detectado..")
                adiciona_linha_log("Amplitude: {}, Similaridade: {} - Fora do Ar".format(tt.amplitude, soma))
                metric = 2
                send_status_metric(metric)
                double_test = 2
        else:
            print("not noise - {}".format(soma))
            if (metric != 0):
                adiciona_linha_log("Operação Normal")
                metric = 0  
        
        if (metric != 0):
            if (double_test == 2 ):
                shutil.copy(temp_doubt, double_name)
                double_test = 0
            dest_file = os.path.join(audiorecorder.configs['FILES']['saved_files_folder'], dataFormatada)
            convert_to_mp3(temp_file, dest_file)
         

    except Exception as err:
        print (err)


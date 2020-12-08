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

while (1):
    try:
        tt.listen()
        temp_file = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'temp.wav')
        dataFormatada = datetime.now().strftime('%d%m%Y_%H%M%S.mp3')
         
        amplitude_min = int(audiorecorder.configs['DETECTION_PARAM']['silence_offset']) 
        if ((tt.amplitude_l < amplitude_min) or (tt.amplitude_r < amplitude_min)):
            print("silence - Ch1 {} Ch2 {}".format(tt.amplitude_l, tt.amplitude_r))
            if (metric != 1):
                if tt.amplitude_l < amplitude_min and tt.amplitude_l < amplitude_min:
                    adiciona_linha_log("Both channel - Silencio L+R:{}".format (tt.amplitude_l+tt.amplitude_r))
                elif tt.amplitude_l < amplitude_min:                
                    adiciona_linha_log("Ch1 Amplitude: {}, - Silencio".format(tt.amplitude_l))
                elif tt.amplitude_r < amplitude_min:                
                    adiciona_linha_log("Ch2 Amplitude: {}, - Silencio".format(tt.amplitude_r))
                metric = 1
                send_status_metric(metric)
        
        elif (abs(tt.amplitude_l - tt.amplitude_r) < 1):
            print("fora do ar {} {} ".format(tt.amplitude_l, tt.amplitude_r))
            if metric != 2:
                adiciona_linha_log("Both channel - Fora do AR",)
                metric = 2
                send_status_metric(metric)
       
        else:
            print("not noise {} {}".format(tt.amplitude_l, tt.amplitude_r))
            if (metric != 0):
                adiciona_linha_log("Operação Normal {} {}".format(tt.amplitude_l, tt.amplitude_r))
                metric = 0
        if metric != 0:
            dest_file = os.path.join(audiorecorder.configs['FILES']['saved_files_folder'], dataFormatada)
            convert_to_mp3(temp_file, dest_file)
         

    except Exception as err:
        print (err)


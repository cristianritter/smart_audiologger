import subprocess
import audiorecorder
from datetime import date, datetime, timedelta
import shutil
import os
import time
from threading import Thread
from pyzabbix import ZabbixMetric, ZabbixSender
import sox
import wave
import parse_config
import threading


#its better to create a ramdisk to use because rw disk stressfull
configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')
temp_folder = configs['FILES']['temp_folder']
definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])

temp_file = os.path.join(temp_folder,'temp.wav')
doubt_file = os.path.join(temp_folder,'doubt.wav')
temp_out_of_phase = os.path.join(temp_folder,'out_of_phase.wav')
temp_fail_file = os.path.join(temp_folder,'fail.wav')
temp_hour_file = os.path.join(temp_folder,'hour_file.wav')

amplitude_min = float(audiorecorder.configs['DETECTION_PARAM']['silence_offset']) 
stereo_min = float(audiorecorder.configs['DETECTION_PARAM']['stereo_offset'])
similarity_tolerance = float(audiorecorder.configs['DETECTION_PARAM']['similarity_tolerance'])

tt = audiorecorder.AudioRec()
last_closed_hour = 30
metric = 5
double_test = 0
fail_name = ""

class Main(Thread):
    def run(self):
        while 1:
            main()
            time.sleep(1)

def close_hour_file(): 
    definitive_day_dir = os.path.join(definitive_folder, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d'))    
    definitive_hour_file = os.path.join(definitive_day_dir, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d_%H.mp3'))
    print(datetime.now().strftime('%M%S'))
    if int(datetime.now().strftime('%M%S')) > int(configs['AUDIO_PARAM']['input_block_time']):
        global last_closed_hour
        if last_closed_hour != int(datetime.now().strftime('%H')):
            print("entrou")
            last_closed_hour = int(datetime.now().strftime('%H'))
            if not os.path.exists(definitive_day_dir):
                os.mkdir(definitive_day_dir)
            if os.path.exists(temp_hour_file):            
                convert_wav_to_mp3(temp_hour_file, definitive_hour_file)
          #  shutil.copy(temp_file, temp_hour_file)
            time.sleep(1)
            os.remove(temp_hour_file)
    time.sleep(1)

def is_stereo(filename):
    tfm = sox.Transformer()
    tfm.oops()
    try:
        os.remove(temp_out_of_phase)
    except:
        pass
    tfm.build_file(temp_file,temp_out_of_phase)
    oops_stat = sox.file_info.stat(temp_out_of_phase)
    return oops_stat['RMS     amplitude']
         
def compair_fingerprint(): 
    finger1 = calculate_fingerprints(os.path.join(parse_config.ROOT_DIR, configs['FILES']['sample_file']))
    finger2 = calculate_fingerprints(temp_file)
    soma = 0
    for idx, item in enumerate(finger1):
        cont = (bin(int(item) ^ int(finger2[idx])).count("1"))
        soma += cont
    soma /= len(finger1)
    return soma

def calculate_fingerprints(filename):
    fpcalc_out = subprocess.check_output('fpcalc -algorithm 5 -channels 2 -raw %s'
                                    % (filename)).decode()
    lista_fp = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
    lista_fp[len(lista_fp)-1]=lista_fp[len(lista_fp)-1][:9]
    return lista_fp

def adiciona_linha_log(texto):
    dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    mes_ano = datetime.now().strftime('_%Y%m')
    try:
        logfilename = configs['FILES']['log_folder']+'log'+mes_ano+'.txt'
        f = open(logfilename, 'a')
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, "ERRO ao adicionar linha log: ", err)

def send_status_metric():
    time.sleep(int(audiorecorder.configs['ZABBIX']['send_metrics_interval']))
    global metric
    try:
        packet = [
            ZabbixMetric(configs['ZABBIX']['hostname'], configs['ZABBIX']['key'], metric)
        ]
        ZabbixSender(zabbix_server=configs['ZABBIX']['zabbix_server'], zabbix_port=int(configs['ZABBIX']['port'])).send(packet)
    except:
        pass

def append_files(source, dest):
    data = []
    hf = wave.open(dest, 'rb')
    data.append( [hf.getparams(), hf.readframes(hf.getnframes())] )
    hf.close()
    hf = wave.open(source, 'rb')
    data.append( [hf.getparams(), hf.readframes(hf.getnframes())] )
    hf.close()
   
    hf = wave.open(dest, 'wb')
    hf.setparams(data[0][0])
    hf.writeframes(data[0][1])
    hf.writeframes(data[1][1])
    hf.close()
 
def convert_wav_to_mp3(source, dest):
    subprocess.check_output('sox %s %s'
                            % (source, dest)) 

def main():
    global metric
    try:
        tt.listen()      
        stereo = is_stereo(temp_file)
        soma = compair_fingerprint()
        if ((tt.channels_rms_lvl['L'] < amplitude_min) or (tt.channels_rms_lvl['R'] < amplitude_min)):
            print("Silence Detected - Ch1 lvl:{} Ch2 lvl: {}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R']))
            if (metric != 1):
                adiciona_linha_log("Silence Detected - Ch1 lvl:{} Ch2 lvl: {}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R']))
                metric = 1
                #send_status_metric()       
        
        elif (stereo < stereo_min and soma < similarity_tolerance):
            print("Apeears be noise by stereo comparation {} and fingerprint {:.2f}".format(stereo,soma))
            
            if metric != 2 and double_test == 0:
                shutil.copy(temp_file, doubt_file)
                double_test = 1

            elif double_test == 1:
                adiciona_linha_log("Fora do Ar by stereo comparation {} and fingerprint {:.2f}".format(stereo,soma))
                metric = 2
                #send_status_metric()
       
        elif (tt.clipped['clipped_count'] > 100):
            print("Clipped audio in {} samples".format(tt.clipped))
            if metric != 3:
                adiciona_linha_log("Problemas no AR by clipped counting {}".format(tt.clipped['clippes']))
                metric = 3
                #send_status_metric()
                 
        else:
            print("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{} fingerprint:{:.2f}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R'], stereo, soma))
            if (metric != 0):
                adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{} fingerprint:{}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R'], stereo, soma))
                metric = 0
 
        if metric == 0:
            data_file = datetime.now().strftime('%d%m%Y_%H%M%S.mp3')
            if os.path.exists(temp_fail_file):
                subprocess.check_output('sox %s %s'
                            % (temp_fail_file, os.path.join(configs['FILES']['saved_files_folder'], data_file))) 
                os.remove(temp_fail_file)
            
        if metric != 0:
            if not os.path.exists(temp_fail_file):
                shutil.copy(temp_file, temp_fail_file)
            if double_test == 1:
                double_test = 0
                append_files(doubt_file, temp_fail_file)
            append_files(temp_file, temp_fail_file)

        if os.path.exists(temp_hour_file):
            append_files(temp_file, temp_hour_file)

        close_hour_file()
        #send_status_metric()
        

    except Exception as err:
        print (err)

Main().start()

            
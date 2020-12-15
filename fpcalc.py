import subprocess
import audiorecorder
from datetime import date, datetime
import shutil
import os
import time
from threading import Thread
from pyzabbix import ZabbixMetric, ZabbixSender
import sox


#its better to create a ramdisk to use because rw disk stressfull

temp_file = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'temp.wav')
temp_out_of_phase = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'out_of_phase.wav')
amplitude_min = float(audiorecorder.configs['DETECTION_PARAM']['silence_offset']) 
stereo_min = float(audiorecorder.configs['DETECTION_PARAM']['stereo_offset'])
similarity_tolerance = float(audiorecorder.configs['DETECTION_PARAM']['similarity_tolerance']) 
temp_doubt = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'doubt.wav')

class Waiter(Thread):
    def run(self):
        while 1:
            time.sleep(int(audiorecorder.configs['ZABBIX']['send_metrics_interval']))
            global metric
            send_status_metric(metric)

def is_stereo(filename):
    tfm = sox.Transformer()
    tfm.oops()
    try:
        os.remove(temp_out_of_phase)
    except:
        pass
    tfm.build_file(temp_file,temp_out_of_phase)
    is_silent = sox.file_info.stat(temp_out_of_phase)
    return is_silent['RMS     amplitude']
         
def compair_fingerprint(): 
    finger1 = calculate_fingerprints(os.path.join(audiorecorder.parse_config.ROOT_DIR, audiorecorder.configs['FILES']['sample_file']))
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
    print(dataFormatada, texto)
    try:
        f = open(audiorecorder.configs['FILES']['log_folder']+'log'+mes_ano+'.txt', "a")
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, err)

def send_status_metric(value):
    try:
        packet = [
            ZabbixMetric(audiorecorder.configs['ZABBIX']['hostname'], audiorecorder.configs['ZABBIX']['key'], value)
        ]
        ZabbixSender(zabbix_server=audiorecorder.configs['ZABBIX']['zabbix_server'], zabbix_port=int(audiorecorder.configs['ZABBIX']['port'])).send(packet)
    except:
        pass

def convert_to_mp3(wav_file, mp3_file):
    cmd = 'lame %s %s --silent' % (wav_file,mp3_file)
    subprocess.call(cmd, shell=True)

tt = audiorecorder.AudioRec()
Waiter().start()
metric = 0
double_test = 0

while (1):
    try:
        tt.listen()      
        dataFormatada = datetime.now().strftime('%d%m%Y_%H%M%S.mp3')
        if ( int(datetime.now().strftime('%M%S') ) > (5958 - int(configs['AUDIO_PARAM']['input_block_time']):
            tt.close_hour_file 
 
        stereo = is_stereo(temp_file)
        soma = compair_fingerprint()
        if ((tt.channels_rms_lvl['L'] < amplitude_min) or (tt.channels_rms_lvl['R'] < amplitude_min)):
            print("Silence Detected - Ch1 lvl:{} Ch2 lvl: {}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R']))
            if (metric != 1):
                adiciona_linha_log("Silence Detected - Ch1 lvl:{} Ch2 lvl: {}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R']))
                metric = 1
                send_status_metric(metric)       
        
        elif (stereo < stereo_min and soma < similarity_tolerance):
            print("Apeears be noise by stereo comparation {} and fingerprint {}".format(stereo,soma))
            
            if metric != 2 and double_test == 0:
                shutil.copy(temp_file, temp_doubt)
                doubt_name = dataFormatada
                double_test = 1

            elif double_test == 1:
                adiciona_linha_log("Fora do Ar by stereo comparation {} and fingerprint {}".format(stereo,soma))
                dest_doubt = os.path.join(audiorecorder.configs['FILES']['saved_files_folder'], doubt_name)
                convert_to_mp3(temp_doubt, dest_doubt)
                metric = 2
                send_status_metric(metric)
                double_test = 0

        elif (tt.clipped['clipped_count'] > 100):
            print("Clipped audio in {} samples".format(tt.clipped))
            if metric != 3:
                adiciona_linha_log("Problemas no AR by clipped counting {}".format(tt.clipped['clippes']))
                metric = 3
                send_status_metric(metric)
                 
        else:
            double_test = 0
            print("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{} fingerprint:{}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R'], stereo, soma))
            if (metric != 0):
                adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{} fingerprint:{}".format(tt.channels_rms_lvl['L'], tt.channels_rms_lvl['R'], stereo, soma))
                metric = 0
 
        if metric != 0:
            dest_file = os.path.join(audiorecorder.configs['FILES']['saved_files_folder'], dataFormatada)
            convert_to_mp3(temp_file, dest_file)
        
    except Exception as err:
        print (err)


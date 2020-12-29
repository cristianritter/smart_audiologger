from datetime import date, datetime, timedelta
from threading import Thread
from pyzabbix import ZabbixMetric, ZabbixSender
import parse_config
import time
import subprocess
import os
import shutil
import sox
import struct
import wave

configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')
temp_folder = configs['FILES']['temp_folder']
definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
temp_file = os.path.join(temp_folder,'temp.wav')
temp_out_of_phase = os.path.join(temp_folder,'out_of_phase.wav')
temp_normalized = os.path.join(temp_folder,'normalized.wav')
temp_monoCH1 = os.path.join(temp_folder,'monoCH1.wav')
temp_monoCH2 = os.path.join(temp_folder,'monoCH2.wav')
temp_fail_file = os.path.join(temp_folder,'fail.wav')
temp_hour_file_p = os.path.join(temp_folder,'hour_file_p.mp3')
temp_hour_file_i = os.path.join(temp_folder,'hour_file_i.mp3')
log_folder = configs['FILES']['log_folder']
silence_offset = float(configs['DETECTION_PARAM']['silence_offset']) 
stereo_offset = float(configs['DETECTION_PARAM']['stereo_offset'])
similarity_tolerance = float(configs['DETECTION_PARAM']['similarity_tolerance'])
INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])
AUDIO_COMPRESSION = configs['AUDIO_PARAM']['compression']

attemps = 3
status = 5

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

def compair_fingerprint(): 
    finger1 = calculate_fingerprints(os.path.join(parse_config.ROOT_DIR, configs['FILES']['sample_file']))
    finger2 = calculate_fingerprints(temp_file)
    if len(finger2) < len(finger1):
        for_finger = finger2
    else:
        for_finger = finger1
    soma = 0
    for idx, _ in enumerate(for_finger):
        cont = (bin(int(finger1[idx]) ^ int(finger2[idx])).count("1"))
        soma += cont
    soma /= len(finger1)
    return soma

def calculate_fingerprints(filename):
    fpcalc_out = subprocess.check_output('fpcalc -algorithm 5 -channels 2 -raw %s'
                                    % (filename)).decode()
    lista_fp = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
    lista_fp[len(lista_fp)-1]=lista_fp[len(lista_fp)-1][:9]
    return lista_fp

def file_stats(filename):
    tfm = sox.Transformer()
    tfm.oops()
    remixch1_dictionary = {1: [1], 2: [1] }
    monoch1 = sox.Transformer()
    monoch1.remix(remixch1_dictionary)
    remixch2_dictionary = {1: [2], 2: [2] }
    monoch2 = sox.Transformer()
    monoch2.remix(remixch2_dictionary)
    
    tfm.build_file(temp_file,temp_out_of_phase)
    monoch1.build_file(temp_file,temp_monoCH1)
    monoch2.build_file(temp_file,temp_monoCH2)
    temp_stat = sox.file_info.stat(temp_file)
    oops_stat = sox.file_info.stat(temp_out_of_phase)
    monoch1_stat = sox.file_info.stat(temp_monoCH1)
    monoch2_stat = sox.file_info.stat(temp_monoCH2)
    os.remove(temp_monoCH1)
    os.remove(temp_monoCH2)
    os.remove(temp_out_of_phase)    
    retorno = {}
    retorno['oopsRMS']=oops_stat['RMS     amplitude']
    retorno['tempRMS']=temp_stat['RMS     amplitude']
    retorno['CH1RMS']=monoch1_stat['RMS     amplitude']
    retorno['CH2RMS']=monoch2_stat['RMS     amplitude']
    return retorno


class HorasPares(Thread):
    def run(self):
        while 1:
            if int(datetime.now().strftime('%M%S')) > (5959 - INPUT_BLOCK_TIME) and int(datetime.now().strftime('%H'))%2 != 0:
                while (int(datetime.now().strftime('%M%S'))!= 0):
                    pass
                subprocess.check_output('sox -q -t waveaudio 0 -d %s trim 0 %d' 
                                                % (temp_hour_file_p, 3599))
            time.sleep(INPUT_BLOCK_TIME)
   
class HorasImpares(Thread):
    def run(self):
        while 1:
            if int(datetime.now().strftime('%M%S')) > (5959 - INPUT_BLOCK_TIME) and int(datetime.now().strftime('%H'))%2 == 0:
                while (int(datetime.now().strftime('%M%S'))!= 0):
                    pass
                subprocess.check_output('sox -q -t waveaudio 0 -d %s trim 0 %d' 
                                                % (temp_hour_file_i, 3599))
            time.sleep(INPUT_BLOCK_TIME)

class copia_arquivos(Thread):
    def conversao_final(self, filename_s, filename_d):
        subprocess.check_output('sox %s -C %s %s' 
                                                % (filename_s, AUDIO_COMPRESSION, filename_d))
    def run(self):
        while 1:
            if int(datetime.now().strftime('%M%S')) <= (30) and int(datetime.now().strftime('%H'))%2 != 0: #é impar
                definitive_day_dir = os.path.join(definitive_folder, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d'))    
                definitive_hour_file = os.path.join(definitive_day_dir, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d_%H.mp3'))
                if not os.path.exists(definitive_day_dir):
                    os.mkdir(definitive_day_dir)
                if os.path.exists(temp_hour_file_p):            
                    self.conversao_final(temp_hour_file_p, definitive_hour_file)
                    time.sleep(200)
                    os.remove(temp_hour_file_p)                   
            elif int(datetime.now().strftime('%M%S')) <= (30) and int(datetime.now().strftime('%H'))%2 == 0: #é par
                definitive_day_dir = os.path.join(definitive_folder, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d'))    
                definitive_hour_file = os.path.join(definitive_day_dir, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d_%H.mp3'))
                if not os.path.exists(definitive_day_dir):
                    os.mkdir(definitive_day_dir)
                if os.path.exists(temp_hour_file_i):            
                    self.conversao_final(temp_hour_file_i, definitive_hour_file)
                    time.sleep(200)
                    os.remove(temp_hour_file_i)                   
            time.sleep(30)


def verificar_silencio(infos):
    if float(infos['CH1RMS']) < silence_offset or float(infos['CH2RMS']) < silence_offset:
        return 1            

def verificar_oops_RMS(infos):
    log = {}
    log['oopsRMS'] = float(infos['oopsRMS'])
    log['value'] = 0 
    if  log['oopsRMS'] < stereo_offset:
        log['value'] = 1
    else:
        log['value'] = 0
    return log

def verificar_fingerprint():
    log = {}
    log['similarity'] = compair_fingerprint()
    log['value'] = 0 
    if log['similarity'] < similarity_tolerance:
        log['value'] = 1 
    return log

def verificar_clipped(debug=False):
    max = 0
    contagem = 0
    hf = wave.open(temp_file, 'r')
    bloco_len = hf.getnframes()
    if bloco_len > 200000:
        bloco_len = 200000
    for _ in range(bloco_len):
        wavedata = hf.readframes(1)
        data = struct.unpack("2h", wavedata)
        valor = abs(int(data[0]))
        if valor > max:
            max = valor
        if valor == 32768:
            contagem += 1
    hf.close()
    if debug == True:
        return max
    if contagem > 0:
        return 1

def verifica_resultados(infos):
    global attemps
    global status
    fingerprint_results = verificar_fingerprint()
    oops_results = verificar_oops_RMS(infos)
    if verificar_silencio(infos):
        attemps = 3
        if status != 0:
            print("Silence Detected. Ch1 Lvl:{:.4f} Ch2 lvl: {:.4f}".format(infos['CH1RMS'], infos['CH2RMS']))
            adiciona_linha_log("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']))
            status = 0
        else:
            print("Silence Detected. Ch1 Lvl:{:.4f} Ch2 lvl: {:.4f}".format(infos['CH1RMS'], infos['CH2RMS']))
        
    
    elif verificar_clipped():
        attemps = 3
        if status != 1:
            print("Clipped audio Detected.")
            adiciona_linha_log("Clipped audio detected. Tunning problem or Input volume too high")
            status = 1
        else:
            print("Clipped audio Detected. Tunning Failure or Source Problem")
    
    elif oops_results['value'] and fingerprint_results['value']:
        if attemps <= 0:
            if status != 2:
                print("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                adiciona_linha_log("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                status= 2
            else:
                print("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
        else:
            print("Appears to be a Tuning failure ...  Stereo Gap: {:.4f} and Fingerprint Similarity: {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
            attemps -=1
    
    else:
        attemps = 3
        if status != 3:
            print("On Air Ch1 lvl:{:.4f} Ch1 lvl:{:.4f} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
            adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
            status= 3
        else:       
            print("On Air Ch1 lvl:{:.4f} Ch1 lvl:{:.4f} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))

HorasImpares().start()
HorasPares().start()
copia_arquivos().start()

def Main():
    while 1:
        if os.path.exists(temp_file):
            os.remove(temp_file)
        subprocess.check_output('sox -q -t waveaudio 0 -d %s trim 0 %d'
                                        % (temp_file, INPUT_BLOCK_TIME))
        infos = file_stats(temp_file)
        print("\n")
        verifica_resultados(infos)

Main()
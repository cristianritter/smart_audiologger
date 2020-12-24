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
temp_hour_file = os.path.join(temp_folder,'hour_file.wav')
log_folder = configs['FILES']['log_folder']
silence_offset = float(configs['DETECTION_PARAM']['silence_offset']) 
stereo_offset = float(configs['DETECTION_PARAM']['stereo_offset'])
similarity_tolerance = float(configs['DETECTION_PARAM']['similarity_tolerance'])
INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])

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
    retorno = {}
    retorno['oopsRMS']=oops_stat['RMS     amplitude']
    retorno['tempRMS']=temp_stat['RMS     amplitude']
    retorno['CH1RMS']=monoch1_stat['RMS     amplitude']
    retorno['CH2RMS']=monoch2_stat['RMS     amplitude']
    return retorno


class Main(Thread):
    def create_hour_file(self, duracao):
        print ("Iniciando gravação arquivo da hora")
        subprocess.check_output('sox -t waveaudio 0 -d %s trim 0 %d' 
                                                % (temp_hour_file, duracao))

    def run(self):
        while 1:
            if int(datetime.now().strftime('%M%S')) > 5959 - INPUT_BLOCK_TIME:
                definitive_day_dir = os.path.join(definitive_folder, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d'))    
                definitive_hour_file = os.path.join(definitive_day_dir, (datetime.now()-timedelta(hours=1)).strftime('%Y%m%d_%H.mp3'))
                if not os.path.exists(definitive_day_dir):
                    os.mkdir(definitive_day_dir)
                if os.path.exists(temp_hour_file):            
                    shutil.copy(temp_hour_file, definitive_hour_file)            
        
                while (int(datetime.now().strftime('%M%S'))!= 0):
                    pass
                self.create_hour_file(3599)
            time.sleep(INPUT_BLOCK_TIME)
   

def verificar_silencio(infos):
    if float(infos['CH1RMS']) < silence_offset or float(infos['CH2RMS']) < silence_offset:
        return 1            

def verificar_oops_RMS():
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
    for i in range(bloco_len):
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
    if contagem > bloco_len*0.01:
        return 1

def verifica_resultados(infos):
    global attemps
    global status
    fingerprint_results = verificar_fingerprint()
    oops_results = verificar_oops_RMS()
    if verificar_silencio(infos):
        attemps = 3
        if status != 0:
            adiciona_linha_log("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']))
            status = 0
        else:
            print("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']))
        
    
    elif verificar_clipped():
        attemps = 3
        if status != 1:
            adiciona_linha_log("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']))
            status = 1
        else:
            print("Clipped audio Detected.")
    
    elif oops_results['value'] and fingerprint_results['value']:
        if attemps <= 0:
            if status != 2:
                adiciona_linha_log("Tuning failure detected. Stereo Gap {} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                status= 2
            else:
                print("Tuning failure detected. Stereo Gap {} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
        else:
            print("Appears to be a Tuning failure ...  Stereo Gap: {:.2f} and Fingerprint Similarity: {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
            attemps -=1
    
    else:
        attemps = 3
        if status != 3:
            adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{:.2f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
            status= 3
        else:       
            print("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{:.2f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))



Main().start()

while 1:
    subprocess.check_output('sox -t waveaudio 0 -d %s trim 0 %d'
                                        % (temp_file, INPUT_BLOCK_TIME))
    infos = file_stats(temp_file)
    verifica_resultados(infos)

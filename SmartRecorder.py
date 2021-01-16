try:
    print ("Importando bibliotecas... ")
    from datetime import date, datetime, timedelta
    from threading import Thread
    import parse_config
    from time import sleep
    from subprocess import check_output
    import os.path
    import sox
    from struct import unpack
    from wave import open
    import license_verify
    from sys import exit as EXIT
    import save_log
    import zabbix_metric
    import telegram_sender

    print ("Carregando configurações... ")
    configuration = parse_config.ConfPacket()
    configs = configuration.load_config('FILES, AUDIO_PARAM, DETECTION_PARAM')
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
    silence_offset = float(configs['DETECTION_PARAM']['silence_offset']) 
    stereo_offset = float(configs['DETECTION_PARAM']['stereo_offset'])
    similarity_tolerance = float(configs['DETECTION_PARAM']['similarity_tolerance'])
    INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])
    AUDIO_COMPRESSION = configs['AUDIO_PARAM']['compression']
    AUDIO_DEVICE = int(configs['AUDIO_PARAM']['device_index'])
    NAME = configs['FILES']['name']

    default_attempts_value = 3
    attempts = default_attempts_value
    status = 5

    print ("Definindo classes e funções... ")  

    class Gravador(Thread):
        def run(self):
            while 1:
                current_record_length = 3559 - self.current_seconds()
                partial_record_length = 0
                definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
                definitive_day_dir = os.path.join(definitive_folder, datetime.now().strftime('%Y%m%d'))  
                definitive_hour_file = os.path.join(definitive_day_dir, datetime.now().strftime('%Y%m%d_%H.mp3'))
                definitive_partial_file = ''
                if not os.path.exists(definitive_day_dir):
                    os.mkdir(definitive_day_dir)

                if os.path.exists(definitive_hour_file) and current_record_length > 0:
                    partial_record_length = int(sox.file_info.stat(definitive_hour_file)['Length (seconds)']) 
                    definitive_partial_file = definitive_hour_file[:-4]+'_partial.mp3'
                    if os.path.exists(definitive_partial_file):
                        os.remove(definitive_partial_file)
                    os.rename(definitive_hour_file, definitive_partial_file)

                silence_time = 3559 - (current_record_length + partial_record_length)
                check_output('sox -q -n -C {} -c 2 silence.mp3 trim 0 {}'.format(AUDIO_COMPRESSION, silence_time))
            
                if current_record_length > 0:
                    check_output('sox {} silence.mp3 -q -t waveaudio {} -C {} {} trim 0 {} '.format(definitive_partial_file, AUDIO_DEVICE, AUDIO_COMPRESSION, definitive_hour_file, current_record_length))
                os.remove(definitive_partial_file)
                os.remove('silence.mp3')
        
        def current_seconds(self):
                currentminutesseconds = datetime.now().strftime('%M%S')
                currentseconds = int(currentminutesseconds[0:2])*60+int(currentminutesseconds[3:5])
                return currentseconds

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
        try:
            fpcalc_out = check_output('fpcalc -algorithm 5 -channels 2 -raw %s'
                                            % (filename)).decode()
            lista_fp = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
            lista_fp[len(lista_fp)-1]=lista_fp[len(lista_fp)-1][:9]
            return lista_fp
        except Exception as ERR:
            print("Erro com o arquivo FPCALC "+str(ERR))

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
        hf = open(temp_file, 'r')
        bloco_len = hf.getnframes()
        if bloco_len > 200000:
            bloco_len = 200000
        for _ in range(bloco_len):
            wavedata = hf.readframes(1)
            data = unpack("2h", wavedata)
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
        print('- '+NAME+' -')
        fingerprint_results = verificar_fingerprint()
        oops_results = verificar_oops_RMS(infos)
        if verificar_silencio(infos):
            attemps = default_attempts_value
            if status != 0:
                print("Silence Detected. Ch1 Lvl:{:.4f} Ch2 lvl: {:.4f}".format(infos['CH1RMS'], infos['CH2RMS']))
                save_log.adiciona_linha_log("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']),INPUT_BLOCK_TIME*-1)
                telegram_sender.send_message(NAME+' - Silence detected.')
                zabbix_metric.send_status_metric(NAME+" - Silence Detected")
                status = 0
            else:
                print("Silence Detected. Ch1 Lvl:{:.4f} Ch2 lvl: {:.4f}".format(infos['CH1RMS'], infos['CH2RMS']))
            
        
        elif verificar_clipped():
            attemps = default_attempts_value
            if status != 1:
                print("Clipped audio detected. Tunning problem or Input volume too high.")
                save_log.adiciona_linha_log("Clipped audio detected. Tunning problem or Input volume too high.",INPUT_BLOCK_TIME*-1)
                telegram_sender.send_message(NAME+' - Clipped Audio detected.')
                zabbix_metric.send_status_metric(NAME+" - Clipped Audio Detected")
                status = 1
            else:
                print("Clipped audio detected. Tunning problem or Input volume too high.")
        
        elif oops_results['value'] and fingerprint_results['value']:
            if attemps <= 0:
                if status != 2:
                    print("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                    save_log.adiciona_linha_log("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']), time_offset=INPUT_BLOCK_TIME*-1*default_attempts_value)
                    telegram_sender.send_message(NAME+' - Tunning failure Detected')
                    zabbix_metric.send_status_metric(NAME+" - Tunning failure Detected")
                    status= 2
                else:
                    print("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
            else:
                print("Appears to be a Tuning failure ...  Stereo Gap: {:.4f} and Fingerprint Similarity: {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                attemps -=1
        
        else:
            attemps = default_attempts_value
            if status != 3:
                print("On Air Ch1 lvl:{:.4f} Ch1 lvl:{:.4f} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
                save_log.adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
                telegram_sender.send_message(NAME+' - On Air.')
                status= 3
            else:       
                print("On Air Ch1 lvl:{:.4f} Ch1 lvl:{:.4f} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
                zabbix_metric.send_status_metric(NAME+" - On Air")
                
    def carregar_licenca():
        License = license_verify.Lic()
        result = License.verifica(1)
        if result == 0:
            print('Falha ao validar a licença', 'Adquira uma permissão para utilizar o aplicativo')
            sleep(50)
            EXIT()

    carregar_licenca()
    Gravador().start()

    def Main():
        while 1:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            check_output('sox -q -t waveaudio %d -d %s trim 0 %d'
                                            % (AUDIO_DEVICE, temp_file, INPUT_BLOCK_TIME))
            infos = file_stats(temp_file)
            print("\n")
            verifica_resultados(infos)
    print("Operação iniciada!")
    Main()
except Exception as Err:
    print (Err)
    sleep(50)
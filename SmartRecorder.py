try:
    print ("Importando bibliotecas... ")
    from datetime import date, datetime, timedelta
    from threading import Thread
    import parse_config
    from time import sleep
    from subprocess import check_output, Popen, PIPE
    import os.path
    from struct import unpack
    from wave import open
    import license_verify
    from sys import exit as EXIT
    import save_log
    import zabbix_metric
    import telegram_sender
    from shutil import rmtree
    import pyaudio
    import list_devices

    ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
    print("Carregando DLLS...")
    try:
        SOX_DIR = os.path.join(ROOT_DIR, 'sox-14-4-1')
        SOX = os.path.join(SOX_DIR, 'sox')     
        os.add_dll_directory(r'{}'.format(SOX_DIR))
    except Exception as Err:
        print('DLL ERROR - '+str(Err))
        EXIT()

    print ("Carregando configurações... ")
    configuration = parse_config.ConfPacket()
    configs = configuration.load_config('FILES, AUDIO_PARAM, DETECTION_PARAM')
    temp_folder = configs['FILES']['temp_folder']
    definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
    temp_file = os.path.join(temp_folder,'temp.wav')
    silence_offset = float(configs['DETECTION_PARAM']['silence_offset']) 
    stereo_offset = float(configs['DETECTION_PARAM']['stereo_offset'])
    default_attempts_value = int(configs['DETECTION_PARAM']['fp_attempts'])
    similarity_tolerance = float(configs['DETECTION_PARAM']['similarity_tolerance'])
    INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])
    AUDIO_COMPRESSION = configs['AUDIO_PARAM']['compression']
    AUDIO_DEVICE = int(configs['AUDIO_PARAM']['audio_device'])
    CHANNELS = int(configs['AUDIO_PARAM']['channels'])
    INPUT_GAIN = int(configs['AUDIO_PARAM']['input_gain'])
    NAME = configs['FILES']['name']
    LIFETIME = int(configs['FILES']['lifetime'])

    pa = pyaudio.PyAudio()
    print("Dispositivo de audio: ", pa.get_device_info_by_index(AUDIO_DEVICE)["name"])

    attemps = default_attempts_value
    status = 5

    print("Verificando diretórios")
    if not os.path.exists(definitive_folder):
        os.mkdir(definitive_folder)
    if not os.path.exists(temp_folder):
        os.mkdir(temp_folder)

    print ("Definindo classes e funções... ")  

    def finaliza(definitive_hour_file, definitive_partial_file, comm_append_partial, comm_append_synth):
        definitive_full_file = definitive_hour_file[:-4]+'_full.mp3'
        comm_append_final = '"| {} {} -C {} -c {} -p"'.format(
                            SOX, definitive_hour_file, AUDIO_COMPRESSION, CHANNELS)
        comando = ' {} --combine concatenate {} {} {}  {}'.format(
                        SOX, comm_append_partial, comm_append_synth, comm_append_final, definitive_full_file)    
        check_output(comando)

        try:
            if os.path.exists(definitive_partial_file):
                os.remove(definitive_partial_file)
            if os.path.exists(definitive_hour_file):
                os.remove(definitive_hour_file)
                os.rename(definitive_full_file, definitive_hour_file)
        except Exception as ERR:
            print(ERR)
             
    def gravar():   
        while 1:
            print('Iniciando loop. Current seconds=', current_seconds())
            if current_seconds() > 3500:
                print('Aguardando o inicio da próxima hora para iniciar a gravação.')
                sleep(1)
                continue
          
            definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
            partial_record_length = 0
            comm_append_partial = ''
            comm_append_synth = ''
            definitive_partial_file = ''
             
            definitive_day_dir = os.path.join(definitive_folder, datetime.now().strftime('%Y%m%d'))  
            if not os.path.exists(definitive_day_dir):
                os.mkdir(definitive_day_dir)
              
            current_record_length = 3599 - current_seconds()                
               
            definitive_hour_file = os.path.join(definitive_day_dir, datetime.now().strftime('%Y%m%d_%H.mp3'))
            if os.path.exists(definitive_hour_file):
                print('Foram encontrados arquivos antigos...')
                definitive_partial_file = definitive_hour_file[:-4]+'_partial.mp3'
                if os.path.exists(definitive_partial_file):
                    definitive_hour_file_old = definitive_hour_file[:-4]+'_old.mp3'
                    if os.path.exists(definitive_hour_file_old):
                        os.remove(definitive_hour_file_old)
                    os.rename(definitive_hour_file, definitive_hour_file_old)
                    print('Organizando arquivos ...')
                    check_output('{} {} {} {}'.format(
                            SOX, definitive_partial_file, definitive_hour_file_old, definitive_hour_file
                                            ))
                    os.remove(definitive_partial_file)
                    os.remove(definitive_hour_file_old)
                
                print('Criando arquivo parcial...')
                os.rename(definitive_hour_file, definitive_partial_file)
                #partial_record_length = int(sox.file_info.stat(definitive_partial_file)['Length (seconds)']) 
                partial_record_length = float(
                    check_output('{} --i -D {}'.format(
                            SOX, definitive_partial_file))
                    #sox.file_info.stat(definitive_partial_file)['Length (seconds)']
                    ) 
                comm_append_partial = '"|{} {} -C {} -c {} -p"'.format(
                            SOX, definitive_partial_file, AUDIO_COMPRESSION, CHANNELS)
                print('Comprimento do audio parcial encontrado: ', partial_record_length)

            current_record_length = 3599 - current_seconds()                    
            silence_time = 3599 - (current_record_length + partial_record_length)
            print('Partial record length: ', partial_record_length)
            print('Tempo de  gravação nesta hora: ', current_record_length, 'Enxerto de silencio: ', silence_time)                             
            if silence_time > 2:
                comm_append_synth = '"|{} -n -C {} -c {} -p synth {} pl D2"'.format(
                            SOX, AUDIO_COMPRESSION, CHANNELS, silence_time)

            comm_gravacao = '{} -q -t waveaudio {} -C {} -c {} {} gain {} trim 0 {}'.format(
                        SOX, AUDIO_DEVICE, AUDIO_COMPRESSION, CHANNELS, definitive_hour_file, INPUT_GAIN, current_record_length)

            print('Iniciando a gravação. Current seconds=', current_seconds())
            check_output(comm_gravacao)
            print('Finalizando a gravação. Current seconds=', current_seconds())
            T = Thread(target=finaliza, args=(definitive_hour_file, definitive_partial_file, comm_append_partial, comm_append_synth))
            T.start()
            print('Tudo pronto. Current seconds: ', current_seconds())

    def current_seconds():
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
            fpcalc_out = check_output('fpcalc -algorithm 5 -channels {} -raw {}'.format(CHANNELS, filename)).decode()
            lista_fp = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
            lista_fp[len(lista_fp)-1]=lista_fp[len(lista_fp)-1][:9]
            return lista_fp
        except Exception as ERR:
            print("Erro com o arquivo FPCALC "+str(ERR))

    def file_stats(filename):
        temp_out_of_phase = os.path.join(temp_folder,'out_of_phase.wav')
        temp_monoCH1 = os.path.join(temp_folder,'monoCH1.wav')
        temp_monoCH2 = os.path.join(temp_folder,'monoCH2.wav')
    
        check_output('{} {} {} remix 1,2i 1,2i'.format(
                            SOX, temp_file, temp_out_of_phase
                                            ))

        check_output('{} {} {} remix 1 1'.format(
                            SOX, temp_file, temp_monoCH1
                                            ))
        
        check_output('{} {} {} remix 2 2'.format(
                            SOX, temp_file, temp_monoCH2
                                            ))
       
        temp_stat = Popen('{} {} -n stat'.format(
                            SOX, temp_file ), stdout=None, stderr=PIPE ).communicate()[1].decode()
        oops_stat = Popen('{} {} -n stat'.format(
                            SOX, temp_out_of_phase ), stdout=None, stderr=PIPE).communicate()[1].decode()
        monoch1_stat = Popen('{} {} -n stat'.format(
                            SOX, temp_monoCH1 ), stdout=None, stderr=PIPE).communicate()[1].decode()
        monoch2_stat = Popen('{} {} -n stat'.format(
                            SOX, temp_monoCH2 ), stdout=None, stderr=PIPE).communicate()[1].decode()

        temp_stat =  float(temp_stat[temp_stat.find('RMS     amplitude')+23:temp_stat.find('RMS     amplitude')+31])
        oops_stat =  float(oops_stat[oops_stat.find('RMS     amplitude')+23:oops_stat.find('RMS     amplitude')+31])
        monoch1_stat =  float(monoch1_stat[monoch1_stat.find('RMS     amplitude')+23:monoch1_stat.find('RMS     amplitude')+31])
        monoch2_stat =  float(monoch2_stat[monoch2_stat.find('RMS     amplitude')+23:monoch2_stat.find('RMS     amplitude')+31])
        
        os.remove(temp_monoCH1)
        os.remove(temp_monoCH2)
        os.remove(temp_out_of_phase)    

        retorno = {}
        retorno['oopsRMS']=oops_stat
        retorno['tempRMS']=temp_stat
        retorno['CH1RMS']=monoch1_stat
        retorno['CH2RMS']=monoch2_stat
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
            print("Silence Detected. Ch1 Lvl:{:.4f} Ch2 lvl: {:.4f}".format(infos['CH1RMS'], infos['CH2RMS']))
            if status != 0:
                save_log.adiciona_linha_log("Silence Detected. Ch1 Lvl:{} Ch2 lvl: {}".format(infos['CH1RMS'], infos['CH2RMS']),(INPUT_BLOCK_TIME*-2))
                telegram_sender.send_message(NAME+' - Silence detected.')
                zabbix_metric.send_status_metric(NAME+" - Silence Detected")
                status = 0
            
        elif verificar_clipped():
            attemps = default_attempts_value
            print("Clipped audio detected. Tunning problem or Input volume too high.")
            if status != 1:
                save_log.adiciona_linha_log("Clipped audio detected. Tunning problem or Input volume too high.",(INPUT_BLOCK_TIME*-1))
                telegram_sender.send_message(NAME+' - Clipped Audio detected.')
                zabbix_metric.send_status_metric(NAME+" - Clipped Audio Detected")
                status = 1
           
        elif oops_results['value'] and fingerprint_results['value']:
            if attemps <= 1:
                print("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                if status != 2:
                    save_log.adiciona_linha_log("Tuning failure detected. Stereo Gap {:.4f} and Fingerprint Similarity {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']), time_offset=(INPUT_BLOCK_TIME*-1*(default_attempts_value+1)))
                    telegram_sender.send_message(NAME+' - Tunning failure Detected')
                    zabbix_metric.send_status_metric(NAME+" - Tunning failure Detected")
                    status= 2
            else:
                print("Appears to be a Tuning failure ...  Stereo Gap: {:.4f} and Fingerprint Similarity: {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                zabbix_metric.send_status_metric(NAME+" - Appears to be a Tuning failure")
                save_log.adiciona_linha_log("Appears to be a Tuning failure ...  Stereo Gap: {:.4f} and Fingerprint Similarity: {:.2f}".format(oops_results['oopsRMS'],fingerprint_results['similarity']))
                attemps -=1
        
        else:
            attemps = default_attempts_value
            print("On Air Ch1 lvl:{:.4f} Ch1 lvl:{:.4f} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']))
            zabbix_metric.send_status_metric(NAME+" - On Air")
            if status != 3:
                save_log.adiciona_linha_log("On Air Ch1 lvl:{} Ch1 lvl:{} stereo:{:.4f} fingerprint:{:.2f}".format(infos['CH1RMS'], infos['CH2RMS'], oops_results['oopsRMS'], fingerprint_results['similarity']), time_offset=(INPUT_BLOCK_TIME*-1))
                telegram_sender.send_message(NAME+' - On Air.')
                status= 3
                
    def carregar_licenca():
        License = license_verify.Lic()
        result = License.verifica(1)
        if result == 0:
            print('Falha ao validar a licença', 'Adquira uma permissão para utilizar o aplicativo')
            sleep(50)
            EXIT()

    def apagar_arquivos_antigos():
        while 1:
            limit_date = int(  (datetime.now()-timedelta(days=LIFETIME)  ).strftime('%Y%m%d'))
            for e in os.scandir(definitive_folder):
                if e.is_dir():
                    if e.name.isdigit():
                        if int(e.name) < limit_date:
                            try:
                                rmtree(os.path.join(definitive_folder, e.name))
                            except Exception as ERR:
                                save_log.adiciona_linha_log(str(ERR))
            sleep(3600)
    
    carregar_licenca()
    
    t = Thread(target=gravar)
    t.start()

    antigos = Thread(target=apagar_arquivos_antigos)
    antigos.start()

    def Main():
        while 1:
            if os.path.exists(temp_file):
                os.remove(temp_file)
            check_output('{} -q -t waveaudio {} -c {} -d {} gain {} trim 0 {}'.format(SOX, AUDIO_DEVICE, CHANNELS, temp_file, INPUT_GAIN, INPUT_BLOCK_TIME) )
            sleep(0.1)
            infos = file_stats(temp_file)
            print("\n")
            verifica_resultados(infos)
    print("Operação iniciada!")
    Main()
except Exception as Err:
    print (Err)
    save_log.adiciona_linha_log (str(Err))
    sleep(50)
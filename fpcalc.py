import subprocess
import audiorecorder
from datetime import date, datetime
import shutil
import os
#its better to create a ramdisk to use because rw disk stressfull

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
        f = open('log.txt', "a")
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, err)

tt = audiorecorder.AudioRec()

printar = 0
while (1):
    tt.listen()
    finger1 = calculate_fingerprints(audiorecorder.configs['FILES']['sample_file'])
    temp_file = os.path.join(audiorecorder.configs['FILES']['temp_folder'],'temp.wav')
    finger2 = calculate_fingerprints(temp_file)
    soma = 0
    for idx, item in enumerate(finger1):
        cont = (bin(int(finger1[idx]) ^ int(finger2[idx])).count("1"))
        soma += cont
    soma /= len(finger1)

    if (tt.amplitude < 0.012):
        print("silence")
        if (printar != 1):
            adiciona_linha_log("Amplitude: {}, Similaridade: {} - Silencio".format(tt.amplitude, soma))
            printar = 1
    elif (soma < 9):
        print("noise")
        if (printar != 2):
            adiciona_linha_log("Amplitude: {}, Similaridade: {} - Fora do Ar".format(tt.amplitude, soma))
            printar = 2
    else:
        print("not noise")
        if (printar != 3):
            adiciona_linha_log("Operação Normal")
            printar = 3  
    if (printar != 3):
        dataFormatada = datetime.now().strftime('%d%m%Y_%H%M%S.wav')
        dest_file = os.path.join(audiorecorder.configs['FILES']['saved_files_folder'], dataFormatada)
        shutil.copyfile(temp_file, dest_file)

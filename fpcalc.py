import subprocess
import audiorecorder
from datetime import date, datetime
#create a ramdisk to use because rw disk stressfull

def calculate_fingerprints(filename):
    fpcalc_out = subprocess.check_output('fpcalc -raw -length 5 %s'
                                    % (filename)).decode()
    returno = fpcalc_out[fpcalc_out.find('=', 12)+1:].split(',')
    returno[len(returno)-1]=returno[len(returno)-1][:9]
    return returno

def adiciona_linha_log(texto):
    dataFormatada = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    print(dataFormatada, texto)
    try:
        f = open('log.txt', "a")
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        print(dataFormatada, err)

tt = audiorecorder.TapTester()

printar = 0
while (1):
    tt.listen()

    finger1 = calculate_fingerprints("pinknoise.wav")
    finger2 = calculate_fingerprints("temp.wav")


    soma = 0
    for idx, item in enumerate(finger1):
        cont = (bin(int(finger1[idx]) ^ int(finger2[idx])).count("1"))
        soma += cont

    soma /= len(finger1)
    print(soma)

    if (tt.amplitude < 0.015):
        print("silence")
        if (printar != 1):
            adiciona_linha_log("silencio")
            printar = 1
    elif (soma < 10):
        print("noise")
        if (printar != 2):
            adiciona_linha_log("fora do ar")
            printar = 2
 
    else:
        print("not noise")
        if (printar != 3):
            adiciona_linha_log("operacao normal")
            printar = 3
 
        





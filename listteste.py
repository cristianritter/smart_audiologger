import subprocess
from threading import Thread
import time

import wave
import struct

class Main(Thread):
    def run(self):
        while 1:
            print ("passou")
            time.sleep(1)

#Main().start()
    max = 0
    contagem = 0
    hf = wave.open('newfile.wav', 'r')
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
    retorno = {}
    retorno['maximo'] = max
    retorno['clipped_count'] = contagem
   
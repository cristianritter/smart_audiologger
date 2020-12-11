#!/usr/bin/python
import pyaudio
import struct
import math
import wave
import time
import io
import parse_config
import os
import audioop

configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')

FORMAT = pyaudio.paInt16 
SHORT_NORMALIZE = (1.0/32768.0)
CHANNELS = int(configs['AUDIO_PARAM']['channels'])
RATE = int(configs['AUDIO_PARAM']['rate'])  
INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])
INPUT_FRAMES_PER_BLOCK = int(RATE*INPUT_BLOCK_TIME)

def get_rms_mono (block, ch1, ch2):
    data = audioop.tomono(block, 2, ch1, ch2)
    rms = audioop.rms(data, 2)
    return rms

def get_if_clipped (block):
    count = len(block)/2
    format = "%dh"%(count)
    shorts = struct.unpack( format, block )
    maximo = (max(shorts))
    soma = 0
    for sample in shorts:
        # sample is a signed short in +/- 32768. 
        # normalize it to 1.0
        if abs(sample) == 32768:
            soma += 1
    retorno = {}
    retorno['maximo'] = maximo
    retorno['clippes'] = soma
    return retorno

class AudioRec(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()

    def find_input_device(self):
        device_index = None            
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            print( "Device %d: %s"%(i,devinfo["name"]) )

            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    device_index = i
                    return device_index

        if device_index == None:
            print( "No preferred input found; using default input device." )

        return device_index

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = INPUT_FRAMES_PER_BLOCK)
        return stream     

    def save_to_file( self, block ):
        temp_file = os.path.join(configs['FILES']['temp_folder'],'temp.wav')
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(block)
        wf.close()
        time.sleep(1)

    def listen(self):
        try:
            block = self.stream.read(INPUT_FRAMES_PER_BLOCK)
        except IOError as e:
            print( "Error recording: %s"%e )
            return
        self.save_to_file(block)
        gain = float(configs['DETECTION_PARAM']['ch1_gain'])
        self.amplitude_l = get_rms_mono(block, gain, 0)/1000
        self.amplitude_r = get_rms_mono(block, 0, 1)/1000
        self.clipped = get_if_clipped(block)

 
if __name__ == "__main__":
    tt = AudioRec()
    tt.listen()
    print("Com o sistema operando normal, ajuste o nivel de audio até retornar aprox 20k")
    print("Nivel atual: {}".format(tt.clipped['maximo']))

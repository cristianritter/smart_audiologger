#!/usr/bin/python
import pyaudio
import struct
import wave
import time
import parse_config
import os
import audioop
from datetime import date, datetime
import subprocess
import shutil
import sox

configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')
saved_files_folder = os.path.join(configs['FILES']['saved_files_folder'])
temp_file = os.path.join(configs['FILES']['temp_folder'],'temp.wav')

FORMAT = pyaudio.paInt16 
CHANNELS = int(configs['AUDIO_PARAM']['channels'])
RATE = int(configs['AUDIO_PARAM']['rate'])  
INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])

class AudioRec(object):
    def __init__(self):
        self.pa = pyaudio.PyAudio()
        self.stream = self.open_mic_stream()

    def open_mic_stream( self ):
        device_index = self.find_input_device()

        stream = self.pa.open(   format = FORMAT,
                                 channels = CHANNELS,
                                 rate = RATE,
                                 input = True,
                                 input_device_index = device_index,
                                 frames_per_buffer = RATE*INPUT_BLOCK_TIME)
        return stream     

    def find_input_device(self):
        device_index = int(configs['AUDIO_PARAM']['device_index'])
        devices_file = os.path.join(parse_config.ROOT_DIR, 'devices.txt')   
        f = open(devices_file, "w")
        for i in range( self.pa.get_device_count() ):     
            devinfo = self.pa.get_device_info_by_index(i)   
            for keyword in ["mic","input"]:
                if keyword in devinfo["name"].lower():
                    print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                    f.write("Found an input: device %d - %s"%(i,devinfo["name"]) )
        f.close()
        print( "Using device %d - %s"%(device_index,self.pa.get_device_info_by_index(device_index) ["name"]))
        return device_index

    def save_block_to_temp_file( self, block ):
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(2)
        wf.setframerate(RATE)
        wf.writeframes(block)
        wf.close()
        time.sleep(0.1)

    def append_block_to_hour_file(self, block):
        mes_ano_dia = datetime.now().strftime('%Y%m%d')
        mes_ano_dia_hora = datetime.now().strftime('%Y%m%d_%H.mp3')
        day_dir = os.path.join(configs['FILES']['temp_folder'],mes_ano_dia)
        definitive_day_dir = os.path.join(configs['FILES']['saved_files_folder'],mes_ano_dia)
        hour_file = os.path.join(day_dir, mes_ano_dia_hora)
        definitive_hour_file = os.path.join(definitive_day_dir, mes_ano_dia_hora)

        try:
            os.mkdir(day_dir)
        except:
            pass
        try:
            shutil.copy(hour_file, hour_file+'.mp3')
            subprocess.check_output('sox %s %s %s'
                                    % (hour_file+'.mp3', temp_file, hour_file))
        except:
            subprocess.check_output('sox %s %s'
                                    % (temp_file, hour_file))
            pass
        os.remove(hour_file+'.mp3')
        comprimento = sox.file_info.stat(hour_file)
        if ( float(comprimento['Length (seconds)']) > 3599 ):
            os.mkdir(definitive_day_dir)
            shutil.copy(hour_file, definitive_hour_file)
            os.remove(hour_file)
        
    def listen(self):
        try:
            block = self.stream.read(RATE*INPUT_BLOCK_TIME)
        except IOError as e:
            print( "Error recording: %s"%e )
            return
        self.channels_rms_lvl = self.get_rms(block)
        self.clipped = self.get_if_clipped(block)
        self.save_block_to_temp_file(block)
        self.append_block_to_hour_file(block)
        
    def get_rms (self, block):
        data_l = audioop.tomono(block, 2, 1, 0)
        chL_rms = audioop.rms(data_l, 2)/1000
        data_r = audioop.tomono(block, 2, 0, 1)
        chR_rms = audioop.rms(data_r, 2)/1000
        retorno = {}
        retorno['L'] = chL_rms
        retorno['R'] = chR_rms
        return retorno

    def get_if_clipped (self, block):
        count = len(block)/2
        format = "%dh"%(count)
        shorts = struct.unpack( format, block )
        maximo = (max(shorts))
        soma = 0
        for sample in shorts:
            if abs(sample) == 32768:
                soma += 1
        retorno = {}
        retorno['maximo'] = maximo
        retorno['clipped_count'] = soma
        return retorno

if __name__ == "__main__":
    tt = AudioRec()
    tt.listen()
    print("Com o sistema operando normal, ajuste o nivel de audio até retornar aprox 20k")
    print("Nivel atual: {}".format(tt.clipped['maximo']))

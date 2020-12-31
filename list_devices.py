import parse_config
import os
import pyaudio

configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')
pa = pyaudio.PyAudio()

def find_input_device():
    devices_file = os.path.join(parse_config.ROOT_DIR, 'devices.txt')   
    f = open(devices_file, "w")
    for i in range( pa.get_device_count() ):     
        devinfo = pa.get_device_info_by_index(i)   
        for keyword in ["mic","input"]:
            if keyword in devinfo["name"].lower():
                print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
                f.write("Found an input: device %d - %s\n"%(i,devinfo["name"]) )
    f.close()

find_input_device()
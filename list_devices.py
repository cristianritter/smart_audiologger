import os
import pyaudio
import time

try: 
    pa = pyaudio.PyAudio()

    def find_input_device():
        devices_file = 'devices.txt'   
        f = open(devices_file, "w")
        for i in range( pa.get_device_count() ):     
            devinfo = pa.get_device_info_by_index(i)   
            print( "Found an input: device %d - %s"%(i,devinfo["name"]) )
            f.write("Found an input: device %d - %s\n"%(i,devinfo["name"]) )
        f.close()

    find_input_device()

except Exception as ERR:
    print(ERR)
    time.sleep(10)


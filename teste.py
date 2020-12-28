import subprocess
import logging
import os
#logging.getLogger('sox').setLevel(logging.ERROR)
FNULL = open(os.devnull, 'w')
subprocess.Popen('sox -t waveaudio 0 -d %s trim 0 %d'
                                        % ("teste.mp3", 10), stdout=FNULL)
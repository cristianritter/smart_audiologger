import subprocess
import logging
import os
logging.getLogger('sox').setLevel(logging.ERROR)
FNULL = open(os.devnull, 'w')
subprocess.check_output('sox -q -t waveaudio 0 -d %s trim 0 %d '
                                        % ("teste.mp3", 3))
import soundfile as sf
import pyloudnorm as pyln

pyln.normalize.warnings.simplefilter('error', UserWarning)

if __name__ == "__main__":
    data, rate = sf.read("R:/temp.wav") # load audio

    # peak normalize audio to -1 dB
    peak_normalized_audio = pyln.normalize.peak(data, -1.0)

    # measure the loudness first 
    meter = pyln.Meter(rate) # create BS.1770 meter
    loudness2 = meter.integrated_loudness(data)
 
    # loudness normalize audio to -12 dB LUFS
    loudness_normalized_audio = pyln.normalize.loudness(data, loudness2, -12.0)
    
    

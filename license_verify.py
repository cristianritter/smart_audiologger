import subprocess
import hashlib
import os
from datetime import datetime, timedelta
import sys
import urllib.request


ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
license_file = os.path.join(ROOT_DIR, 'license.lic' )
current_machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
APPS_NAMES = ['SmartLogger Player', 'SmartLogger Gravador']
        
with urllib.request.urlopen('https://raw.githubusercontent.com/cristianritter/licenses/main/Audiologger') as f:
    html = f.read().decode('utf-8')

online_licence_list = html.split("\n")
#print (licence_list)

def adiciona_linha_log(texto, time_offset=0):
    dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
    try:
        logfilename = "log.txt"
        f = open(logfilename, 'a')
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except Exception as err:
        pass

license_content = []

class Lic:
    def __init__(self, app):
       self.app = app
    
    def verifica(self):
        try:
            f = open(license_file, "r")
            global license_content
            license_content = f.readlines()
            f.close()
            for idx, item in enumerate(license_content):
                if '\n' in item:
                    license_content[idx] = license_content[idx].split('\n')[0]
        except Exception as Err:
            print(Err)

            adiciona_linha_log(str(Err))

        root_b = ROOT_DIR.encode('UTF-8')
        root_dig = hashlib.sha224(root_b).hexdigest()
        maq_b = current_machine_id.encode('UTF-8')
        maq_dig = hashlib.sha224(maq_b).hexdigest()
        app_b = self.app.encode('UTF-8')
        app_dig = hashlib.sha224(app_b).hexdigest()
        codig_de_maquina_b = "{}{}".format(maq_dig, root_dig).encode('UTF-8')
        codigo_de_maquina_dig = hashlib.sha224(codig_de_maquina_b).hexdigest()
        uniao_b = "{}{}".format(codigo_de_maquina_dig, app_dig).encode('UTF-8')
        uniao_dig = hashlib.sha224(uniao_b).hexdigest()
        
        if uniao_dig in license_content:
            print('Licença verificada')
            return 0

        elif uniao_dig in online_licence_list:
            print('Licença verificada')
            return 0
     
        else:
            print("Licença inválida")
            print("Informe este código de maquina: {}".format(codigo_de_maquina_dig))
            adiciona_linha_log("Erro ao verificar a licença do software")
            adiciona_linha_log("Informe este código de maquina: {}".format(codigo_de_maquina_dig))
            sys.exit()
           
def main():
    a = Lic(APPS_NAMES[0])
    a.verifica()

if __name__ == '__main__':
    main()


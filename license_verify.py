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
        
def adiciona_linha_log(texto, time_offset=0):
    dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
    try:
        logfilename = "log.txt"
        f = open(logfilename, 'a')
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except:
        pass

html_text = ''

try:
    print("Verificando licença online ...")
    with urllib.request.urlopen('https://raw.githubusercontent.com/cristianritter/licenses/main/Audiologger') as f:
        html_text = f.read().decode('utf-8')
except:
    print("Não foi possível verificar a licença online, por favor verifique sua conexão com a internet.")

online_licence_list = html_text.split("\n")


file_license_content = []

class Lic:
    def __init__(self, app_name):
       self.app_name = app_name
    
    def verifica(self):
        try:
            if os.path.exists(license_file):
                f = open(license_file, "r")
                global license_content
                license_content = f.readlines()
                f.close()
                for idx, item in enumerate(file_license_content):
                    if '\n' in item:
                        file_license_content[idx] = file_license_content[idx].split('\n')[0]
        except Exception as Err:
            adiciona_linha_log(str(Err))

        root_b = ROOT_DIR.encode('UTF-8')
        root_dig = hashlib.sha224(root_b).hexdigest()
        maq_b = current_machine_id.encode('UTF-8')
        maq_dig = hashlib.sha224(maq_b).hexdigest()
        app_b = self.app_name.encode('UTF-8')
        app_dig = hashlib.sha224(app_b).hexdigest()
        codig_de_maquina_b = "{}{}".format(maq_dig, root_dig).encode('UTF-8')
        codigo_de_maquina_dig = hashlib.sha224(codig_de_maquina_b).hexdigest()
        uniao_b = "{}{}".format(codigo_de_maquina_dig, app_dig).encode('UTF-8')
        uniao_dig = hashlib.sha224(uniao_b).hexdigest()
        
        if uniao_dig in file_license_content:
            print('Licença local validada.')
            return 'local'

        elif uniao_dig in online_licence_list:
            print('Licença online validada.')
            return 'online'
     
        else:
            print("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            print("Consulte mais informações no arquivo de log")
            adiciona_linha_log("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            adiciona_linha_log("Email: cristianritter@gmail.com")
            adiciona_linha_log("Informe este código de maquina: {}".format(codigo_de_maquina_dig))
            return 0
           
def main():
    a = Lic(APPS_NAMES[0])
    a.verifica()

if __name__ == '__main__':
    main()


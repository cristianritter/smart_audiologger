import subprocess
import hashlib
import os
from datetime import datetime, timedelta
import sys
import urllib.request
import PySimpleGUI as sg

        
def adiciona_linha_log(texto, time_offset=0):
    dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
    try:
        logfilename = "log.txt"
        f = open(logfilename, 'a')
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except:
        pass


class Lic:
    def __init__(self):
        self.ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
        self.license_file = os.path.join(self.ROOT_DIR, 'license.lic' )
        self.current_machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
        self.APPS_NAMES = ['SmartLogger Player', 'SmartLogger Gravador']

    def find_online(self):
        #html_text = ''
        try:
            print("Verificando licença online ...")
            with urllib.request.urlopen('https://raw.githubusercontent.com/cristianritter/licenses/main/Audiologger') as f:
                html_text = f.read().decode('utf-8')
            online_licence_list = html_text.split("\n")
            return online_licence_list
        except:
            return 0
    
    def find_offline(self):
        try:
            offline_licenses = []
            if os.path.exists(self.license_file):
                f = open(self.license_file, "r")
                file_content = f.readlines()
                f.close()
                for item in file_content:
                    offline_licenses.append(item[:56])
            return offline_licenses
        except Exception as Err:
            adiciona_linha_log(str(Err))
            return 0

    def gera_dev_unique_cod(self):
        root_cod_b = self.ROOT_DIR.encode('UTF-8')
        root_cod_digest = hashlib.sha224(root_cod_b).hexdigest()
        bios_cod_b = self.current_machine_id.encode('UTF-8')
        bios_cod_digest = hashlib.sha224(bios_cod_b).hexdigest()
        dev_uniq_b = "{}{}".format(bios_cod_digest, root_cod_digest).encode('UTF-8')
        dev_uniq_digest = hashlib.sha224(dev_uniq_b).hexdigest()
        return dev_uniq_digest

    def gera_final_app_cod(self, app_idx):
        app_name_b = self.APPS_NAMES[app_idx].encode('UTF-8')
        app_name_digest = hashlib.sha224(app_name_b).hexdigest()
        final_b = "{}{}".format(self.gera_dev_unique_cod(), app_name_digest).encode('UTF-8')
        final_digest = hashlib.sha224(final_b).hexdigest()
        return final_digest

    def verifica(self, app_idx):
        print("Verificando licença de uso para:", self.APPS_NAMES[app_idx])
        final_cod = self.gera_final_app_cod(app_idx)

        if final_cod in self.find_offline():
            print('Licença local validada.')
            return 'local'

        elif final_cod in self.find_online():
            print('Licença Online validada.')
            return 'online'
     
        else:
            print("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            print("Consulte mais informações no arquivo de log")
            adiciona_linha_log("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            adiciona_linha_log("Email: cristianritter@gmail.com")
            adiciona_linha_log("Informe este código de maquina: {}".format(self.gera_dev_unique_cod()))
            return 0
           
def main():
    a = Lic()
    b = a.verifica(0)
    if b == 0:
        sg.popup('Falha ao validar a licença', 'Adquira uma permissão para utilizar o aplicativo')


if __name__ == '__main__':
    main()


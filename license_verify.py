from subprocess import check_output
from hashlib import sha224
import os
from datetime import datetime, timedelta
import urllib.request
import PySimpleGUI as sg
from sys import exit as EXIT
ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

class ativacao:
    # Setup GUI window for output of media
    def __init__(self, codigo, size, scale=1.0, theme='DarkBlue'):
        self.theme = theme  # This can be changed, but I'd stick with a dark theme
        self.default_bg_color = sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']
        self.window_size = size  # The size of the GUI window
        self.codigo = codigo
        self.window = self.create_window()
            
    def create_window(self):
        """ Create GUI instance """
        sg.change_look_and_feel(self.theme)
        main_layout = [
            [sg.Text('SmartAudiLogger', font='Fixedsys 45 ', text_color='White', tooltip="By SmartLogger®")],
            [sg.Text('Não encontramos uma licença válida.', font='Fixedsys 12 bold', text_color='gray')],
            [sg.Input(self.codigo, size=(30,4), readonly=True, font='Courier 15', text_color='black', background_color='black' )],
            [sg.Text("Solicite o código de ativação enviando o codigo acima para o desenvolvedor.", font='Fixedsys 12 bold', text_color='gray')],
            [sg.Input(("Cole aqui o código de ativação."), size=(30,4), font='Courier 15', key='ATIVAR', enable_events=True)],  
        ] 
        window = sg.Window('SmartPlayer', main_layout, element_justification='center', finalize=True)
        return window

        
def adiciona_linha_log(texto, time_offset=0):
    dataFormatada = (datetime.now()+timedelta(seconds=time_offset)).strftime('%d/%m/%Y %H:%M:%S')
    try:
        logfilename = os.path.join(ROOT_DIR, "log.txt")
        f = open(logfilename, 'a')
        f.write(dataFormatada + " " + texto +"\n")
        f.close()
    except:
        pass

def adiciona_licenca(texto):
    try:
        logfilename = os.path.join(ROOT_DIR, "license.lic")
        f = open(logfilename, 'a')
        f.write(texto +"\n")
        f.close()
    except:
        pass

class Lic:
    def __init__(self):
        self.ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
        self.license_file = os.path.join(self.ROOT_DIR, 'license.lic' )
        self.current_machine_id = check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
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
        root_cod_digest = sha224(root_cod_b).hexdigest()
        bios_cod_b = self.current_machine_id.encode('UTF-8')
        bios_cod_digest = sha224(bios_cod_b).hexdigest()
        dev_uniq_b = "{}{}".format(bios_cod_digest, root_cod_digest).encode('UTF-8')
        dev_uniq_digest = sha224(dev_uniq_b).hexdigest()
        return dev_uniq_digest

    def gera_final_app_cod(self, app_idx):
        app_name_b = self.APPS_NAMES[app_idx].encode('UTF-8')
        app_name_digest = sha224(app_name_b).hexdigest()
        final_b = "{}{}".format(self.gera_dev_unique_cod(), app_name_digest).encode('UTF-8')
        final_digest = sha224(final_b).hexdigest()
        return final_digest

    def verifica(self, app_idx):
        print("Verificando licença de uso para:", self.APPS_NAMES[app_idx])
        final_cod = self.gera_final_app_cod(app_idx)

        if final_cod in self.find_offline():
            print('Licença local validada.')
            return 'Arquivo Local'

        elif final_cod in self.find_online():
            print('Licença Online validada.')
            return 'Online'
     
        else:
            print("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            print("Consulte mais informações no arquivo de log")
            adiciona_linha_log("Não foi encontrada uma licença válida. Por favor contate o desenvolvedor.")
            adiciona_linha_log("Email: cristianritter@gmail.com")
            adiciona_linha_log("Informe este código de maquina: {}".format(self.gera_dev_unique_cod()))
            janela_de_ativacao(app_idx, self.gera_dev_unique_cod(), final_cod)
            return 0
           
def janela_de_ativacao(id_software, codigo_de_maquina, final_cod):
    lg = ativacao(codigo_de_maquina, size=(500, 500), scale=0.5)
    lg.window.force_focus()
    while 1:
        event, values = lg.window.read(timeout=100)
        #print(event)
        if event == None:
            return
        if event == 'ATIVAR':
            print(values['ATIVAR'])
            if values['ATIVAR'] == final_cod:
                sg.popup("Ativado. Reinicie o software.")
                adiciona_licenca(final_cod)
                EXIT()
                
    lg.window.Close()

def main():
    a = Lic()
    b = a.verifica(0)
    if b == 0:
        sg.popup('Falha ao validar a licença', 'Adquira uma permissão para utilizar o aplicativo')


if __name__ == '__main__':
    main()



import subprocess
import hashlib
import PySimpleGUI as sg
import os
current_machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
print(current_machine_id)

lista = ['SmartLogger Player', 'SmartLogger Gravador']

class license_layout:
    # Setup GUI window for output of media
    def __init__(self, size, scale=1.0, theme='DarkBlue'):
        self.theme = theme  # This can be changed, but I'd stick with a dark theme
        self.default_bg_color = sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']
        self.window_size = size  # The size of the GUI window
        self.player_size = [x*scale for x in size]  # The size of the media output window
        self.window = self.create_window()
        #self.check_platform()  # Window handler adj for Linux/Windows/MacOS

    def create_window(self):
        """ Create GUI instance """
        sg.change_look_and_feel(self.theme)
        global lista
        main_layout = [
            [sg.Text("Selecione o produto:")],
            [sg.Combo(lista, readonly=True, key='APP')],
            [sg.Text("Identificador de maquina:")],
            [sg.InputText(key='INPUT')],
            [sg.Button('Generate..')],
            [sg.Multiline('Preencha o campo Identificador de maquina e clique em Gerar', disabled=True, key='RESULT')],
         ] 
        window = sg.Window('Audiologger NSC', main_layout, element_justification='center', finalize=True)
        
        # Expand the time element so that the row elements are positioned correctly
        #window['CONFIG'].expand(expand_x=True)
        return window

def main():
    lg = license_layout(size=(500, 500), scale=0.5)
    lg.window.force_focus()
    while 1:
        event, values = lg.window.read(timeout=100)
        if event == None:
            exit()
            break
        if event == 'Generate..':
            #if len(values['INPUT']) != 10:
            #    lg.window['RESULT'].update('Identificador de maquina inválido')
            #elif len(values['APP']) == 0:
            #    lg.window['RESULT'].update('Selecione um aplicativo')
            #else:
            if 1:
                app_b = values['APP'].encode('UTF-8')
                app_dig = hashlib.sha224(app_b).hexdigest()
                maq_dig = values['INPUT']               
                uniao_b = "{}{}".format(maq_dig, app_dig).encode('UTF-8')
                uniao_dig = hashlib.sha224(uniao_b).hexdigest()
                lg.window['RESULT'].update(uniao_dig)
                f = open('license.lic', 'w')
                f.write(uniao_dig)
                f.close()
    lg.window.Close()

main()

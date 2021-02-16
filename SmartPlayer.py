"""
    SmartLogger
    Author: Cristian Ritter
    Modified: 2021
"""

import PySimpleGUI as sg
from sys import platform as PLATFORM
from sys import exit as EXIT
from datetime import datetime, timedelta
import os
import webbrowser
from time import sleep
import parse_config
import license_verify
import os
from subprocess import check_output
from threading import Thread

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root

print("Carregando DLLS...")
try:
    #os.add_dll_directory(os.getcwd())
    try:
        VLC_DIR = os.path.join(ROOT_DIR, 'VLC\\')
        SOX_DIR = os.path.join(ROOT_DIR, 'sox-14-4-1\\')
        SOX = os.path.join(SOX_DIR, 'sox')
        
        os.add_dll_directory(r'{}'.format(VLC_DIR))
        os.add_dll_directory(r'{}'.format(SOX_DIR))
        #os.add_dll_directory(r'C:\Program Files (x86)\VideoLAN\VLC')
    except Exception as Err:
        sg.popup('DLL ERROR - '+str(Err))
        EXIT()
        
    print("Importando VLC...")
    import vlc

    ASSETS_PATH = os.path.join(ROOT_DIR, 'Assets/') 
    BUTTON_DICT = {img[:-4].upper(): ASSETS_PATH + img for img in os.listdir(ASSETS_PATH)}
    DEFAULT_IMG = ASSETS_PATH + 'background3.png'
    ICON = ASSETS_PATH + 'player.ico'

    print("Carregando configurações...")
    def select_config_file(filename):
        configuration = parse_config.ConfPacket()
        global configs
        configs = configuration.load_config('FILES, AUDIO_PARAM', filename)
        global temp_folder
        temp_folder = configs['FILES']['temp_folder']
        global log_folder
        log_folder = configs['FILES']['log_folder']
        global definitive_folder
        definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])
        global INPUT_BLOCK_TIME
        INPUT_BLOCK_TIME = int(configs['AUDIO_PARAM']['input_block_time'])
        global NAME
        NAME = (configs['FILES']['name'])
        

    l = []

    class config_select:
        # Setup GUI window for output of media
        def __init__(self, license_result, size, scale=1.0, theme='DarkBlue'):
            self.license_result = license_result
            self.theme = theme  # This can be changed, but I'd stick with a dark theme
            self.default_bg_color = sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']
            self.window_size = size  # The size of the GUI window
            self.window = self.create_window()
            
        def create_window(self):
            """ Create GUI instance """
            sg.change_look_and_feel(self.theme)
            configs_list = []
            config_files = os.listdir(ROOT_DIR)
            for item in config_files:
                if item[-4:] == '.ini':
                    configs_list.append(item)
            main_layout = [
                [sg.Text('SmartPlayer', font='Fixedsys 45 ', text_color='White', tooltip="By SmartLogger®")],
                [sg.Text('Configuração:', font='Fixedsys 12 bold', text_color='gray')],
                [sg.Listbox((configs_list), size=(30,4), key = 'CONFIG', font='Courier 15',tooltip="Selecione o arquivo de configuração correto para acessar as gravações.")],
                [sg.Image(os.path.join(ASSETS_PATH, 'wave.png'))],
                [sg.Text("Tipo de licença encontrada: " + self.license_result, font='Fixedsys 12 bold', text_color='gray')]
            ] 
            window = sg.Window('SmartPlayer', main_layout, element_justification='center', icon=ICON, finalize=True)
            
            # Expand the time element so that the row elements are positioned correctly
            window['CONFIG'].expand(expand_y=True)
            return window

    class MediaPlayer:
        failtimes_list = []
        returntimes_list = []
        jump_list = []
        time_old = 0
        segundos_total = 0
        values = dict()
        def __init__(self, size, scale=1.0, theme='DarkBlue'):
            """ Media player constructor """
            self.paused = False
            # Setup media player
            self.instance = vlc.Instance()
            self.list_player = self.instance.media_list_player_new()
            self.media_list = self.instance.media_list_new([])
            self.list_player.set_media_list(self.media_list)
            self.player = self.list_player.get_media_player()

            self.track_cnt = 0  # Count of tracks loaded into `media_list`
            self.track_num = 0  # Index of the track currently playing

            # Setup GUI window for output of media
            self.theme = theme  # This can be changed, but I'd stick with a dark theme
            self.default_bg_color = sg.LOOK_AND_FEEL_TABLE[self.theme]['BACKGROUND']
            self.window_size = size  # The size of the GUI window
            self.player_size = [x*scale for x in size]  # The size of the media output window
            self.window = self.create_window()
            self.check_platform()  # Window handler adj for Linux/Windows/MacOS

        def button(self, key, image, tooltip, **kwargs):
            """ Create media player button """
            return sg.Button(image_filename=image, border_width=0, pad=(0, 0), key=key,
                            button_color=('white', self.default_bg_color), tooltip=tooltip)

        def create_window(self):
            """ Create GUI instance """
            sg.change_look_and_feel(self.theme)
            
            # Column layout for media player button controls
            buttons_group = [[sg.In(key='CALENDAR', enable_events=True, visible=False), sg.CalendarButton('', image_filename=BUTTON_DICT['CALENDAR'], pad=(0,0),  
                    button_color=('white', self.default_bg_color), border_width=0, key='CALENDAR', format=('%Y%m%d')),
                    self.button('REWIND', BUTTON_DICT['START'], "Navegar entre os eventos marcados."),
                    self.button('REWIND_10', BUTTON_DICT['REWIND_10'], "Recuar 10s"),
                    self.button('REWIND_1', BUTTON_DICT['REWIND_1'], "Recuar 1s"),
                    self.button('PLAY', BUTTON_DICT['PLAY_OFF'], "Pausar ou Resumir a execução."),
                    self.button('FORWARD_1', BUTTON_DICT['FORWARD_1'], "Avançar 1s"),
                    self.button('FORWARD_10', BUTTON_DICT['FORWARD_10'], "Avançar 10s"),
                    self.button('FORWARD', BUTTON_DICT['END'], "Navegar entre os eventos marcados."),
                    ]]

            
            # Column layout for media info and instructions
            info_column = [[sg.Text('Loading...',
                            size=(45, 3), font=(sg.DEFAULT_FONT, 8), pad=(0, 5), key='INFO')]]

            direita_column = [   
                [sg.Text('dd/mm/aaaa',
                        font=(sg.DEFAULT_FONT, 8, 'bold'), key='NOW'), 
                sg.Text('Horários disponíveis: ', 
                        font=(sg.DEFAULT_FONT, 8, 'bold'))], 
                [sg.Listbox(l, size=(40, 24), enable_events=True, key='LISTA', tooltip="Selecione uma data para visualizar as gravações disponíveis.")],
                [sg.Text('LOG de ocorrências disponível AQUI', key = 'LOG', 
                        enable_events=True, font=(sg.DEFAULT_FONT, 9, 'underline'), tooltip="Clique para abrir.")],
                [sg.Text('Copyright ® 2021', key = 'COPYRIGHT', 
                        enable_events=True, font=(sg.DEFAULT_FONT, 8))],
                
            ]
            
            # ------ Menu Definition ------ #      
            menu_def = [['File', ['Open config', 'Exit']],      
                        ['Help', 'About...'], ]      

            # Main GUI layout

            coluna_export = [[sg.Text('- Exportação -', justification='center', size=(25,1))],
                            [sg.Button("Mark In", size=[10,1], button_color=['white','black'], border_width='5', key='MARK_IN', tooltip="Marque a posição de inicio do trecho desejado."),
                            sg.Button("Mark Out", size=[10,1], button_color=['black','white'], border_width='5', key='MARK_OUT', tooltip="Marque a posição de fim do trecho desejado.")], 
                            [sg.In('00:00', size=[11,1], justification='center', key='IN_TEXT', readonly='True', text_color='black', tooltip="Você não pode editar manualmente esse campo."),
                            sg.In('00:10', size=[11,1], justification='center', key='OUT_TEXT', readonly='True', text_color='black', tooltip="Você não pode editar manualmente esse campo.")],
                            [sg.FolderBrowse("Export", key='EXPORT', size=[22,1], button_color=['green','white'], pad=[5,5], enable_events=True, disabled=True, tooltip="Use para exportar um trecho do audio.")],
                            ]

            coluna_esquerda = [
                [sg.Menu(menu_def, tearoff=False)],
                [sg.Image(filename=DEFAULT_IMG, pad=(0, 5), size=self.player_size, key='VID_OUT')],

                [sg.Text('00:00', key='TIME_ELAPSED'),

                sg.Slider(range=(0, 1), enable_events=True, resolution=0.0001, disable_number_display=True,
                        background_color='#83D8F5', orientation='h', key='TIME', tooltip='Tente utilizar a rolagem do mouse para avançar ou retroceder.'),

                # Elements for tracking media length and track counts
                sg.Text('00:00', key='TIME_TOTAL')],
              
                [sg.Graph(canvas_size=(self.player_size[0], 20), graph_bottom_left=(-57, 0), graph_top_right=(840, 20), background_color=self.default_bg_color, enable_events=True, key='GRAPH')],
                
                # Button and media information layout (created above)
                [sg.Column(buttons_group), sg.Column(info_column), sg.Column(coluna_export,background_color='black', element_justification='center') ]
            ]

            principal = [
                [sg.Column(coluna_esquerda), sg.Column(direita_column)]
            ]


            # Create a PySimpleGUI window from the specified parameters
            window = sg.Window('SmartLogger', principal, element_justification='center', icon=ICON, finalize=True, return_keyboard_events=True)

            # Expand the time element so that the row elements are positioned correctly
            window['TIME'].expand(expand_x=True)
            return window

        def check_platform(self):
            """ Platform specific adjustments for window handler """
            if PLATFORM.startswith('linux'):
                self.player.set_xwindow(self.window['VID_OUT'].Widget.winfo_id())
            else:
                self.player.set_hwnd(self.window['VID_OUT'].Widget.winfo_id())

        def add_media(self, track=None):
            """ Add new track to list player with meta data if available """
            
            self.media_list = self.instance.media_list_new()
            self.list_player.set_media_list(self.media_list)
            self.player = self.list_player.get_media_player()

            if track is None:
                return  # User did not provide any information
        
            media = self.instance.media_new(track)
            media.set_meta(0, track.replace('\\', '/').split('/').pop())  # filename
            media.set_meta(1, 'Local Media')  # Default author value for local media

            media.set_meta(10, track)  # Url if online media else use filename

            self.media_list.add_media(media)
            self.track_cnt = self.media_list.count()

                # Update infobar with added track
            self.window['INFO'].update(f'Loaded: {media.get_meta(0)}')
            self.window.read(1)  # refresh the screen

                # Update the track counter
            if self.track_cnt == 1:
                self.track_num = 1
                self.list_player.play()

        def get_time_elapsed(self):
            return "{:02d}:{:02d}".format(*divmod(self.player.get_time() // 1000, 60))

        def get_current_audio_filepath(self, values):
            folder = values['CALENDAR']+'\\'
            sourcepath = os.path.join(definitive_folder, folder)
            dados = values['LISTA'][0]
            filename = os.path.join(sourcepath, dados)
            return filename           

        def get_meta(self, meta_type):
            """ Retrieve saved meta data from tracks in media list """
            media = self.player.get_media()
            return media.get_meta(meta_type)

        def get_track_info(self):
            sleep(0.1)
            """ Show author, title, and elasped time if video is loaded and playing """
            time_elapsed = "{:02d}:{:02d}".format(*divmod(self.player.get_time() // 1000, 60))
            time_total = "{:02d}:{:02d}".format(*divmod(self.player.get_length() // 1000, 60))
            if self.media_list.count() == 0:
                self.window['INFO'].update('Selecione uma data no CALENDARIO.')
            else:
                message = "{}\n{}".format(self.get_meta(1).upper(), self.get_meta(0))
                self.window['INFO'].update(message)
                self.window['TIME_ELAPSED'].update(time_elapsed)
                windowtime = self.player.get_position()
                self.window['TIME'].update(windowtime)
                self.window['TIME_TOTAL'].update(time_total)
                self.time_old =  windowtime
     
        def play(self):
            """ Called when the play button is pressed """
            if self.media_list.count() == 0:
                return
            if self.paused:
                self.list_player.pause()
                self.paused = False
                self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])     
            elif not self.paused:
                self.list_player.pause()
                self.paused = True
                self.window['PLAY'].update(image_filename=BUTTON_DICT['PAUSE_ON'])
            
        def stop(self):
            """ Called when the stop button is pressed """
            self.player.stop()
            self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
            self.paused = False

        def pause(self):
            """ Called when the pause button is pressed """
            self.window['PAUSE'].update(
                image_filename=BUTTON_DICT['PAUSE_ON'] if self.player.is_playing() else BUTTON_DICT['PAUSE_OFF'])
            self.window['PLAY'].update(
                image_filename=BUTTON_DICT['PLAY_OFF'] if self.player.is_playing() else BUTTON_DICT['PLAY_ON'])
            self.player.pause()

        def jump_next_fail(self):
            if len(self.jump_list) == 0:
                return
            destino = 0
            for item in self.jump_list:
                if (self.player.get_time() / 1000) < (item - (INPUT_BLOCK_TIME+5)):
                    destino = item - (INPUT_BLOCK_TIME+5)
                    break  
            tamanho = self.player.get_length() // 1000
            position = 0
            if tamanho != 0:
                position = destino / tamanho
            self.set_position(position)

        def jump_previous_fail(self):
            """ Called when the skip previous button is pressed """
            if len(self.jump_list) == 0:
                return
            destino = 0
            for item in reversed(self.jump_list):
                if ((self.player.get_time() / 1000)-1) > (item - (INPUT_BLOCK_TIME+5)):
                    destino = item - (INPUT_BLOCK_TIME+5)
                    break
            tamanho = self.player.get_length() // 1000
            position = 0
            if tamanho != 0:
                position = destino / tamanho
            self.set_position(position)
                
        def reset_pause_play(self):
            """ Reset pause play buttons after skipping tracks """
            self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])

        def load_single_track(self, track):
            """ Open a popup to request url or filepath for single track """
            if track is None:
                return
            else:
                self.window['INFO'].update('Loading media...')
                self.window['IN_TEXT'].update('00:00')
                self.window['OUT_TEXT'].update('00:10')
                self.window.read(1)
                self.add_media(track)
                self.play()
        
            # Increment the track counter
            self.track_cnt = self.media_list.count()
            self.track_num = 1
            while self.player.get_length() <= 0:
                sleep(0.1)
            
            self.segundos_total = self.player.get_length() / 1000
        
        def redraw_fail_positions(self, values):
            self.failtimes_list.clear()
            self.returntimes_list.clear()
            self.jump_list.clear()  

            lognm = "log_"+values['CALENDAR'][0:6]+".txt"
            logfile = os.path.join(log_folder, lognm)
            
            if not os.path.exists(logfile):
                f = open(logfile, 'a')
                f.write("\n")
                f.close()
            f = open(logfile, "r")

            dados = values['LISTA'][0]
            logtext = (dados[6:8] + '/' + dados[4:6] + '/' + dados[:4] + ' ' + dados[9:11])
            self.jump_list.append(0)
            for x in f: #le linhas
                if logtext in x:
                    pos = int(x[14:16])*60+int(x[17:19]) #posicao segundos
                    self.jump_list.append(pos)
                    if 'On Air' in x:
                        self.returntimes_list.append(pos)
                    else:
                        self.failtimes_list.append(pos) #seconds
                    
            segundos_total = self.player.get_length() / 1000
            graph = self.window['GRAPH']
            graph.DrawRectangle((-0, 0), (self.player_size[0]-180,20), fill_color='black')
            window_size = self.player_size[0]-180
            for segundos_atual in self.failtimes_list:
                graph.DrawLine (  ((window_size/segundos_total)*segundos_atual, 0), ((window_size/segundos_total)*segundos_atual, 20), color='red', width = 4)
            for segundos_atual in self.returntimes_list:
                graph.DrawLine (  ((window_size/segundos_total)*segundos_atual, 0), ((window_size/segundos_total)*segundos_atual, 20), color='white', width = 3)
            graph.update()
            
        def is_in_out_ok(self):
            begin_seconds = int(self.values['IN_TEXT'][0:2])*60 + int(self.values['IN_TEXT'][3:5]) 
            end_seconds = int(self.values['OUT_TEXT'][0:2])*60 + int(self.values['OUT_TEXT'][3:5])
            segundos_total = self.player.get_length() / 1000
            if begin_seconds > end_seconds or end_seconds > segundos_total:            
                self.window['EXPORT'].Update(disabled=True)
            else:
                self.window['EXPORT'].Update(disabled=False)

        def set_position(self, arg):
            self.player.audio_set_mute(True)
            sleep(0.05)
            self.player.set_position(arg)
            sleep(0.05)
            self.player.audio_set_mute(False)
            self.get_track_info()

    def select_config_window(license_result, mp):
        mp.stop()
        l.clear()
        mp.window['LISTA'].update(l)
        mp.window.Hide()
      
        lg = config_select(license_result, size=(500, 500), scale=0.5)
        lg.window.force_focus()
        while 1:
            event, values = lg.window.read(timeout=100)
            if event == None:
                EXIT()
            if(len(values['CONFIG']) > 0):
                if os.path.exists(os.path.join(ROOT_DIR, values['CONFIG'][0])):
                    select_config_file(values['CONFIG'][0])
                    break
        lg.window.Close()

        calendar_event(mp)
        mp.window.set_title('SmartPlayer - {}'.format(NAME))
        mp.window.UnHide()

    License = license_verify.Lic()
    license_result = License.verifica(0)
    if license_result == 0:
        sg.popup('Falha ao validar a licença', 'Adquira uma permissão para utilizar o aplicativo')
        EXIT()

    def atualiza(mp):
        while 1:
            if not 'CALENDAR' in mp.values:
                mp.window['CALENDAR'].update(datetime.now().strftime('%Y%m%d'))
                mp.values['CALENDAR'] = datetime.now().strftime('%Y%m%d')
                calendar_event(mp)

            if mp.segundos_total != mp.player.get_length() / 1000 and mp.segundos_total > 0:
                        mp.redraw_fail_positions(mp.values)
                        mp.segundos_total = mp.player.get_length() / 1000
            if mp.segundos_total > 0:
                mp.is_in_out_ok()
            mp.get_track_info() 
            sleep(1)

    def calendar_event(mp):
        if not 'CALENDAR' in mp.values:
            return
        mp.window['NOW'].update(mp.values['CALENDAR'][6:8] + '/' + mp.values['CALENDAR'][3:5] + '/' + mp.values['CALENDAR'][:4])
        mp.stop()
        mp.add_media()
        folder = mp.values['CALENDAR']+'\\'
        sourcepath = os.path.join(definitive_folder, folder)
        l.clear()
        if not os.path.exists(sourcepath):
            mp.window['LISTA'].update(l)
            return
        for e in os.listdir(sourcepath):
            if 'partial' in e:
                continue
            else:
                l.append(e)
        mp.window['LISTA'].update(l)
    
    def main():
        mp = MediaPlayer(size=(1920, 720), scale=0.5)
        select_config_window(license_result, mp)
        T = Thread(target=atualiza, args=(mp,), daemon=True)
        T.start()
        while True:
            if not T.is_alive():
                T = Thread(target=atualiza, args=(mp,), daemon=True)
                T.start()
                print("Reiniciando...")
            event, mp.values = mp.window.read(timeout=500)
            if event == None or event == 'Exit':
                EXIT()

            if event == "Open config":
                select_config_window(license_result, mp)
            
            if event == 'MouseWheel:Up':
                mp.set_position(mp.values['TIME']-(0.0003/(mp.player.get_length()/3600000)))
                
            if event == 'MouseWheel:Down':
                mp.set_position(mp.values['TIME']+(0.0003/(mp.player.get_length()/3600000)))
                
                
            if event == 'About...':
                sg.Popup("Feito por:", "Eng. Cristian Ritter", "cristianritter@gmail.com", title="Sobre o aplicativo")
            
            if event == 'PLAY':
                mp.play()
            
            if event == 'FORWARD':
                mp.jump_next_fail()
            
            if event == 'FORWARD_1':
                limite = 0.0003/(mp.player.get_length()/3600000)
                mp.set_position(mp.values['TIME']+limite)

            if event == 'FORWARD_10':
                limite = 0.0028/(mp.player.get_length()/3600000)
                mp.set_position(mp.values['TIME']+limite)

            if event == 'REWIND':
                mp.jump_previous_fail()

            if event == 'REWIND_1':
                limite = 0.0003/(mp.player.get_length()/3600000)
                mp.set_position(mp.values['TIME']-limite)

            if event == 'REWIND_10':
                limite = 0.0028/(mp.player.get_length()/3600000)
                mp.set_position(mp.values['TIME']-limite)

            if event == 'TIME':
                if round(mp.values['TIME'],3) == round(mp.time_old,3):
                    continue
                limite = 0.002/(mp.player.get_length()/3600000)
                if mp.values['TIME'] > (1-limite):
                    mp.set_position(mp.values['TIME']-limite)
                else:
                    mp.set_position(mp.values['TIME'])
                
            if event == 'LOG':
                if (len(mp.values['CALENDAR'])) == 0:
                    mp.values['CALENDAR']=datetime.now().strftime('%Y%m%d')
                lognm = "log_"+mp.values['CALENDAR'][0:6]+".txt"
                logfile = os.path.join(log_folder, lognm)
                if os.path.exists(logfile):
                    webbrowser.open(logfile)

            if event == 'CALENDAR':
                calendar_event(mp)

            if event == 'MARK_IN':
                mp.window['EXPORT'].update(disabled=True)
                if (mp.segundos_total) <= 0:
                    continue
                mp.window['IN_TEXT'].update(mp.get_time_elapsed())
                
            if event == 'MARK_OUT':
                mp.window['EXPORT'].update(disabled=True)
                if (mp.segundos_total) <= 0:
                    continue
                mp.window['OUT_TEXT'].update(mp.get_time_elapsed())
                
            if event == 'EXPORT':
                if (len(mp.values['LISTA'])) == 0 or (len (mp.values['EXPORT'])) == 0:
                    continue
                current_filepath = mp.get_current_audio_filepath(mp.values)
                filename = str(current_filepath[:-4]).split('\\')
                begin_seconds = int(mp.values['IN_TEXT'][0:2])*60 + int(mp.values['IN_TEXT'][3:5]) 
                end_seconds = int(mp.values['OUT_TEXT'][0:2])*60 + int(mp.values['OUT_TEXT'][3:5])
                
                dest = os.path.join(mp.values['EXPORT'], filename[len(filename)-1]+'_'+str(begin_seconds)+'_'+str(end_seconds)+'.mp3')
                check_output("{} {} {} trim {} {}".format(SOX, current_filepath,dest,begin_seconds,(end_seconds-begin_seconds)))
                sg.popup("Que legal! O arquivo já está disponível na pasta: ", dest)
                pass

            if event == 'LISTA':
                mp.stop()
                if not 'LISTA' in mp.values:
                    continue
                filename = mp.get_current_audio_filepath(mp.values)
                if not os.path.exists(filename):
                    sg.popup("Arquivo não disponível. Por favor atualize a lista.")
                    continue
                mp.load_single_track(filename)      
                mp.list_player.next()
                mp.redraw_fail_positions(mp.values)
                    
    if __name__ == '__main__':
        main()

except Exception as Err:
    sg.popup(Err)

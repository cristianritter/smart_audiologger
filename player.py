"""
    VLC media player for local and online streaming media
    Author: Israel Dryer
    Modified: 2020-01-23
"""
import vlc
import PySimpleGUI as sg
from sys import platform as PLATFORM
from datetime import datetime
import os
import webbrowser
import time
import parse_config


PATH = './Assets/'
BUTTON_DICT = {img[:-4].upper(): PATH + img for img in os.listdir(PATH)}
DEFAULT_IMG = PATH + 'background2.png'
ICON = PATH + 'player.ico'

configuration = parse_config.ConfPacket()
configs = configuration.load_config('FILES, AUDIO_PARAM, ZABBIX, DETECTION_PARAM')
temp_folder = configs['FILES']['temp_folder']
temp_hour_file = os.path.join(temp_folder,'hour_file.wav')
log_folder = configs['FILES']['log_folder']
definitive_folder = os.path.join(configs['FILES']['saved_files_folder'])


l = []

class MediaPlayer:
    failtimes_list = []

    def __init__(self, size, scale=1.0, theme='DarkBlue'):
        """ Media player constructor """
        self.failtimes_list.append(0)
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

        # Unmute the volume if muted
        if self.player.audio_get_mute():
            self.toggle_mute()

    def button(self, key, image, **kwargs):
        """ Create media player button """
        return sg.Button(image_filename=image, border_width=0, pad=(0, 0), key=key,
                         button_color=('white', self.default_bg_color))

    def create_window(self):
        """ Create GUI instance """
        sg.change_look_and_feel(self.theme)
        
        # Column layout for media player button controls
        col1 = [[
                 sg.In(key='CALENDAR', enable_events=True, visible=False), sg.CalendarButton('', image_filename=BUTTON_DICT['CALENDAR'], pad=(0,0),  
                        button_color=('white', self.default_bg_color), border_width=0, key='CALENDAR', format=('%Y%m%d')),
                 self.button('START', BUTTON_DICT['START']),
                 self.button('REWIND', BUTTON_DICT['REWIND']),
                 self.button('PAUSE', BUTTON_DICT['PAUSE_OFF']),
                 self.button('PLAY', BUTTON_DICT['PLAY_OFF']),
                 self.button('STOP', BUTTON_DICT['STOP']),
                 self.button('FORWARD', BUTTON_DICT['FORWARD'])
                         ]]
                 

        # Column layout for media info and instructions
        col2 = [[sg.Text('Open a FILE, STREAM, or PLAYLIST to begin',
                         size=(45, 3), font=(sg.DEFAULT_FONT, 8), pad=(0, 5), key='INFO')]]
        
        col3 = [     
            [sg.Listbox(l, size=(40, 25), enable_events=True, key='LISTA')],
            [sg.Text('Abrir arquivo de LOG', key = 'LOG', 
                    enable_events=True, font=(sg.DEFAULT_FONT, 8, 'underline'))]
        ]

        # Main GUI layout
        main_layout = [
            
            # Media output element -- this is the video output element
            [sg.Image(filename=DEFAULT_IMG, pad=(0, 5), size=self.player_size, key='VID_OUT')],

            # Element for tracking elapsed time
            [sg.Text('00:00', key='TIME_ELAPSED'),

             # This slide can be used to adjust the playback positon of the video
            sg.Slider(range=(0, 1), enable_events=True, resolution=0.0001, disable_number_display=True,
                       background_color='#83D8F5', orientation='h', key='TIME'),

             # Elements for tracking media length and track counts
            sg.Text('00:00', key='TIME_TOTAL'),
            sg.Text('          ', key='TRACKS')],

            [sg.Graph(canvas_size=(900, 20), graph_bottom_left=(-60, 0), graph_top_right=(840, 20), background_color=self.default_bg_color, enable_events=True, key='graph')],
            
            # Button and media information layout (created above)
            [sg.Column(col1), sg.Column(col2)]
        ]

        main_2col = [
            [sg.Column(main_layout), sg.Column(col3)]
        ]


        # Create a PySimpleGUI window from the specified parameters
        window = sg.Window('Audiologger NSC', main_2col, element_justification='center', icon=ICON, finalize=True)

        
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

      
         # This is a file path and not an online url
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

    def get_meta(self, meta_type):
        """ Retrieve saved meta data from tracks in media list """
        media = self.player.get_media()
        return media.get_meta(meta_type)

    def get_track_info(self):
        """ Show author, title, and elasped time if video is loaded and playing """
        time_elapsed = "{:02d}:{:02d}".format(*divmod(self.player.get_time() // 1000, 60))
        time_total = "{:02d}:{:02d}".format(*divmod(self.player.get_length() // 1000, 60))
        if self.media_list.count() == 0:
            self.window['INFO'].update('Open a FILE, STREAM, or PLAYLIST to begin')
        else:
            message = "{}\n{}".format(self.get_meta(1).upper(), self.get_meta(0))
            self.window['INFO'].update(message)
            self.window['TIME_ELAPSED'].update(time_elapsed)
            self.window['TIME'].update(self.player.get_position())
            self.window['TIME_TOTAL'].update(time_total)
            self.window['TRACKS'].update('{} of {}'.format(self.track_num, self.track_cnt))
            #self.window['INFO'].update('Press PLAY to Start')

    def play(self):
        """ Called when the play button is pressed """
        self.list_player.play()
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])

    def stop(self):
        """ Called when the stop button is pressed """
        self.player.stop()
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_OFF'])
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['TIME'].update(value=0)
        self.window['TIME_ELAPSED'].update('00:00')

    def pause(self):
        """ Called when the pause button is pressed """
        self.window['PAUSE'].update(
            image_filename=BUTTON_DICT['PAUSE_ON'] if self.player.is_playing() else BUTTON_DICT['PAUSE_OFF'])
        self.window['PLAY'].update(
            image_filename=BUTTON_DICT['PLAY_OFF'] if self.player.is_playing() else BUTTON_DICT['PLAY_ON'])
        self.player.pause()

    def jump_to_begin(self):
        self.player.set_position(0)
        self.get_track_info()
    def jump_next_fail(self):
        if len(self.failtimes_list) == 0:
            return
        destino = 0
        for item in self.failtimes_list:
            if (self.player.get_time() / 1000) < item:
                destino = item
                break
            
        """ Called when the skip next button is pressed """
        tamanho = self.player.get_length() // 1000
        position = destino / tamanho
        
        self.player.set_position(position)
        self.get_track_info()
        

        #self.list_player.next()
        #self.reset_pause_play()
        #if not self.track_cnt == self.track_num:
        #    self.track_num += 1

    def jump_previous_fail(self):
        """ Called when the skip previous button is pressed """
        if len(self.failtimes_list) == 0:
            return
        destino = 0
        for item in reversed(self.failtimes_list):
            if ((self.player.get_time() / 1000)-1) > item:
                destino = item
                break

        tamanho = self.player.get_length() // 1000
        position = destino / tamanho
        
        self.player.set_position(position)
        self.get_track_info()
            
        tamanho = self.player.get_length() // 1000
        position = destino / tamanho
        
        self.player.set_position(position)
        self.get_track_info()

        #self.list_player.previous()
        #self.reset_pause_play()
        #if not self.track_num == 1:
        #    self.track_num -= 1

    def reset_pause_play(self):
        """ Reset pause play buttons after skipping tracks """
        self.window['PAUSE'].update(image_filename=BUTTON_DICT['PAUSE_OFF'])
        self.window['PLAY'].update(image_filename=BUTTON_DICT['PLAY_ON'])

    def toggle_mute(self):
        """ Called when the sound button is pressed """
        self.window['SOUND'].update(
            image_filename=BUTTON_DICT['SOUND_ON'] if self.player.audio_get_mute() else BUTTON_DICT['SOUND_OFF'])
        self.player.audio_set_mute(not self.player.audio_get_mute())        

    def load_single_track(self, track):
        """ Open a popup to request url or filepath for single track """
        #track = sg.PopupGetFile('Browse for local media or enter URL:',
        #                        title='Load Media')
        if track is None:
            return
        else:
            self.window['INFO'].update('Loading media...')
            self.window.read(1)
            self.add_media(track)
        if self.media_list.count() > 0:
            self.play()
        #self.skip_next()

    def load_playlist_from_file(self):
        """ Open text file and load to new media list. Assumes `playlist.txt` is in root directory """

        # Read contents of playlist file
        with open('./playlist.txt', 'r') as f:
            try:
                playlist = f.read().splitlines()
            except IOError:
                sg.popup_error('There was an error opening the file. Please make sure `playlist.txt` is in\
                the same path as the media player executable', title='Playlist Error')
                return

        # Send message to window and update
        self.window['INFO'].update('Loading playlist...')
        self.window.read(1)

        # Add each track to the playlist if a valid url or file path
        for track in playlist:
            if track.strip():
                self.add_media(track.replace('\\', '/'))

                # Play this track if player not playing (allows for faster perceived startup)
                if not self.player.is_playing:
                    self.play()

        # Increment the track counter
        self.track_cnt = self.media_list.count()
        self.track_num = 1


def main():
    """ The main program function """

    # Create the media player
    mp = MediaPlayer(size=(1920, 1080), scale=0.5)
    

    # Main event loop
    while True:
        event, values = mp.window.read(timeout=20)
        mp.get_track_info()
        if event in (None, 'Exit'):
            break
        if event == 'PLAY':
            mp.play()
        if event == 'PAUSE':
            mp.pause()
        if event == 'FORWARD':
            mp.jump_next_fail()
        if event == 'REWIND':
            mp.jump_previous_fail()
        if event == 'STOP':
            mp.stop()
        if event == 'SOUND':
            mp.toggle_mute()
        if event == 'TIME':
            mp.player.set_position(values['TIME'])
            mp.get_track_info()
        if event == 'PLUS':
            mp.load_single_track(None)
        if event == 'START':
            mp.jump_to_begin()
        if event == 'LOG':
            if (len(values['CALENDAR'])) == 0:
                continue
            lognm = "log_"+values['CALENDAR'][0:6]+".txt"
            logfile = os.path.join(log_folder, lognm)
            webbrowser.open(logfile)

        if event == 'CALENDAR':
            folder = values['CALENDAR']+'\\'
            sourcepath = os.path.join(definitive_folder, folder)
            l.clear()
            if not os.path.exists(sourcepath):
                continue
            for e in os.listdir(sourcepath):
                l.append(e)
            if values['CALENDAR'] == datetime.now().strftime('%Y%m%d'):
                l.append("Last Minutes ...")
            mp.window['LISTA'].update(l)
        
        if event == 'LISTA':
            if (len(values['LISTA'])) == 0:
                continue
            graph = mp.window['graph']  
            graph.DrawRectangle( (-0, 0), (800,20), fill_color='gray' )
            graph.update()
            folder = values['CALENDAR']+'\\'
            sourcepath = os.path.join(definitive_folder, folder)
            if values['LISTA'][0] != "Last Minutes ...":
                dados = values['LISTA'][0]
                filename = os.path.join(sourcepath, dados)
            else:
                dados = datetime.now().strftime('%Y%m%d_%H.mp3')
                filename = temp_hour_file             
            
            mp.load_single_track(filename)
            time.sleep(0.2)
            mp.list_player.next()
            mp.failtimes_list.clear()
            segundos_total = mp.player.get_length() / 1000
            lognm = "log_"+values['CALENDAR'][0:6]+".txt"
            logfile = os.path.join(log_folder, lognm)
            f = open(logfile, "r")
            logtext = (dados[6:8] + '/' + dados[4:6] + '/' + dados[:4] + ' ' + dados[9:11])
            for x in f: #le linhas
                if logtext in x:
                    pos = int(x[14:16])*60+int(x[17:19]) #posicao segundos
                    mp.failtimes_list.append(pos) #seconds
                    param = 785 / segundos_total
                    graph.DrawLine ((param*pos, 0), (param*pos, 20), color='white', width = 2)
                    print(param*pos)

if __name__ == '__main__':
    main()
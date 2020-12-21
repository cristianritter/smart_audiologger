
import PySimpleGUI as sg
 

l = []
l.append('Byte |  Value  | Attribute')
l.append('   0 | | Re-Assigned Sector Count' )
l.append('   1 |    | Program Fail Count (Worst Case Component)')
l.append('11:8 |    | Reserved Block Count (SSD Total)')

layout = [[sg.Listbox(l, size=(40, 20))]]
sg.Window("Dell SMART Attributes",
        layout+[[sg.OK()]],
        font=('monospace', 16)).Read() 

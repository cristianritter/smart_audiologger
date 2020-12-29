import subprocess
import hashlib
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__)) # This is your Project Root
license_file = os.path.join(ROOT_DIR, 'license.lic' )
current_machine_id = subprocess.check_output('wmic csproduct get uuid').decode().split('\n')[1].strip()
lista = ['SmartLogger Player', 'SmartLogger Gravador']
        
class license:
    def __init__(self, app):
       self.app = app
    
    def verifica(self):
        try:
            f = open(license_file, "r")
            global license_content
            license_content = f.read()
            f.close()
        except:
            exit()

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
        print(uniao_dig)
        if uniao_dig != license_content:
            print(license_content)
            print("Licença inválida")
            print("Informe este código de maquina: {}".format(codigo_de_maquina_dig))
            return codigo_de_maquina_dig
        else:
            print('Licença verificada')
            return 0

a = license(lista[0])
a.verifica()


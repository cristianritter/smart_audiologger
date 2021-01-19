from datetime import date, datetime, timedelta
from time import sleep
from threading import Thread

  
def funcao(x, y):
 print(x,y)

T = Thread(name='b',target=funcao, args=(1,2))
T.start()
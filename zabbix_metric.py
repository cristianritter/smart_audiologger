from pyzabbix import ZabbixMetric, ZabbixSender
import parse_config
import save_log

configuration = parse_config.ConfPacket()
configs = configuration.load_config('ZABBIX')
 
def send_status_metric(value):
    try:
        packet = [
            ZabbixMetric(configs['ZABBIX']['hostname'], configs['ZABBIX']['key'], value)
        ]
        ZabbixSender(zabbix_server=configs['ZABBIX']['zabbix_server'], zabbix_port=int(configs['ZABBIX']['port'])).send(packet)
    except Exception as err:
        save_log.adiciona_linha_log("Falha de conexão com o Zabbix - "+str(err))
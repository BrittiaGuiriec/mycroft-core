import ast
import re
import sys
from subprocess import Popen, PIPE

import tornado.websocket
from shutil import copyfile
from WiFiTools import ap_link_tools
from wpaCLITools import wpaClientTools
from app.util.LinkUtils import ScanForAP

from mycroft.util.log import getLogger


LOGGER = getLogger("WiFiSetupClient")

import time



def bash_command(cmd):
    print cmd
    try:
        proc = Popen(cmd, shell=False, stdout=PIPE, stderr=PIPE)
        stdout,stderr = proc.communicate('n\n')
    except:
        LOGGER.warn( "bash fail")

def Exit_gracefully(signal, frame):
    print "caught SIGINT"
    S.station_mode_off()
    print "exiting"
    sys.exit(0)

class APConfig():
    file_template = 'config.templates/etc/hostapd/hostapd.conf.template'
    file_path = '/etc/hostapd/hostapd.conf'
    interface = 'wlan0'
    driver = 'nl80211'
    ssid = 'PI3-AP'
    hw_mode = 'g'
    channel = 6
    country_code = 'US'
    ieee80211n = 1
    wmm_enabled = 1
    ht_capab = '[HT40][SHORT-GI-20][DSSS_CCK-40]'
    macaddr_acl = 0
    ignore_broadcast_ssid = 0

    def copy_config_ap(self):
        copyfile(self.file_template, self.file_path)
        copyfile('config.templates/etc/dhcpcd.conf.hostapd', '/etc/dhcpcd.conf')
        copyfile('config.templates/etc/default/hostapd.hostapd', '/etc/default/hostapd')
        copyfile('config.templates/etc/dnsmasq.conf.hostapd', '/etc/dnsmasq.conf')
        copyfile('config.templates/etc/network/interfaces.hostapd', '/etc/network/interfaces')


    def write_config(self):
        ha.set_ssid(APConf,self.ssid)
        APConf.write()      

class MainHandler(tornado.web.RequestHandler):
   def get(self):
        apScan = ScanForAP('scan', 'wlan0')
        apScan.start()
        apScan.join()
        self.ap = apScan.join()
        self.render("index.html",
        ap=self.ap)
		
class JSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info( "request for jquery.min.js")
        self.render("jquery-2.2.3.min.js")

class BootstrapMinJSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info("request for bootstrap,min.js")
        self.render("bootstrap-3.3.7-dist/js/bootstrap.min.js")

class BootstrapMinCSSHandler(tornado.web.RequestHandler):
    def get(self):
        LOGGER.info("request for bootstrap.min.css")
        self.render("bootstrap-3.3.7-dist/css/bootstrap.min.css")

class WSHandler(tornado.websocket.WebSocketHandler):
    def check_origin(self,origin):
        return True
    def open(self):
        LOGGER.info('a user is connected')

    def on_message(self, message):
        LOGGER.info('received message: %s\n' % message)
        self.write_message(message + ' OK')
        self.message_switch(message)

    def on_close(self):
        LOGGER.info('connection closed\n')

    def is_match(self, regex, text):
        self.pattern = re.compile(regex)
        return self.pattern.search(text) is not None

    def message_switch(self,message):
        self.dict2 = ast.literal_eval(message)
        LOGGER.info(type(self.dict2))
        if self.is_match("'ap_on'", message) is True:
            station_mode_on()
        elif self.is_match("'ap_off'", message) is True:
            station_mode_off()
        elif self.is_match("'scan_networks'", message) is True:
            print "Need: Refresh page/div/unhide/something"
        elif self.is_match("'ssid'", message) is True:
            print "SSID selected: ", self.dict2['ssid']
            wifi_connection_settings['ssid'] = self.dict2['ssid']
        elif self.is_match("'passphrase'", message) is True:
            print "PASSPHRASE Recieved:", self.dict2
            print self.dict2['passphrase']
            wifi_connection_settings['passphrase'] = self.dict2['passphrase']
            ssid = wifi_connection_settings['ssid']
            passphrase = self.dict2['passphrase']
            ssid = '''"''' + ssid +  '''"'''
            passphrase = '''"''' + passphrase + '''"'''
            WiFi = wpaClientTools()
            network_id = WiFi.wpa_cli_add_network('wlan0')['stdout'].strip()
            print network_id
            print WiFi.wpa_cli_set_network('wlan0', str(network_id), 'ssid', ssid)
            print WiFi.wpa_cli_set_network('wlan0', str(network_id), 'psk', passphrase)
            print WiFi.wpa_cli_enable_network('wlan0', network_id)
            x = 15
            while x > 0:
                try:
                    if WiFi.wpa_cli_status('wlan0')['wpa_state'] == 'COMPLETED':
                        print "CONNECTED"
                        self.write_message("Authenication Sucessful")
                        print WiFi.wpa_save_network(str(network_id))
                        self.write_message("Saving Network SSID and Passphrase")
                        print WiFi.wpa_cli_disable_network(str(network_id))
                        x = 0
                except:
                    self.write_message("Attempting to Authenticate")
                    print "no"
                    x = x - 1
                    time.sleep(1)
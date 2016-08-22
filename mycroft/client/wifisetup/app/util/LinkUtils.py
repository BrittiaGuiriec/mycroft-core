#!/bin/env python
import threading
from collections import defaultdict
from wifi import Cell
from operator import itemgetter
from mycroft.client.wifisetup.app.util.bashThreadHandling import bash_command
from mycroft.util.log import getLogger
LOGGER = getLogger("WiFiSetupClient")


class ScanForAP(threading.Thread):
    def __init__(self, name, interface):
        threading.Thread.__init__(self)
        self.name = name
        self.interface = interface

    def run(self):
        ap_scan_results = defaultdict(list)
        try:
            for cell in Cell.all(self.interface):
                ap_scan_results['network'].append({
                    'ssid': cell.ssid,
                    'signal': cell.signal,
                    'quality': cell.quality,
                    'frequency': cell.frequency,
                    'encrypted': cell.encrypted,
                    'channel': cell.channel,
                    'address': cell.address,
                    'mode': cell.mode
                })

            #################################################
            # Clean up the list of networks.
            #################################################
            # First, sort by name and strength
            nets_byNameAndStr = sorted(ap_scan_results['network'], key=itemgetter('ssid', 'quality'), reverse=True)
            # now strip out duplicates (e.g. repeaters with the same SSID), keeping the first (strongest)
            lastSSID = "."
            for n in nets_byNameAndStr[:]:
                if (n['ssid'] == lastSSID):
                    nets_byNameAndStr.remove(n)
                else:
                    lastSSID = n['ssid']
                    # Finally, sort by strength alone
            ap_scan_results['network'] = sorted(nets_byNameAndStr, key=itemgetter('quality'), reverse=True)
            self._return = ap_scan_results
        except:
            print "ap scan fail"

    def join(self):
        threading.Thread.join(self)
        return self._return


def link_add_vap():
    LOGGER.warn(bash_command('iw dev wlan0 interface add uap0 type __ap'))
    time.sleep(2)
    LOGGER.warn(bash_command('ifdown upa0'))
    time.sleep(2)
    LOGGER.warn(bash_command('ifup upa0'))
    time.sleep(2)
    return


def client_mode_config(iface, ssid, passphrase):
    write_wpa_supplicant_conf(ssid, passphrase)


def client_connect_test(iface, ssid, passphrase):
    LOGGER.warn(bash_command('wpa_supplicant -iwlan0 -Dnl80211 -c /etc/wpa_supplicant/wpa_supplicant.conf'))
    LOGGER.warn(bash_command('ifdown wlan0'))
    LOGGER.warn(bash_command('ifconfig wlan0 up'))
    connect = JoinAP('Connecting to Network', iface, ssid, passphrase)
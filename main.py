# main.py

import datetime
# import whois
import json
import socket
import time
import traceback
from random import choice
from threading import Thread
from urllib.parse import quote as urlencode
from urllib.parse import unquote
from urllib.error import URLError

import pytz
import requests
import socks
import subprocess

from pytrends.request import TrendReq

import settings
import translate_krzb
from settings import settings as option
from settings import getconfig
from helpers import get_pretty_json_string, shell

from tgbich import run_tgbich
from ircbich import ircbich_init_and_loop


functions = {'tg': run_tgbich, 'irc': ircbich_init_and_loop}


print(f"{__file__}, {__name__}: starting")

from multiprocessing import Process
import os


print(f"{__file__}, {__name__}: pytrends: processing Trend Requests")
while True:
    try:
        pytrends = TrendReq(hl='ru-RU', tz=360)
        break
    except KeyboardInterrupt as e:
        raise e
    except:
        traceback.print_exc()
        TIME_TO_SLEEP_SECONDS = 1
        print("sleeping %s seconds" % str(TIME_TO_SLEEP_SECONDS))
        time.sleep(TIME_TO_SLEEP_SECONDS)
        continue
print(f"{__file__}, {__name__}: pytrends: completed.")


# launch processes
def launch_all():
    print("processing configs")
    cfg = getconfig()
    print("processing connections")
    connections = cfg["connections"]
    for key in connections.keys():
        print(f"processing connections.{key}")
        section = connections[key]
        for section_key in section.keys():
            print(f"  processing connections.{key}.{section_key}")
            conn_props = section[section_key]
            print(f"    launching connection {key}.{section_key}, conn_props='{conn_props}'")
            Process(target=functions[key], args=(key, conn_props, cfg, )).start()
            print(f"    launched connection {key}.{section_key}")
            print(f"  processed connections.{key}.{section_key}")
        print(f"processed connections.{key}")
    print("all launched; processed all connections")

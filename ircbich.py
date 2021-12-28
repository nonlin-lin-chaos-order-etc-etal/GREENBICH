# ircbich.py

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

import os
import pytz
import requests
import socks
import subprocess

from pytrends.request import TrendReq

import settings
import translate_krzb
from settings import settings as option
from settings import getconfig
from helpers import get_pretty_json_string, shell, LOG_TRACE

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
# pip3 install xlrd pandas
import pandas as pd

from abstractbich import BichBot


class IrcBich(BichBot):

    databuf = b''
    socket_closed = False
    data = None
    irc_socket = None


    def __init__(self, settings_key, connection_settings: dict, config):
        super(IrcBich, self).__init__(settings_key, connection_settings, config)
        self.irc_server_hostname = self.connection_settings('irc_server_hostname')
        self.port = int(self.connection_settings('port'))
        self.channelsProps = self.connection_settings('channelsProps')
        self.channelsList = list(self.channelsProps.keys())
        self.BOT_NAME_PREFIX = self.connection_settings('InitialBotNick')
        self.botName = self.BOT_NAME_PREFIX
        self.botNickSalt = 0
        self.nickserv_password = self.connection_setting_or_None('nickserv_password')

        self.titleEnabled = bool(self.connection_settings('titleEnabled'))

        self.master_secret = settings.settings('master_secret')


    @staticmethod
    def link_title(n):
        """ Parses message to find links and get linked page titles """

        title = "Unknown"
        link_r = None
        if 'http://' in n or 'https://' in n:
            try:
                link_r = n.split('//', 1)[1].split(' ', 1)[0].rstrip()
            except:
                traceback.print_exc()
                print('Link wrong!')
        link = 'http://' + link_r
        get_title = requests.get(link, timeout=10)

        unquoted_link = unquote(link)  # TODO WTF? call should be removed or used?
        txt_title = get_title.text
        if '</TITLE>' in txt_title or '</title>' in txt_title \
                or '</Title>' in txt_title:
            if '</TITLE>' in txt_title:
                title = '\x02Title\x02 of ' + n + ': ' + \
                        txt_title.split('</TITLE>', 1)[0].split('>')[-1]
            elif '</title>' in txt_title:
                title = '\x02Title\x02 of ' + n + ': ' + \
                        txt_title.split('</title>', 1)[0].split('>')[-1]
            elif '</Title>' in txt_title:
                title = '\x02Title\x02 of ' + n + ': ' + \
                        txt_title.split('</Title>', 1)[0].split('>')[-1]

            return title.replace('\r', '').replace('\n', '').replace('www.', '').strip()
        else:
            return 'Title not found'


    class MyPingsToServerThread(Thread):
        def __init__(self, my_bot):
            Thread.__init__(self)
            self.my_bot = my_bot

        def run(self):
            self.my_bot.pinger_of_server()


    def init_socket(self, client_socket):
        self.databuf = b''
        self.socket_closed = False

    def extract_line(self):
        # socket must be closed for this call.
        if not self.socket_closed: raise Exception

        a = self.databuf.find(b'\r')
        b = self.databuf.find(b'\n')
        if a != -1 and b != -1: a = min(a, b)
        if b != -1 and a == -1: a = b
        if a != -1:
            line = self.databuf[0:a]
            if self.databuf[a] == 0xD:
                a = a + 1
                if a < len(self.databuf) and self.databuf[a] == 0xA:
                    a = a + 1
            else:
                if self.databuf[a] == 0xA:
                    a = a + 1
            self.databuf = self.databuf[a:] if a < len(self.databuf) else b''
            return line
        return self.databuf

    def extract_line_1(self):
        # if LOG_TRACE: print("extract_line_1() #0: databuf", databuf, "socket_closed", socket_closed)
        a = self.databuf.find(b'\r')
        b = self.databuf.find(b'\n')
        if a != -1 and b != -1: a = min(a, b)
        if b != -1 and a == -1: a = b
        if a != -1:
            if LOG_TRACE: print("#1: a:", a, "len(databuf):", len(self.databuf), "databuf[a]==b'SLASHr':",
                                self.databuf[a] == 0xD, "databuf[a]:", self.databuf[a], "a < len(databuf)-1:",
                                a < len(self.databuf) - 1)
            if (self.databuf[a] == 0xD and a < len(self.databuf) - 1) or self.databuf[a] == 0xA:
                if LOG_TRACE: print("#2")
                line = self.databuf[0:a]
                if self.databuf[a] == 0xD:
                    if LOG_TRACE: print("#3")
                    a = a + 1
                    if self.databuf[a] == 0xA:
                        if LOG_TRACE: print("#4")
                        a = a + 1
                else:
                    if LOG_TRACE: print("#5")
                    if self.databuf[a] == 0xA:
                        if LOG_TRACE: print("#6")
                        a = a + 1
                if LOG_TRACE: print("#7, a:", a)
                self.databuf = self.databuf[a:]
                if LOG_TRACE: print("returning line:", line)
                return line
            # else read more
        # else read more
        if LOG_TRACE: print("returning None")
        return None

    def get_line(self, client_socket):
        if self.socket_closed:
            return self.extract_line()
        line = self.extract_line_1()
        if line is not None: return line
        while True:
            r = client_socket.recv(81920)
            if len(r) == 0:
                if LOG_TRACE: print("EOF")
                self.socket_closed = True
                return self.extract_line()
            if LOG_TRACE: print("RX:", r)
            self.databuf += r
            line = self.extract_line_1()
            if line is not None: return line

    # Function shortening of ic.self.send.  
    def send(self, msg):
        print(f"TX: {msg}")
        retval = self.irc_socket.send(bytes(msg, 'utf-8'))
        return retval

    def login_and_loop(self):
        global sys, tb
        while True:
            print("---new iter---", flush=True)
            try:
                mask2ctx = {}
                from time import sleep as sleep_seconds
                print("sleeping 50ms...")
                sleep_seconds(0.05)
                if self.connection_setting_or_None('socks5_host'):
                    host = self.connection_option('socks5_host')
                    print(f"new socks.socksocket({host})")
                    self.irc_socket = socks.socksocket()
                    self.irc_socket.set_proxy(socks.SOCKS5, host,
                                              self.connection_option('socks5_port'), True,
                                              self.connection_option('socks5_username'),
                                              self.connection_option('socks5_password'))
                else:
                    print("new socket(AF_INET,SOCK_STREAM)")
                    self.irc_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                print("connecting... irc_server_hostname='" + self.irc_server_hostname + "' port='" + str(
                    self.port) + "'…")
                self.irc_socket.connect((self.irc_server_hostname, self.port))
                self.init_socket(self.irc_socket)
                print("connected, self.sending login handshake, self.botName=[" + self.botName + "]…")
                # print (self.irc_socket.recv(2048).decode("UTF-8"))
                self.send('NICK ' + self.botName + '\r\n')
                self.send('USER ' + self.botName + ' ' + self.botName + ' ' + self.botName + ' :irc bot\r\n')
                # self.send('NickServ IDENTIFY '+settings.settings('password')+'\r\n')
                # self.send('MODE '+self.botName+' +x')

                name = ''
                message = ''
                message_voting = ''
                voting_results = ''

                count_voting = 0
                count_vote_plus = 0
                count_vote_minus = 0
                count_vote_all = 0
                while_count = 0

                btc_usd = 0
                eth_usd = 0
                usd_rub = 0
                eur_rub = 0
                btc_rub = 0
                btc_usd_old = 0
                eth_usd_old = 0
                usd_rub_old = 0
                eur_rub_old = 0
                btc_rub_old = 0
                btc_usd_su = ''
                eth_usd_su = ''
                usd_rub_su = ''
                eur_rub_su = ''
                time_vote = 0

                whois_ip = ''
                whois_ip_get_text = ''

                timer_exc = 0
                time_exc = 0

                where_mes_exc = ''
                t2 = 0

                dict_users = {}
                dict_count = {}
                dict_voted = {}
                list_vote_ip = []

                # List who free from anti-flood function.
                list_floodfree = settings.settings('list_floodfree')
                list_bot_not_work = settings.settings('list_bot_not_work')

                keepingConnection = True
                while keepingConnection:
                    try:
                        data = self.get_line(self.irc_socket).decode("UTF-8")
                        print("got line:[" + data + "]", flush=True)
                        if data == "":
                            print("data=='', self.irc_socket.close(), keepingConnection=False, iterating...")
                            self.irc_socket.close()
                            keepingConnection = False
                            continue
                    except UnicodeDecodeError as decodeException:
                        print(f"UnicodeDecodeError {decodeException}, iterating...")
                        continue
                    tokens1 = data.split(" ")

                    sender_mask = None

                    dataTokensDelimitedByWhitespace = tokens1
                    # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
                    # dataTokensDelimitedByWhitespace[1] PRIVMSG

                    # dataTokensDelimitedByWhitespace[2] #ru
                    # OR
                    # dataTokensDelimitedByWhitespace[2] BichBot

                    # dataTokensDelimitedByWhitespace[3] :!курс
                    communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
                        dataTokensDelimitedByWhitespace) > 2 else None
                    lineJoined = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(
                        dataTokensDelimitedByWhitespace) >= 4 else ""
                    sender = communicationsLineName
                    sent_by = dataTokensDelimitedByWhitespace[0][1:]

                    if len(tokens1) > 1 and tokens1[1] == "433":  # "Nickname is already in use" in data
                        self.botNickSalt = self.botNickSalt + 1
                        self.botName = self.BOT_NAME_PREFIX + str(self.botNickSalt)
                        self.send('NICK ' + self.botName + '\r\n')
                        continue
                    if len(tokens1) >= 4 and tokens1[1] == "MODE" and "+x" in tokens1[
                        3]:  #:GreenBich MODE GreenBich :+x
                        self.send('JOIN ' + (",".join(self.channelsList)) + ' \r\n')
                        continue
                    #
                    if self.nickserv_password is not None and len(tokens1) > 1 and tokens1[
                        1] == "001":  # 001 nick :Welcome to the Internet Relay Network
                        self.send('NICKSERV IDENTIFY ' + self.nickserv_password + '\r\n')
                    if data.find('PING') != -1:
                        try:
                            print("ping_received")
                            self.send('PONG ' + data.split(" ")[1] + '\r\n')
                            print("pong sent with data_str")
                        except:
                            traceback.print_exc()
                            self.send('PONG')
                            print("pong sent without data_str")
                        continue
                    if data.find('PONG') != -1:
                        print("server pong_received")
                        self.pong_received = True
                        continue

                    # 001 welcome
                    spws = tokens1
                    if len(spws) > 1 and spws[1] == "001":
                        self.MyPingsToServerThread(self).start()
                        self.send('MODE ' + self.botName + ' +xB\r\n')
                        continue

                    ws_tokens = tokens1

                    try:
                        message = None
                        # got line:[:test2!~username@ipaddr PRIVMSG #channel :msg]
                        if len(ws_tokens) >= 4:
                            src = ws_tokens[0]
                            cmd = ws_tokens[1]
                            chan = ws_tokens[2]
                            msg = " ".join(ws_tokens[3:])

                            if cmd == "PRIVMSG":
                                name = src.split('!')[0][1:]
                                sender_mask = src[1:]
                                message = msg[1:]
                                print(__name__, f"message: '{message}'", flush=True)
                            try:
                                ip_user = None  # "data.split('@',1)[1].split(' ',1)[0]
                            except:
                                print(__name__, 'error getting ip_user')
                    except:
                        traceback.print_exc()
                        sys.stderr.flush()

                    # got line:[:test1!~username@ipaddr NICK :test2]
                    try:
                        if len(ws_tokens) >= 3:
                            src = ws_tokens[0]
                            cmd = ws_tokens[1]
                            msg = " ".join(ws_tokens[2:])

                            if cmd == "NICK":
                                old_mask = src[1:]
                                print(__name__, "old_mask: '" + old_mask + "'", flush=True)
                                old_mask_split = old_mask.split("!")
                                new_nick = msg[1:]
                                new_mask = new_nick + "!" + old_mask_split[1]
                                print(__name__, "new_mask: '" + new_mask + "'", flush=True)
                                self.replace_nick_mask2ctx(mask2ctx, old_mask, new_mask)
                    except:
                        traceback.print_exc()
                        sys.stderr.flush()

                    where_message = "unknown_where"

                    if self.enableother1 or self.connection_setting_or_None("enable_krako_translation"):
                        # print(__file__, "krako test")
                        try:
                            where_message = communicationsLineName
                            if message is not None and (message.startswith('!k') or message.startswith("!к")) and \
                                    dataTokensDelimitedByWhitespace[1] == "PRIVMSG":
                                if self.grantCommand(sent_by, communicationsLineName):
                                    print(__name__, "krako test success", flush=True)
                                    m = message.strip()
                                    if m == "!k" or m == "!к":
                                        print(f"{__name__} krako: mask2ctx='{mask2ctx}', sender_mask='{sender_mask}'", flush=True)
                                        prev_msg = self.get_prev_msg(mask2ctx, sender_mask)
                                        print(f"{__name__} krako translating prev_msg: '{prev_msg}'", flush=True)
                                        tr_txt = prev_msg
                                    else:
                                        tr_txt = m[2:].strip()
                                    res_txt = translate_krzb.tr(tr_txt)
                                    self.send(f'PRIVMSG {where_message} :\x02перевод с кракозябьечьего:\x02 {res_txt}\r\n')
                                    continue
                        except KeyboardInterrupt as ex:
                            tb.print_exc()
                            sys.stderr.flush()
                            self.send(f'PRIVMSG {where_message} :\x02!k error:\x02 {ex}\r\n')
                            raise ex
                        except BaseException as ex:
                            tb.print_exc()
                            sys.stderr.flush()
                            self.send(f'PRIVMSG {where_message} :\x02!k error:\x02 {ex}\r\n')
                            continue

                    """
                    print(__name__, "before set_prev_msg: message='"+str(message)+"', sender_mask='"+str(sender_mask)+"'")
                    """
                    if message is not None and sender_mask is not None:
                        # print(__name__, "set_prev_msg")
                        try:
                            self.set_prev_msg(mask2ctx, sender_mask, message)
                            print(__name__, "set_prev_msg left ok", flush=True)
                        except KeyboardInterrupt as e:
                            print(__name__, "set_prev_msg left with exception: KeyboardInterrupt", flush=True)
                            raise e
                        except:
                            traceback.print_exc()
                            print(__name__, "set_prev_msg left with exception", flush=True)

                    # print(__name__, "point 3.1", flush=True)
                    if self.enableother1 or self.connection_setting_or_None("enable_hextoip"):
                        if ':!hextoip' in lineJoined and dataTokensDelimitedByWhitespace[1] == "PRIVMSG":
                            if self.grantCommand(sent_by, communicationsLineName):
                                print(__file__, "hextoip test success")
                                try:
                                    hex_value = message.split('!hextoip ', 1)[1].strip()
                                    self.send(
                                        'PRIVMSG ' + communicationsLineName + ' :\x02hextoip:\x02 ' + self.convert_hex_to_ip(
                                            hex_value) + '\r\n')
                                except KeyboardInterrupt:
                                    raise
                                except BaseException as e:
                                    traceback.print_exc()
                                    self.send(
                                        f'PRIVMSG {communicationsLineName} :\x02hextoip:\x02 error: {str(e)}.\r\n'
                                    )
                                continue

                    """if 'PRIVMSG '+channel+' :!help' in data or 'PRIVMSG '+self.botName+' :!справка' in data or 'PRIVMSG '+self.botName+' :!помощь' in data or 'PRIVMSG '+self.botName+' :!хелп' in data:
                        self.send('NOTICE %s : Помощь по командам бота:\r\n' %(name))
                        self.send('NOTICE %s : ***Функция опроса: [!опрос (число) сек (тема опрос)], например\
                        (пишем без кавычек: \"!опрос 60 сек Вы любите ониме?\", если не писать время, то время\
                        установится на 60 сек\r\n' %(name))
                        self.send('NOTICE %s : ***Функция курса: просто пишите (без кавычек): "%s, курс". Писать\
                        можно и в приват боту\r\n' %(name, bot_nick))
                        self.send('NOTICE %s : ***Функция whois: что бы узнать расположение IP, просто пишите\
                        (без кавычек): \"!где айпи (IP)\", пример: \"!где айпи \
                        188.00.00.01\". Писать можно и в приват к боту\r\n' %(name))
                        self.send('NOTICE %s : ***Функция перевода с английских букв на русские: \"!п tekst perevoda\", пример: \"!п ghbdtn\r\n' %(name))

                        """
                    # Anti-flood

                    # print(__name__, "point 3.2", flush=True)
                    while_count += 1
                    if while_count == 50:
                        while_count = 0
                        dict_count = {}

                    # print(__name__, "point 3.3", flush=True)
                    # Insert nick in dict: dic_count.  
                    if data.find('PRIVMSG') != -1 and name not in dict_count and \
                            name not in list_floodfree:
                        dict_count[name] = int(1)
                        # if 'PRIVMSG '+channel in data:
                        #    where_message = channel #todo
                        if 'PRIVMSG ' + self.botName in data:
                            where_message = self.botName
                        else:
                            where_message = None

                    # If new message as last message: count +1.  
                    if data.find('PRIVMSG') != -1 and message == dict_users.get(name) \
                            and name not in list_floodfree:
                        dict_count[name] += int(1)

                    # print(__name__, "point 3.4", flush=True)
                    if data.find('PRIVMSG') != -1 and name not in list_floodfree:
                        dict_users[name] = message

                    # Message about flood and kick. 
                    # if data.find('PRIVMSG') != -1 and name not in list_floodfree:
                    #    for key in dict_count: 
                    #        if dict_count[key] == 3 and key != 'none':
                    #            self.send('PRIVMSG '+where_message+' :'+key+', Прекрати флудить!\r\n')
                    #            dict_count[key] += 1
                    #        elif dict_count[key] > 5 and key != 'none':
                    #            self.send('KICK '+channel+' '+key+' :Я же сказал не флуди!\r\n')
                    #            dict_count[key] = 0

                    # Out command.  
                    """
                    if data.find('PRIVMSG '+channel+' :!quit') != -1 and name == masterName:
                        self.send('PRIVMSG '+channel+' :Хорошо, всем счастливо оставаться!\r\n')
                        self.send('QUIT\r\n')
                        sys.exit()
                    """
                    # Messages by bot.  
                    """
                    if "PRIVMSG %s :!напиши "%(channel) in data or\
                       "PRIVMSG %s :!напиши "%(self.botName) in data and name == masterName:
                        mes_per_bot = message.split('!напиши ',1)[1]
                        self.send(mes_per_bot)
                    """
                    # print(__name__, "point 2.3", flush=True)
                    if self.enableother1:
                        """
                        if 'PRIVMSG ' + channel + ' :!где айпи' in data \
                                or 'PRIVMSG ' + self.botName + ' :!где айпи' in data:

                            if self.grantCommand(sent_by, communicationsLineName):
                                if 'PRIVMSG ' + channel + ' :!где айпи' in data:
                                    where_message_whois = channel

                                elif 'PRIVMSG ' + self.botName + ' :!где айпи' in data:
                                    where_message_whois = name

                                try:
                                    whois_ip = data.split('!где айпи ', 1)[1].split('\r', 1)[0].strip()
                                    get_whois = whois.whois(whois_ip)
                                    print(get_whois)
                                    country_whois = get_whois['country']
                                    city_whois = get_whois['city']
                                    address_whois = get_whois['address']

                                    if country_whois == None:
                                        country_whois = 'Unknown'
                                    if city_whois == None:
                                        city_whois = 'Unknown'
                                    if address_whois == None:
                                        address_whois = 'Unknown'

                                    whois_final_reply = ' \x02IP:\x02 ' + whois_ip + ' \x02Страна:\x02 ' + \
                                                        country_whois + ' \x02Адрес:\x02 ' + address_whois
                                    self.send('PRIVMSG ' + where_message_whois + ' :' + whois_final_reply + '\r\n')

                                except:
                                    print('get Value Error in whois service!')
                                    self.send('PRIVMSG ' + where_message_whois + ' :Ошибка! Вводите только IP адрес \
                                            из цифр, разделенных точками!\r\n')
                    # Info from link at channel
    
                    if self.enableother1 and self.titleEnabled:
                        if 'PRIVMSG %s :' % (channel) in data and '.png' not in data and '.jpg' not in data and '.doc' \
                                not in data and 'tiff' not in data and 'gif' not in data and '.jpeg' not in data and '.pdf' not in data:
                            if 'http://' in data or 'https://' in data or 'www.' in data:
                                if self.grantCommand(sent_by, communicationsLineName):
                                    try:
                                        self.send('PRIVMSG %s :%s\r\n' % (channel, link_title(data)))
                                    except requests.exceptions.ConnectionError:
                                        print('Ошибка получения Title (requests.exceptions.ConnectionError)')
                                        self.send('PRIVMSG ' + channel + ' :Ошибка ConnectionError\r\n')
                                    except:
                                        traceback.print_exc()
                                        # voting

                    # print(__name__, "point 2.2", flush=True)
                    t = time.time()
                    if self.enableother1:
                        if '!стоп опрос' in data and 'PRIVMSG' in data and name == masterName:
                            t2 = 0
                            print('счетчик опроса сброшен хозяином!')
                    if self.enableother1:
                        if 'PRIVMSG ' + channel + ' :!опрос ' in data and ip_user not in list_bot_not_work:
                            if self.grantCommand(sent_by, communicationsLineName):
                                if t2 == 0 or t > t2 + time_vote:
                                    if ' сек ' not in data:
                                        time_vote = 60
                                        # Make variable - text-voting-title form massage.
                                        message_voting = message.split('!опрос', 1)[1].strip()
                                    if ' сек ' in data:
                                        try:
                                            # Get time of timer from user message.
                                            time_vote = int(message.split('!опрос', 1)[1].split('сек', 1)[0].strip())
                                            # Make variable - text-voting-title form massage.
                                            message_voting = message.split('!опрос', 1)[1].split('сек', 1)[1].strip()
                                        except:
                                            time_vote = 60
                                            # Make variable - text-voting-title form massage.
                                            message_voting = message.split('!опрос', 1)[1].strip()

                                    if min_timer > time_vote or max_timer < time_vote:
                                        self.send('PRIVMSG %s :Ошибка ввода таймера голосования.\
                                                    Введите от %s до %s сек!\r\n' % (channel, min_timer, max_timer))
                                        continue

                                    t2 = time.time()
                                    count_vote_plus = 0
                                    count_vote_minus = 0
                                    vote_all = 0
                                    count_voting = 0
                                    list_vote_ip = []
                                    # Do null voting massiv.
                                    dict_voted = {}
                                    self.send('PRIVMSG %s :Начинается опрос: \"%s\". Опрос будет идти \
    %d секунд. Чтобы ответить "да", пишите: \"!да\" \
    ", чтобы ответить "нет", пишите: \"!нет\". Писать можно как открыто в канал,\
    так и в приват боту, чтобы голосовать анонимно \r\n' % (channel, message_voting, time_vote))
                                    list_vote_ip = []

                    # If find '!да' count +1.  
                    if self.enableother1:
                        if data.find('PRIVMSG ' + channel + ' :!да') != -1 or data.find(
                                'PRIVMSG ' + self.botName + ' :!да') != -1:
                            if ip_user not in list_vote_ip and t2 != 0:
                                count_vote_plus += 1
                                dict_voted[name] = 'yes'
                                list_vote_ip.append(ip_user)
                                # Make notice massage to votes user.
                                self.send('NOTICE ' + name + ' :Ваш ответ \"да\" учтен!\r\n')

                    # If find '!нет' count +1.  
                    if self.enableother1:
                        if data.find('PRIVMSG ' + channel + ' :!нет') != -1 or data.find(
                                'PRIVMSG ' + self.botName + ' :!нет') != -1:
                            if ip_user not in list_vote_ip and t2 != 0:
                                count_vote_minus += 1
                                dict_voted[name] = 'no'
                                list_vote_ip.append(ip_user)
                                # Make notice massage to votes user.
                                self.send('NOTICE ' + name + ' :Ваш ответ \"нет\" учтен!\r\n')

                    # If masterName self.send '!список голосования': self.send to him privat messag with dictonary Who How voted.  
                    if self.enableother1:
                        if data.find('PRIVMSG ' + self.botName + ' :!список опроса') != -1 and name == masterName:
                            for i in dict_voted:
                                self.send('PRIVMSG ' + masterName + ' : ' + i + ': ' + dict_voted[i] + '\r\n')

                    # Count how much was message in channel '!голосование'.  
                    if self.enableother1:
                        if data.find('PRIVMSG ' + channel + ' :!опрос') != -1 and t2 != 0:
                            count_voting += 1

                    print(__name__, "point 2.1", flush=True)
                    # If voting is not end, and users self.send '!голосование...': self.send message in channel.  
                    t4 = time.time()
                    if self.enableother1:
                        if data.find('PRIVMSG ' + channel + ' :!опрос') != -1 and t4 - t2 > 5:
                            t3 = time.time()
                            time_vote_rest_min = (time_vote - (t3 - t2)) // 60
                            time_vote_rest_sec = (time_vote - (t3 - t2)) % 60
                            if (time_vote - (t3 - t2)) > 0:
                                self.send('PRIVMSG %s : Предыдущий опрос: \"%s\" ещё не окончен, до окончания \
опроса осталось: %d мин %d сек\r\n \
' % (channel, message_voting, time_vote_rest_min, time_vote_rest_sec))

                    # Make variable message rusults voting.  
                    vote_all = count_vote_minus + count_vote_plus
                    voting_results = 'PRIVMSG %s : результаты опроса: \"%s\", "Да" ответило: %d \
                    человек(а), "Нет" ответило: %d человек(а), Всего ответило: %d человек(а) \
\r\n' % (channel, message_voting, count_vote_plus, count_vote_minus, vote_all)

                    # When voting End: self.send to channel ruselts and time count to zero.  
                    if t-t2 > time_vote and t2 != 0:
                        t2 = 0
                        self.send('PRIVMSG '+channel+' : Опрос окончен!\r\n')
                        self.send(voting_results)
                    """

                    print("calling maybe_print_news()", flush=True)
                    self.maybe_print_news(self.botName, data)
                    self.maybe_print_search(self.botName, data, sent_by)
                    if self.maybe_quotes(data, sent_by, communicationsLineName):
                        print("maybe_quotes() returned True, continuing loop", flush=True)
                        continue
                    else:
                        print("maybe_quotes() returned False", flush=True)
                    # if self.maybe_choice(self.botName, data): continue

                    #:nick!uname@addr.i2p PRIVMSG #ru :!курс
                    #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
                    where_mes_exc = communicationsLineName
                    # print(__name__, "point 4.1", flush=True)
                    if len(dataTokensDelimitedByWhitespace) > 3:
                        # print(__name__, "point 4.2", flush=True)

                        fe_msg = "FreiEx(GST): N/A"

                        line = " ".join(dataTokensDelimitedByWhitespace[3:])
                        is_in_private_query = where_mes_exc == self.botName
                        bot_mentioned = self.botName in line
                        commWithBot = is_in_private_query or bot_mentioned
                        # print(__name__, f"point 4.3, line: '{line}', commWithBot: '{commWithBot}'", flush=True)
                        try:
                            if 'курс' in line and commWithBot:
                                if self.grantCommand(sent_by, communicationsLineName):
                                    print(__name__, 'курс', flush=True)
                                    is_dialogue_with_master = False
                                    if where_mes_exc == self.botName:  # /query
                                        tokensNick1 = dataTokensDelimitedByWhitespace[0].split("!")
                                        tokensNick1 = tokensNick1[0].split(":")
                                        tokensNick1 = tokensNick1[1]
                                        where_mes_exc = tokensNick1
                                        is_dialogue_with_master = self.master_secret in line
                                        if is_dialogue_with_master: self.send(
                                            'PRIVMSG %s :%s\r\n' % (where_mes_exc, "hello, Master!"))
                                    print('курс куда слать будем:', where_mes_exc, "is_dialogue_with_master:",
                                          is_dialogue_with_master, flush=True)
                                    s = self.compose_markets_report(irc_markup_bool=True)
                                    self.send('PRIVMSG %s :\x033%s\r\n' % (where_mes_exc, s))
                                    print(__name__, "point 6.1", flush=True)
                                # print(__name__, "point 5.0", flush=True)
                                    

                        except:
                            # print(__name__, "point 5.1", flush=True)
                            tb.print_exc()
                            import sys
                            sys.stderr.flush()
                            raise ()


            except KeyboardInterrupt:
                raise
            except:
                import traceback as tb
                tb.print_exc()
                import sys
                sys.stderr.flush()
                print("self.irc_socket.close(), iterate", flush=True)
                try:
                    self.irc_socket.close()
                except KeyboardInterrupt as e:
                    raise e
                except:
                    import traceback as tb
                    tb.print_exc()
                    import sys
                    sys.stderr.flush()
                continue

    def pinger_of_server(self):
        print("spawned pinger_of_server, key: '%s'" % self.settings_key)
        while True:
            print("---new ping to server---")
            self.pong_received = False
            self.send('PING :' + str(time.time()) + '\r\n')
            time.sleep(180)
            if self.pong_received:
                continue
            else:
                print("ping to server timeout, closing socket, key: '%s'" % self.settings_key)
                self.irc_socket.close()
                print("exiting pinger of server, key: '%s'" % self.settings_key)
                return


def ircbich_init_and_loop(settings_key, connection_settings: dict, config):
    connection_props = connection_settings
    print(f'ircbich_init_and_loop settings_key="{settings_key}"')
    print(f'{settings_key}.parent pid: {os.getppid()}')
    print(f'{settings_key}.pid: {os.getpid()}')
    bot = IrcBich(settings_key, connection_settings, config)
    bot.login_and_loop()


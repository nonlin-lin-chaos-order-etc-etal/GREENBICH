# abstractbich.py

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
from helpers import get_pretty_json_string, shell, LOG_TRACE, TOTAL_WORLD_CAP_TRILLIONS_USD

from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
# pip3 install xlrd pandas
import pandas as pd


ENABLE_EXMO = True


class BichBot:
    WHEEL_SIZE = 5
    WHEEL_TIME_SECONDS = 60

    wheelGrants = {}

    old_news_cache = {}
    old_news_cache_index = {}

    # min & max timer for voting stuff.
    min_timer = 30
    max_timer = 300

    btcToRurFloat = "Unknown"

    def __init__(self, settings_key, connection_settings: dict, config):
        self.config = config
        self.connection_props = connection_settings
        self.settings_key = settings_key

        self.coinmarketcap_apikey = settings.settings('coinmarketcap_apikey')
        self.rapidapi_appkey = settings.settings('rapidapi_appkey')
        self.onlycmc = bool(self.connection_settings('onlycmc'))
        self.enableother1 = not self.onlycmc
        self.gnome1rur = float(settings.settings('gnome1_rur_float'))
        self.gnomeBtcTransaction1 = float(settings.settings('gnome_btc_transaction1_BTC_float'))  # BTC
        self.gnome_btc_amount2_BTC_float = float(settings.settings('gnome_btc_amount2_BTC_float'))  # BTC
        self.gnome1rur = self.gnome1rur + (
                (self.gnome_btc_amount2_BTC_float - self.gnomeBtcTransaction1) * 9500.0 * 65.0)
        self.measurementRur1 = self.gnome1rur
        self.measurementRur2 = self.gnome1rur

    def settings_by_key(self, key):
        return self.getconfig()[key]

    def getconfig(self):
        return self.config

    def fetch_sp500_index(self, irc_markup_bool):
        spglobal_hostid = settings.settings('spglobal_hostid')
        url = f'https://www.spglobal.com/spdji/en/idsexport/file.xls?hostIdentifier={spglobal_hostid}&redesignExport=true&languageId=1&selectedModule=PerformanceTableView&selectedSubModule=Daily&indexId=340'
        parameters = {}
        headers = {}
        try:
            print('fetch_sp500_index: get url=' + url, flush=True)
            session = Session()
            session.headers.update(headers)
            response = session.get(url, params=parameters)
            if response.status_code == 200:
                df = pd.read_excel(response.content)
                print(f"{__name__}: df:\n{df}")
                print(f"{__name__}: df.keys():\n{df.keys()}")
                print(f"{__name__}: col count:\n{len(df.keys())}")
                price_row_found = False
                price_col_found = False
                price_row_index = None
                price_col_index = None
                col_index = 0
                for col_name in df.keys():
                    col = df[col_name]
                    row_index = 0
                    for cell in col:
                        value = f'{cell}'.strip()
                        if value == 'Price Return\nS&P 500':
                            price_row_found = True
                            price_row_index = row_index
                            print("price_row_index: ", price_row_index)
                        else:
                            # print(f"val: '{value}'")
                            if value == 'Index Level':
                                price_col_found = True
                                price_col_index = col_index
                                print("price_col_index: ", price_col_index)
                        if price_row_found and price_col_found:
                            break
                        row_index = row_index + 1
                    if price_row_found and price_col_found:
                        break
                    col_index = col_index + 1
                if not price_row_found or not price_col_found:
                    return f'S&P500 Error: Unknown Format'
                else:
                    boldon = "\x02" if irc_markup_bool else "<b>"
                    boldoff = "\x02" if irc_markup_bool else "</b>"
                    return f'{boldon}S&P500 Index:{boldoff} {"{:0,.2f}".format(float(df.iloc[price_row_index, price_col_index]))}'
            else:
                reason = response.reason
                if reason is None:
                    reason = "(No message)"
                else:
                    if irc_markup_bool:
                        reason = reason[:10]
                return f'S&P500 Error: HTTP{response.status_code} {reason}'
        except KeyboardError:
            raise
        except (ConnectionError, Timeout, TooManyRedirects, BaseException) as e:
            import traceback as tb
            tb.print_exc()
            print(__name__, e, flush=True)
            return f'S&P500 Error: {e}'

    @staticmethod
    def get_create_ctx_from_mask2ctx(mask2ctx, mask):
        if mask in mask2ctx:
            ctx = mask2ctx[mask]
        else:
            ctx = {}
            mask2ctx[mask] = ctx
        return ctx

    @staticmethod
    def replace_nick_mask2ctx(mask2ctx, prev_mask, new_mask):
        print(__name__, "replace_nick_mask2ctx(, prev_mask='" + str(prev_mask) + "', new_mask=" + str(new_mask) + ")",
              flush=True)
        if prev_mask in mask2ctx:
            ctx = mask2ctx[prev_mask]
            del mask2ctx[prev_mask]
        else:
            ctx = {}
        mask2ctx[new_mask] = ctx

    def set_prev_msg(self, mask2ctx, mask, message):
        print(__name__, f"set_prev_msg enter, args: (, mask='{mask}', message='{message}')", flush=True)
        if mask is None or message is None:
            print(__name__, "set_prev_msg point 1, leaving", flush=True)
            return
        # print(__name__, "set_prev_msg point 2", flush=True)
        ctx = self.get_create_ctx_from_mask2ctx(mask2ctx, mask)
        # print(__name__, "set_prev_msg point 3", flush=True)
        ctx["prev_msg"] = message
        print(__name__, "set_prev_msg point 4, leaving", flush=True)

    def get_prev_msg(self, mask2ctx, mask):
        ctx = self.get_create_ctx_from_mask2ctx(mask2ctx, mask)
        return ctx["prev_msg"] if "prev_msg" in ctx else None

    @staticmethod
    def fmt2(your_numeric_value):
        return "{:0,.2f}".format(float(your_numeric_value))

    @staticmethod
    def get_interest_by_country(country):
        return pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True, inc_geo_code=False)

    @staticmethod
    def get_trending_searches(country_str, kwlist=None):
        return pytrends.trending_searches(pn=country_str).to_numpy()

    @staticmethod
    def convert_hex_to_ip(hex_value):
        a = int(hex_value[0:2], 16)
        b = int(hex_value[2:4], 16)
        c = int(hex_value[4:6], 16)
        d = int(hex_value[6:8], 16)
        return "%s.%s.%s.%s" % (str(a), str(b), str(c), str(d))

    @staticmethod
    def ru_latest_news_newsapi_org():
        apikey = option("newsapi_apikey")
        url = "http://newsapi.org/v2/top-headlines?country=ru&apiKey=%s" % apikey
        resp = requests.get(url=url)
        if resp.status_code != 200:
            return []
        # print (__file__, resp.text)
        rjson = resp.json()
        print(f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
        if "articles" in rjson:
            arts = rjson["articles"]
            if arts is None:
                return []
            return arts
        return []

    @staticmethod
    def ua_latest_news_newsapi_org():
        apikey = option("newsapi_apikey")
        url = "http://newsapi.org/v2/top-headlines?country=ua&apiKey=%s" % apikey
        resp = requests.get(url=url)
        if resp.status_code != 200:
            return []
        # print (__file__, resp.text)
        rjson = resp.json()
        print(f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
        if "articles" in rjson:
            arts = rjson["articles"]
            if arts is None:
                return []
            return arts
        return []

    @staticmethod
    def latest_news_google_news_ru():
        apikey = option("newsapi_apikey")
        url = "http://newsapi.org/v2/top-headlines?sources=google-news-ru&apiKey=%s" % apikey
        resp = requests.get(url=url)
        if resp.status_code != 200:
            return []
        # print (__file__, resp.text)
        rjson = resp.json()
        print(f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
        if "articles" in rjson:
            arts = rjson["articles"]
            if arts is None:
                return []
            return arts
        return []

    @staticmethod
    def format_currency(value):
        return "{:0,.2f}".format(float(value))

    @staticmethod
    def format_total_cap(total_market_cap_usd):
        total_market_cap_usd_t = float(total_market_cap_usd) / 1.0e12
        b = "$"+"{:0,.2f}T".format(total_market_cap_usd_t)
        total_str = "{:0,.2f}T".format(TOTAL_WORLD_CAP_TRILLIONS_USD)
        p = "{:0,.2f}".format(total_market_cap_usd_t / TOTAL_WORLD_CAP_TRILLIONS_USD * 100.0) + f'% of the world cap e.g. $'+f'{total_str}'
        return b + " (" + p + ')'

    def fetch_last_hour_new_news(self, old_news_cache=None, kwlist=None):
        array = self.get_trending_searches(country_str="russia", kwlist=kwlist)
        newer = []
        for lines in array:
            line = lines[0]
            if line is None:
                continue
            if line in old_news_cache:
                continue
            newer.append(line)
        return newer

    @staticmethod
    def is_runews_command(bot_nick, str_line):
        """
            :x!y@example.org PRIVMSG BichBot :msg text
        """
        dataTokensDelimitedByWhitespace = str_line.split(" ")
        # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
        # dataTokensDelimitedByWhitespace[1] PRIVMSG

        # dataTokensDelimitedByWhitespace[2] #ru
        #  OR
        # dataTokensDelimitedByWhitespace[2] BichBot

        # dataTokensDelimitedByWhitespace[3] :!курс
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
            dataTokensDelimitedByWhitespace) > 2 else None
        where_mes_exc = communicationsLineName
        if len(dataTokensDelimitedByWhitespace) > 3:
            line = " ".join(dataTokensDelimitedByWhitespace[3:])
            is_in_private_query = where_mes_exc == bot_nick
            bot_mentioned = bot_nick in line
            commWithBot = is_in_private_query or bot_mentioned
            return commWithBot and ("runews" in line or "руновости" in line) or (
                    "!runews" in line or "!руновости" in line)
        else:
            return False

    def is_uanews_command(self, bot_nick, str_line):
        #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
        dataTokensDelimitedByWhitespace = str_line.split(" ")
        # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
        # dataTokensDelimitedByWhitespace[1] PRIVMSG

        # dataTokensDelimitedByWhitespace[2] #ru
        # OR
        # dataTokensDelimitedByWhitespace[2] BichBot

        # dataTokensDelimitedByWhitespace[3] :!курс
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
            dataTokensDelimitedByWhitespace) > 2 else None
        where_mes_exc = communicationsLineName
        if len(dataTokensDelimitedByWhitespace) > 3:
            line = " ".join(dataTokensDelimitedByWhitespace[3:])
            is_in_private_query = where_mes_exc == bot_nick
            bot_mentioned = bot_nick in line
            commWithBot = is_in_private_query or bot_mentioned
            return commWithBot and ("uanews" in line or "укрновости" in line) or (
                    "!uanews" in line or "!укрновости" in line)
        else:
            return False

    def is_search_command(self, bot_nick, str_line):
        #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
        dataTokensDelimitedByWhitespace = str_line.split(" ")
        # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
        # dataTokensDelimitedByWhitespace[1] PRIVMSG

        # dataTokensDelimitedByWhitespace[2] #ru
        # OR
        # dataTokensDelimitedByWhitespace[2] BichBot

        # dataTokensDelimitedByWhitespace[3] :!курс
        #:server.org 332 GreenBich #ru :поисковик: search.org
        if len(dataTokensDelimitedByWhitespace) < 4: return False
        if dataTokensDelimitedByWhitespace[1] != "PRIVMSG": return False
        communicationsLineName = dataTokensDelimitedByWhitespace[2]
        where_mes_exc = communicationsLineName
        line = " ".join(dataTokensDelimitedByWhitespace[3:])
        is_in_private_query = where_mes_exc == bot_nick
        bot_mentioned = bot_nick in line
        commWithBot = is_in_private_query or bot_mentioned
        return commWithBot and ("search" in line or "поиск" in line) or ("!search" in line or "!поиск" in line)

    def is_search_command2(self, bot_nick, str_line):
        #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
        dataTokensDelimitedByWhitespace = self.data.split(" ")
        # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
        # dataTokensDelimitedByWhitespace[1] PRIVMSG

        # dataTokensDelimitedByWhitespace[2] #ru
        # OR
        # dataTokensDelimitedByWhitespace[2] BichBot

        # dataTokensDelimitedByWhitespace[3] :!курс
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
            dataTokensDelimitedByWhitespace) > 2 else None
        where_mes_exc = communicationsLineName
        if len(dataTokensDelimitedByWhitespace) > 3:
            line = " ".join(dataTokensDelimitedByWhitespace[3:])
            is_in_private_query = where_mes_exc == bot_nick
            bot_mentioned = bot_nick in line
            commWithBot = is_in_private_query or bot_mentioned
            return commWithBot and ("search2" in line or "поиск2" in line) or ("!search2" in line or "!поиск2" in line)
        else:
            return False

    @staticmethod
    def print_wheel(wheel):
        s = "{[\r\n"
        for dt in wheel['datetimes']:
            s += "  " + str(dt) + "\r\n"
        s += "]}"
        return s

    def grantCommand(self, sent_by, commLine):
        sent_by = 'anyone'  # nicks don't matter as ddoser might use multiple random nicks
        if not sent_by in self.wheelGrants:
            wheel = {}
            self.wheelGrants[sent_by] = wheel
            wheel['datetimes'] = [datetime.datetime.now(pytz.utc)]
            print(__name__, f"command_granted clause 1, wheel: {self.print_wheel(wheel)}")
            return True
        else:
            wheel = self.wheelGrants[sent_by]
            datetimes = wheel['datetimes']

            while len(datetimes) > self.WHEEL_SIZE:
                datetimes = datetimes[1:]
            wheel['datetimes'] = datetimes
            if len(datetimes) < self.WHEEL_SIZE:
                print(__name__, f"command_granted clause 3, wheel: {self.print_wheel(wheel)}")
                datetimes.append(datetime.datetime.now(pytz.utc))
                wheel['datetimes'] = datetimes
                return True
            granted = datetimes[0] < datetime.datetime.now(pytz.utc) - datetime.timedelta(
                seconds=self.WHEEL_TIME_SECONDS)
            if not granted:
                print(__name__, f"command not granted, wheel: {self.print_wheel(wheel)}")
                if "floodDetectedSentTime" in wheel:
                    floodDetectedSentTime = wheel["floodDetectedSentTime"]
                else:
                    floodDetectedSentTime = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)

                if floodDetectedSentTime < datetime.datetime.now(pytz.utc) - datetime.timedelta(
                        seconds=self.WHEEL_TIME_SECONDS):
                    wheel["floodDetectedSentTime"] = datetime.datetime.now(pytz.utc)
                    self.send(f'PRIVMSG {commLine} :Flood detected, ignoring.\r\n')
            else:
                print(__name__, f"command_granted clause 2, wheel: {self.print_wheel(wheel)}")
                datetimes.append(datetime.datetime.now(pytz.utc))
                datetimes = datetimes[1:]
                wheel['datetimes'] = datetimes
            return granted

    def connection_settings(self, key2):
        return self.connection_settings_dict()[key2]

    def connection_option(self, key2):
        return self.connection_settings(key2)

    def connection_setting_or_None(self, key2):
        dic = self.connection_settings_dict()
        return dic[key2] if key2 in dic else None

    def connection_settings_dict(self):
        return self.connection_props

    def web_search(self, query_str, number_of_results):
        pageNumber = 1
        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/WebSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
              (urlencode(query_str), str(pageNumber), str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1', "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
                   "X-RapidAPI-Key": self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ws_resp", json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None

    """
    def web_search2(self, query_str, number_of_results):
        search2RestClient = Search2RestClient(option("dataforseo_api_login"), option("dataforseo_api_password"))
        resp_json = search2RestClient.get(path)

        pageNumber = 1
        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/WebSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
              (urlencode(query_str), str(pageNumber), str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1', "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
                   "X-RapidAPI-Key": self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ws_resp", json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None
    """

    def news_search_ctxwebsrch(self, query_str, number_of_results):
        pageNumber = 1
        url = "https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/NewsSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
              (urlencode(query_str), str(pageNumber), str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1', "X-RapidAPI-Host": "contextualwebsearch-websearch-v1.p.rapidapi.com",
                   "X-RapidAPI-Key": self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ns_resp", json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None

    def sendmsg(self, to_addr, msg):
        self.send('PRIVMSG %s :%s\r\n' % (to_addr, msg))

    """
    def print_new_news_googletrends(self, to_addr, kwlist=None):
        old_news_cache = self.old_news_cache
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache = {}
            old_news_cache[to_addr] = cache
        array_of_strings = self.fetch_last_hour_new_news(cache, kwlist=kwlist)
        cnt = self.get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for line in array_of_strings:
            if line is None: continue
            resultUrl = self.news_search(line, 1)
            self.sendmsg(to_addr, "%s: %s %s" % (str((index + 1)), line, resultUrl if resultUrl else ""))
            cache[line] = {"recently_sent": True}
            sent = sent + 1
            index = index + 1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")
    """

    def print_new_runews_newsapi_org(self, to_addr):
        old_news_cache = self.old_news_cache
        old_news_cache_index = self.old_news_cache_index
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache = {}
            old_news_cache[to_addr] = cache
        if to_addr in old_news_cache_index:
            cache_index = old_news_cache_index[to_addr]
        else:
            cache_index = []
            old_news_cache_index[to_addr] = cache_index
        arts = self.ru_latest_news_newsapi_org() + self.latest_news_google_news_ru()

        cnt = self.get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for a in arts:
            if a is None: continue
            url = a["url"]
            if url in cache: continue
            self.sendmsg(to_addr, "%s %s" % (str(url), str(a["title"])))
            cache[url] = True
            cache_index.append(url)
            while len(cache_index) > 100:
                first_url = cache_index.pop(0)
                del cache[first_url]
            sent = sent + 1
            index = index + 1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")

    def print_new_uanews_newsapi_org(self, to_addr):
        old_news_cache = self.old_news_cache
        old_news_cache_index = self.old_news_cache_index
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache = {}
            old_news_cache[to_addr] = cache
        if to_addr in old_news_cache_index:
            cache_index = old_news_cache_index[to_addr]
        else:
            cache_index = []
            old_news_cache_index[to_addr] = cache_index
        arts = self.ua_latest_news_newsapi_org()

        cnt = self.get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for a in arts:
            if a is None: continue
            url = a["url"]
            if url in cache: continue
            self.sendmsg(to_addr, "%s %s" % (str(url), str(a["title"])))
            cache[url] = True
            cache_index.append(url)
            while len(cache_index) > 100:
                first_url = cache_index.pop(0)
                del cache[first_url]
            sent = sent + 1
            index = index + 1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")

    def maybe_print_news(self, bot_nick, str_incoming_line):
        sent_by = "unknown_sentBy"
        dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
            dataTokensDelimitedByWhitespace) > 2 else None
        if self.is_runews_command(bot_nick, str_incoming_line):
            if self.grantCommand(sent_by, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(
                    dataTokensDelimitedByWhitespace) >= 4 else ""
                if line.startswith(":"): line = line[1:]
                print("'%s'" % line)
                p = line.find("news")
                if p == -1:
                    p = line.find("новости")
                    if p == -1:
                        pass
                    else:
                        p = p + len("новости")
                        line = line[p:].strip()
                        print("'%s'" % line)
                        if line != '': kwlist.append(line)
                else:
                    p = p + len("news")
                    line = line[p:].strip()
                    print("'%s'" % line)
                    if line != '': kwlist.append(line)
                if len(kwlist) == 0:
                    self.print_new_runews_newsapi_org(where_mes_exc)
                else:
                    resultUrl = self.news_search_ctxwebsrch(kwlist[0], 1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Новостей не найдено"))
        if self.is_uanews_command(bot_nick, str_incoming_line):
            if self.grantCommand(sent_by, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(
                    dataTokensDelimitedByWhitespace) >= 4 else ""
                if line.startswith(":"): line = line[1:]
                print("'%s'" % line)
                p = line.find("news")
                if p == -1:
                    p = line.find("новости")
                    if p == -1:
                        pass
                    else:
                        p = p + len("новости")
                        line = line[p:].strip()
                        print("'%s'" % line)
                        if line != '': kwlist.append(line)
                else:
                    p = p + len("news")
                    line = line[p:].strip()
                    print("'%s'" % line)
                    if line != '': kwlist.append(line)
                if len(kwlist) == 0:
                    self.print_new_uanews_newsapi_org(where_mes_exc)
                else:
                    resultUrl = self.news_search_ctxwebsrch(kwlist[0], 1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Новостей не найдено"))

    def write_quotes(self):
        print(__name__, "writing quotes.json")
        with open('quotes.json', 'w') as myfile:
            myfile.write(get_pretty_json_string(self.quotes_array))
        shell("echo \"begin...\" && cp -v ~user/vcs/greenbich-runtime/quotes.json /DK/hutor_i2p_htdocs/ && echo \"exit status: $?\" && ls -alh /DK/hutor_i2p_htdocs/ && echo \"exit status: $?\" && echo \"done.\"")


    def read_quotes(self):
        # read file
        # try:
        print(__name__, "reading quotes.json")
        with open('quotes.json', 'r') as myfile:
            quotes_array = myfile.read()
        self.quotes_array = json.loads(quotes_array)
        # except:
        #    traceback.print_exc()
        #    print(__name__, "warning: setting empty quotes_array")
        #    quotes_array = []

    # tok1[0] :nick!uname@addr.i2p
    # tok1[1] PRIVMSG

    # tok1[2] #ru
    # OR
    # tok1[2] BichBot

    # tok1[3] :!!aq/!!q
    # tok1[4:] tokens
    def print_quote(self, tok1):
        at = tok1[2]
        query = " ".join(tok1[4:]).strip()
        if len(query) == 0:
            # print a random quote
            self.read_quotes()
            from random import choice
            q = choice(self.quotes_array)
            poster = q['posted-by'].split("!")[0]
            self.sendmsg(at, f"[{q['id']}] {q['text']} ({poster} at {q['date-posted']})")
            return

        try:
            num = int(query)
        except ValueError:
            # self.search_for_quote(query)
            query = query.lower()
            self.read_quotes()
            for q in self.quotes_array:
                msg = q["text"]
                if query in msg.lower():
                    poster = q['posted-by'].split("!")[0]
                    self.sendmsg(at, f"[{q['id']}] {msg} ({poster} at {q['date-posted']})")
                    return
            return
        if num > 0:
            num = num - 1
            self.read_quotes()
            if num >= len(self.quotes_array):
                self.sendmsg(at, f"Max quote number: {len(self.quotes_array)}.")
            else:
                q = self.quotes_array[num]
                poster = q['posted-by'].split("!")[0]
                self.sendmsg(at, f"[{num + 1}] {q['text']} ({poster} at {q['date-posted']})")
        else:
            self.sendmsg(at, f"Need a positive int.")

    def add_quote(self, tok1, communicationsLineName):
        self.read_quotes()
        length = len(self.quotes_array)
        for i in range(length):
            q = self.quotes_array[i]
            if not "id" in q:
                q["id"] = i + 1
        quote = " ".join(tok1[4:])
        quoteId = length + 1
        self.quotes_array.append({
            "id": quoteId,
            "posted-by": tok1[0][1:],
            "text": quote,
            "date-posted": str(datetime.datetime.now(pytz.utc))
        })
        at = tok1[2]
        self.write_quotes()
        if self.is_compact_for_channel(communicationsLineName):
            if len(quote) >= 15:
                report = f"Quote [{quoteId}] added: '{quote[:7]}...{quote[-7:]}'."
            else:
                report = f"Quote [{quoteId}] added: '{quote}'."
        else:
            report = f"Quote added: [{quoteId}] {quote}"
        self.sendmsg(at, report)

    def maybe_quotes(self, str_incoming_line, sent_by, commLineName):
        tok1 = str_incoming_line.split(" ")
        if len(tok1) < 3: return False
        if tok1[1] != "PRIVMSG": return False
        cmdtok = tok1[3].split(":")
        if len(cmdtok) < 2: return False
        cmd = cmdtok[1]
        if not cmd.startswith("!!"): return False
        if cmd == "!!q":
            if self.grantCommand(sent_by, commLineName):
                self.print_quote(tok1)
                return True
        #if cmd == "!!aq":
        #    if self.grantCommand(sent_by, commLineName):
        #        self.add_quote(tok1, commLineName)
        #        return True
        return False

    def help_make_choice(self, message):
        if ' или ' in message:
            s = message.split(' или ')
            if len(s) > 1:
                return choice(s).strip('?')
        if message.endswith('?'):
            return choice(['да', 'нет'])
        return None

    def maybe_choice(self, bot_nick, str_incoming_line):
        tok1 = str_incoming_line.split(" ")
        if len(tok1) < 3: return False
        if tok1[1] != "PRIVMSG": return False
        message = " ".join(tok1[3:])[1:]
        if not bot_nick in message: return False
        reply = self.help_make_choice(message)
        if not reply: return False
        at = tok1[2]
        self.sendmsg(at, reply)
        return True

    def maybe_print_search(self, bot_nick, str_incoming_line, sent_by):
        dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
            dataTokensDelimitedByWhitespace) > 2 else None
        if self.is_search_command(bot_nick, str_incoming_line):
            if self.grantCommand(sent_by, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(
                    dataTokensDelimitedByWhitespace) >= 4 else ""
                if line.startswith(":"): line = line[1:]
                print("'%s'" % line)
                p = line.find("search")
                if p == -1:
                    p = line.find("поиск")
                    if p == -1:
                        pass
                    else:
                        p = p + len("поиск")
                        line = line[p:].strip()
                        print("'%s'" % line)
                        if line != '': kwlist.append(line)
                else:
                    p = p + len("search")
                    line = line[p:].strip()
                    print("'%s'" % line)
                    if line != '': kwlist.append(line)
                if len(kwlist) == 0:
                    self.sendmsg(where_mes_exc, "Чего синьорам найти?")
                else:
                    resultUrl = self.web_search(kwlist[0], 1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Результатов не найдено"))

    """
    def maybe_print_search2(self, bot_nick, str_incoming_line, sent_by, communicationsLineName):
        if self.is_search_command2(bot_nick, str_incoming_line):
            if self.grantCommand(sent_by, communicationsLineName):
                kwlist = []
                dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
                communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(
                    dataTokensDelimitedByWhitespace) > 2 else None
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(
                    dataTokensDelimitedByWhitespace) >= 4 else ""
                if line.startswith(":"): line = line[1:]
                print("'%s'" % line)
                p = line.find("search2")
                if p == -1:
                    p = line.find("поиск2")
                    if p == -1:
                        pass
                    else:
                        p = p + len("поиск2")
                        line = line[p:].strip()
                        print("'%s'" % line)
                        if line != '': kwlist.append(line)
                else:
                    p = p + len("search2")
                    line = line[p:].strip()
                    print("'%s'" % line)
                    if line != '': kwlist.append(line)
                if len(kwlist) == 0:
                    self.sendmsg(where_mes_exc, "Чего синьорам найти?")
                else:
                    resultUrl = self.web_search2(kwlist[0], 1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Результатов не найдено"))
    """

    def get_news_count_for_channel(self, commLineName):
        props = self.channelsProps[commLineName] if commLineName in self.channelsProps else None
        if props is None: return 10
        return props['news_count'] if 'news_count' in props else 3

    def is_compact_for_channel(self, commLineName):
        COMPACT_DEFAULT = True
        props = self.channelsProps[commLineName] if commLineName in self.channelsProps else None
        modes = props['modes'] if props is not None and 'modes' in props else None
        return modes['compact'] if modes is not None and 'compact' in modes else COMPACT_DEFAULT

    def compose_markets_report(self, irc_markup_bool=False):
        boldon = "\x02" if irc_markup_bool else "<b>"
        boldoff = "\x02" if irc_markup_bool else "</b>"
        separ = " | " if irc_markup_bool else """
"""
        separ2 = " | " if irc_markup_bool else """

"""
        try:
            # This example uses Python 2.7 and the python-request library.

            url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
            parameters = {
                'symbol': 'BTC,ETH,DASH,DOGE,ZEC,NEAR,XMR',
                'convert': 'USD'
            }
            headers = {
                'Accepts': 'application/json',
                'X-CMC_PRO_API_KEY': self.coinmarketcap_apikey,
            }

            session = Session()
            session.headers.update(headers)

            rate_cmc_str = f"{separ2}CoinMarketCap:{separ2}"
            
            try:
                print('!курс session.get url=' + url)
                response = session.get(url, params=parameters)
                if LOG_TRACE: print("cmc.text:", response.text)
                cmc = json.loads(response.text)
                # if LOG_TRACE: print(f"cmc.json: {get_pretty_json_string(cmc)}")
                btc_usd = cmc["data"]["BTC"]["quote"]["USD"]["price"]
                eth_usd = cmc["data"]["ETH"]["quote"]["USD"]["price"]
                dash_usd = cmc["data"]["DASH"]["quote"]["USD"]["price"]
                doge_usd = cmc["data"]["DOGE"]["quote"]["USD"]["price"]
                zec_usd = cmc["data"]["ZEC"]["quote"]["USD"]["price"]
                near_usd = cmc["data"]["NEAR"]["quote"]["USD"]["price"]
                xmr_usd = cmc["data"]["XMR"]["quote"]["USD"]["price"]
                btc_usd_str = str(self.format_currency(btc_usd))
                eth_usd_str = str(self.format_currency(eth_usd))
                dash_usd_str = str(self.format_currency(dash_usd))
                doge_usd_str = str(self.format_currency(doge_usd))
                zec_usd_str = str(self.format_currency(zec_usd))
                near_usd_str = str(self.format_currency(near_usd))
                xmr_usd_str = str(self.format_currency(xmr_usd))

                rate_cmc_str += f'{boldon}BTC/USD:{boldoff} {btc_usd_str}{separ}{boldon}ETH/USD:{boldoff} {eth_usd_str}{separ}{boldon}NEAR/USD:{boldoff} {near_usd_str}{separ}{boldon}DASH/USD:{boldoff} {dash_usd_str}{separ}{boldon}ZEC/USD:{boldoff} {zec_usd_str}{separ}{boldon}XMR/USD:{boldoff} {xmr_usd_str}'  # \x02DOGE/USD:\x02 {doge_usd_str}

            except (ConnectionError, Timeout, TooManyRedirects) as e:
                traceback.print_exc()
                rate_cmc_str += str(e)

            RUR_SYMBOL = "RUB"

            parameters = {
                'symbol': 'DOGE',
                'convert': RUR_SYMBOL
            }

            try:
                print('!курс rur session.get url=' + url)
                response = session.get(url, params=parameters)
                cmc = json.loads(response.text)
                if LOG_TRACE: print("cmc_rur:", cmc)
                doge_rur = cmc["data"]["DOGE"]["quote"][RUR_SYMBOL]["price"]
                doge_rur_str = str(self.format_currency(doge_rur))

                rate_cmc_str += f'{separ}{boldon}DOGE/RUR:{boldoff} {doge_rur_str}'
            except (ConnectionError, Timeout, TooManyRedirects) as e:
                traceback.print_exc()
                rate_cmc_str += str(e)

            url = 'https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest'
            parameters = {}

            try:
                print('!cmc-global-metrics session.get url=' + url, flush=True)
                response = session.get(url, params=parameters)
                cmc = json.loads(response.text)
                if LOG_TRACE: print("cmc global-metrics:", cmc)
                total_market_cap_usd = cmc["data"]["quote"]["USD"]["total_market_cap"]
                total_market_cap_str = str(self.format_total_cap(total_market_cap_usd))

                rate_cmc_str += f'{separ2}{boldon}Total Crypto Cap:{boldoff} {total_market_cap_str}.{separ2}'

            except (ConnectionError, Timeout, TooManyRedirects) as e:
                import traceback as tb
                tb.print_exc()
                rate_cmc_str += f"{separ2}{e}{separ2}"

            # docs: https://docs.kuna.io/docs/%D0%BF%D0%BE%D1%81%D0%BB%D0%B5%D0%B4%D0%BD%D0%B8%D0%B5-%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D0%B5-%D0%BF%D0%BE-%D1%80%D1%8B%D0%BD%D0%BA%D1%83-%D1%82%D0%B8%D0%BA%D0%B5%D1%80%D1%8B
            """
        [
	      [
	        "btcuah",   # символ рынка [0]
	        208001,     # цена BID [1]
	        11200693,   # объем ордербука BID 2
	        208499,     # цена ASK [3]
	        29.255569,  # объем ордербука ASK 4
	        5999,       # изменение цены за 24 часа в котируемой валюте 5
	        -2.8,       # изменение цены за 24 часа в процентах 6
	        208001,     # последняя цена 7
	        11.3878,    # объем торгов за 24 часа в базовой валюте VOL24 [8]
	        215301,     # максимальная цена за 24 часа 9
	        208001      # минимальная цена за 24 часа 10
	      ]
	    ]
	    """
            url = 'https://api.kuna.io/v3/tickers?symbols=everusdt'
            parameters = {
            }
            headers = {
                'Accepts': 'application/json',
            }

            try:
                print('!курс session.get url=' + url, flush=True)
                response = session.get(url, params=parameters)
                retval = json.loads(response.text)
                if LOG_TRACE: print("kuna:", retval)
                bid = retval[0][1]
                ask = retval[0][3]
                vol24 = retval[0][8]
                bid_str = str(self.format_currency(bid))
                ask_str = str(self.format_currency(ask))
                vol24_str = str(self.format_currency(vol24))

                kuna_str = f'Kuna.io {boldon}EVER/USDT{boldoff}: BID {bid_str} ASK {ask_str} VOL24 {vol24_str}'
            except (ConnectionError, Timeout, TooManyRedirects) as e:
                print(__name__, e, flush=True)
                kuna_str = 'Kuna.io error: ' + str(e)

            sp500index_str = self.fetch_sp500_index(irc_markup_bool)

            btcToUsdFloat = None
            btcToRurFloat = None

            try:
                import urllib.request
                url = "https://api.freiexchange.com/public/ticker/GST"
                print("querying %s" % (url,), flush=True)
                req = urllib.request.Request(
                    url,
                    data=None,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                    }
                )
                fe_ticker = urllib.request.urlopen(req).read()
                # urllib.request.urlopen(url).read()
                print("fe_ticker (a response):", fe_ticker, flush=True)
                fe_ticker = json.loads(fe_ticker)
                if "GST_BTC" in fe_ticker:
                    gst_resp = fe_ticker["GST_BTC"][0]
                    volume24h_gst = float(gst_resp["volume24h"])
                    volume24h_btc_lit = gst_resp["volume24h_btc"]
                    volume24h_btc = float(volume24h_btc_lit)
                    volume24h_rur = float(self.btcToRurFloat) * volume24h_btc if \
                        self.btcToRurFloat != "Unknown" \
                        else None
                    last_lit = gst_resp["last"]
                    last = float(last_lit)
                    last_rur = float(self.btcToRurFloat) * last if \
                        self.btcToRurFloat != "Unknown" \
                        else None
                    highestBuy_lit = gst_resp["highestBuy"]
                    highestBuy = float(highestBuy_lit)
                    highestBuy_rur = float(self.btcToRurFloat) * highestBuy if \
                        self.btcToRurFloat != "Unknown" \
                        else None
                    lowestSell_lit = gst_resp["lowestSell"]
                    lowestSell = float(lowestSell_lit)
                    lowestSell_rur = float(self.btcToRurFloat) * lowestSell if \
                        self.btcToRurFloat != "Unknown" \
                        else None

                    # fe_msg = "FreiEx(GST): VOL24:"+fmt2(volume24h_rur)+"RUR LAST:"+fmt2(last_rur)+"RUR S:"+fmt2(lowestSell_rur)+"RUR B:"+fmt2(highestBuy_rur)+"RUR"
                    fe_msg = f"FreiExchange.com {boldon}GST/BTC:{boldoff} VOL24:{volume24h_btc_lit}BTC LAST:{last_lit} S:{lowestSell_lit} B:{highestBuy_lit}"
                else:
                    fe_msg = "FreiExchange.com error"
            except KeyboardInterrupt:
                raise
            except BaseException as ex:
                print("ex:", str(ex), flush=True)
                traceback.print_exc()
                sys.stdout.flush()
                sys.stderr.flush()
            print("after frei exchange poll", flush=True)

            # exmo and frei
            if ENABLE_EXMO:
                try:
                    import urllib.request
                    url = "http://api.exmo.com/v1/ticker/"
                    print("querying %s" % (url,), flush=True)
                    exmo_ticker = json.loads(urllib.request.urlopen(url).read())
                    print(f"exmo_ticker: {exmo_ticker}")
                    # "USD_RUB":{"buy_price":"63.520002", "sell_price":"63.7", "last_trade":"63.678587", "high":"64.21396756", "low":"63.35", "avg":"63.78778311", "vol":"281207.5729779", "vol_curr":"17906900.90093241", "updated":1564935589 }
                    # "BTC_RUB":{"buy_price":"692674.53013854","sell_price":"694990", "last_trade":"693302.09","high":"700000","low":"675000.00100102", "avg":"687445.89449801","vol":"223.90253022", "vol_curr":"155232092.15894149", "updated":1564935590 }
                    # exmo_BTC_RUB_json = exmo_ticker["BTC_RUB"]
                    """
                    exmo_BTC_USD_json = exmo_ticker[
                        "BTC_USD"] if not 'error' in exmo_ticker else None
                    exmo_ETH_USD_json = exmo_ticker[
                        "ETH_USD"] if not 'error' in exmo_ticker else None
                    """
                    exmo_TONCOIN_USD_json = exmo_ticker[
                        "TONCOIN_USDT"] if not 'error' in exmo_ticker else None
                    # exmo_USD_RUB_json = exmo_ticker["USD_RUB"]

                    """
                    exmo_BTC_USD_sell_price = exmo_BTC_USD_json[
                        "sell_price"] if not 'error' in exmo_ticker else None
                    btcToUsdFloat = float(
                        exmo_BTC_USD_sell_price) if not 'error' in exmo_ticker else None
                    btcToRurFloat = float(exmo_ticker["BTC_RUB"][
                                              "buy_price"]) if not 'error' in exmo_ticker else None
                    """

                    if 'error' in exmo_ticker:
                        exmos = f"Exmo.me error: {exmo_ticker['error']}"
                    else:
                        """
                        ircProtocolDisplayText_exmo = 'Exmo.me: ' + \
                                                      'BTC/USD S ' + str(
                            self.format_currency(exmo_BTC_USD_sell_price)) + ' B ' + str(
                            self.format_currency(exmo_BTC_USD_json["buy_price"])) + f"{separ}" + \
                                                      'ETH/USD S ' + str(
                            self.format_currency(
                                exmo_ETH_USD_json["sell_price"])) + ' B ' + str(
                            self.format_currency(exmo_ETH_USD_json["buy_price"])) + f"{separ}" + \
                                                      "BTC/RUR S " + str(
                            self.format_currency(
                                float(exmo_ticker["BTC_RUB"]["sell_price"]))) + ' B ' + str(
                            self.format_currency(
                                float(exmo_ticker["BTC_RUB"]["buy_price"]))) + "."
                        """
                        tons = self.format_currency(exmo_TONCOIN_USD_json["sell_price"])
                        tonb = self.format_currency(exmo_TONCOIN_USD_json["buy_price"])
                        sexmo = f'Exmo.me {boldon}TONCOIN/USDT:{boldoff} S {tons} B {tonb}'
                except (ConnectionError, Timeout, TooManyRedirects, URLError) as e:
                    print(__name__, e, flush=True)
                    sexmo = f"Exmo.me error: {e}"

                """
                # btcToRurFloat = None
                is_dialogue_with_master = False
                if self.btcToRurFloat != "Unknown" and is_dialogue_with_master:
                    self.gnome2rur = float(self.btcToRurFloat) * float(self.gnome_btc_amount2_BTC_float)
                    self.gnomeDeltaGlobalRur = self.gnome2rur - self.gnome1rur
                    self.measurementRur1 = self.measurementRur2
                    self.measurementRur2 = self.gnome2rur
                    self.gnomeDeltaLocalRur = self.measurementRur2 - self.measurementRur1
                    print("gnome_btc_amount2_BTC_float:", self.gnome_btc_amount2_BTC_float,
                          "gnome2rur:", self.gnome2rur, "btcToRurFloat:", self.btcToRurFloat,
                          "gnomeDeltaGlobalRur:", self.gnomeDeltaGlobalRur, "measurementRur1:",
                          self.measurementRur1, "measurementRur2:", self.measurementRur2,
                          "gnomeDeltaLocalRur:", self.gnomeDeltaLocalRur, flush=True)
                    gnomeHodlDeltaStr = "Всего выросло: %s%s руб. Локально: %s%s руб. — %s" % (
                        ("+" if self.gnomeDeltaGlobalRur >= 0 else ""),
                        self.format_currency(self.gnomeDeltaGlobalRur),
                        ("+" if self.gnomeDeltaLocalRur >= 0 else ""),
                        self.format_currency(self.gnomeDeltaLocalRur),
                        ("растёт денежка, растёт!" if self.gnomeDeltaLocalRur >= 0
                         else "убытки-с =( читаем книжку! http://knijka.i2p/"))
                else:
                    gnomeHodlDeltaStr = "??? руб."
                """

            # Bitcoin.com Markets API
            # Coming soon
            # https://developer.bitcoin.com/

            exmo_postfix = f"{separ}{sexmo}" if ENABLE_EXMO else ""
            s = f'{sp500index_str}{separ2}{fe_msg}{rate_cmc_str}{kuna_str}{exmo_postfix}'  # , gnomeHodlDeltaStr
        except BaseException as e:
            print(__name__, e, flush=True)
            s = f'Error: {e}'
        print(__name__, "returning composed market report:", s, flush=True)
        return s


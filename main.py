from random import choice
import traceback as tb
import traceback
import socket
import pytz
# import socks
import sys
import time
import requests
import settings
import translate_krzb
import whois
import json
from urllib.parse import unquote
from urllib.parse import quote as urlencode
from settings import settings as option
from threading import Thread
import traceback
import datetime

LOG_TRACE = True

ENABLE_EXMO = False


def get_pretty_json_string(value):
    return json.dumps(value, indent=4, sort_keys=True, ensure_ascii=False)


def settings_by_key(key):
    return getconfig()[key]


def getconfig():
    return config  # TODO use local contexts instead of globals


def get_create_ctx_from_mask2ctx(mask2ctx, mask):
    if mask in mask2ctx:
        ctx = mask2ctx[mask]
    else:
        ctx = {}
        mask2ctx[mask] = ctx
    return ctx

def replace_nick_mask2ctx(mask2ctx, prev_mask, new_mask):
    print(__name__, "replace_nick_mask2ctx(, prev_mask='"+str(prev_mask)+"', new_mask="+str(new_mask)+")", flush=True)
    if prev_mask in mask2ctx:
        ctx = mask2ctx[prev_mask]
        del mask2ctx[prev_mask]
    else:
        ctx = {}
    mask2ctx[new_mask]=ctx

def set_prev_msg(mask2ctx, mask, message):
    print(__name__, f"set_prev_msg enter, args: (, mask='{mask}', message='{message}')", flush=True)
    if mask is None or message is None:
        print(__name__, "set_prev_msg point 1, leaving", flush=True)
        return
    #print(__name__, "set_prev_msg point 2", flush=True)
    ctx = get_create_ctx_from_mask2ctx(mask2ctx, mask)
    #print(__name__, "set_prev_msg point 3", flush=True)
    ctx["prev_msg"]=message
    print(__name__, "set_prev_msg point 4, leaving", flush=True)

def get_prev_msg(mask2ctx, mask):
    ctx = get_create_ctx_from_mask2ctx(mask2ctx, mask)
    return ctx["prev_msg"] if "prev_msg" in ctx else None

def fmt2(your_numeric_value):
    return "{:0,.2f}".format(float(your_numeric_value))

from pytrends.request import TrendReq
while True:
    try:
        pytrends = TrendReq(hl='ru-RU', tz=360)
        break
    except KeyboardInterrupt as e:
        raise e
    except:
        traceback.print_exc()
        TIME_TO_SLEEP_SECONDS = 1
        print ( "sleeping %s seconds" % str(TIME_TO_SLEEP_SECONDS) )
        time.sleep(TIME_TO_SLEEP_SECONDS)
        continue

def get_interest_by_country(country):
    return pytrends.interest_by_region(resolution='COUNTRY', inc_low_vol=True, inc_geo_code=False)

def get_trending_searches(country_str, kwlist=None):
    return pytrends.trending_searches(pn=country_str).to_numpy()

def convert_hex_to_ip(hex_value):
    a=int(hex_value[0:2], 16)
    b=int(hex_value[2:4], 16)
    c=int(hex_value[4:6], 16)
    d=int(hex_value[6:8], 16)
    return "%s.%s.%s.%s" % (str(a), str(b), str(c), str(d))

# Function of parcing of get TITLE from link.  
def link_title(n):
    if 'http://' in n or 'https://' in n:
        try:
            link_r = n.split('//',1)[1].split(' ',1)[0].rstrip()
        except:
            print('Link wrong!')      
    elif 'www.' in n:
        try:
            link_r = n.split('www.',1)[1].split(' ',1)[0].rstrip()    
        except:
            print('Link wrong!')
    link = 'http://'+link_r        
    max_t_link = 30
    t_link = time.time()
    for i in requests.get(link, stream=True, verify=False):
        t2_link = time.time()
        if t2_link > t_link + max_t_link:
            requests.get(link, stream=True).close()
            print('Title - Ошибка! Превышено время ожидания!')
            link_stat = False
            break
        else:
            link_stat = True

    if link_stat == True:
        unquoted_link = unquote(link)
        get_title = requests.get(link, timeout = 10)
        txt_title = get_title.text
        if '</TITLE>' in txt_title or '</title>' in txt_title\
                      or '</Title>' in txt_title:
            if '</TITLE>' in txt_title:
                title = '\x02Title\x02 of '+n+': '+\
                txt_title.split('</TITLE>',1)[0].split('>')[-1]
            elif '</title>' in txt_title:
                title = '\x02Title\x02 of '+n+': '+\
                txt_title.split('</title>',1)[0].split('>')[-1]
            elif '</Title>' in txt_title:
                title = '\x02Title\x02 of '+n+': '+\
                txt_title.split('</Title>',1)[0].split('>')[-1]

            return title.replace('\r','').replace('\n','').replace\
                   ('www.','').replace('http://','').replace\
                   ('https://','').strip()
        else:
            return 'Title not found'

def ru_latest_news_newsapi_org():
    apikey=option("newsapi_apikey")
    url="http://newsapi.org/v2/top-headlines?country=ru&apiKey=%s" % apikey
    resp = requests.get(url=url)
    if resp.status_code != 200: return []
    #print (__file__, resp.text)
    rjson = resp.json()
    print (f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
    if "articles" in rjson:
        arts = rjson["articles"]
        if arts is None: return []
        return arts
    return []

def ua_latest_news_newsapi_org():
    apikey=option("newsapi_apikey")
    url="http://newsapi.org/v2/top-headlines?country=ua&apiKey=%s" % apikey
    resp = requests.get(url=url)
    if resp.status_code != 200: return []
    # print (__file__, resp.text)
    rjson = resp.json()
    print (f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
    if "articles" in rjson:
        arts = rjson["articles"]
        if arts is None: return []
        return arts
    return []

def latest_news_google_news_ru():
    apikey=option("newsapi_apikey")
    url="http://newsapi.org/v2/top-headlines?sources=google-news-ru&apiKey=%s" % apikey
    resp = requests.get(url=url)
    if resp.status_code != 200: return []
    # print (__file__, resp.text)
    rjson = resp.json()
    print (f'{__file__} {__name__} ns_resp {get_pretty_json_string(rjson)}')
    if "articles" in rjson:
        arts = rjson["articles"]
        if arts is None: return []
        return arts
    return []
  

def format_currency(value):
    return "{:0,.2f}".format(float(value))


def format_total_cap(total_market_cap_usd):
    total_market_cap_usd_t = float(total_market_cap_usd) / 1.0e12
    b = "{:0,.2f}".format(total_market_cap_usd_t)+"T USD"
    p = "{:0,.2f}".format(total_market_cap_usd_t/60.0*100.0)+'% of entire world cap e.g. 60T USD'
    return b+" ("+p+')'


def fetch_last_hour_new_news(old_news_cache=None, kwlist=None):
    array = get_trending_searches(country_str="russia", kwlist=kwlist)
    newer = []
    for lines in array:
        line = lines[0]
        if line is None: continue
        if line in old_news_cache: continue
        newer.append(line)
    return newer


def is_runews_command(bot_nick, str_line):
    """
        :defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
    """
    dataTokensDelimitedByWhitespace = str_line.split(" ")
    # dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
    # dataTokensDelimitedByWhitespace[1] PRIVMSG

    # dataTokensDelimitedByWhitespace[2] #ru
    #  OR
    # dataTokensDelimitedByWhitespace[2] BichBot

    # dataTokensDelimitedByWhitespace[3] :!курс
    communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
    where_mes_exc = communicationsLineName
    if len(dataTokensDelimitedByWhitespace) > 3:
        line = " ".join(dataTokensDelimitedByWhitespace[3:])
        is_in_private_query = where_mes_exc == bot_nick
        bot_mentioned = bot_nick in line
        commWithBot = is_in_private_query or bot_mentioned
        return commWithBot and ("runews" in line or "руновости" in line) or ("!runews" in line or "!руновости" in line)
    else:
        return False

def is_uanews_command(bot_nick, str_line):
    #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
    dataTokensDelimitedByWhitespace = str_line.split(" ")
    #dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
    #dataTokensDelimitedByWhitespace[1] PRIVMSG

    #dataTokensDelimitedByWhitespace[2] #ru
    # OR
    #dataTokensDelimitedByWhitespace[2] BichBot

    #dataTokensDelimitedByWhitespace[3] :!курс
    communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
    where_mes_exc = communicationsLineName
    if len(dataTokensDelimitedByWhitespace) > 3:
        line = " ".join(dataTokensDelimitedByWhitespace[3:])
        is_in_private_query = where_mes_exc == bot_nick
        bot_mentioned = bot_nick in line
        commWithBot = is_in_private_query or bot_mentioned
        return commWithBot and ("uanews" in line or "укрновости" in line) or ("!uanews" in line or "!укрновости" in line)
    else:
        return False

def is_search_command(bot_nick, str_line):
    #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
    dataTokensDelimitedByWhitespace = str_line.split(" ")
    #dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
    #dataTokensDelimitedByWhitespace[1] PRIVMSG

    #dataTokensDelimitedByWhitespace[2] #ru
    # OR
    #dataTokensDelimitedByWhitespace[2] BichBot

    #dataTokensDelimitedByWhitespace[3] :!курс
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

def is_search_command2(bot_nick, str_line):
    #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
    dataTokensDelimitedByWhitespace = data.split(" ")
    #dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
    #dataTokensDelimitedByWhitespace[1] PRIVMSG

    #dataTokensDelimitedByWhitespace[2] #ru
    # OR
    #dataTokensDelimitedByWhitespace[2] BichBot

    #dataTokensDelimitedByWhitespace[3] :!курс
    communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
    where_mes_exc = communicationsLineName
    if len(dataTokensDelimitedByWhitespace) > 3:
        line = " ".join(dataTokensDelimitedByWhitespace[3:])
        is_in_private_query = where_mes_exc == bot_nick
        bot_mentioned = bot_nick in line
        commWithBot = is_in_private_query or bot_mentioned
        return commWithBot and ("search2" in line or "поиск2" in line) or ("!search2" in line or "!поиск2" in line)
    else:
        return False

class MyPingsToServerThread(Thread):
    def __init__(self, myBot):
        Thread.__init__(self)
        self.myBot = myBot
    
    def run(self):
        self.myBot.pinger_of_server()

def print_wheel(wheel):
    s = "{[\r\n"
    for dt in wheel['datetimes']:
        s+="  "+str(dt)+"\r\n"
    s+="]}"
    return s


WHEEL_SIZE = 5
WHEEL_TIME_SECONDS = 60

class MyBot:
    wheelGrants = {}
    def grantCommand(self, sentBy, commLine):
        sentBy = 'anyone' # nicks don't matter as ddoser might use multiple random nicks
        if not sentBy in self.wheelGrants:
            wheel = {}
            self.wheelGrants[sentBy] = wheel
            wheel['datetimes'] = [datetime.datetime.now(pytz.utc)]
            print(__name__, f"command_granted clause 1, wheel: {print_wheel(wheel)}")
            return True
        else:
            wheel = self.wheelGrants[sentBy]
            datetimes = wheel['datetimes']

            while len(datetimes) > WHEEL_SIZE:
                datetimes = datetimes[1:]
            wheel['datetimes'] = datetimes
            if len(datetimes) < WHEEL_SIZE:
                print(__name__, f"command_granted clause 3, wheel: {print_wheel(wheel)}")
                datetimes.append(datetime.datetime.now(pytz.utc))
                wheel['datetimes'] = datetimes
                return True
            granted = datetimes[0] < datetime.datetime.now(pytz.utc) - datetime.timedelta(seconds=WHEEL_TIME_SECONDS)
            if not granted:
                print(__name__, f"command not granted, wheel: {print_wheel(wheel)}")
                if "floodDetectedSentTime" in wheel:
                    floodDetectedSentTime = wheel["floodDetectedSentTime"]
                else:
                    floodDetectedSentTime = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)

                if floodDetectedSentTime < datetime.datetime.now(pytz.utc) - datetime.timedelta(seconds=WHEEL_TIME_SECONDS):
                    wheel["floodDetectedSentTime"] = datetime.datetime.now(pytz.utc)
                    self.send(f'PRIVMSG {commLine} :Flood detected, ignoring.\r\n')
            else:
                print(__name__, f"command_granted clause 2, wheel: {print_wheel(wheel)}")
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

    def __init__(self, settings_key, connection_props):
        self.settings_key = settings_key
        self.connection_props = connection_props

        self.irc_server_hostname = self.connection_settings('irc_server_hostname')
        self.port = int(self.connection_settings('port'))
        self.channelsProps = self.connection_settings('channelsProps')
        self.channelsList = list(self.channelsProps.keys())
        self.BOT_NAME_PREFIX = self.connection_settings('InitialBotNick')
        self.botName = self.BOT_NAME_PREFIX
        self.botNickSalt = 0
        self.nickserv_password = self.connection_setting_or_None('nickserv_password')
        self.coinmarketcap_apikey = settings.settings('coinmarketcap_apikey')
        self.rapidapi_appkey = settings.settings('rapidapi_appkey')
        self.titleEnabled = bool(self.connection_settings('titleEnabled'))
        self.onlycmc = bool(self.connection_settings('onlycmc'))
        self.enableother1 = not self.onlycmc
        self.gnome1rur = float(settings.settings('gnome1_rur_float'))
        self.gnomeBtcTransaction1 = float(settings.settings('gnome_btc_transaction1_BTC_float')) #BTC
        self.gnome_btc_amount2_BTC_float = float(settings.settings('gnome_btc_amount2_BTC_float')) #BTC
        self.master_secret = settings.settings('master_secret')
        self.gnome1rur = self.gnome1rur + ((self.gnome_btc_amount2_BTC_float - self.gnomeBtcTransaction1) * 9500.0 * 65.0)
        self.measurementRur1 = self.gnome1rur
        self.measurementRur2 = self.gnome1rur

    old_news_cache={}
    old_news_cache_index={}

    def web_search(self, query_str, number_of_results):
        pageNumber=1
        url="https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/WebSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
            (urlencode(query_str),str(pageNumber),str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1',"X-RapidAPI-Host":"contextualwebsearch-websearch-v1.p.rapidapi.com","X-RapidAPI-Key":self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ws_resp",json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None

    def web_search2(self, query_str, number_of_results):
        search2RestClient=Search2RestClient(option("dataforseo_api_login"), option("dataforseo_api_password"))
        resp_json = search2RestClient.get(path)


        pageNumber=1
        url="https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/WebSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
            (urlencode(query_str),str(pageNumber),str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1',"X-RapidAPI-Host":"contextualwebsearch-websearch-v1.p.rapidapi.com","X-RapidAPI-Key":self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ws_resp",json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None

    def news_search_ctxwebsrch(self, query_str, number_of_results):
        pageNumber=1
        url="https://contextualwebsearch-websearch-v1.p.rapidapi.com/api/Search/NewsSearchAPI?q=%s&pageNumber=%s&pageSize=%s&autocorrect=true&safeSearch=true" % \
            (urlencode(query_str),str(pageNumber),str(number_of_results))
        headers = {'User-agent': 'bichbot/0.0.1',"X-RapidAPI-Host":"contextualwebsearch-websearch-v1.p.rapidapi.com","X-RapidAPI-Key":self.rapidapi_appkey}
        resp = requests.get(url=url, headers=headers)
        rjson = resp.json()
        print("ns_resp",json.dumps(rjson, sort_keys=True, indent=4))
        for v in rjson["value"]: return v["url"]
        return None

    def sendmsg(self, to_addr,msg):
        self.send('PRIVMSG %s :%s\r\n'%(to_addr,msg))

    def print_new_news_googletrends(self, to_addr, kwlist=None):
        old_news_cache = self.old_news_cache
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache={}
            old_news_cache[to_addr]=cache
        array_of_strings = fetch_last_hour_new_news(cache,kwlist=kwlist)
        cnt = get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for line in array_of_strings:
            if line is None: continue
            resultUrl = news_search(line,1)
            self.sendmsg(to_addr, "%s: %s %s" % (str((index+1)),line,resultUrl if resultUrl else ""))
            cache[line] = {"recently_sent":True}
            sent=sent+1
            index=index+1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")

    def print_new_runews_newsapi_org(self, to_addr):
        old_news_cache = self.old_news_cache
        old_news_cache_index = self.old_news_cache_index
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache={}
            old_news_cache[to_addr]=cache
        if to_addr in old_news_cache_index:
            cache_index = old_news_cache_index[to_addr]
        else:
            cache_index=[]
            old_news_cache_index[to_addr]=cache_index
        arts = ru_latest_news_newsapi_org() + latest_news_google_news_ru()

        cnt = self.get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for a in arts:
            if a is None: continue
            url = a["url"]
            if url in cache: continue
            self.sendmsg(to_addr, "%s %s" % ( str(url), str(a["title"]) ))
            cache[url] = True
            cache_index.append(url)
            while len(cache_index)>100:
                first_url = cache_index.pop(0)
                del cache[first_url]
            sent=sent+1
            index=index+1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")

    def print_new_uanews_newsapi_org(self, to_addr):
        old_news_cache = self.old_news_cache
        old_news_cache_index = self.old_news_cache_index
        if to_addr in old_news_cache:
            cache = old_news_cache[to_addr]
        else:
            cache={}
            old_news_cache[to_addr]=cache
        if to_addr in old_news_cache_index:
            cache_index = old_news_cache_index[to_addr]
        else:
            cache_index=[]
            old_news_cache_index[to_addr]=cache_index
        arts = ua_latest_news_newsapi_org()

        cnt = self.get_news_count_for_channel(to_addr)
        sent = 0
        index = 0
        for a in arts:
            if a is None: continue
            url = a["url"]
            if url in cache: continue
            self.sendmsg(to_addr, "%s %s" % ( str(url), str(a["title"]) ))
            cache[url] = True
            cache_index.append(url)
            while len(cache_index)>100:
                first_url = cache_index.pop(0)
                del cache[first_url]
            sent=sent+1
            index=index+1
            if sent >= cnt: break
        if sent == 0: self.sendmsg(to_addr, "Нет новостей у меня")

    def maybe_print_news(self, bot_nick, str_incoming_line):
        dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
        if is_runews_command(bot_nick, str_incoming_line):
            if self.grantCommand(sentBy, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(dataTokensDelimitedByWhitespace)>=4 else ""
                if line.startswith(":"):line=line[1:]
                print("'%s'"%line)
                p = line.find("news")
                if p == -1:
                    p = line.find("новости")
                    if p == -1:
                        pass
                    else:
                        p=p+len("новости")
                        line = line[p:].strip()
                        print("'%s'"%line)
                        if line != '': kwlist.append(line)
                else:
                    p = p+len("news")
                    line = line[p:].strip()
                    print("'%s'"%line)
                    if line != '': kwlist.append(line)
                if len(kwlist)==0:
                    self.print_new_runews_newsapi_org(where_mes_exc)
                else:
                    resultUrl = self.news_search_ctxwebsrch(kwlist[0],1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Новостей не найдено"))
        if is_uanews_command(bot_nick, str_incoming_line):
            if self.grantCommand(sentBy, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(dataTokensDelimitedByWhitespace)>=4 else ""
                if line.startswith(":"):line=line[1:]
                print("'%s'"%line)
                p = line.find("news")
                if p == -1:
                    p = line.find("новости")
                    if p == -1:
                        pass
                    else:
                        p=p+len("новости")
                        line = line[p:].strip()
                        print("'%s'"%line)
                        if line != '': kwlist.append(line)
                else:
                    p = p+len("news")
                    line = line[p:].strip()
                    print("'%s'"%line)
                    if line != '': kwlist.append(line)
                if len(kwlist)==0:
                    self.print_new_uanews_newsapi_org(where_mes_exc)
                else:
                    resultUrl = self.news_search_ctxwebsrch(kwlist[0],1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Новостей не найдено"))

    def write_quotes(self):
        print(__name__, "writing quotes.json")
        with open('quotes.json', 'w') as myfile:
            myfile.write(get_pretty_json_string(self.quotes_array))

    def read_quotes(self):
        # read file
        #try:
        print(__name__, "reading quotes.json")
        with open('quotes.json', 'r') as myfile:
            quotes_array=myfile.read()
        self.quotes_array = json.loads(quotes_array)
        #except:
        #    traceback.print_exc()
        #    print(__name__, "warning: setting empty quotes_array")
        #    quotes_array = []

    #tok1[0] :nick!uname@addr.i2p
    #tok1[1] PRIVMSG

    #tok1[2] #ru
    # OR
    #tok1[2] BichBot

    #tok1[3] :!!aq/!!q
    #tok1[4:] tokens
    def print_quote(self, tok1):
        at = tok1[2]
        query = " ".join(tok1[4:])
        try:
            num = int(query)
        except ValueError:
            self.sendmsg(at, f"Need a positive int.")
            return
        if num > 0:
            num = num - 1
            self.read_quotes()
            if num >= len(self.quotes_array):
                self.sendmsg(at, f"Max quote number: {len(self.quotes_array)}.")
            else:
                q = self.quotes_array[num]
                poster = q['posted-by'].split("!")[0]
                self.sendmsg(at, f"[{num+1}] {q['text']} ({poster} at {q['date-posted']})")
        else:
            self.sendmsg(at, f"Need a positive int.")

    def add_quote(self, tok1):
        self.read_quotes()
        length = len(self.quotes_array)
        quote = " ".join(tok1[4:])
        self.quotes_array.append({
            "posted-by": tok1[0][1:],
            "text": quote,
            "date-posted": str(datetime.datetime.now(pytz.utc))
        })
        at = tok1[2]
        self.write_quotes()
        self.sendmsg(at, f"Quote added: [{length+1}] {quote}")
        pass
    def maybe_quotes(self, str_incoming_line, sentBy, commLineName):
        tok1 = str_incoming_line.split(" ")
        if len(tok1)<3: return False
        if tok1[1] != "PRIVMSG": return False
        cmdtok = tok1[3].split(":")
        if len(cmdtok)<2: return False
        cmd = cmdtok[1]
        if not cmd.startswith("!!"): return False
        if cmd == "!!q":
            if self.grantCommand(sentBy, commLineName):
                self.print_quote(tok1)
                return True
        if cmd == "!!aq":
            if self.grantCommand(sentBy, commLineName):
                self.add_quote(tok1)
                return True
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
        if len(tok1)<3: return False
        if tok1[1] != "PRIVMSG": return False
        message = " ".join(tok1[3:])[1:]
        if not bot_nick in message: return False
        reply = self.help_make_choice(message)
        if not reply: return False
        at = tok1[2]
        self.sendmsg(at, reply)
        return True

    def maybe_print_search(self, bot_nick, str_incoming_line, sentBy):
        dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
        communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
        if is_search_command(bot_nick, str_incoming_line):
            if self.grantCommand(sentBy, communicationsLineName):
                kwlist = []
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(dataTokensDelimitedByWhitespace)>=4 else ""
                if line.startswith(":"):line=line[1:]
                print("'%s'"%line)
                p = line.find("search")
                if p == -1:
                    p = line.find("поиск")
                    if p == -1:
                        pass
                    else:
                        p=p+len("поиск")
                        line = line[p:].strip()
                        print("'%s'"%line)
                        if line != '': kwlist.append(line)
                else:
                    p = p+len("search")
                    line = line[p:].strip()
                    print("'%s'"%line)
                    if line != '': kwlist.append(line)
                if len(kwlist)==0:
                    self.sendmsg(where_mes_exc, "Чего синьорам найти?")
                else:
                    resultUrl = self.web_search(kwlist[0],1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Результатов не найдено"))

    def maybe_print_search2(self, bot_nick, str_incoming_line, sentBy, communicationsLineName):
        if is_search_command2(bot_nick, str_incoming_line):
            if self.grantCommand(sentBy, communicationsLineName):
                kwlist = []
                dataTokensDelimitedByWhitespace = str_incoming_line.split(" ")
                communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
                where_mes_exc = communicationsLineName
                line = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(dataTokensDelimitedByWhitespace)>=4 else ""
                if line.startswith(":"):line=line[1:]
                print("'%s'"%line)
                p = line.find("search2")
                if p == -1:
                    p = line.find("поиск2")
                    if p == -1:
                        pass
                    else:
                        p=p+len("поиск2")
                        line = line[p:].strip()
                        print("'%s'"%line)
                        if line != '': kwlist.append(line)
                else:
                    p = p+len("search2")
                    line = line[p:].strip()
                    print("'%s'"%line)
                    if line != '': kwlist.append(line)
                if len(kwlist)==0:
                    self.sendmsg(where_mes_exc, "Чего синьорам найти?")
                else:
                    resultUrl = web_search2(kwlist[0],1)
                    self.sendmsg(where_mes_exc, "%s" % (resultUrl if resultUrl else "Результатов не найдено"))

    databuf = b''
    socket_closed = False
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
            if self.databuf[a]==0xD:
                a=a+1
                if a<len(self.databuf) and self.databuf[a]==0xA:
                    a=a+1
            else:
                if self.databuf[a]==0xA:
                    a=a+1
            self.databuf = self.databuf[a:] if a < len(self.databuf) else b''
            return line
        return self.databuf

    def extract_line_1(self):
        #if LOG_TRACE: print("extract_line_1() #0: databuf", databuf, "socket_closed", socket_closed)
        a = self.databuf.find(b'\r')
        b = self.databuf.find(b'\n')
        if a != -1 and b != -1: a = min(a, b)
        if b != -1 and a == -1: a = b
        if a != -1:
            if LOG_TRACE: print("#1: a:", a, "len(databuf):", len(self.databuf), "databuf[a]==b'SLASHr':", self.databuf[a]==0xD, "databuf[a]:", self.databuf[a], "a < len(databuf)-1:", a < len(self.databuf)-1)
            if (self.databuf[a]==0xD and a < len(self.databuf)-1) or self.databuf[a]==0xA:
                if LOG_TRACE: print("#2")
                line = self.databuf[0:a]
                if self.databuf[a]==0xD:
                    if LOG_TRACE: print("#3")
                    a=a+1
                    if self.databuf[a]==0xA:
                        if LOG_TRACE: print("#4")
                        a=a+1
                else:
                    if LOG_TRACE: print("#5")
                    if self.databuf[a]==0xA:
                        if LOG_TRACE: print("#6")
                        a=a+1
                if LOG_TRACE: print("#7, a:", a)
                self.databuf = self.databuf[a:]
                if LOG_TRACE: print("returning line:", line)
                return line
            #else read more
        #else read more
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
      retval = self.irc_socket.send(bytes(msg,'utf-8'))
      return retval

          
    # Install min & max timer vote.  
    min_timer = 30
    max_timer = 300

    def get_news_count_for_channel(self, commLineName):
        props = self.channelsProps[commLineName] if commLineName in self.channelsProps else None
        if props is None: return 10
        return props['news_count'] if 'news_count' in props else 3

    def pinger_of_server(self):
        print ("spawned pinger_of_server, key: '%s'" % self.settings_key)
        while True:
            print("---new ping to server---")
            self.pong_received=False
            self.send('PING :'+str(time.time())+'\r\n')
            time.sleep(180)
            if self.pong_received:
                continue
            else:
                print ("ping to server timeout, closing socket, key: '%s'" % self.settings_key)
                self.irc_socket.close()
                print ("exiting pinger of server, key: '%s'" % self.settings_key)
                return

    def login_and_loop(self):
        while True:
            print("---new iter---", flush=True)
            try:
                mask2ctx = {}
                from time import sleep as sleep_seconds
                print("sleeping 50ms...")
                sleep_seconds(0.05)
                if self.connection_setting_or_None('socks5_host'):
                    host = self.connection_option('socks5_host')
                    print (f"new socks.socksocket({host})")
                    self.irc_socket = socks.socksocket()
                    self.irc_socket.set_proxy(socks.SOCKS5, host, \
                        self.connection_option('socks5_port'), True, self.connection_option('socks5_username'), \
                        self.connection_option('socks5_password'))
                else:
                    print ("new socket(AF_INET,SOCK_STREAM)")
                    self.irc_socket = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
                print("connecting... irc_server_hostname='"+self.irc_server_hostname+"' port='"+str(self.port)+"'…")
                self.irc_socket.connect ((self.irc_server_hostname, self.port))
                self.init_socket(self.irc_socket)
                print("connected, self.sending login handshake, self.botName=["+self.botName+"]…")
                #print (self.irc_socket.recv(2048).decode("UTF-8"))
                self.send('NICK '+self.botName+'\r\n')
                self.send('USER '+self.botName+' '+self.botName+' '+self.botName+' :irc bot\r\n')
                #self.send('NickServ IDENTIFY '+settings.settings('password')+'\r\n')
                #self.send('MODE '+self.botName+' +x')

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

                keepingConnection=True
                while keepingConnection:
                    try:
                        data = self.get_line(self.irc_socket).decode("UTF-8")
                        print("got line:["+data+"]", flush=True)
                        if data=="":
                            print("data=='', self.irc_socket.close(), keepingConnection=False, iterating...");
                            self.irc_socket.close()
                            keepingConnection=False
                            continue
                    except UnicodeDecodeError as decodeException:
                        print(f"UnicodeDecodeError {decodeException}, iterating...")
                        continue
                    tokens1 = data.split(" ");

                    sender_mask = None

                    dataTokensDelimitedByWhitespace = tokens1
                    #dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
                    #dataTokensDelimitedByWhitespace[1] PRIVMSG

                    #dataTokensDelimitedByWhitespace[2] #ru
                    # OR
                    #dataTokensDelimitedByWhitespace[2] BichBot

                    #dataTokensDelimitedByWhitespace[3] :!курс
                    communicationsLineName = dataTokensDelimitedByWhitespace[2] if len(dataTokensDelimitedByWhitespace) > 2 else None
                    lineJoined = " ".join(dataTokensDelimitedByWhitespace[3:]) if len(dataTokensDelimitedByWhitespace) >= 4 else ""
                    sender = communicationsLineName
                    sentBy = dataTokensDelimitedByWhitespace[0][1:]

                    if len(tokens1)>1 and tokens1[1]=="433": #"Nickname is already in use" in data
                        self.botNickSalt=self.botNickSalt+1
                        self.botName = self.BOT_NAME_PREFIX+str(self.botNickSalt)
                        self.send('NICK '+self.botName+'\r\n')
                        continue
                    if len(tokens1)>=4 and tokens1[1]=="MODE" and "+x" in tokens1[3]: #:GreenBich MODE GreenBich :+x
                        self.send('JOIN '+(",".join(self.channelsList))+' \r\n')
                        continue
                    #
                    if self.nickserv_password is not None and len(tokens1)>1 and tokens1[1]=="001": #001 nick :Welcome to the Internet Relay Network
                        self.send('NICKSERV IDENTIFY '+self.nickserv_password+'\r\n')
                    if data.find('PING') != -1:
                        try:
                          print("ping_received")
                          self.send('PONG '+data.split(" ")[1]+'\r\n')
                          print("pong sent with data_str")
                        except:
                          traceback.print_exc()
                          self.send('PONG')
                          print("pong sent without data_str")
                        continue
                    if data.find('PONG') != -1:
                        print("server pong_received")
                        self.pong_received=True
                        continue

                    #001 welcome
                    spws = tokens1
                    if len(spws) > 1 and spws[1]=="001":
                        MyPingsToServerThread(self).start()
                        self.send('MODE '+self.botName+' +xB\r\n')
                        continue
                    
                    ws_tokens = tokens1

                    try:
                        message = None
                        #got line:[:test2!~username@ipaddr PRIVMSG #channel :msg]
                        if len(ws_tokens)>=4:
                            src = ws_tokens[0]
                            cmd = ws_tokens[1]
                            chan = ws_tokens[2]
                            msg = " ".join(ws_tokens[3:])

                            if cmd == "PRIVMSG":
                                name = src.split('!')[0][1:]
                                sender_mask = src[1:]
                                message = msg[1:]
                                print(__name__, f"message: '{message}'",flush=True)
                            try:
                                ip_user=None#"data.split('@',1)[1].split(' ',1)[0]
                            except:
                                print(__name__, 'error getting ip_user')
                    except:
                        import traceback as tb
                        tb.print_exc()
                        import sys
                        sys.stderr.flush()

                    #got line:[:test1!~username@ipaddr NICK :test2]
                    try:
                        if len(ws_tokens)>=3:
                            src = ws_tokens[0]
                            cmd = ws_tokens[1]
                            msg = " ".join(ws_tokens[2:])

                            if cmd == "NICK":
                                old_mask = src[1:]
                                print(__name__, "old_mask: '"+old_mask+"'",flush=True)
                                old_mask_split = old_mask.split("!")
                                new_nick = msg[1:]
                                new_mask = new_nick+"!"+old_mask_split[1]
                                print(__name__, "new_mask: '"+new_mask+"'",flush=True)
                                replace_nick_mask2ctx(mask2ctx, old_mask, new_mask)
                    except:
                        import traceback as tb
                        tb.print_exc()
                        import sys
                        sys.stderr.flush()

                    if self.enableother1 or self.connection_setting_or_None("enable_krako_translation"):
                        #print(__file__, "krako test")
                        try:
                            where_message = communicationsLineName
                            if message is not None and (("!k" in message) or ("!к" in message)) and dataTokensDelimitedByWhitespace[1] == "PRIVMSG":
                                if self.grantCommand(sentBy, communicationsLineName):
                                    print(__name__, "krako test success",flush=True)
                                    if (message == "!k") or (message == "!к"):
                                        print(__name__, "krako: mask2ctx='"+str(mask2ctx)+"', sender_mask='"+str(sender_mask)+"'",flush=True)
                                        prev_msg = get_prev_msg(mask2ctx, sender_mask)
                                        print(__name__, "krako translating prev_msg: '"+str(prev_msg)+"'",flush=True)
                                        tr_txt = prev_msg
                                    else:
                                        if (':!k' in lineJoined): tr_txt = message.split('!k ',1)[1].strip()
                                        else:
                                            if (':!к' in lineJoined): tr_txt = message.split('!к ',1)[1].strip()
                                    res_txt = translate_krzb.tr(tr_txt)
                                    self.send('PRIVMSG '+where_message+' :\x02перевод с кракозябьечьего:\x02 '+res_txt+'\r\n')
                                    continue
                        except KeyboardInterrupt as ex:
                            import traceback as tb
                            tb.print_exc()
                            import sys
                            sys.stderr.flush()
                            self.send('PRIVMSG '+where_message+' :\x02!k error:\x02 '+str(ex)+'\r\n')
                            raise ex
                        except BaseException as ex:
                            import traceback as tb
                            tb.print_exc()
                            import sys
                            sys.stderr.flush()
                            self.send('PRIVMSG '+where_message+' :\x02!k error:\x02 '+str(ex)+'\r\n')
                            continue
                    
                    #print(__name__, "before set_prev_msg: message='"+str(message)+"', sender_mask='"+str(sender_mask)+"'")
                    if message is not None and sender_mask is not None:
                        #print(__name__, "set_prev_msg")
                        try:
                            set_prev_msg(mask2ctx, sender_mask, message)
                            print(__name__, "set_prev_msg left ok", flush=True)
                        except KeyboardInterrupt as e:
                            print(__name__, "set_prev_msg left with exception: KeyboardInterrupt", flush=True)
                            raise e
                        except:
                            tb.print_exc()
                            print(__name__, "set_prev_msg left with exception", flush=True)

                    #print(__name__, "point 3.1", flush=True)
                    if self.enableother1 or self.connection_setting_or_None("enable_hextoip"):
                        if ':!hextoip' in lineJoined and dataTokensDelimitedByWhitespace[1] == "PRIVMSG":
                            if self.grantCommand(sentBy, communicationsLineName):
                                print(__file__, "hextoip test success")
                                try:
                                    hex_value = message.split('!hextoip ',1)[1].strip()
                                    self.send('PRIVMSG '+communicationsLineName+' :\x02hextoip:\x02 '+convert_hex_to_ip(hex_value)+'\r\n')
                                except KeyboardInterrupt as e:
                                    raise e
                                except BaseException as e:
                                    tb.print_exc()
                                    self.send('PRIVMSG '+communicationsLineName+' :\x02hextoip:\x02 error: '+str(e)+'\r\n')
                                continue

                    #-----------Bot_help---------------

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
                    #-----------Antiflood-------------

                    #print(__name__, "point 3.2", flush=True)
                    while_count += 1
                    if while_count == 50:
                        while_count = 0
                        dict_count = {}
                            
                    #print(__name__, "point 3.3", flush=True)
                    # Insert nick in dict: dic_count.  
                    if data.find('PRIVMSG') != -1 and name not in dict_count and\
                       name not in list_floodfree:
                        dict_count[name] = int(1)
                        #if 'PRIVMSG '+channel in data:
                        #    where_message = channel #todo
                        if 'PRIVMSG '+self.botName in data:
                            where_message = self.botName
                        else: where_message=None
                    
                    # If new message as last message: count +1.  
                    if data.find('PRIVMSG') != -1 and message == dict_users.get(name)\
                       and name not in list_floodfree:
                        dict_count[name] += int(1)
                    
                    #print(__name__, "point 3.4", flush=True)
                    # Add key and value in massiv.  
                    if data.find('PRIVMSG') != -1 and name not in list_floodfree:
                        dict_users[name] = message
                    
                    # Message about flood and kick. 
                    #if data.find('PRIVMSG') != -1 and name not in list_floodfree:
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
                    #---------Whois service--------------------------
                    #print(__name__, "point 2.3", flush=True)

                    if self.enableother1:
                      if 'PRIVMSG '+channel+' :!где айпи' in data\
                       or 'PRIVMSG '+self.botName+' :!где айпи' in data:

                        if self.grantCommand(sentBy, communicationsLineName):
                            if 'PRIVMSG '+channel+' :!где айпи' in data:
                                where_message_whois = channel
                                
                            elif 'PRIVMSG '+self.botName+' :!где айпи' in data:
                                where_message_whois = name
                                          
                            try:
                                whois_ip = data.split('!где айпи ',1)[1].split('\r',1)[0].strip()
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
                                           
                                whois_final_reply = ' \x02IP:\x02 '+whois_ip+' \x02Страна:\x02 '+\
                                    country_whois+' \x02Адрес:\x02 '+address_whois
                                self.send('PRIVMSG '+where_message_whois+' :'+whois_final_reply+'\r\n')

                            except:
                                print('get Value Error in whois service!')
                                self.send('PRIVMSG '+where_message_whois+' :Ошибка! Вводите только IP адрес \
    из цифр, разделенных точками!\r\n')
                                         
                    #---------Info from link in channel-------------
                    
                    if self.enableother1 and self.titleEnabled:
                        if 'PRIVMSG %s :'%(channel) in data and '.png' not in data and '.jpg' not in data and '.doc'\
                        not in data and 'tiff' not in data and 'gif' not in data and '.jpeg' not in data and '.pdf' not in data:
                            if 'http://' in data or 'https://' in data or 'www.' in data:
                                if self.grantCommand(sentBy, communicationsLineName):
                                    try:
                                       self.send('PRIVMSG %s :%s\r\n'%(channel,link_title(data)))
                                    except requests.exceptions.ConnectionError:
                                        print('Ошибка получения Title (requests.exceptions.ConnectionError)')
                                        self.send('PRIVMSG '+channel+' :Ошибка ConnectionError\r\n')
                                    except:
                                        print('Exception')  
                    #---------Voting--------------------------------
                                
                    #print(__name__, "point 2.2", flush=True)
                    t = time.time()
                    if self.enableother1:
                      if '!стоп опрос' in data and 'PRIVMSG' in data and name == masterName:
                        t2 = 0
                        print('счетчик опроса сброшен хозяином!')
                    if self.enableother1:
                      if 'PRIVMSG '+channel+' :!опрос ' in data and ip_user not in list_bot_not_work:
                        if self.grantCommand(sentBy, communicationsLineName):
                            if t2 == 0 or t > t2+time_vote:
                                if ' сек ' not in data:
                                    time_vote = 60
                                    # Make variable - text-voting-title form massage.  
                                    message_voting = message.split('!опрос',1)[1].strip()
                                if ' сек ' in data:
                                    try:
                                        # Get time of timer from user message.  
                                        time_vote = int(message.split('!опрос',1)[1].split('сек',1)[0].strip())
                                        # Make variable - text-voting-title form massage.  
                                        message_voting = message.split('!опрос',1)[1].split('сек',1)[1].strip()
                                    except:
                                        time_vote = 60
                                        # Make variable - text-voting-title form massage.  
                                        message_voting = message.split('!опрос',1)[1].strip()

                                if min_timer>time_vote or max_timer<time_vote:
                                    self.send('PRIVMSG %s :Ошибка ввода таймера голосования.\
    Введите от %s до %s сек!\r\n'%(channel,min_timer,max_timer))
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
    так и в приват боту, чтобы голосовать анонимно \r\n' % (channel,message_voting,time_vote))
                                list_vote_ip = []
                                
                    # If find '!да' count +1.  
                    if self.enableother1:
                      if data.find('PRIVMSG '+channel+' :!да') != -1 or data.find('PRIVMSG '+self.botName+' :!да') != -1:
                        if ip_user not in list_vote_ip and t2 != 0:
                            count_vote_plus +=1
                            dict_voted[name] = 'yes'
                            list_vote_ip.append(ip_user)
                            # Make notice massage to votes user.  
                            self.send('NOTICE '+name+' :Ваш ответ \"да\" учтен!\r\n')

                    # If find '!нет' count +1.  
                    if self.enableother1:
                      if data.find('PRIVMSG '+channel+' :!нет') != -1 or data.find('PRIVMSG '+self.botName+' :!нет') != -1:
                        if ip_user not in list_vote_ip and t2 != 0:
                            count_vote_minus +=1
                            dict_voted[name] = 'no'
                            list_vote_ip.append(ip_user)
                            # Make notice massage to votes user.  
                            self.send('NOTICE '+name+' :Ваш ответ \"нет\" учтен!\r\n')
                   
                    # If masterName self.send '!список голосования': self.send to him privat messag with dictonary Who How voted.  
                    if self.enableother1:
                      if data.find('PRIVMSG '+self.botName+' :!список опроса') !=-1 and name == masterName:
                        for i in dict_voted:
                            self.send('PRIVMSG '+masterName+' : '+i+': '+dict_voted[i]+'\r\n')

                    # Count how much was message in channel '!голосование'.  
                    if self.enableother1:
                      if data.find('PRIVMSG '+channel+' :!опрос') != -1 and t2 != 0:
                        count_voting += 1

                    print(__name__, "point 2.1", flush=True)
                    # If voting is not end, and users self.send '!голосование...': self.send message in channel.  
                    t4 = time.time()
                    if self.enableother1:
                      if data.find('PRIVMSG '+channel+' :!опрос') != -1 and t4-t2 > 5:
                        t3 = time.time()
                        time_vote_rest_min = (time_vote-(t3-t2))//60
                        time_vote_rest_sec = (time_vote-(t3-t2))%60
                        if (time_vote-(t3-t2)) > 0:
                            self.send('PRIVMSG %s : Предыдущий опрос: \"%s\" ещё не окончен, до окончания \
опроса осталось: %d мин %d сек\r\n \
' % (channel,message_voting,time_vote_rest_min,time_vote_rest_sec))

                    # Make variable message rusults voting.  
                    vote_all = count_vote_minus + count_vote_plus
                    """
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
                    self.maybe_print_search(self.botName, data, sentBy)
                    if self.maybe_quotes(data, sentBy, communicationsLineName):
                        print("maybe_quotes() returned True, continuing loop", flush=True)
                        continue
                    else:
                        print("maybe_quotes() returned False", flush=True)
                    # if self.maybe_choice(self.botName, data): continue

                    #:nick!uname@addr.i2p PRIVMSG #ru :!курс
                    #:defender!~defender@example.org PRIVMSG BichBot :Чтобы получить войс, ответьте на вопрос: Как называется blah blah?
                    where_mes_exc = communicationsLineName
                    #print(__name__, "point 4.1", flush=True)
                    if len(dataTokensDelimitedByWhitespace) > 3:
                      #print(__name__, "point 4.2", flush=True)

                      fe_msg = "FreiEx(GST): N/A"

                      line = " ".join(dataTokensDelimitedByWhitespace[3:])
                      is_in_private_query = where_mes_exc == self.botName
                      bot_mentioned = self.botName in line
                      commWithBot = is_in_private_query or bot_mentioned
                      #print(__name__, f"point 4.3, line: '{line}', commWithBot: '{commWithBot}'", flush=True)
                      try:
                        if 'курс' in line and commWithBot:
                            if self.grantCommand(sentBy, communicationsLineName):
                                print(__name__, 'курс', flush=True)
                                is_dialogue_with_master = False
                                if where_mes_exc == self.botName: #/query
                                    tokensNick1=dataTokensDelimitedByWhitespace[0].split("!")
                                    tokensNick1=tokensNick1[0].split(":")
                                    tokensNick1=tokensNick1[1]
                                    where_mes_exc=tokensNick1
                                    is_dialogue_with_master = master_secret in line
                                    if is_dialogue_with_master: self.send('PRIVMSG %s :%s\r\n'%(where_mes_exc,"hello, Master!"))
                                print('курс куда слать будем:', where_mes_exc, "is_dialogue_with_master:", is_dialogue_with_master, flush=True)

                                try:
                                    #This example uses Python 2.7 and the python-request library.
                                    
                                    from requests import Request, Session
                                    from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
                                    import json
                                    
                                    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
                                    parameters = {
                                      'symbol':'BTC,ETH,DASH,DOGE,ZEC',
                                      'convert':'USD'
                                    }
                                    headers = {
                                      'Accepts': 'application/json',
                                      'X-CMC_PRO_API_KEY': self.coinmarketcap_apikey,
                                    }
                                    
                                    session = Session()
                                    session.headers.update(headers)

                                    rate_cmc_str = "CoinMarketCap: "
                                    
                                    try:
                                      print('!курс session.get url='+url)
                                      response = session.get(url, params=parameters)
                                      cmc = json.loads(response.text)
                                      if LOG_TRACE: print("cmc:", cmc)
                                      btc_usd = cmc["data"]["BTC"]["quote"]["USD"]["price"]
                                      eth_usd = cmc["data"]["ETH"]["quote"]["USD"]["price"]
                                      dash_usd = cmc["data"]["DASH"]["quote"]["USD"]["price"]
                                      doge_usd = cmc["data"]["DOGE"]["quote"]["USD"]["price"]
                                      zec_usd = cmc["data"]["ZEC"]["quote"]["USD"]["price"]
                                      btc_usd_str = str(format_currency(btc_usd))
                                      eth_usd_str = str(format_currency(eth_usd))
                                      dash_usd_str = str(format_currency(dash_usd))
                                      doge_usd_str = str(format_currency(doge_usd))
                                      zec_usd_str = str(format_currency(zec_usd))
                                      
                                      rate_cmc_str += f'\x02BTC/USD:\x02 {btc_usd_str} \x02ETH/USD:\x02 {eth_usd_str} \x02DASH/USD:\x02 {dash_usd_str} \x02ZEC/USD:\x02 {zec_usd_str}' # \x02DOGE/USD:\x02 {doge_usd_str}

                                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                                      tb.print_exc()
                                      rate_cmc_str += str(e)

                                    RUR_SYMBOL="RUB"

                                    parameters = {
                                      'symbol':'DOGE',
                                      'convert':RUR_SYMBOL
                                    }

                                    try:
                                      print('!курс rur session.get url='+url)
                                      response = session.get(url, params=parameters)
                                      cmc = json.loads(response.text)
                                      if LOG_TRACE: print("cmc_rur:", cmc)
                                      doge_rur = cmc["data"]["DOGE"]["quote"][RUR_SYMBOL]["price"]
                                      doge_rur_str = str(format_currency(doge_rur))
                                      
                                      rate_cmc_str += f' \x02DOGE/RUR:\x02 {doge_rur_str}'

                                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                                      tb.print_exc()
                                      rate_cmc_str += str(e)

                                    url = 'https://pro-api.coinmarketcap.com/v1/global-metrics/quotes/latest'
                                    parameters = {}

                                    try:
                                      print('!cmc-global-metrics session.get url='+url, flush=True)
                                      response = session.get(url, params=parameters)
                                      cmc = json.loads(response.text)
                                      if LOG_TRACE: print("cmc global-metrics:", cmc)
                                      total_market_cap_usd = cmc["data"]["quote"]["USD"]["total_market_cap"]
                                      total_market_cap_str = str(format_total_cap(total_market_cap_usd))
                                      
                                      rate_cmc_str += ' \x02Total Crypto Cap:\x02 ' + total_market_cap_str + "."

                                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                                      import traceback as tb
                                      tb.print_exc()
                                      rate_cmc_str += "; "+str(e)


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
                                    url = 'https://api.kuna.io/v3/tickers?symbols=tonusdt'
                                    parameters = {
                                    }
                                    headers = {
                                      'Accepts': 'application/json',
                                    }
                                    
                                    try:
                                      print('!курс session.get url='+url, flush=True)
                                      response = session.get(url, params=parameters)
                                      retval = json.loads(response.text)
                                      if LOG_TRACE: print("kuna:", retval)
                                      bid = retval[0][1]
                                      ask = retval[0][3]
                                      vol24 = retval[0][8]
                                      bid_str = str(format_currency(bid))
                                      ask_str = str(format_currency(ask))
                                      vol24_str = str(format_currency(vol24))
                                      
                                      kuna_str = 'Kuna.io \x02TON/USDT\x02: BID '+bid_str+' ASK '+ask_str+' VOL24 '+vol24_str+"."
                                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                                      print(__name__, e, flush=True)
                                      kuna_str = 'Kuna.io error: '+str(e)

                                    btcToUsdFloat = None
                                    btcToRurFloat = None

                                    try:
                                      import urllib.request
                                      url = "https://api.freiexchange.com/public/ticker/GST"
                                      print("querying %s"%(url,), flush=True)
                                      req = urllib.request.Request(
                                            url, 
                                            data=None, 
                                            headers={
                                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/35.0.1916.47 Safari/537.36'
                                            }
                                      )
                                      fe_ticker = urllib.request.urlopen(req).read()
                                      # urllib.request.urlopen(url).read()
                                      print("fe_ticker (a response):",fe_ticker,flush=True)
                                      fe_ticker = json.loads(fe_ticker)
                                      if "GST_BTC" in fe_ticker:
                                        gst_resp = fe_ticker["GST_BTC"][0]
                                        volume24h_gst = float(gst_resp["volume24h"])
                                        volume24h_btc_lit = gst_resp["volume24h_btc"]
                                        volume24h_btc = float(volume24h_btc_lit)
                                        volume24h_rur = btcToRurFloat*volume24h_btc if btcToRurFloat is not None else None
                                        last_lit = gst_resp["last"]
                                        last = float(last_lit)
                                        last_rur = btcToRurFloat*last if btcToRurFloat is not None else None
                                        highestBuy_lit = gst_resp["highestBuy"]
                                        highestBuy = float(highestBuy_lit)
                                        highestBuy_rur = btcToRurFloat*highestBuy if btcToRurFloat is not None else None
                                        lowestSell_lit = gst_resp["lowestSell"]
                                        lowestSell = float(lowestSell_lit)
                                        lowestSell_rur = btcToRurFloat*lowestSell if btcToRurFloat is not None else None

                                        #fe_msg = "FreiEx(GST): VOL24:"+fmt2(volume24h_rur)+"RUR LAST:"+fmt2(last_rur)+"RUR S:"+fmt2(lowestSell_rur)+"RUR B:"+fmt2(highestBuy_rur)+"RUR"
                                        fe_msg = f"FreiEx(GST_BTC): VOL24:{volume24h_btc_lit}BTC LAST:{last_lit} S:{lowestSell_lit} B:{highestBuy_lit}"
                                      else:
                                        fe_msg = "Error in FreiEx(GST) response"
                                    except KeyboardInterrupt as ex:
                                        print("ex:",str(ex),flush=True)
                                        raise e
                                    except BaseException as ex:
                                        print("ex:",str(ex),flush=True)
                                        tb.print_exc()
                                        import sys
                                        sys.stdout.flush()
                                        sys.stderr.flush()
                                    print("after freiexchange poll", flush=True)

                                    #exmo and frei
                                    if ENABLE_EXMO:
                                     try:
                                      import urllib.request
                                      url = "http://api.exmo.com/v1/ticker/"
                                      print("querying %s"%(url,), flush=True)
                                      exmo_ticker = json.loads(urllib.request.urlopen(url).read())
                                      #print("exmo_ticker:", exmo_ticker)
                                      #"USD_RUB":{"buy_price":"63.520002", "sell_price":"63.7", "last_trade":"63.678587", "high":"64.21396756", "low":"63.35", "avg":"63.78778311", "vol":"281207.5729779", "vol_curr":"17906900.90093241", "updated":1564935589 }
                                      #"BTC_RUB":{"buy_price":"692674.53013854","sell_price":"694990", "last_trade":"693302.09","high":"700000","low":"675000.00100102", "avg":"687445.89449801","vol":"223.90253022", "vol_curr":"155232092.15894149", "updated":1564935590 }
                                      #exmo_BTC_RUB_json = exmo_ticker["BTC_RUB"]
                                      exmo_BTC_USD_json = exmo_ticker["BTC_USD"] if not 'error' in exmo_ticker else None
                                      exmo_ETH_USD_json = exmo_ticker["ETH_USD"] if not 'error' in exmo_ticker else None
                                      #exmo_USD_RUB_json = exmo_ticker["USD_RUB"]

                                      exmo_BTC_USD_sell_price = exmo_BTC_USD_json["sell_price"] if not 'error' in exmo_ticker else None
                                      btcToUsdFloat = float(exmo_BTC_USD_sell_price) if not 'error' in exmo_ticker else None
                                      btcToRurFloat = float(exmo_ticker["BTC_RUB"]["buy_price"]) if not 'error' in exmo_ticker else None

                                      if 'error' in exmo_ticker:
                                        ircProtocolDisplayText_exmo="Exmo API returned error: '%s'" % str(exmo_ticker['error'])
                                      else:
                                        ircProtocolDisplayText_exmo = 'Курс Exmo: '+ \
                                            'BTC/USD S '+str(format_currency(exmo_BTC_USD_sell_price))+' B '+str(format_currency(exmo_BTC_USD_json["buy_price"]))+" | "+ \
                                            'ETH/USD S '+str(format_currency(exmo_ETH_USD_json["sell_price"]))+' B '+str(format_currency(exmo_ETH_USD_json["buy_price"]))+" | "+ \
                                            "BTC/RUR S "+str(format_currency(float(exmo_ticker["BTC_RUB"]["sell_price"])))+' B '+str(format_currency(float(exmo_ticker["BTC_RUB"]["buy_price"])))+"."

                                     except (ConnectionError, Timeout, TooManyRedirects) as e:
                                      print(__name__, e, flush=True)

                                     #btcToRurFloat = None
                                     is_dialogue_with_master = False
                                     if btcToRurFloat is not None and is_dialogue_with_master:
                                        gnome2rur = btcToRurFloat * gnome_btc_amount2_BTC_float
                                        gnomeDeltaGlobalRur = gnome2rur-gnome1rur
                                        measurementRur1=measurementRur2
                                        measurementRur2=gnome2rur
                                        gnomeDeltaLocalRur = measurementRur2-measurementRur1
                                        print("gnome_btc_amount2_BTC_float:", gnome_btc_amount2_BTC_float, "gnome2rur:", gnome2rur, "btcToRurFloat:", btcToRurFloat, "gnomeDeltaGlobalRur:", gnomeDeltaGlobalRur, "measurementRur1:", measurementRur1, "measurementRur2:", measurementRur2, "gnomeDeltaLocalRur:", gnomeDeltaLocalRur, flush=True);
                                        gnomeHodlDeltaStr="Всего выросло: %s%s руб. Локально: %s%s руб. — %s" % ( \
                                                    ("+" if gnomeDeltaGlobalRur>=0 else "") , format_currency(gnomeDeltaGlobalRur) , \
                                                    ("+" if gnomeDeltaLocalRur>=0 else "") , format_currency(gnomeDeltaLocalRur) , \
                                                        ("растёт денежка, растёт!"  if gnomeDeltaLocalRur>=0 
                                                                                    else "убытки-с =( читаем книжку! http://knijka.i2p/"));
                                     else:
                                        gnomeHodlDeltaStr="??? руб.";

                                    # Bitcoin.com Markets API
                                    # Coming soon
                                    # https://developer.bitcoin.com/

                                    if ENABLE_EXMO:
                                        self.send_res_exc = '%s | %s | %s | %s' % (str(fe_msg), rate_cmc_str, ircProtocolDisplayText_exmo, kuna_str) #, gnomeHodlDeltaStr
                                    else:
                                        self.send_res_exc = f'{fe_msg} | {rate_cmc_str} | {kuna_str}' #, gnomeHodlDeltaStr
                                    print("self.send_res_exc:", self.send_res_exc, flush=True)
                                    print("where_mes_exc:", where_mes_exc, flush=True)
                                    self.send('PRIVMSG %s :\x033%s\r\n'%(where_mes_exc,self.send_res_exc))
                                    print(__name__, "point 6.1", flush=True)
                                except (ConnectionError, Timeout, TooManyRedirects) as e:
                                    print(__name__, "point 6.1.ex", flush=True)
                                    print(__name__, e, flush=True)
                                except KeyError as e:
                                    print(__name__, e, flush=True)
                                    self.send_res_exc = 'error in response json: %s' % str(e)
                                    print(__name__, "self.send_res_exc:", self.send_res_exc, flush=True)
                                    print(__name__, "where_mes_exc:", where_mes_exc, flush=True)
                                    self.send('PRIVMSG %s :%s\r\n'%(where_mes_exc,self.send_res_exc))
                                    print(__name__, "send exited", flush=True)
                            #print(__name__, "point 5.0", flush=True)
                      except:
                        #print(__name__, "point 5.1", flush=True)
                        tb.print_exc()
                        import sys
                        sys.stderr.flush()
                        raise()


            except KeyboardInterrupt as e:
                raise e
            except:
                import traceback as tb
                tb.print_exc()
                import sys
                sys.stderr.flush()
                print("self.irc_socket.close(), iterate", flush=True);
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


from multiprocessing import Process
import os

def init_and_loop(settings_key, connection_props):
    print('init_and_loop settings_key="%s"' % settings_key)
    print('%s.parent pid:' % settings_key, os.getppid())
    print('%s.pid:' % settings_key, os.getpid())
    bot = MyBot(settings_key, connection_props)
    bot.login_and_loop()

#launch two threads with botsconn and login_and_loop
def launch_all():
    from settings import getconfig
    print("processing configs")
    connections = getconfig()["connections"]
    for key in connections.keys():
        conn_props = connections[key]
        print("launching connection '"+key+"', conn_props='"+str(conn_props)+"'")
        Process(target=init_and_loop, args=(key,conn_props,)).start()
        print("launched connection '"+key+"'")
    print("processed all connections")

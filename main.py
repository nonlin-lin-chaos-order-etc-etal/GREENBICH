import socket
import sys
import time
import requests
import settings
import translate_krzb
import whois

from urllib.parse import unquote

def format_currency(value):
    return "{:0,.2f}".format(float(value))

# Function shortening of ic.send.  
def send(mes):
  return irc.send(bytes(mes,'utf-8'))

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
          
# Install min & max timer vote.  
min_timer = 30
max_timer = 300

network = settings.settings('network')
port = int(settings.settings('port'))
channel = settings.settings('channel')
BOT_NAME_PREFIX = settings.settings('botName')
botName = BOT_NAME_PREFIX
botNickSalt = 0
masterName = settings.settings('masterName')
coinmarketcap_apikey = settings.settings('coinmarketcap_apikey')
titleEnabled = bool(settings.settings('titleEnabled'))
onlycmc = bool(settings.settings('onlycmc'))
enableother1 = not onlycmc
gnome1rur = float(settings.settings('gnome1_rur_float'))
gnomeBtcTransaction1 = float(settings.settings('gnome_btc_transaction1_BTC_float')) #BTC

while True:
    print("---new iter---")
    try:
        print("new socket(AF_INET,SOCK_STREAM)")
        irc = socket.socket (socket.AF_INET, socket.SOCK_STREAM)
        print("connecting... network=["+network+"] port=["+str(port)+"]…")
        irc.connect ((network, port))
        print("connected, sending login handshake, botName=["+botName+"]…")
        #print (irc.recv(2048).decode("UTF-8"))
        send('NICK '+botName+'\r\n')
        send('USER '+botName+' '+botName+' '+botName+' :ircbot\r\n')
        #send('NickServ IDENTIFY '+settings.settings('password')+'\r\n')
        #send('MODE '+botName+' +x')

        #-------Global_variables--------------------
           
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
        btc_usd_su = str('')
        eth_usd_su = str('')
        usd_rub_su = str('')
        eur_rub_su = str('')
        time_vote = 0

        whois_ip = ''
        whois_ip_get_text = ''

        timer_exc = 0
        time_exc = 0

        where_mes_exc = ''
        t2 = 0

        #-------Massives----------------------------

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
                data = irc.recv(2048).decode("UTF-8")
                print("rx:["+data+"]")
                if data=="":
                    print("data=='', irc.close(), keepingConnection=False, iterate");
                    irc.close()
                    keepingConnection=False
                    continue
            except UnicodeDecodeError as decodeException:
                print("UnicodeDecodeError ", decodeException)
                continue
            tokens1 = data.split(" ");
            if len(tokens1)>1 and tokens1[1]=="433": #"Nickname is already in use" in data
                botNickSalt=botNickSalt+1
                botName = BOT_NAME_PREFIX+str(botNickSalt)
                send('NICK '+botName)
                continue
            if data.find('PING') != -1:
                send('PONG '+data.split(" ")[1]+'\r\n')

            #001 welcome
            spws = tokens1
            if len(spws) > 1 and spws[1]=="001":
                send('JOIN '+channel+' \r\n')
                continue
            
            # Make variables Name, Message, IP from user message.
            if data.find('PRIVMSG') != -1:
                name = data.split('!',1)[0][1:]
                message = data.split('PRIVMSG',1)[1].split(':',1)[1]
            try:
                ip_user=None#"data.split('@',1)[1].split(' ',1)[0]
            except:
                print('error getting ip_user')

            if enableother1:
                #-----------Translate_krzb---------    

                if 'PRIVMSG '+channel+' :!п ' in data \
                   or 'PRIVMSG '+botName+' :!п ' in data:
                    if 'PRIVMSG '+channel+' :!п ' in data:
                        where_message = channel            
                    elif 'PRIVMSG '+botName+' :!п ' in data:
                        where_message = name
                    
                    tr_txt = message.split('!п ',1)[1].strip()
                    res_txt = translate_krzb.tr(tr_txt)
                    send('PRIVMSG '+where_message+' :\x02перевод с кракозябьечьего:\x02 '+res_txt+'\r\n')

            #-----------Bot_help---------------

            if 'PRIVMSG '+channel+' :!help' in data or 'PRIVMSG '+botName+' :!справка' in data or 'PRIVMSG '+botName+' :!помощь' in data or 'PRIVMSG '+botName+' :!хелп' in data:
                send('NOTICE %s : Помощь по командам бота:\r\n' %(name))
                send('NOTICE %s : ***Функция опроса: [!опрос (число) сек (тема опрос)], например\
        (пишем без кавычек: \"!опрос 60 сек Вы любите ониме?\", если не писать время, то время\
        установится на 60 сек\r\n' %(name))
                send('NOTICE %s : ***Функция курса: просто пишите (без кавычек): \"!курс\". Писать\
        можно и в приват боту\r\n' %(name))
                send('NOTICE %s : ***Функция whois: что бы узнать расположение IP, просто пишите\
        (без кавычек): \"!где айпи (IP)\", пример: \"!где айпи \
        188.00.00.01\". Писать можно и в приват к боту\r\n' %(name))
                send('NOTICE %s : ***Функция перевода с английских букв на русские: \"!п tekst perevoda\", пример: \"!п ghbdtn\r\n' %(name))

            #-----------Anti_flood-------------

            # Count of while.  
            while_count += 1
            if while_count == 50:
                while_count = 0
                dict_count = {}
                    
            # Insert nick in dict: dic_count.  
            if data.find('PRIVMSG') != -1 and name not in dict_count and\
               name not in list_floodfree:
                dict_count[name] = int(1)
                if 'PRIVMSG '+channel in data:
                    where_message = channel
                elif 'PRIVMSG '+botName in data:
                    where_message = botName
            
            # If new message as last message: count +1.  
            if data.find('PRIVMSG') != -1 and message == dict_users.get(name)\
               and name not in list_floodfree:
                dict_count[name] += int(1)
            
            # Add key and value in massiv.  
            if data.find('PRIVMSG') != -1 and name not in list_floodfree:
                dict_users[name] = message
            
            # Message about flood and kick. 
            #if data.find('PRIVMSG') != -1 and name not in list_floodfree:
            #    for key in dict_count: 
            #        if dict_count[key] == 3 and key != 'none':
            #            send('PRIVMSG '+where_message+' :'+key+', Прекрати флудить!\r\n')
            #            dict_count[key] += 1
            #        elif dict_count[key] > 5 and key != 'none':
            #            send('KICK '+channel+' '+key+' :Я же сказал не флуди!\r\n')
            #            dict_count[key] = 0
                    
              
            # Out command.  
            if data.find('PRIVMSG '+channel+' :!quit') != -1 and name == masterName:
                send('PRIVMSG '+channel+' :Хорошо, всем счастливо оставаться!\r\n')
                send('QUIT\r\n')
                sys.exit()

            # Message per bot.  
            if "PRIVMSG %s :!напиши "%(channel) in data or\
               "PRIVMSG %s :!напиши "%(botName) in data and name == masterName:
                mes_per_bot = message.split('!напиши ',1)[1]
                send(mes_per_bot)
                
            #---------Whois service--------------------------

            if enableother1:
              if 'PRIVMSG '+channel+' :!где айпи' in data\
               or 'PRIVMSG '+botName+' :!где айпи' in data:

                if 'PRIVMSG '+channel+' :!где айпи' in data:
                    where_message_whois = channel
                    
                elif 'PRIVMSG '+botName+' :!где айпи' in data:
                    where_message_whois = name
                              
                try:
                    whois_ip = data.split('!где айпи ',1)[1].split('\r',1)[0].strip()
                    get_whois = whois.whois(whois_ip)
                    country_whois = get_whois['country']
                    city_whois = get_whois['city']
                    address_whois = get_whois['address']    
                    print(get_whois)

                    if country_whois == None:
                        country_whois = 'None'
                    if city_whois == None:
                        city_whois = 'None'
                    if address_whois == None:
                        address_whois = 'None'    
                               
                    whois_final_reply = ' \x02IP:\x02 '+whois_ip+' \x02Страна:\x02 '+\
                    country_whois+' \x02Адресс:\x02 '+address_whois+'\r\n'
                    send('PRIVMSG '+where_message_whois+' :'+whois_final_reply)            

                except:
                    print('get Value Error in whois service!')
                    send('PRIVMSG '+where_message_whois+' :Ошибка! Вводите только IP адрес \
        из цифр, разделенных точками!\r\n')
                             
            #---------Info from link in channel-------------
            
            if enableother1 and titleEnabled:
                if 'PRIVMSG %s :'%(channel) in data and '.png' not in data and '.jpg' not in data and '.doc'\
                not in data and 'tiff' not in data and 'gif' not in data and '.jpeg' not in data and '.pdf' not in data:
                    if 'http://' in data or 'https://' in data or 'www.' in data:
                        try:
                           send('PRIVMSG %s :%s\r\n'%(channel,link_title(data)))
                        except requests.exceptions.ConnectionError:
                            print('Ошибка получения Title (requests.exceptions.ConnectionError)')
                            send('PRIVMSG '+channel+' :Ошибка, возможно такого адреса нет\r\n')
                        except:
                            print('Error link!')  
            #---------Voting--------------------------------
                        
            t = time.time()
            if enableother1:
              if '!стоп опрос' in data and 'PRIVMSG' in data and name == masterName:
                t2 = 0
                print('счетчик опроса сброшен хозяином!')
            if enableother1:
              if 'PRIVMSG '+channel+' :!опрос ' in data and ip_user not in list_bot_not_work:
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
                        send('PRIVMSG %s :Ошибка ввода таймера голосования.\
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
                    send('PRIVMSG %s :Начинается опрос: \"%s\". Опрос будет идти \
        %d секунд. Чтобы ответить "да", пишите: \"!да\" \
        ", чтобы ответить "нет", пишите: \"!нет\". Писать можно как открыто в канал,\
        так и в приват боту, чтобы голосовать анонимно \r\n' % (channel,message_voting,time_vote))
                    list_vote_ip = []
                        
            # If find '!да' count +1.  
            if enableother1:
              if data.find('PRIVMSG '+channel+' :!да') != -1 or data.find('PRIVMSG '+botName+' :!да') != -1:
                if ip_user not in list_vote_ip and t2 != 0:
                    count_vote_plus +=1
                    dict_voted[name] = 'yes'
                    list_vote_ip.append(ip_user)
                    # Make notice massage to votes user.  
                    send('NOTICE '+name+' :Ваш ответ \"да\" учтен!\r\n')

            # If find '!нет' count +1.  
            if enableother1:
              if data.find('PRIVMSG '+channel+' :!нет') != -1 or data.find('PRIVMSG '+botName+' :!нет') != -1:
                if ip_user not in list_vote_ip and t2 != 0:
                    count_vote_minus +=1
                    dict_voted[name] = 'no'
                    list_vote_ip.append(ip_user)
                    # Make notice massage to votes user.  
                    send('NOTICE '+name+' :Ваш ответ \"нет\" учтен!\r\n')
           
            # If masterName send '!список голосования': send to him privat messag with dictonary Who How voted.  
            if enableother1:
              if data.find('PRIVMSG '+botName+' :!список опроса') !=-1 and name == masterName:
                for i in dict_voted:
                    send('PRIVMSG '+masterName+' : '+i+': '+dict_voted[i]+'\r\n')

            # Count how much was message in channel '!голосование'.  
            if enableother1:
              if data.find('PRIVMSG '+channel+' :!опрос') != -1 and t2 != 0:
                count_voting += 1

            # If voting is not end, and users send '!голосование...': send message in channel.  
            t4 = time.time()
            if enableother1:
              if data.find('PRIVMSG '+channel+' :!опрос') != -1 and t4-t2 > 5:
                t3 = time.time()
                time_vote_rest_min = (time_vote-(t3-t2))//60
                time_vote_rest_sec = (time_vote-(t3-t2))%60
                if (time_vote-(t3-t2)) > 0:
                    send('PRIVMSG %s : Предыдущий опрос: \"%s\" ещё не окончен, до окончания \
        опроса осталось: %d мин %d сек\r\n \
        ' % (channel,message_voting,time_vote_rest_min,time_vote_rest_sec))

            # Make variable message rusults voting.  
            vote_all = count_vote_minus + count_vote_plus
            voting_results = 'PRIVMSG %s : результаты опроса: \"%s\", "Да" ответило: %d \
        человек(а), "Нет" ответило: %d человек(а), Всего ответило: %d человек(а) \
        \r\n' % (channel, message_voting, count_vote_plus, count_vote_minus, vote_all)

            # When voting End: send to channel ruselts and time count to zero.  
            if t-t2 > time_vote and t2 != 0:
                t2 = 0
                send('PRIVMSG '+channel+' : Опрос окончен!\r\n')
                send(voting_results)
            
            #:nick!uname@addr.i2p PRIVMSG #ru :!курс
            dataTokensDelimitedByWhitespace = data.split(" ")
            #dataTokensDelimitedByWhitespace[0] :nick!uname@addr.i2p
            #dataTokensDelimitedByWhitespace[1] PRIVMSG
            #dataTokensDelimitedByWhitespace[2] #ru
            #dataTokensDelimitedByWhitespace[3] :!курс
            if (len(dataTokensDelimitedByWhitespace) > 3) and ('!курс' in dataTokensDelimitedByWhitespace[3]):
                print('!курс')
                communicationsLineName = dataTokensDelimitedByWhitespace[2]
                where_mes_exc = communicationsLineName
                print('курс куда слать будем:', where_mes_exc)

                try:
                    #This example uses Python 2.7 and the python-request library.
                    
                    from requests import Request, Session
                    from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
                    import json
                    
                    url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest'
                    parameters = {
                      'symbol':'BTC,ETH',
                      'convert':'USD'
                    }
                    headers = {
                      'Accepts': 'application/json',
                      'X-CMC_PRO_API_KEY': coinmarketcap_apikey,
                    }
                    
                    session = Session()
                    session.headers.update(headers)
                    
                    try:
                      print('!курс session.get url='+url)
                      response = session.get(url, params=parameters)
                      cmc = json.loads(response.text)
                      print("cmc:", cmc)
                      btc_usd = cmc["data"]["BTC"]["quote"]["USD"]["price"]
                      eth_usd = cmc["data"]["ETH"]["quote"]["USD"]["price"]
                      btc_usd_str = str(format_currency(btc_usd))
                      eth_usd_str = str(format_currency(eth_usd))
                      
                      send_res_exc_cmc = '\x033Курс CoinMarketCap: \x02BTC/USD:\x02 '+btc_usd_str+' \x02ETH/USD:\x02 '+eth_usd_str+"."

                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                      print(e)

                    btcToUsdFloat = None
                    btcToRurFloat = None
                    #exmo
                    try:
                      import urllib.request
                      url = "http://api.exmo.com/v1/ticker/"
                      print("querying %s"%(url,))
                      exmo_ticker = urllib.request.urlopen(url).read()
                      exmo_ticker = json.loads(exmo_ticker)
                      print("exmo_ticker:", exmo_ticker)
                      #"USD_RUB":{"buy_price":"63.520002", "sell_price":"63.7", "last_trade":"63.678587", "high":"64.21396756", "low":"63.35", "avg":"63.78778311", "vol":"281207.5729779", "vol_curr":"17906900.90093241", "updated":1564935589 }
                      #"BTC_RUB":{"buy_price":"692674.53013854","sell_price":"694990", "last_trade":"693302.09","high":"700000","low":"675000.00100102", "avg":"687445.89449801","vol":"223.90253022", "vol_curr":"155232092.15894149", "updated":1564935590 }
                      #exmo_BTC_RUB_json = exmo_ticker["BTC_RUB"]
                      exmo_BTC_USD_json = exmo_ticker["BTC_USD"]
                      #exmo_USD_RUB_json = exmo_ticker["USD_RUB"]

                      exmo_BTC_USD_sell_price = exmo_BTC_USD_json["sell_price"]
                      btcToUsdFloat = float(exmo_BTC_USD_sell_price)

                      btcToRurFloat = float(exmo_ticker["BTC_RUB"]["sell_price"])
                      ircProtocolDisplayText_exmo = '\x033Курс Exmo: \x02BTC/USD \x02\x02sell price:\x02 '+str(format_currency(exmo_BTC_USD_sell_price))+', \x02buy price:\x02 '+str(format_currency(exmo_BTC_USD_json["buy_price"]))+"."


                    except (ConnectionError, Timeout, TooManyRedirects) as e:
                      print(e)

                    if btcToRurFloat is not None:
                        gnome2rur = btcToRurFloat * gnomeBtcTransaction1
                        gnomeDeltaRur = gnome2rur-gnome1rur
                        gnomeHodlDeltaStr="%s%s руб. — %s" % ( ("+" if gnomeDeltaRur>=0 else "-") , format_currency(gnomeDeltaRur) , ("растёт денежка, растёт!" if gnomeDeltaRur>=0 else "убытки-с =( читаем книжку! http://knijka.i2p/"));
                    else:
                        gnomeHodlDeltaStr="??? руб.";
                    send_res_exc = '%s | %s | Гном.HODLER: %s' % (send_res_exc_cmc, ircProtocolDisplayText_exmo, gnomeHodlDeltaStr)
                    print("send_res_exc:", send_res_exc)
                    print("where_mes_exc:", where_mes_exc)
                    send('PRIVMSG %s :%s\r\n'%(where_mes_exc,send_res_exc))
                except (ConnectionError, Timeout, TooManyRedirects) as e:
                    print(e)
    except ConnectionResetError as e: #on write to socket?
        print("ConnectionResetError ", e)
        print("irc.close(), iterate");
        irc.close()
        continue



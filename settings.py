import json

# read file
with open('local.json', 'r') as myfile:
    data=myfile.read()
config = json.loads(data)

network = 'irc.tambov.ru'
port = 7770
channel = '#magi'
botName = 'BichBot'
masterName = 'her1001'
list_floodfree = ['Батый', 'Батый_', botName, masterName]
list_bot_not_work = ['iphone.telenet.ru', 'ec2-54-211-164-67.compute-1.amazonaws.com']

def settings(x):
    if x == 'network':
        return network
    elif x == 'port':
        return port
    elif x == 'botName':
        return botName
    elif x == 'masterName':
        return masterName
    elif x == 'password':
        return config["password"]
    elif x == 'list_floodfree':
        return list_floodfree
    elif x == 'channel':
        return channel
    elif x == 'list_bot_not_work':
        return list_bot_not_work
    elif x == 'coinmarketcap_apikey':
        return config["coinmarketcap_apikey"]
    else: return 'N/A'

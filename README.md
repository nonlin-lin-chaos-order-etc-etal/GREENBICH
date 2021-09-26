# 💚👾💚 Зелёный Бич (GreenBich) 💚👾💚

## 💚👾💚 Green Ecology bot 💚👾💚

Ecology is disjointly more important than religions and all the other things and domains.

## Temporary Official Site

💚 ⊙ https://BiocentricClouds.Dev/ 🐸🌈🧚🐁+∞¤💎💚vv∞8👾☯🌌💚💞🧙💚

--------*

Россия или экология? Русские и россияне сами о себе позаботятся, а экология существенно важнее. И всё, кроме религии, существенно менее важно. И религия тоже в целом менее важна, чем экология.

Думаю, что религия это комфорт, доброта, прогресс. А вот экология в рамках настоящего и бесконечного* будущего кардинально принципиально важнее, нежели комфорт и уют.

И дизджойнтно важнее. Ecology is disjointly more important than religion and all the other things and domains.

## Заметки по инсталляции клона бота

Put the following into `local.json`:
```
{
    "connections": {
        "net1key":{
             "irc_server_hostname":"127.0.0.1"
            ,"port":6667
            ,"channelsProps":{"#chan1":{"news_count":5},"#chan2":{"news_count":10},"#chan3":{"news_count":1}}
            ,"password": "x"
            ,"titleEnabled":false
            ,"onlycmc":true
            ,"enable_krako_translation":true
            ,"enable_hextoip":true
            
            ,"InitialBotNick":"botnick"
        },
        "net2key":{
            //same as above
        },
        ...
    }
    ,"coinmarketcap_apikey": "xxxx"
    ,"rapidapi_appkey":"xxxx"
    ,"rapidapi_ctxwebsearch_X-RapidAPI-Host":"contextualwebsearch-websearch-v1.p.rapidapi.com"
    ,"dataforseo_api_login":"xxx@xxx"
    ,"dataforseo_api_password":"xxxx"
    ,"newsapi_apikey":"xxxx"
    ,"gnome1_rur_float":1.0
    ,"gnome_btc_transaction1_BTC_float": 0.1
    ,"gnome_btc_amount2_BTC_float": 0.1
    ,"master_secret":"secretpasswhere"
    ,"list_floodfree":["nick1", "nick2"]
    ,"list_bot_not_work":["host1", "host2"]
}
    
```

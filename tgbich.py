# tgbich.py

from abstractbich import BichBot
from helpers import get_pretty_json_string, shell, LOG_TRACE

import os
import asyncio
from aiogram import Bot, Dispatcher, types


class TgBich(BichBot):
    def __init__(self, settings_key, connection_settings: dict, config):
        super(TgBich, self).__init__(settings_key, connection_settings, config)
        self.BOT_TOKEN = self.connection_settings('BOT_TOKEN')
        print(f"{self}: entering asyncio.run(self.main())");
        asyncio.run(self.main())
        print(f"{self}: completed asyncio.run(self.main())");


    async def cmd_start_handler(self, event: types.Message):
        await event.answer(
            f"""Hello, {event.from_user.get_mention(as_html=True)} 👋!

<b>Help:</b>

/m /markets - see the markets report (курсы валют, индикаторы и прочее);
/h /help - see the help and welcome message.

<b>Bot author:</b> @ConstAlphaRusDev (Гипн aka гном)""",
            parse_mode=types.ParseMode.HTML,
        )

    async def cmd_markets_handler(self, event: types.Message):
        markets_report_str = self.compose_markets_report()
        print(f"{self}: markets_report_str '{markets_report_str}'");
        await event.answer(
            markets_report_str,
            parse_mode=types.ParseMode.HTML,
        )

    async def main(self):
        print(f"{self}: new Bot");
        self.bot = Bot(token=self.BOT_TOKEN)
        print(f"{self}: done new Bot");
        try:
            print(f"{self}: new Dispatcher");
            self.disp = Dispatcher(bot=self.bot)
            print(f"{self}: done new Dispatcher");
            self.disp.register_message_handler(self.cmd_start_handler, commands={"start", "s", "h", "help", "?"})
            self.disp.register_message_handler(self.cmd_markets_handler, commands={"markets", "m", "курс"})
            print(f"{self}: entering start_polling()");
            await self.disp.start_polling()
            print(f"{self}: completed start_polling()");
        finally:
            print(f"{self}: finally: entering bot.close()");
            await self.bot.close()
            print(f"{self}: finally: completed bot.close()");



def run_tgbich(settings_key, connection_settings: dict, config):
    connection_props = connection_settings
    print(f'run_tgbich settings_key="{settings_key}"')
    print(f'{settings_key}.parent pid: {os.getppid()}')
    print(f'{settings_key}.pid: {os.getpid()}')
    bot = TgBich(settings_key, connection_settings, config)
    bot.login_and_loop()


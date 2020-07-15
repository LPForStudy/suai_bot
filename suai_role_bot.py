import json
import discord
from datetime import datetime
from discord.ext import commands

# Класс бота; Наследуем класс Bot из commands
cogs = ['cmd_cog'] # Модули (другие файлы)
class Bot(commands.Bot):
    def __init__(self):
        # super - обращение к наследуемLому классу
        # __init__ - отвечает за инициализацию класса
        super().__init__(command_prefix="!", case_insensitive=True)

        self.uptime = datetime.utcnow() # Просто берем аптайм для теста
        for cog in cogs:
            #import traceback
            #try:
            self.load_extension(cog) # загружаем по одному
            #except:
            #    traceback.print_exc()

    async def on_ready(self): # Одноразовый ивент, когда все системы бота запущены
        print('My name: ' + self.user.name)

bot = Bot() # создаем экземпляр бота
with open("config.json", "r") as conf:
    config = json.load(conf)

#Запуск бота
#print(config)
bot.run(config['TOKEN'])
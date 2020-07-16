import json
from discord.ext import commands
from discord.ext.commands import has_permissions
import discord
from google_sheet import gSheet
from googleapiclient import discovery
from oauth2client.service_account import ServiceAccountCredentials
import httplib2

class cmd_cog(commands.Cog):
    groups_number = 5 # Здесь задается список групп в таблице
    
    #Сервисные переменные для доступа к таблицам
    CREDENTIALS_FILE = 'credentials.json'  #  ← имя скачанного файла с закрытым ключом
    credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, ['https://www.googleapis.com/auth/spreadsheets','https://www.googleapis.com/auth/drive'])
    httpAuth = credentials.authorize(httplib2.Http())
    service = discovery.build('sheets', 'v4', http = httpAuth)
    spreadsheetId = '1K1zp958fmDLVgroOM5iqtTzvNHzmFijRyd3675PsK-o'
    
    bot = None
    bot_role_name = None
    mode = None
    
    #Массивы для хранения информации о группах
    title = [0]*groups_number
    sheet_id = [0]*groups_number
    table = [0]
    students = [0]

    sheet=gSheet() #Объявление объекта класса, ответственного за работу с таблицей

    def __init__(self, bot):
        self.bot = bot
        self.mode = None
        self.bot_role_name = None
        with open('config.json', 'r') as file:
            config = json.load(file)
            self.bot_role_name = config['ROLE_NAME']
            self.mode = config['MODE']

    ### Текстовые команды ###
    @commands.command(name='ping')
    async def pp(self, ctx):
        await ctx.send('Модуль регистрации работает.')

    @commands.command(name='soft')
    @has_permissions(administrator=True)  
    async def softMode(self, ctx):
        with open("config.json","r") as conf:
            data = json.load(conf)
        with open("config.json","w") as conf:
            data['MODE'] = "soft"
            self.mode = "soft"
            json.dump(data, conf)
        await ctx.send("Установлен мягкий режим проверки.")

    @commands.command(name='hard')
    @has_permissions(administrator=True)  
    async def hardMode(self, ctx):
        with open("config.json","r") as conf:
            data = json.load(conf)
        with open("config.json","w") as file:
            data['MODE'] = "hard"
            self.mode = "hard"
            json.dump(data, file)
        await ctx.send("Установлен строгий режим проверки.")
    
    @commands.command(name='getmode')
    async def getMode(self, ctx):
        with open("config.json", "r") as conf:
            config = json.load(conf)
            self.mode = config['MODE']
            await ctx.send("Current mode: " + config['MODE'])
        
    @commands.command(name='register')
    #!register <group_id> <Full name>
    async def _register(self, ctx, *args):
        if self.mode != 'hard':
            return
        member = ctx.message.author
        if 0 <= len(args) < 4:
            await ctx.send(f"{member.mention}, неверное количество аргументов в команде.\n`!register <группа> <фамилия> <имя> <отчество>`")
            return
        group = str(args[0])
        fio = (args[1] + ' ' + args[2] + ' ' + args[3]).lower()
        # Поиск группы
        from discord.utils import get
        invalid_role = get(member.guild.roles, name = "invalid_name")
        if invalid_role not in member.roles:
            await ctx.send(f"{member.mention}, у тебя уже имеется группа.")
            return

        group_role = get(member.guild.roles, name = group)
        if group_role == None:
            await ctx.send(f"{member.mention}, такой группы не существует.")
            return
        # Поиск студента... Копипаст кода, оптимизация?
        self.sheet.getTitles(self.service,self.spreadsheetId,self.title,self.sheet_id,self.groups_number)
        req_id = 0
        for title in self.title:
            if group == title:
                break
            else:
                req_id = req_id + 1

        self.students = self.sheet.getStudents(self.service, self.spreadsheetId, self.title[req_id], 
                                               self.table, self.students, self.groups_number)
        for student in self.students:
            if fio == student[0].lower():
                await member.add_roles(group_role)
                await ctx.send(f"{member.mention} - установлена группа {group}.")
                await member.remove_roles(invalid_role)
                return
        await ctx.send(f"{member.mention}, ученик в такой группе не найден.")
  
    ### Мягкий режим ###
    async def soft(self, before, after):
        # Достаем список всех ролей
        from discord.utils import get
        
        invalid_role = get(after.guild.roles, name = "invalid_name")
        
        if invalid_role == None:
            await after.guild.create_role(name="invalid_name")
            invalid_role = get(after.guild.roles, name = "invalid_name")
        
        if invalid_role not in after.roles:
            return
        #Если пользователь обнулил свой ник
        if after.nick == None:
            return

        bot_role = get(before.guild.roles, name = self.bot_role_name)
        groups = before.guild.roles
        groups = [x for x in groups if x.position in range(invalid_role.position+1, bot_role.position)]
        
        # Добавляем группы
        for group in groups:
            if after.nick.find(group.name) != -1:
                await after.add_roles(group)
                await after.remove_roles(invalid_role)
                channel = after.guild.system_channel
                await channel.send('Группа установлена для {0.mention}.'.format(after._user))
                return

    ### Жесткий режим ###
    async def hard(self, before, after):
        
        #self.sheet.getStudents(self.service, self.spreadsheetId, self.title, self.sheet_id, self.table, self.students, self.groups_number) # Получаем информацию о студентах из таблицы
        self.sheet.getTitles(self.service,self.spreadsheetId,self.title,self.sheet_id,self.groups_number)
        
        # Достаем список всех ролей
        from discord.utils import get
        invalid_role = get(after.guild.roles, name = "invalid_name")
        
        if invalid_role == None:
            await after.guild.create_role(name="invalid_name")
            invalid_role = get(after.guild.roles, name = "invalid_name")

        if invalid_role not in after.roles:
            return
        
        #Если пользователь обнулил свой ник
        if after.nick == None:
            return

        #Роль бота нужна для позиционирования
        bot_role = get(before.guild.roles, name = self.bot_role_name)
        #Загружаем и отсеиваем роли. Роль неправильных юзеров будет над everyone, нужные между ней и ролью бота
        groups = before.guild.roles
        groups = [x for x in groups if x.position in range(invalid_role.position+1, bot_role.position)]
        
        req_id = 0
        #Поиск нужной группы по указанной в никнейме группе
        for title in self.title:
            if after.nick.find(title) != -1:
                break
            else:
                req_id = req_id + 1
        if(req_id >= self.groups_number):
            return
        #Получаем данные с листа        
        self.students = self.sheet.getStudents(self.service, self.spreadsheetId, self.title[req_id], self.table, self.students, self.groups_number)
        #Отправлять на сервер, а не в личные сообщения
        channel = after.guild.system_channel

        #Ищем в полученном массиве студентов
        for student in self.students:
            if after.nick.lower().find(student[0].lower()) != -1:
                #Если нашли нужного студента в таблице, просматриваем список групп на сервере и выдаем ему указанную в его нике
                for group in groups:
                    if after.nick.find(group.name) != -1:
                        await after.add_roles(group)
                        await after.remove_roles(invalid_role)
                        
                        await channel.send('Группа установлена для {0.mention}.'.format(after._user))
                        return
        await channel.send('Такого студента нет в списке {0.mention}.'.format(after._user))
    ### Прослушки событий ###
    @commands.Cog.listener()
    async def on_member_join(self, member):
        from discord.utils import get
        invalid_role = get(member.guild.roles, name = "invalid_name")
        
        channel = member.guild.system_channel
        if channel is not None:
            await channel.send('Добро пожаловать на сервер - {0.mention}. Команды бота: 1)!register <группа> <Фамилия> <Имя> <Отчество>.'.format(member))
            await member.add_roles(invalid_role, reason='New member')

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        # Строгая проверка на событие смены ника
        if after.nick == before.nick:
            return

        if self.mode == 'soft':
            await self.soft(before, after)
        elif self.mode == 'hard':
            await self.hard(before, after)

def setup(bot):
    bot.add_cog(cmd_cog(bot))
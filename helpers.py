from datetime import datetime
import requests
import asyncio
import discord
import cards_list
import io
ALLOWED_USER_IDS = [int(id) for id in os.getenv('ALLOWED_USER_IDS').split(',')]
LOGS_ID = int(os.getenv('LOGS_ID'))
headers = {
    'Authorization': os.getenv('KEY')
}

cards = []

def check_permission(interaction):
    allowed_users = ALLOWED_USER_IDS
    return interaction.user.id in allowed_users

def addCard(data):
    pairs = data.split()
    for pair in pairs:
        card, nickname = pair.split(':')
        cards_list.addCard(card, nickname)

def removeCard(data):
    cards = data.split()
    for card in cards:
        if card.isdigit() == True:
            cards_list.removeCard(card)
        else:
            cards_list.removeCardbyName(card)

def getCards():
    cards = cards_list.getCards()
    formatted_cards = [f"`{card.split(':')[1]}`:{card.split(':')[0]}" for card in cards]
    return " ".join(formatted_cards) + "\n"

def getBalance():
    balLink = 'https://spworlds.ru/api/public/card'
    res = requests.get(balLink, headers=headers)
    balance = res.json()['balance']
    return f'> 🏦 Баланс казны: `{balance} АР`\n'

def SalaryTransaction(nickname):
    payback = {
        'receiver': nickname['card'],
        'amount': nickname['amount'],
        'comment': f'ЗП ФБР: {nickname["name"]}'
    }
    transLink = 'https://spworlds.ru/api/public/transactions'
    post = requests.post(transLink, headers=headers, json=payback)
    return post

def Transaction(nickname, comment):
    comment = nickname["name"] if comment is None else comment + " | " + nickname["name"]
    payback = {
        'receiver': nickname['card'],
        'amount': nickname['amount'],
        'comment': f'Перевод: {comment}'
    }
    transLink = 'https://spworlds.ru/api/public/transactions'
    post = requests.post(transLink, headers=headers, json=payback)
    return post

def importCards(data):
    pairs = data.split()
    for pair in pairs:
        card, amount = pair.split(':')
        name = cards_list.getName(card)
        if name is None:
            return False
        trans = {
            'card': card,
            'name': name[0],
            'amount': int(amount)
        }
        cards.append(trans)
    return True

async def deny_access(interaction):
    message = await interaction.response.send_message('> ❌ Отказано в доступе', ephemeral=True)
    await asyncio.sleep(5)
    await message.delete()

class SearchButtonView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Найти', style=discord.ButtonStyle.blurple, custom_id='search_button')
    async def search_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SearchModal())

class SearchModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title='Поиск карты')
        self.search_input = discord.ui.TextInput(label='Введите никнейм или номер карты')
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value
        result = searchCard(query)
        await interaction.response.send_message(result, ephemeral=True)

def searchCard(query):
    cards = cards_list.getCards()
    for card in cards:
        card_number, nickname = card.split(':')
        if query == card_number or query == nickname:
            return f'> ✅ Найдено ```{nickname} : {card_number}```'
    return '> ❌ Не найдено'

async def sendLogs(bot, string, avatar_url, avatar_name, logType):
    LOGS_ID = LOGS_ID
    channel = bot.get_channel(LOGS_ID)
    today = datetime.today().strftime("%d.%m")
    if logType == 'salary':
        embed_string = f'💸 Зарплата выдана\n```'
        try:
            pairs = string.split()
            for pair in pairs:
                card, amount = pair.split(':')
                nickname = str(cards_list.getName(card))
                embed_string += f'{nickname[2:-3]} : {amount} АР\n'
            embed_string += '```'
            embed = discord.Embed(description=embed_string, color=discord.Color.green())
            embed.set_footer(text='Выдано ' + avatar_name + f' • {today}', icon_url=avatar_url)
            await channel.send(embed=embed)       
        except:
            print(f'> Ошибко посхалко кароче')
            await channel.send(f'> Ошибко посхалко кароче') 
    if logType == 'payment':
        embed_string = f'💸 Выволнен перевод\n```'
        try:
            pairs = string.split()
            for pair in pairs:
                card, amount = pair.split(':')
                nickname = str(cards_list.getName(card))
                embed_string += f'{nickname[2:-3]} : {amount} АР\n'
            embed_string += '```'
            embed = discord.Embed(description=embed_string, color=discord.Color.green())
            embed.set_footer(text='Исполнитель ' + avatar_name + f' • {today}', icon_url=avatar_url)
            await channel.send(embed=embed)       
        except:
            print(f'> Ошибко посхалко кароче')
            await channel.send(f'> Ошибко посхалко кароче') 
    if logType == 'add_card':
        embed_string = f'➕ Карта добавлена\n```'
        pairs = string.split()
        for pair in pairs:
            card, name = pair.split(':')
            embed_string += f'{card} : {name}\n'
        embed_string += '```'
        embed = discord.Embed(description=embed_string, color=discord.Color.blue())
        embed.set_footer(text='Добавлено ' + avatar_name + f' • {today}', icon_url=avatar_url)
        await channel.send(embed=embed) 
    if logType == 'remove_card':
        embed_string = f'➖ Карта удалена\n```'
        pairs = string.split()
        for pair in pairs:
            nickname = str(cards_list.getName(pair))
            embed_string += f'{pair} : {nickname[2:-3]}\n'
        embed_string += '```'
        embed = discord.Embed(description=embed_string, color=discord.Color.red())
        embed.set_footer(text='Удалено ' + avatar_name + f' • {today}', icon_url=avatar_url)
        await channel.send(embed=embed) 

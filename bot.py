from discord.ui import View, Button, Modal, TextInput
from discord.ext import commands, tasks
from discord.ext import commands
from dotenv import load_dotenv
import cards_list
import requests
import asyncio
import discord
import os
load_dotenv()
TOKEN = os.getenv('TOKEN')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
ALLOWED_ROLE_ID = int(os.getenv('ALLOWED_ROLE_ID'))

headers = {
    'Authorization': os.getenv('KEY')
}

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())

cards = []


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
    return f'> 🏦 Баланс казны: `{balance}`\n'

def Transaction(nickname):
    payback = {
        'receiver': nickname['card'],
        'amount': nickname['amount'],
        'comment': f'ЗП ФБР: {nickname["name"]}'
    }
    transLink = 'https://spworlds.ru/api/public/transactions'
    post = requests.post(transLink, headers=headers, json=payback)
    return post

def importCards(data):
    pairs = data.split()
    for pair in pairs:
        card, amount = pair.split(':')
        name = cards_list.getName(card)
        trans = {
            'card': card,
            'name': name[0],
            'amount': int(amount)
        }
        cards.append(trans)

def check_permission(interaction):
    allowed_user_ids = [358244619332354049, 506437001306701826, 512645963727372290]
    return interaction.user.id in allowed_user_ids

async def deny_access(interaction):
    message = await interaction.response.send_message('> ❌ Отказано в доступе')
    await asyncio.sleep(5)
    await message.delete()

class SearchButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label='Найти', style=discord.ButtonStyle.blurple, custom_id='search_button')
    async def search_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SearchModal())

class SearchModal(Modal):
    def __init__(self):
        super().__init__(title='Поиск карты')
        self.search_input = TextInput(label='Введите никнейм или номер карты')
        self.add_item(self.search_input)

    async def on_submit(self, interaction: discord.Interaction):
        query = self.search_input.value
        result = search_card(query)
        await interaction.response.send_message(result)

def search_card(query):
    cards = cards_list.getCards()
    for card in cards:
        card_number, nickname = card.split(':')
        if query == card_number or query == nickname:
            return f'Найдено `{nickname}`:{card_number}'
    return 'Не найдено'

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Активен!"))
    print(f'{bot.user} подрублен!')
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

@bot.tree.command(name="menu", description="Показать все доступные команды", guild=discord.Object(id=GUILD_ID))
async def cmdMenu(interaction: discord.Interaction):
    if not check_permission(interaction):
        await deny_access(interaction)
        return

    commands = [
        '`balance` - Показать баланс казны',
        '`salary` - Выдать зарплату. Синтаксис номер карты:сумма',
        '`card_list` - Показать список карт сотрудников',
        '`add_card` - Добавить карту(ы). Синтаксис номер карты:нийнейм',
        '`remove_card` - Удалить карту(ы). Синтаксис: никнейм/номер карты'
    ]
    command_list = "\n".join(commands)
    embed = discord.Embed(title="📃 Список доступных команд", description=command_list, color=discord.Color.blue())
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="balance", description="Показать баланс казны", guild=discord.Object(id=GUILD_ID))
async def cmdBalance(interaction: discord.Interaction):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    balance = getBalance()
    await interaction.response.send_message(balance)

@bot.tree.command(name="salary", description="Выдать зарплату", guild=discord.Object(id=GUILD_ID))
async def cmdSalary(interaction: discord.Interaction, trans_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    importCards(trans_string)
    for card in cards:
        Transaction(card)
    cards.clear()
    await interaction.response.send_message('> ✅ Зарплата успешно выдана!')

@bot.tree.command(name="card_list", description="Показать список карт", guild=discord.Object(id=GUILD_ID))
async def cmdGetCards(interaction: discord.Interaction):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    card_list = getCards()
    embed = discord.Embed(title='📄 Карты сотрудников', description=card_list, color=discord.Color.blue())
    view = SearchButtonView()
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="add_card", description="Добавить карту", guild=discord.Object(id=GUILD_ID))
async def cmdAddCard(interaction: discord.Interaction, card_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    addCard(card_string)
    await interaction.response.send_message('> ✅ Карта(ы) успешно добавлена(ы)!')

@bot.tree.command(name="remove_card", description="Удалить карту", guild=discord.Object(id=GUILD_ID))
async def cmdRemoveCard(interaction: discord.Interaction, card_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    removeCard(card_string)
    await interaction.response.send_message('> ✅ Карта(ы) успешно удалена(ы)!')

if __name__ == '__main__':
    cards_list.open_connection()
    bot.run(BOT_TOKEN)
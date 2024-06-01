from discord.ui import View, Button, Modal, TextInput
from discord.ext import commands, tasks
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from datetime import datetime

import cards_list
import requests
import asyncio
import discord
import os
import io


load_dotenv()
TOKEN = os.getenv('TOKEN')
BOT_TOKEN = os.getenv('BOT_TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
ALLOWED_USER_IDS = [int(id) for id in os.getenv('ALLOWED_USER_IDS').split(',')]
LOGS_ID = int(os.getenv('LOGS_ID'))

headers = {
    'Authorization': os.getenv('KEY')
}

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
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
        if name is None:
            return 0
        trans = {
            'card': card,
            'name': name[0],
            'amount': int(amount)
        }
        cards.append(trans)
    return 1


async def deny_access(interaction):
    message = await interaction.response.send_message('> ❌ Отказано в доступе', ephemeral=True)
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
        result = searchCard(query)
        await interaction.response.send_message(result, ephemeral=True)

def searchCard(query):
    cards = cards_list.getCards()
    for card in cards:
        card_number, nickname = card.split(':')
        if query == card_number or query == nickname:
            return f'> ✅ Найдено ```{nickname} : {card_number}```'
    return '> ❌ Не найдено'

async def sendLogs(string, avatar_url, avatar_name, logType):
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
            print(nickname)
            embed_string += f'{pair} : {nickname[2:-3]}\n'
        embed_string += '```'
        embed = discord.Embed(description=embed_string, color=discord.Color.red())
        embed.set_footer(text='Удалено ' + avatar_name + f' • {today}', icon_url=avatar_url)
        await channel.send(embed=embed)       


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
    with open('icon.png', 'rb') as icon_file:
        icon_data = icon_file.read()
        icon_bytes = io.BytesIO(icon_data)

        embed = discord.Embed(title="📃 Список доступных команд", description=command_list, color=discord.Color.blue())
        embed.set_thumbnail(url="attachment://icon.png")
        user = await bot.fetch_user(512645963727372290)
        avatar_url = user.display_avatar.url
        embed.set_footer(text='Made by @wa1ne', icon_url=avatar_url)

        await interaction.response.send_message(embed=embed, file=discord.File(icon_bytes, "icon.png"), ephemeral=True)


@bot.tree.command(name="balance", description="Показать баланс казны", guild=discord.Object(id=GUILD_ID))
async def cmdBalance(interaction: discord.Interaction):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    balance = getBalance()
    await interaction.response.send_message(balance, ephemeral=True)

@bot.tree.command(name="salary", description="Выдать зарплату", guild=discord.Object(id=GUILD_ID))
async def cmdSalary(interaction: discord.Interaction, trans_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    imported = importCards(trans_string)
    if imported == 1:
        for card in cards:
            Transaction(card)
        cards.clear()
        await interaction.response.send_message('> ✅ Зарплата успешно выдана!', ephemeral=True)
        member = interaction.user
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        avatar_name = member.display_name
        await sendLogs(trans_string, avatar_url, avatar_name, logType='salary')
    else:
        await interaction.response.send_message('> ❌ Одна/Несколько из заданных карт не добавлены в базу данных. используйте `/add_card`, чтобы это исправить', ephemeral=True)
        await asyncio.sleep(5)
        await interaction.delete_original_response()

@bot.tree.command(name="card_list", description="Показать список карт", guild=discord.Object(id=GUILD_ID))
async def cmdGetCards(interaction: discord.Interaction):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    card_list = getCards()
    embed = discord.Embed(title='📄 Карты сотрудников', description=card_list, color=discord.Color.blue())
    view = SearchButtonView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="add_card", description="Добавить карту", guild=discord.Object(id=GUILD_ID))
async def cmdAddCard(interaction: discord.Interaction, card_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return 
    addCard(card_string)
    await interaction.response.send_message('> ✅ Карта(ы) успешно добавлена(ы)!', ephemeral=True)
    member = interaction.user
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    avatar_name = member.display_name
    await sendLogs(card_string, avatar_url, avatar_name, logType='add_card')
    await asyncio.sleep(5)
    await interaction.delete_original_response()

@bot.tree.command(name="remove_card", description="Удалить карту", guild=discord.Object(id=GUILD_ID))
async def cmdRemoveCard(interaction: discord.Interaction, card_string: str):
    if not check_permission(interaction):
        await deny_access(interaction)
        return
    card_id = card_string
    print(f'id = {card_id}')
    await interaction.response.send_message('> ✅ Карта(ы) успешно удалена(ы)!', ephemeral=True)
    member = interaction.user
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    avatar_name = member.display_name
    await sendLogs(card_id, avatar_url, avatar_name, logType='remove_card')
    removeCard(card_string)
    await asyncio.sleep(5)
    await interaction.delete_original_response()


@bot.tree.command(name="clear", description="Удалить сообщения", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="Количество сообщений для удаления", message_id="ID сообщения для удаления")
async def clear(interaction: discord.Interaction, amount: int = None, message_id: str = None):
    if not interaction.user.id == 512645963727372290:
        await interaction.response.send_message('> ❌ У вас нет прав для удаления сообщений.', ephemeral=True)
        return

    if amount is None and message_id is None:
        await interaction.response.send_message('> ❌ Укажите количество сообщений для удаления или ID сообщения.', ephemeral=True)
        return

    if amount is not None and amount <= 0:
        await interaction.response.send_message('> ❌ Введите положительное число для удаления сообщений.', ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    if message_id is not None:
        try:
            message = await interaction.channel.fetch_message(int(message_id))
            await message.delete()
            await interaction.followup.send(f'> ✅ Сообщение с ID `{message_id}` удалено.', ephemeral=True)
        except discord.NotFound:
            await interaction.followup.send('> ❌ Сообщение с указанным ID не найдено.', ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send('> ❌ У меня нет прав для удаления этого сообщения.', ephemeral=True)
        except discord.HTTPException as e:
            await interaction.followup.send(f'> ❌ Ошибка при удалении сообщения: {e}', ephemeral=True)
    else:
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(f'> ✅ Удалено {len(deleted)} сообщений.', ephemeral=True)

if __name__ == '__main__':
    cards_list.open_connection()
    bot.run(BOT_TOKEN)
    

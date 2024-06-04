from discord.ext import commands
from discord import app_commands
import discord
import logging
import sys
import asyncio
import io

import cards_list
import helpers

BOT_TOKEN = os.getenv('TOKEN')
GUILD_ID = int(os.getenv('GUILD_ID'))
ALLOWED_USER_IDS = [int(id) for id in os.getenv('ALLOWED_USER_IDS').split(',')]
LOGS_ID = int(os.getenv('LOGS_ID'))

bot = commands.Bot(command_prefix='!', intents=discord.Intents.default())
logging.basicConfig(filename='error.log', level=logging.ERROR)

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="Активен!"))
    print(f'{bot.user} подрублен!')
    await bot.tree.sync(guild=discord.Object(id=GUILD_ID))

@bot.tree.command(name="menu", description="Показать все доступные команды", guild=discord.Object(id=GUILD_ID))
async def cmdMenu(interaction: discord.Interaction):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return

    commands = [
        '`balance` - Показать баланс казны',
        '`salary` - Выдать зарплату. Синтаксис номер карты:сумма',
        '`payment` - Выполнить перевод с казны ФБР',
        '`cardList` - Показать список карт сотрудников',
        '`addCard` - Добавить карту(ы). Синтаксис номер карты:нийнейм',
        '`removeCard` - Удалить карту(ы). Синтаксис: никнейм/номер карты'
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
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return
    balance = helpers.getBalance()
    await interaction.response.send_message(balance, ephemeral=True)

@bot.tree.command(name="salary", description="Выдать зарплату(номеркарты:сумма)", guild=discord.Object(id=GUILD_ID))
async def cmdSalary(interaction: discord.Interaction, trans_string: str):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return
    imported = helpers.importCards(trans_string)
    if imported:
        for card in helpers.cards:
            helpers.SalaryTransaction(card)
        helpers.cards.clear()
        await interaction.response.send_message('> ✅ Зарплата успешно выдана!', ephemeral=True)
        member = interaction.user
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        avatar_name = member.display_name
        await helpers.sendLogs(bot, trans_string, avatar_url, avatar_name, logType='salary')
    else:
        await interaction.response.send_message('> ❌ Одна/Несколько из заданных карт не добавлены в базу данных. используйте `/add_card`, чтобы это исправить', ephemeral=True)

@bot.tree.command(name="payment", description="Перевод с казны", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(transaction="Перевод(номеркарты:сумма)", comment="Комментарий к транзакции (опционально)")
async def cmdPay(interaction: discord.Interaction, transaction: str, comment: str = None):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return

    imported = helpers.importCards(transaction)
    if imported:
        for card in helpers.cards:
            helpers.Transaction(card, comment)
        helpers.cards.clear()
        await interaction.response.send_message('> ✅ Перевод выполнен!', ephemeral=True)
        member = interaction.user
        avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
        avatar_name = member.display_name
        await helpers.sendLogs(bot, transaction, avatar_url, avatar_name, logType='payment')
    else:
        await interaction.response.send_message('> ❌ Одна/Несколько из заданных карт не добавлены в базу данных. используйте `/add_card`, чтобы это исправить', ephemeral=True)

@bot.tree.command(name="cardlist", description="Показать список карт", guild=discord.Object(id=GUILD_ID))
async def cmdGetCards(interaction: discord.Interaction):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return
    card_list = helpers.getCards()
    embed = discord.Embed(title='📄 Карты сотрудников', description=card_list, color=discord.Color.blue())
    view = helpers.SearchButtonView()
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="addcard", description="Добавить карту(номеркарты:ник)", guild=discord.Object(id=GUILD_ID))
async def cmdAddCard(interaction: discord.Interaction, card_string: str):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return 
    helpers.addCard(card_string)
    await interaction.response.send_message('> ✅ Карта(ы) успешно добавлена(ы)!', ephemeral=True)
    member = interaction.user
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    avatar_name = member.display_name
    await helpers.sendLogs(bot, card_string, avatar_url, avatar_name, logType='add_card')

@bot.tree.command(name="removecard", description="Удалить карту(номеркарты)", guild=discord.Object(id=GUILD_ID))
async def cmdRemoveCard(interaction: discord.Interaction, card_string: str):
    if not helpers.check_permission(interaction):
        await helpers.deny_access(interaction)
        return
    card_id = card_string
    await interaction.response.send_message('> ✅ Карта(ы) успешно удалена(ы)!', ephemeral=True)
    member = interaction.user
    avatar_url = member.avatar.url if member.avatar else member.default_avatar.url
    avatar_name = member.display_name
    await helpers.sendLogs(bot, card_id, avatar_url, avatar_name, logType='remove_card')
    helpers.removeCard(card_string)

@bot.tree.command(name="clear", description="Удалить сообщения", guild=discord.Object(id=GUILD_ID))
@app_commands.describe(amount="Количество сообщений для удаления", message_id="ID сообщения для удаления")
async def cmdClear(interaction: discord.Interaction, amount: int = None, message_id: str = None):
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
    sys.stderr = open('error.log', 'a')
    while True:
        try:
            cards_list.open_connection()
            bot.run(BOT_TOKEN)
        except Exception as e:
            logging.error(f'Произошла ошибка: {e}')
            continue
        asyncio.sleep(5)

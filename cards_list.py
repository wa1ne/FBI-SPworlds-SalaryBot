# -*- coding: utf-8 -*-

import sqlite3

def open_connection():
    connection = sqlite3.connect('cardbase.db')
    query = '''
CREATE TABLE IF NOT EXISTS Cards (
card TEXT NOT NULL,
nickname TEXT NOT NULL
);
    '''
    cursor = connection.cursor()
    try:
        cursor.execute(query)
        connection.commit()
    except Exception as e:
       print(f"The error '{e}' occurred")
    connection.close()

def addCard(card_id, nickname):
    connection = sqlite3.connect('cardbase.db')
    cursor = connection.cursor()
    cursor.execute('INSERT INTO Cards (card, nickname) VALUES (?, ?)', (card_id, nickname))
    connection.commit()
    connection.close()

def getName(card_id):
    connection = sqlite3.connect('cardbase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT nickname FROM Cards WHERE card = ?', (card_id,))
    name_result = cursor.fetchall()
    connection.close()
    return name_result[0] if name_result else None


def removeCard(card_id):
    connection = sqlite3.connect('cardbase.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Cards WHERE card = ?', (card_id,))
    connection.commit()
    connection.close()

def removeCardbyName(nickname):
    connection = sqlite3.connect('cardbase.db')
    cursor = connection.cursor()
    cursor.execute('DELETE FROM Cards WHERE nickname = ?', (nickname,))
    connection.commit()
    connection.close()

def getCards():
    connection = sqlite3.connect('cardbase.db')
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM Cards')
    all_cards = cursor.fetchall()
    connection.close()

    formatted_cards = []
    for card in all_cards:
        formatted_card = f"{card[0]}:{card[1]}"
        formatted_cards.append(formatted_card)

    return formatted_cards
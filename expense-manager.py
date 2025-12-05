import matplotlib.pyplot as plt
import sqlite3
import os
import wx
from datetime import datetime


con = None
cursor = None
conn_gui = None
db = None


def conn_creator():
    global con, cursor
    try:
        appdata_path = os.path.normpath(os.path.join(os.getenv('APPDATA'), 'Expense-Manager'))
        os.makedirs(appdata_path, exist_ok=True)
        db = os.path.join(appdata_path, 'expenses.db')

        con = sqlite3.connect(db)
        cursor = con.cursor()

        create_expense_table = '''CREATE TABLE IF NOT EXISTS Expenses (
        user_id INTEGER NOT NULL ,
        time DATETIME NOT NULL,
        amount FLOAT(20,2) NOT NULL,
        category varchar(255) NOT NULL,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(id)
        )'''

        create_user_table = '''CREATE TABLE IF NOT EXISTS Users(
        id INT PRIMARY KEY,
        username varchar(255),
        pass_hash TEXT NOT NULL
        )'''

        cursor.execute(create_expense_table)
        cursor.execute(create_user_table)
    
    except sqlite3.Error as e:
        wx.MessageBox(
            caption = "Database Not Initialized!",
            message = f"Error in DB Initialization: {e}",
            style = wx.OK | wx.ICON_ERROR)
import matplotlib.pyplot as plt
import sqlite3
import os
import wx
from datetime import datetime
from hashlib import sha256


con = None
cursor = None
conn_gui = None
db = None
user_id = None


def conn_creator():

    '''Initializes a database in %appdata\\Roaming\\Expense Manager folder so that regardless of where the code is run from
    the database remains the same'''

    global con, cursor
    try:
        appdata_path = os.path.normpath(os.path.join(os.getenv('APPDATA'), 'Expense-Manager'))
        os.makedirs(appdata_path, exist_ok=True)
        db = os.path.join(appdata_path, 'expenses.db')

        con = sqlite3.connect(db)
        cursor = con.cursor()

        create_expense_table = '''CREATE TABLE IF NOT EXISTS Expenses (
        user_id INTEGER NOT NULL,
        time DATETIME NOT NULL,
        amount FLOAT(20,2) NOT NULL,
        category varchar(255) NOT NULL,
        description TEXT,
        FOREIGN KEY (user_id) REFERENCES Users(id)
        )'''

        create_user_table = '''CREATE TABLE IF NOT EXISTS Users(
        id INTEGER PRIMARY KEY,
        username varchar(255) UNIQUE,
        pass_hash TEXT NOT NULL
        )'''

        cursor.execute(create_expense_table)
        cursor.execute(create_user_table)
    
    except sqlite3.Error as e:
        wx.MessageBox(
            caption = "Database Not Initialized!",
            message = f"Error in DB Initialization\n{e}",
            style = wx.OK | wx.ICON_ERROR
            )
        
def login_manager(checkb, user, passw):
    '''Determines whether the user wants to login or create an account by getting the value from checkbox
    and either checks for proper authorisation or creates a new user account in DB'''

    global cursor, user_id, status_txt

    logged_in = False

    if checkb.GetValue():                       # Checks if the user wants to SIGN IN or SIGN UP
        try:
            acc_command = '''INSERT INTO Users (username, pass_hash) VALUES (?, ?)'''
            cursor.execute(acc_command, (user, passw))
            con.commit()                        # Adds user login_info into database 

            user_data = cursor.execute("SELECT * FROM Users WHERE username = ?", (user,))
            user_data = list(user_data)
        
        except sqlite3.Error as e:
            wx.MessageBox(
                caption = "Sign Up Failed",
                message = f"SQL Error: {e}.\nUsername already exists. Try a unique username.",
                style = wx.OK | wx.ICON_ERROR
            )
    
    else:
        acc_command = '''SELECT * FROM Users WHERE username = ?'''
        user_data = cursor.execute(acc_command, (user,))
        user_data = list(user_data)             # Extracts data from database for authenticates

        if user_data == []:
            wx.MessageBox(
                caption = 'Login Failed',
                message = f"User {user} not found.\nSelect 'Sign Up' checkbox if you want to create an account.",
                style = wx.OK | wx.ICON_ERROR
                )
        
        else:
            if passw == user_data[0][-1]:       # Checks if the user is authorized to access DB or not
                
                user_id = user_data[0][1]
                logged_in = True

                wx.MessageBox(
                caption = "Login Successful",
                message = f"Successfully logged in using Username: {user}",
                style = wx.OK | wx.ICON_INFORMATION
                )
        
            else:
                wx.MessageBox(
                caption = "Login Failed",
                message = f"Incorrect Passowrd.\nKindly login again.",
                style = wx.OK | wx.ICON_INFORMATION
                )

    if logged_in:                               # On Successful login, this block updates status on main page
        user_id = user_data[0][0]
        name = user_data[0][1]
        del status_txt
        status_txt = wx.StaticText(main_Panel, label = f'Logged in as {name}', pos = (85, 15))


def login_ui(event):
    '''Creates a window where a user can create their own account or log into theirs to access their
    own expenses and not others'''

    conn_creator()                              # Creates database if it doesn't exist and lets user login

    login_Dialog = wx.Dialog(main_Frame, title = 'Login to DB', size = (250, 225))
    login_panel = wx.Panel(login_Dialog)

    user_txt = wx.StaticText(login_panel, label = 'Username', pos = (20, 20))
    pass_txt = wx.StaticText(login_panel, label = 'Password', pos = (20, 60))
    username_input = wx.TextCtrl(login_panel, pos = (100, 20))
    pass_input = wx.TextCtrl(login_panel, pos = (100, 60), style = wx.TE_PASSWORD)
    create_acc_checkbox = wx.CheckBox(login_panel, label = "Sign Up", pos = (75, 100))
    log_in_btn = wx.Button(login_panel, label = 'Log In', pos = (85, 130))

    def secure_login_parser(event):
        user = username_input.GetValue()
        pass_hash = sha256(pass_input.GetValue().encode('utf-8')).hexdigest()
        login_manager(create_acc_checkbox, user, pass_hash)
    
    log_in_btn.Bind(wx.EVT_BUTTON, secure_login_parser)

    login_Dialog.ShowModal()
    login_Dialog.Destroy()

app = wx.App()

main_Frame = wx.Frame(None, title = 'VSSS Expense Manager', size = (300, 300))
main_Panel = wx.Panel(main_Frame, size = (400, 300))
main_Frame.Show()

status_txt = wx.StaticText(main_Panel, label = 'Not Logged In!', pos = (100, 15))
login_button = wx.Button(main_Panel, label = 'Log into Database', pos = (90, 45))
login_button.Bind(wx.EVT_BUTTON, login_ui)

app.MainLoop()
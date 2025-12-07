import matplotlib.pyplot as plt
import sqlite3
import os
import wx
from datetime import datetime
from hashlib import sha256
import pandas as pd

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
        time DATE NOT NULL,
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
            logged_in = True
            wx.MessageBox(
            caption = "Login Successful",
            message = f"Successfully logged in using Username: {user}",
            style = wx.OK | wx.ICON_INFORMATION
            )
        
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
        status_txt.SetLabel(label = f'Logged in as {name}')
        status_txt.SetPosition((85, 15))

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


def expense_add_view(event):

    '''Main UI where the Frame is split into two sections: Left one where the user can add new expenses,
    and the Right one where user can see his last 50 sections (the limit can be changed)
    '''
    global user_id, cursor

    if user_id is None:
        wx.MessageBox("You must be logged in to add/view expenses", "Authentication Required", wx.OK | wx.ICON_WARNING)
        login_ui(None)

def statistics(event):

    '''Generates stats based on expenses'''

    global user_id

    if user_id is None:
        wx.MessageBox("You must be logged in to view Statistics", "Authentication Required", wx.OK | wx.ICON_WARNING)
        login_ui(None)

    def get_user_expenses(user_id):
        df = pd.read_sql_query(f"SELECT time, amount, category FROM Expenses WHERE user_id={user_id}", con)

        if df.empty:
            print("No expense data found for user.")
            return None
        
        # Convert timestamp if stored as string
        df['time'] = pd.to_datetime(df['time'])
        return df


    # Spending per day
    def plot_daily_spending(event):
        df = get_user_expenses(user_id)
        if df is None:
            return

        daily = df.groupby(df['time'].dt.date)['amount'].sum()
        daily.plot(kind='bar')
        plt.title("Daily Spending")
        plt.xlabel("Date")
        plt.ylabel("Amount Spent")
        plt.tight_layout()
        plt.show()


    # Category-wise Spending
    def plot_category_spending(event):
        df = get_user_expenses(user_id)
        if df is None:
            return

        category = df.groupby('category')['amount'].sum()
        category.plot(kind='pie', autopct='%1.1f%%')
        plt.title("Category-wise Spending")
        plt.ylabel("")
        plt.tight_layout()
        plt.show()


    # Monthly Spending Trend
    def plot_monthly_spending(event):
        df = get_user_expenses(user_id)
        if df is None:
            return

        monthly = df.groupby(df['time'].dt.to_period("M"))['amount'].sum()
        monthly.index = monthly.index.astype(str)
        monthly.plot(kind='line', marker='o')
        plt.title("Monthly Expense Trend")
        plt.xlabel("Month")
        plt.ylabel("Total Spending")
        plt.grid(True)
        plt.tight_layout()
        plt.show()


    # Top 5 High Expenses
    def plot_top_expenses(event):
        df = get_user_expenses(user_id)
        if df is None:
            return

        top = df.nlargest(5, 'amount').sort_values('amount')
        top.plot(kind='barh', x='time', y='amount')
        plt.title("Top 5 Highest Expenses")
        plt.xlabel("Amount")
        plt.tight_layout()
        plt.show()

    stats_Frame = wx.Frame(main_Frame, title = "Statistics", size = (300, 300))
    stats_Panel = wx.Panel(stats_Frame)

    daily_spend_btn = wx.Button(stats_Panel, label = "Daily Expenditure", pos = (85, 15))
    category_spend_btn = wx.Button(stats_Panel, label = "Category-Wise Expenditures", pos = (60, 55))
    monthly_btn = wx.Button(stats_Panel, label = "Monthly Expenditure", pos = (75, 95))
    top5_spend_btn = wx.Button(stats_Panel, label = "Top 5 Expenditures", pos = (80, 135))

    daily_spend_btn.Bind(wx.EVT_BUTTON, plot_daily_spending)
    category_spend_btn.Bind(wx.EVT_BUTTON, plot_category_spending)
    monthly_btn.Bind(wx.EVT_BUTTON, plot_monthly_spending)
    top5_spend_btn.Bind(wx.EVT_BUTTON, plot_top_expenses)

    stats_Frame.Show()

app = wx.App()

main_Frame = wx.Frame(None, title = 'VSSS Expense Manager', size = (300, 300))
main_Panel = wx.Panel(main_Frame, size = (400, 300))
main_Frame.Show()

status_txt = wx.StaticText(main_Panel, label = 'Not Logged In!', pos = (100, 15))
login_button = wx.Button(main_Panel, label = 'Log into Database', pos = (85, 65))
login_button.Bind(wx.EVT_BUTTON, login_ui)

expense_add_button = wx.Button(main_Panel, label = 'Add / View Expenses', pos = (78, 115))
expense_add_button.Bind(wx.EVT_BUTTON, expense_add_view)
stats_button = wx.Button(main_Panel, label = 'View Statistics', pos = (95, 165))
stats_button.Bind(wx.EVT_BUTTON, statistics)

app.MainLoop()
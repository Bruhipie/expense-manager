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
    global user_id, cursor, con

    try:
        if user_id is None:
            wx.MessageBox("You must be logged in to add/view expenses", "Authentication Required", wx.OK | wx.ICON_WARNING)
            login_ui(None)
            return

        # Use an attribute on main_Frame to keep a reference and prevent garbage collection
        # Also, if it already exists, Raise it instead of creating a new one 
        if hasattr(main_Frame, 'add_view_window') and main_Frame.add_view_window:
            try:
                main_Frame.add_view_window.Raise()
                return
            except:
                # If the window was destroyed but the reference remains, continue to recreate
                pass
        
        add_view_Frame = wx.Frame(main_Frame, title="Add / View Expenses", size=(600, 400))
        main_Frame.add_view_window = add_view_Frame # Keep reference
        
        panel = wx.Panel(add_view_Frame)

        # UI Elements for Adding Expense
        wx.StaticText(panel, label="Add New Expense", pos=(20, 10)).SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))

        wx.StaticText(panel, label="Amount:", pos=(20, 50))
        amount_input = wx.TextCtrl(panel, pos=(100, 45))

        wx.StaticText(panel, label="Category:", pos=(20, 90))
        categories = ["Food", "Transport", "Shopping", "Entertainment", "Utilities", "Other"]
        category_input = wx.ComboBox(panel, pos=(100, 85), choices=categories)

        wx.StaticText(panel, label="Description:", pos=(20, 130))
        desc_input = wx.TextCtrl(panel, pos=(100, 125))

        save_btn = wx.Button(panel, label="Save Expense", pos=(100, 170))

        # UI Elements for Viewing Expenses
        wx.StaticText(panel, label="Recent Expenses", pos=(300, 10)).SetFont(wx.Font(12, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD))
        
        expense_list = wx.ListCtrl(panel, pos=(300, 45), size=(260, 300), style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        expense_list.InsertColumn(0, 'Date', width=80)
        expense_list.InsertColumn(1, 'Category', width=80)
        expense_list.InsertColumn(2, 'Amount', width=80)

        def refresh_list():
            try:
                expense_list.DeleteAllItems()
                if cursor:
                    # Fetch last 50 expenses
                    rows = cursor.execute("SELECT time, category, amount FROM Expenses WHERE user_id=? ORDER BY time DESC LIMIT 50", (user_id,))
                    for row in rows:
                        row_date = str(row[0])
                        # Handle potential different date formats
                        display_date = row_date.split()[0] if ' ' in row_date else row_date
                        
                        index = expense_list.InsertItem(0, display_date) 
                        expense_list.SetItem(index, 1, str(row[1]))
                        expense_list.SetItem(index, 2, str(row[2]))
            except Exception as e:
                wx.MessageBox(f"Error loading list: {e}", "Error", wx.OK | wx.ICON_ERROR)
                print(f"List Error: {e}")

        def save_expense(event):
            try:
                val = amount_input.GetValue()
                if not val:
                    wx.MessageBox("Please enter an amount.", "Input Error", wx.OK | wx.ICON_ERROR)
                    return
                amount = float(val)
                
                category = category_input.GetValue()
                if not category:
                    wx.MessageBox("Please select or enter a category.", "Input Error", wx.OK | wx.ICON_ERROR)
                    return
                    
                description = desc_input.GetValue()
                date_time = datetime.now() # Use current time
                date_time = date_time.replace(microsecond=0)

                query = "INSERT INTO Expenses (user_id, time, amount, category, description) VALUES (?, ?, ?, ?, ?)"
                cursor.execute(query, (user_id, date_time, amount, category, description))
                con.commit()
                
                wx.MessageBox("Expense added successfully!", "Success", wx.OK | wx.ICON_INFORMATION)
                
                # Clear inputs
                amount_input.SetValue("")
                desc_input.SetValue("")
                
                refresh_list()

            except ValueError:
                wx.MessageBox("Invalid Amount. Please enter a valid number.", "Input Error", wx.OK | wx.ICON_ERROR)
            except sqlite3.Error as e:
                wx.MessageBox(f"Database Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
            except Exception as e:
                wx.MessageBox(f"Unexpected Error: {e}", "Error", wx.OK | wx.ICON_ERROR)
                print(f"Save Error: {e}")

        save_btn.Bind(wx.EVT_BUTTON, save_expense)
        
        # Load initial data
        refresh_list()
        
        add_view_Frame.Show()
        
    except Exception as e:
        wx.MessageBox(f"Failed to open window: {e}", "Critical Error", wx.OK | wx.ICON_ERROR)
        print(f"Window Error: {e}")

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
        df['time'] = pd.to_datetime(df['time'], format="%Y-%m-%d %H:%M:%S")
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
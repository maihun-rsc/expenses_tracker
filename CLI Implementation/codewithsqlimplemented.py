# Expense-Tracker
# Created by Rananjay Singh Chauhan on 19/03/25.
# CLI implementation with MySQL

import pandas as pd
import mysql.connector as sql
import csv
import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import os

class Expenses:
     def __init__(self):
          self.expenses = {}
          self.received = {}
          self.category = []
          self.amountspent = []
          self.datespent = []
          self.placeofspending = []
          self.autopay = []
          self.sender = []
          self.amount_received = []
          self.dateofreceiving = []
          self.total_expenses = 0
          self.total_received = 0
          self.account_balance = 0
          self.amount_left = 0
          self.amount_needed = 0
          self.connection = None
          self.cursor = None
          retries = 3
          while retries > 0:
               try:
                    self.connection = sql.connect(
                         host="",
                         user="",  
                         password="",  
                         database=""  
                    )
                    self.cursor = self.connection.cursor()
                    self.cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
                         id INT AUTO_INCREMENT PRIMARY KEY,
                         category VARCHAR(32) NOT NULL,
                         amount DECIMAL(10,2) NOT NULL,
                         date DATE NOT NULL,
                         place VARCHAR(32),
                         autopay BOOLEAN NOT NULL DEFAULT FALSE
                    )''')
                    self.cursor.execute('''CREATE TABLE IF NOT EXISTS received (
                         id INT AUTO_INCREMENT PRIMARY KEY,
                         date DATE NOT NULL,
                         amount DECIMAL(10,2) NOT NULL,
                         sender VARCHAR(32) NOT NULL
                    )''')
                    self.cursor.execute("SELECT DISTINCT DATE_FORMAT(date, '%Y_%m') AS month FROM expenses")
                    months = [row[0] for row in self.cursor.fetchall()]
                    for month in months:
                         month_table = f"expenses_{month}"
                         self.cursor.execute(f"""
                              CREATE TABLE IF NOT EXISTS {month_table} (
                                   id INT AUTO_INCREMENT PRIMARY KEY,
                                   category VARCHAR(32) NOT NULL,
                                   amount DECIMAL(10,2) NOT NULL,
                                   date DATE NOT NULL,
                                   place VARCHAR(32),
                                   autopay BOOLEAN NOT NULL DEFAULT FALSE
                              )
                         """)
                         self.cursor.execute(f"""
                              INSERT IGNORE INTO {month_table} (category, amount, date, place, autopay)
                              SELECT category, amount, date, place, autopay
                              FROM expenses
                              WHERE DATE_FORMAT(date, '%Y_%m') = %s
                         """, (month,))
                    self.connection.commit()
                    self.load_from_csv()
                    print("Database connection established successfully.")
                    break
               except sql.Error as e:
                    retries -= 1
                    print(f"Database connection failed: {e}. Retries left: {retries}")
                    if retries == 0:
                         print("Falling back to in-memory mode (no database).")
                         self.connection = None
                         self.cursor = None

     def load_from_csv(self):
          """Load data from expenses.csv and received.csv into memory and MySQL."""
          try:
               with open('expenses.csv', 'r') as f:
                    reader = csv.DictReader(f)
                    required = {"Category", "Amount", "Date", "Place of Spending", "Auto-Pay"}
                    if not required.issubset(reader.fieldnames):
                         raise ValueError(f"expenses.csv missing required columns: {required - set(reader.fieldnames)}")
                    for row in reader:
                         category = row["Category"].strip()
                         amount = float(row["Amount"])
                         date = pd.to_datetime(row["Date"], format='%Y-%m-%d', errors='coerce')
                         if pd.isna(date):
                              print(f"Skipping invalid date in expenses.csv: {row['Date']}")
                              continue
                         date = date.strftime('%Y-%m-%d')
                         place = row["Place of Spending"].strip()
                         autopay = row["Auto-Pay"].lower() == 'true'
                         self.category.append(category)
                         self.amountspent.append(amount)
                         self.datespent.append(date)
                         self.placeofspending.append(place)
                         self.autopay.append(autopay)
                         if self.connection:
                              self.cursor.execute(
                                   "INSERT IGNORE INTO expenses (category, amount, date, place, autopay) VALUES (%s, %s, %s, %s, %s)",
                                   (category, amount, date, place, autopay)
                              )
               if self.connection:
                    self.connection.commit()
               with open('received.csv', 'r') as f:
                    reader = csv.DictReader(f)
                    required = {"Sender", "Amount", "Date of Receiving"}
                    if not required.issubset(reader.fieldnames):
                         raise ValueError(f"received.csv missing required columns: {required - set(reader.fieldnames)}")
                    for row in reader:
                         sender = row["Sender"].strip()
                         amount = float(row["Amount"])
                         date = pd.to_datetime(row["Date of Receiving"], format='%Y-%m-%d', errors='coerce')
                         if pd.isna(date):
                              print(f"Skipping invalid date in received.csv: {row['Date of Receiving']}")
                              continue
                         date = date.strftime('%Y-%m-%d')
                         self.sender.append(sender)
                         self.amount_received.append(amount)
                         self.dateofreceiving.append(date)
                         if self.connection:
                              self.cursor.execute(
                                   "INSERT IGNORE INTO received (sender, amount, date) VALUES (%s, %s, %s)",
                                   (sender, amount, date)
                              )
               if self.connection:
                    self.connection.commit()
               print("Data loaded from CSV files successfully.")
          except FileNotFoundError as e:
               print(f"CSV file not found: {e}. Starting with empty data.")
          except ValueError as e:
               print(f"Error in CSV data: {e}. Loading partial data.")
          except sql.Error as e:
               print(f"Database error during CSV load: {e}")
               if self.connection:
                    self.connection.rollback()

     def sync_csv_to_sql(self):
          """Check CSV lines against MySQL tables and add missing entries."""
          if not self.connection:
               print("No database connection. Syncing skipped.")
               return
          try:
               with open('expenses.csv', 'r') as f:
                    reader = csv.DictReader(f)
                    required = {"Category", "Amount", "Date", "Place of Spending", "Auto-Pay"}
                    if not required.issubset(reader.fieldnames):
                         raise ValueError(f"expenses.csv missing required columns: {required - set(reader.fieldnames)}")
                    for row in reader:
                         category = row["Category"].strip()
                         amount = float(row["Amount"])
                         date = pd.to_datetime(row["Date"], format='%Y-%m-%d', errors='coerce')
                         if pd.isna(date):
                              print(f"Skipping invalid date in expenses.csv: {row['Date']}")
                              continue
                         date = date.strftime('%Y-%m-%d')
                         place = row["Place of Spending"].strip()
                         autopay = row["Auto-Pay"].lower() == 'true'
                         self.cursor.execute(
                              "SELECT COUNT(*) FROM expenses WHERE category = %s AND amount = %s AND date = %s AND place = %s AND autopay = %s",
                              (category, amount, date, place, autopay)
                         )
                         if self.cursor.fetchone()[0] == 0:
                              self.cursor.execute(
                                   "INSERT INTO expenses (category, amount, date, place, autopay) VALUES (%s, %s, %s, %s, %s)",
                                   (category, amount, date, place, autopay)
                              )
                              self.category.append(category)
                              self.amountspent.append(amount)
                              self.datespent.append(date)
                              self.placeofspending.append(place)
                              self.autopay.append(autopay)
                              print(f"Added missing expense: {category}, ${amount}, {date}")
               with open('received.csv', 'r') as f:
                    reader = csv.DictReader(f)
                    required = {"Sender", "Amount", "Date of Receiving"}
                    if not required.issubset(reader.fieldnames):
                         raise ValueError(f"received.csv missing required columns: {required - set(reader.fieldnames)}")
                    for row in reader:
                         sender = row["Sender"].strip()
                         amount = float(row["Amount"])
                         date = pd.to_datetime(row["Date of Receiving"], format='%Y-%m-%d', errors='coerce')
                         if pd.isna(date):
                              print(f"Skipping invalid date in received.csv: {row['Date of Receiving']}")
                              continue
                         date = date.strftime('%Y-%m-%d')
                         self.cursor.execute(
                              "SELECT COUNT(*) FROM received WHERE sender = %s AND amount = %s AND date = %s",
                              (sender, amount, date)
                         )
                         if self.cursor.fetchone()[0] == 0:
                              self.cursor.execute(
                                   "INSERT INTO received (sender, amount, date) VALUES (%s, %s, %s)",
                                   (sender, amount, date)
                              )
                              self.sender.append(sender)
                              self.amount_received.append(amount)
                              self.dateofreceiving.append(date)
                              print(f"Added missing received: {sender}, ${amount}, {date}")
               self.connection.commit()
               print("CSV data synced with MySQL tables successfully.")
          except FileNotFoundError as e:
               print(f"CSV file not found: {e}. Nothing to sync.")
          except ValueError as e:
               print(f"Error in CSV data: {e}. Syncing partial data.")
          except sql.Error as e:
               print(f"Database error during sync: {e}")
               self.connection.rollback()

     def filter_data(self, table, date_start=None, date_end=None, key=None, value=None, use_monthly=None):
          """Filter data from MySQL based on date range, key (category/sender), or monthly table."""
          if not self.connection:
               print("No database connection. Using in-memory data.")
               df = pd.DataFrame({
                    'category': self.category,
                    'amount': self.amountspent,
                    'date': self.datespent,
                    'place': self.placeofspending,
                    'autopay': self.autopay
               }) if table == "expenses" else pd.DataFrame({
                    'sender': self.sender,
                    'amount': self.amount_received,
                    'date': self.dateofreceiving
               })
          else:
               try:
                    if use_monthly:
                         try:
                              pd.to_datetime(use_monthly, format='%Y-%m-%d')
                              year, month = use_monthly.split('-')[0], use_monthly.split('-')[1]
                              table = f"expenses_{year}_{month}"
                              self.cursor.execute(f"SHOW TABLES LIKE '{table}'")
                              if not self.cursor.fetchone():
                                   print(f"Monthly table {table} does not exist.")
                                   return pd.DataFrame()
                         except ValueError:
                              print(f"Invalid use_monthly format: {use_monthly}. Use YYYY-MM-DD.")
                              return pd.DataFrame()
                    query = f"SELECT * FROM {table}"
                    conditions = []
                    params = []
                    if date_start:
                         conditions.append("date >= %s")
                         params.append(date_start)
                    if date_end:
                         conditions.append("date <= %s")
                         params.append(date_end)
                    if key and value:
                         conditions.append(f"{key} = %s")
                         params.append(value)
                    if conditions:
                         query += " WHERE " + " AND ".join(conditions)
                    self.cursor.execute(query, params)
                    df = pd.DataFrame(
                         self.cursor.fetchall(),
                         columns=[desc[0] for desc in self.cursor.description]
                    )
               except sql.Error as e:
                    print(f"Database error filtering {table}: {e}")
                    return pd.DataFrame()
          return df

     def enter_expenses(self):
          try:
               x = int(input("Enter the number of expenses to be added: "))
               if x < 0:
                    raise ValueError("Number of expenses cannot be negative.")
          except ValueError as e:
               print(f"Error: {e}. Please try again.")
               return
          for i in range(x):
               try:
                    a = input(f"Expense {i+1} - Category: ").strip()
                    if not a:
                         raise ValueError("Category cannot be empty.")
                    b = float(input(f"Expense {i+1} - Amount: "))
                    if b < 0:
                         raise ValueError("Amount cannot be negative.")
                    c = input(f"Expense {i+1} - Date (YYYY-MM-DD): ")
                    try:
                         date_obj = pd.to_datetime(c, format='%Y-%m-%d', errors='raise')
                    except ValueError:
                         try:
                              date_obj = pd.to_datetime(c, errors='raise')  # Try flexible parsing
                         except ValueError:
                              raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., 2025-03-19).")
                    c = date_obj.strftime('%Y-%m-%d')
                    d = input(f"Expense {i+1} - Place: ").strip()
                    e_input = input(f"Expense {i+1} - Auto-pay? (True/False): ").lower()
                    if e_input not in ('true', 'false'):
                         raise ValueError("Please enter 'True' or 'False'.")
                    e = e_input == 'true'
                    self.category.append(a)
                    self.amountspent.append(b)
                    self.datespent.append(c)
                    self.placeofspending.append(d)
                    self.autopay.append(e)
                    if self.connection:
                         year, month = c.split('-')[0], c.split('-')[1]
                         month_table = f"expenses_{year}_{month}"
                         self.cursor.execute(f"""
                              CREATE TABLE IF NOT EXISTS {month_table} (
                                   id INT AUTO_INCREMENT PRIMARY KEY,
                                   category VARCHAR(32) NOT NULL,
                                   amount DECIMAL(10,2) NOT NULL,
                                   date DATE NOT NULL,
                                   place VARCHAR(32),
                                   autopay BOOLEAN NOT NULL DEFAULT FALSE
                              )
                         """)
                         self.cursor.execute(
                              "INSERT INTO expenses (category, amount, date, place, autopay) VALUES (%s, %s, %s, %s, %s)",
                              (a, b, c, d, e)
                         )
                         self.cursor.execute(
                              f"INSERT INTO {month_table} (category, amount, date, place, autopay) VALUES (%s, %s, %s, %s, %s)",
                              (a, b, c, d, e)
                         )
                         self.connection.commit()
                    print(f"Expense {i+1} added successfully: {a}, ${b}, {c}")
               except ValueError as e:
                    print(f"Error in entry {i+1}: {e}. Skipping this entry.")
               except sql.Error as e:
                    print(f"Database error in entry {i+1}: {e}")
                    if self.connection:
                         self.connection.rollback()

     def update_expense_tables(self):
          try:
               self.expenses["Category"] = self.category
               self.expenses["Amount"] = self.amountspent
               self.expenses["Date"] = self.datespent
               self.expenses["Place of Spending"] = self.placeofspending
               self.expenses["Auto-Pay"] = self.autopay
               self.expenses = pd.DataFrame(self.expenses)
          except Exception as e:
               print(f"Error updating expenses table: {e}")

     def update_receiving_table(self):
          try:
               self.received["Sender"] = self.sender
               self.received["Amount"] = self.amount_received
               self.received["Date of Receiving"] = self.dateofreceiving
               self.received = pd.DataFrame(self.received)
          except Exception as e:
               print(f"Error updating received table: {e}")

     def enter_receiving(self):
          try:
               x = int(input("Enter the number of received entries to be added: "))
               if x < 0:
                    raise ValueError("Number of entries cannot be negative.")
          except ValueError as e:
               print(f"Error: {e}. Please try again.")
               return
          for i in range(x):
               try:
                    a = input(f"Received {i+1} - Sender: ").strip()
                    if not a:
                         raise ValueError("Sender cannot be empty.")
                    b = float(input(f"Received {i+1} - Amount: "))
                    if b < 0:
                         raise ValueError("Amount cannot be negative.")
                    c = input(f"Received {i+1} - Date (YYYY-MM-DD): ")
                    try:
                         date_obj = pd.to_datetime(c, format='%Y-%m-%d', errors='raise')
                    except ValueError:
                         try:
                              date_obj = pd.to_datetime(c, errors='raise')  # Try flexible parsing
                         except ValueError:
                              raise ValueError("Invalid date format. Use YYYY-MM-DD (e.g., 2025-03-19).")
                    c = date_obj.strftime('%Y-%m-%d')
                    self.sender.append(a)
                    self.amount_received.append(b)
                    self.dateofreceiving.append(c)
                    if self.connection:
                         self.cursor.execute(
                              "INSERT INTO received (sender, amount, date) VALUES (%s, %s, %s)",
                              (a, b, c)
                         )
                         self.connection.commit()
                    print(f"Received entry {i+1} added successfully: {a}, ${b}, {c}")
               except ValueError as e:
                    print(f"Error in entry {i+1}: {e}. Skipping this entry.")
               except sql.Error as e:
                    print(f"Database error in entry {i+1}: {e}")
                    if self.connection:
                         self.connection.rollback()

     def view_expenses(self):
          print("Filter expenses (leave blank for no filter):")
          date_start = input("Start date (YYYY-MM-DD): ").strip() or None
          date_end = input("End date (YYYY-MM-DD): ").strip() or None
          category = input("Category: ").strip() or None
          use_monthly = input("Use monthly table (enter YYYY-MM-DD to specify month, or leave blank): ").strip() or None
          plot = input("Generate a bar plot? (yes/no): ").lower() == 'yes'
          try:
               df = self.filter_data(
                    "expenses",
                    date_start=date_start,
                    date_end=date_end,
                    key="category" if category else None,
                    value=category,
                    use_monthly=use_monthly
               )
               if df.empty:
                    print("No expenses match the filter.")
               else:
                    df = df.rename(columns={
                         "date": "Date",
                         "amount": "Amount",
                         "category": "Category",
                         "place": "Place",
                         "autopay": "Auto-Pay"
                    })
                    print("\n=== Filtered Expenses ===")
                    print(df[["Date", "Amount", "Category", "Place", "Auto-Pay"]].to_string(index=False))
                    if plot:
                         timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                         plt.figure(figsize=(10, 6))
                         sns.barplot(x='Category', y='Amount', data=df, estimator=sum, palette='muted')
                         plt.title(f"Expenses by Category ({date_start or 'Start'} to {date_end or 'End'})")
                         plt.xlabel("Category")
                         plt.ylabel("Total Amount ($)")
                         plt.xticks(rotation=45)
                         plt.tight_layout()
                         filename = f"view_expenses_barplot_{timestamp}.png"
                         plt.savefig(filename)
                         plt.close()
                         print(f"Bar plot saved as '{filename}'")
          except Exception as e:
               print(f"Error viewing expenses: {e}")

     def view_received(self):
          print("Filter received amounts (leave blank for no filter):")
          date_start = input("Start date (YYYY-MM-DD): ").strip() or None
          date_end = input("End date (YYYY-MM-DD): ").strip() or None
          sender = input("Sender: ").strip() or None
          try:
               df = self.filter_data(
                    "received",
                    date_start=date_start,
                    date_end=date_end,
                    key="sender" if sender else None,
                    value=sender
               )
               if df.empty:
                    print("No received amounts match the filter.")
               else:
                    df = df.rename(columns={
                         "date": "Date",
                         "amount": "Amount",
                         "sender": "Sender"
                    })
                    print("\n=== Filtered Received ===")
                    print(df[["Date", "Amount", "Sender"]].to_string(index=False))
          except Exception as e:
               print(f"Error viewing received: {e}")

     def show_total_expenses(self, month=None):
          try:
               if month:
                    try:
                         pd.to_datetime(month + "-01", format='%Y-%m-%d')  # Validate YYYY-MM format
                    except ValueError:
                         print(f"Invalid month format: {month}. Use YYYY-MM (e.g., 2025-03).")
                         return
                    month_filter = f" WHERE DATE_FORMAT(date, '%Y-%m') = '{month}'"
                    month_table = f"expenses_{month.replace('-', '_')}"
               else:
                    month_filter = ""
                    month_table = None

               if self.connection:
                    # Try monthly table first if specified
                    if month_table:
                         self.cursor.execute(f"SHOW TABLES LIKE '{month_table}'")
                         if self.cursor.fetchone():
                              query = f"SELECT SUM(amount) FROM {month_table}"
                              self.cursor.execute(query)
                         else:
                              query = f"SELECT SUM(amount) FROM expenses{month_filter}"
                              self.cursor.execute(query)
                    else:
                         query = f"SELECT SUM(amount) FROM expenses{month_filter}"
                         self.cursor.execute(query)
                    total = self.cursor.fetchone()[0]
                    self.total_expenses = total if total is not None else 0
               else:
                    if month:
                         df = pd.DataFrame({
                              'amount': self.amountspent,
                              'date': pd.to_datetime(self.datespent)
                         })
                         self.total_expenses = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
                    else:
                         self.total_expenses = sum(self.amountspent)
               month_str = f" for {month}" if month else ""
               print(f"Total Expenses{month_str}: ${self.total_expenses:.2f}")
          except sql.Error as e:
               print(f"Database error: {e}")
               if month:
                    df = pd.DataFrame({
                         'amount': self.amountspent,
                         'date': pd.to_datetime(self.datespent)
                    })
                    self.total_expenses = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
               else:
                    self.total_expenses = sum(self.amountspent)
               month_str = f" for {month}" if month else ""
               print(f"Using in-memory total expenses{month_str}: ${self.total_expenses:.2f}")

     def show_total_received(self, month=None):
          try:
               if month:
                    try:
                         pd.to_datetime(month + "-01", format='%Y-%m-%d')  # Validate YYYY-MM format
                    except ValueError:
                         print(f"Invalid month format: {month}. Use YYYY-MM (e.g., 2025-03).")
                         return
                    month_filter = f" WHERE DATE_FORMAT(date, '%Y-%m') = '{month}'"
               else:
                    month_filter = ""

               if self.connection:
                    query = f"SELECT SUM(amount) FROM received{month_filter}"
                    self.cursor.execute(query)
                    total = self.cursor.fetchone()[0]
                    self.total_received = total if total is not None else 0
               else:
                    if month:
                         df = pd.DataFrame({
                              'amount': self.amount_received,
                              'date': pd.to_datetime(self.dateofreceiving)
                         })
                         self.total_received = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
                    else:
                         self.total_received = sum(self.amount_received)
               month_str = f" for {month}" if month else ""
               print(f"Total Received{month_str}: ${self.total_received:.2f}")
          except sql.Error as e:
               print(f"Database error: {e}")
               if month:
                    df = pd.DataFrame({
                         'amount': self.amount_received,
                         'date': pd.to_datetime(self.dateofreceiving)
                    })
                    self.total_received = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
               else:
                    self.total_received = sum(self.amount_received)
               month_str = f" for {month}" if month else ""
               print(f"Using in-memory total received{month_str}: ${self.total_received:.2f}")

     def calculate_balance(self):
          try:
               month = input("Enter month to filter totals (YYYY-MM, or leave blank for all): ").strip() or None
               self.show_total_expenses(month)
               self.show_total_received(month)
               self.account_balance = self.total_received - self.total_expenses
               self.amount_left = max(0, self.account_balance)
               self.amount_needed = max(0, -self.account_balance)
               print(f"Account Balance: ${self.account_balance:.2f}")
               print(f"Amount Left: ${self.amount_left:.2f}")
               if self.amount_needed > 0:
                    print(f"Amount Needed: ${self.amount_needed:.2f}")
               plot = input("Generate a balance comparison plot? (yes/no): ").lower() == 'yes'
               if plot:
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    balance_data = pd.DataFrame({
                         'Type': ['Expenses', 'Received'],
                         'Amount': [self.total_expenses, self.total_received]
                    })
                    plt.figure(figsize=(6, 6))
                    sns.barplot(x='Type', y='Amount', data=balance_data, palette='Set2')
                    month_str = f" for {month}" if month else ""
                    plt.title(f"Expenses vs Received{month_str}")
                    plt.ylabel("Amount ($)")
                    plt.tight_layout()
                    filename = f"balance_comparison_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Balance comparison plot saved as '{filename}'")
          except Exception as e:
               print(f"Error calculating balance: {e}")

     def save_to_a_csv(self):
          try:
               self.update_expense_tables()
               self.update_receiving_table()
               self.expenses.to_csv('expenses.csv', index=False)
               self.received.to_csv('received.csv', index=False)
               print("Data saved to 'expenses.csv' and 'received.csv' successfully.")
               return self.expenses, self.received
          except IOError as e:
               print(f"Error writing CSV files: {e}")
          except Exception as e:
               print(f"Error saving to CSV: {e}")

     def save_to_a_pdf(self):
          print("Filter data for PDF (leave blank for no filter):")
          date_start = input("Start date (YYYY-MM-DD): ").strip() or None
          date_end = input("End date (YYYY-MM-DD): ").strip() or None
          category = input("Category: ").strip() or None
          use_monthly = input("Use monthly table (enter YYYY-MM-DD to specify month, or leave blank): ").strip() or None
          try:
               expenses_df = self.filter_data(
                    "expenses",
                    date_start=date_start,
                    date_end=date_end,
                    key="category" if category else None,
                    value=category,
                    use_monthly=use_monthly
               )
               received_df = self.filter_data(
                    "received",
                    date_start=date_start,
                    date_end=date_end
               )
               pdf = SimpleDocTemplate("expense_report.pdf", pagesize=letter)
               elements = []
               styles = getSampleStyleSheet()
               title = Paragraph("Expense Report", styles['Heading1'])
               elements.append(title)
               elements.append(Spacer(1, 12))
               if not expenses_df.empty:
                    expenses_df = expenses_df.rename(columns={
                         "date": "Date",
                         "amount": "Amount",
                         "category": "Category",
                         "place": "Place",
                         "autopay": "Auto-Pay"
                    })
                    if len(expenses_df) > 20:  # Basic pagination threshold
                         elements.append(Paragraph("Expenses (First 20 entries shown)", styles['Heading2']))
                         expenses_data = [expenses_df[["Date", "Amount", "Category", "Place", "Auto-Pay"]].columns.tolist()] + expenses_df[["Date", "Amount", "Category", "Place", "Auto-Pay"]].iloc[:20].values.tolist()
                         print("Warning: Large expense dataset truncated to 20 entries in PDF.")
                    else:
                         elements.append(Paragraph("Expenses", styles['Heading2']))
                         expenses_data = [expenses_df[["Date", "Amount", "Category", "Place", "Auto-Pay"]].columns.tolist()] + expenses_df[["Date", "Amount", "Category", "Place", "Auto-Pay"]].values.tolist()
                    expenses_table = Table(expenses_data)
                    expenses_table.setStyle(TableStyle([
                         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('FONTSIZE', (0, 0), (-1, 0), 12),
                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                         ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(expenses_table)
                    elements.append(Spacer(1, 12))
               if not received_df.empty:
                    received_df = received_df.rename(columns={
                         "date": "Date",
                         "amount": "Amount",
                         "sender": "Sender"
                    })
                    if len(received_df) > 20:
                         elements.append(Paragraph("Received (First 20 entries shown)", styles['Heading2']))
                         received_data = [received_df[["Date", "Amount", "Sender"]].columns.tolist()] + received_df[["Date", "Amount", "Sender"]].iloc[:20].values.tolist()
                         print("Warning: Large received dataset truncated to 20 entries in PDF.")
                    else:
                         elements.append(Paragraph("Received", styles['Heading2']))
                         received_data = [received_df[["Date", "Amount", "Sender"]].columns.tolist()] + received_df[["Date", "Amount", "Sender"]].values.tolist()
                    received_table = Table(received_data)
                    received_table.setStyle(TableStyle([
                         ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                         ('FONTSIZE', (0, 0), (-1, 0), 12),
                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                         ('GRID', (0, 0), (-1, -1), 1, colors.black)
                    ]))
                    elements.append(received_table)
               try:
                    pdf.build(elements)
                    print("PDF saved as 'expense_report.pdf' successfully.")
               except IOError as e:
                    print(f"Error writing PDF file: {e}")
               return expenses_df, received_df
          except Exception as e:
               print(f"Error saving to PDF: {e}")
               return pd.DataFrame(), pd.DataFrame()

     def generate_graphs(self):
          print("Filter data for graphs (leave blank for no filter):")
          date_start = input("Start date (YYYY-MM-DD): ").strip() or None
          date_end = input("End date (YYYY-MM-DD): ").strip() or None
          category = input("Category: ").strip() or None
          use_monthly = input("Use monthly table (enter YYYY-MM-DD to specify month, or leave blank): ").strip() or None
          timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
          try:
               df = self.filter_data(
                    "expenses",
                    date_start=date_start,
                    date_end=date_end,
                    key="category" if category else None,
                    value=category,
                    use_monthly=use_monthly
               )
               if df.empty:
                    print("No expense data to graph with this filter.")
                    return
               df['date'] = pd.to_datetime(df['date'])

               try:
                    plt.figure(figsize=(10, 6))
                    sns.barplot(x='category', y='amount', data=df, estimator=sum, palette='viridis')
                    plt.title(f"Spending by Category ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.xlabel("Category")
                    plt.ylabel("Total Amount ($)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    filename = f"spending_by_category_filtered_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Bar chart saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting bar chart: {e}")

               try:
                    plt.figure(figsize=(10, 6))
                    sns.boxplot(x='category', y='amount', data=df, palette='pastel')
                    plt.title(f"Expense Distribution by Category ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.xlabel("Category")
                    plt.ylabel("Amount ($)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    filename = f"expense_distribution_by_category_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Box plot saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting box plot: {e}")

               try:
                    daily_totals = df.groupby('date')['amount'].sum().reset_index()
                    plt.figure(figsize=(12, 6))
                    sns.lineplot(x='date', y='amount', data=daily_totals, marker='o', color='teal')
                    plt.title(f"Spending Over Time ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.xlabel("Date")
                    plt.ylabel("Total Amount ($)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    filename = f"spending_over_time_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Line plot saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting line plot: {e}")

               try:
                    plt.figure(figsize=(10, 6))
                    sns.violinplot(x='category', y='amount', data=df, palette='muted', inner='quartile')
                    plt.title(f"Expense Distribution by Category (Violin) ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.xlabel("Category")
                    plt.ylabel("Amount ($)")
                    plt.xticks(rotation=45)
                    plt.tight_layout()
                    filename = f"expense_violin_by_category_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Violin plot saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting violin plot: {e}")

               try:
                    df['month'] = df['date'].dt.strftime('%Y-%m')
                    pivot = df.pivot_table(values='amount', index='month', columns='category', aggfunc='sum', fill_value=0)
                    plt.figure(figsize=(12, 8))
                    sns.heatmap(pivot, annot=True, fmt='.2f', cmap='YlGnBu', cbar_kws={'label': 'Total Amount ($)'})
                    plt.title(f"Spending Heatmap by Category and Month ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.xlabel("Category")
                    plt.ylabel("Month")
                    plt.tight_layout()
                    filename = f"spending_heatmap_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Heatmap saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting heatmap: {e}")

               try:
                    category_totals = df.groupby('category')['amount'].sum()
                    plt.figure(figsize=(8, 8))
                    category_totals.plot(kind='pie', autopct='%1.1f%%', startangle=90, colors=sns.color_palette('Set2'))
                    plt.title(f"Spending Distribution by Category ({date_start or 'Start'} to {date_end or 'End'})")
                    plt.ylabel("")
                    plt.tight_layout()
                    filename = f"category_distribution_filtered_{timestamp}.png"
                    plt.savefig(filename)
                    plt.close()
                    print(f"Pie chart saved as '{filename}'")
               except Exception as e:
                    print(f"Error plotting pie chart: {e}")

          except sql.Error as e:
               print(f"Database error: {e}")
          except Exception as e:
               print(f"Error generating graphs: {e}")

     def close(self):
          try:
               if self.connection and self.connection.is_connected():
                    self.connection.close()
                    print("Database connection closed successfully.")
               plt.close('all')  # Clear all Matplotlib figures
          except sql.Error as e:
               print(f"Error closing connection: {e}")

def main():
     print("Welcome to Your Personal Expense Tracker")
     try:
          tracker = Expenses()
          while True:
               print("\n=== Menu ===")
               print("1. Enter Expenses")
               print("2. Enter Received")
               print("3. View Expenses")
               print("4. View Received")
               print("5. Show Total Expenses")
               print("6. Show Total Received")
               print("7. Calculate Balance")
               print("8. Save to CSV")
               print("9. Save to PDF")
               print("10. Generate Graphs")
               print("11. Sync CSV to SQL")
               print("12. Exit")
               choice = input("Choose an option: ").strip()
               try:
                    choice_int = int(choice)
                    if choice_int < 1 or choice_int > 12:
                         print("Please enter a number between 1 and 12.")
                         continue
               except ValueError:
                    print("Invalid input. Enter a number between 1 and 12.")
                    continue
               if choice_int == 1:
                    tracker.enter_expenses()
               elif choice_int == 2:
                    tracker.enter_receiving()
               elif choice_int == 3:
                    tracker.view_expenses()
               elif choice_int == 4:
                    tracker.view_received()
               elif choice_int == 5:
                    month = input("Enter month to filter (YYYY-MM, or leave blank for all): ").strip() or None
                    tracker.show_total_expenses(month)
               elif choice_int == 6:
                    month = input("Enter month to filter (YYYY-MM, or leave blank for all): ").strip() or None
                    tracker.show_total_received(month)
               elif choice_int == 7:
                    tracker.calculate_balance()
               elif choice_int == 8:
                    tracker.save_to_a_csv()
               elif choice_int == 9:
                    tracker.save_to_a_pdf()
               elif choice_int == 10:
                    tracker.generate_graphs()
               elif choice_int == 11:
                    tracker.sync_csv_to_sql()
               elif choice_int == 12:
                    tracker.close()
                    print("Goodbye!")
                    break
     except Exception as e:
          print(f"Critical error in main: {e}")
          if 'tracker' in locals():
               tracker.close()

if __name__ == "__main__":
     main()

# app.py
# Expense Tracker Web App with Streamlit (Configurable Currency)
# Created by Rananjay Singh Chauhan on 19/03/25, adapted for Streamlit on 20/03/25

import streamlit as st
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
import seaborn as sns
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

    def filter_data(self, table, date_start=None, date_end=None, key=None, value=None):
        try:
            if table == "expenses":
                df = pd.DataFrame({
                    'category': self.category,
                    'amount': self.amountspent,
                    'date': pd.to_datetime(self.datespent),
                    'place': self.placeofspending,
                    'autopay': self.autopay
                })
            else:  # "received"
                df = pd.DataFrame({
                    'sender': self.sender,
                    'amount': self.amount_received,
                    'date': pd.to_datetime(self.dateofreceiving)
                })
            if date_start:
                df = df[df['date'] >= pd.to_datetime(date_start)]
            if date_end:
                df = df[df['date'] <= pd.to_datetime(date_end)]
            if key and value:
                df = df[df[key] == value]
            return df
        except Exception as e:
            st.error(f"Error filtering data: {e}")
            return pd.DataFrame()

    def enter_expenses(self, category, amount, date, place, autopay, currency_symbol):
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
            date_obj = pd.to_datetime(date, format='%Y-%m-%d', errors='raise')
            date = date_obj.strftime('%Y-%m-%d')
            autopay = autopay
            if not category:
                raise ValueError("Category cannot be empty.")
            self.category.append(category)
            self.amountspent.append(amount)
            self.datespent.append(date)
            self.placeofspending.append(place)
            self.autopay.append(autopay)
            return f"Expense added: {category}, {currency_symbol}{amount:.2f}, {date}"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def enter_receiving(self, sender, amount, date, currency_symbol):
        try:
            amount = float(amount)
            if amount < 0:
                raise ValueError("Amount cannot be negative.")
            date_obj = pd.to_datetime(date, format='%Y-%m-%d', errors='raise')
            date = date_obj.strftime('%Y-%m-%d')
            if not sender:
                raise ValueError("Sender cannot be empty.")
            self.sender.append(sender)
            self.amount_received.append(amount)
            self.dateofreceiving.append(date)
            return f"Received added: {sender}, {currency_symbol}{amount:.2f}, {date}"
        except ValueError as e:
            return f"Error: {e}"
        except Exception as e:
            return f"Unexpected error: {e}"

    def show_total_expenses(self, month=None, currency_symbol="₹"):
        try:
            if month:
                pd.to_datetime(month + "-01", format='%Y-%m-%d')
                df = pd.DataFrame({
                    'amount': self.amountspent,
                    'date': pd.to_datetime(self.datespent)
                })
                self.total_expenses = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
            else:
                self.total_expenses = sum(self.amountspent)
            month_str = f" for {month}" if month else ""
            return f"Total Expenses{month_str}: {currency_symbol}{self.total_expenses:.2f}"
        except ValueError:
            return f"Invalid month format: {month}. Use YYYY-MM."
        except Exception as e:
            return f"Error: {e}"

    def show_total_received(self, month=None, currency_symbol="₹"):
        try:
            if month:
                pd.to_datetime(month + "-01", format='%Y-%m-%d')
                df = pd.DataFrame({
                    'amount': self.amount_received,
                    'date': pd.to_datetime(self.dateofreceiving)
                })
                self.total_received = df[df['date'].dt.strftime('%Y-%m') == month]['amount'].sum()
            else:
                self.total_received = sum(self.amount_received)
            month_str = f" for {month}" if month else ""
            return f"Total Received{month_str}: {currency_symbol}{self.total_received:.2f}"
        except ValueError:
            return f"Invalid month format: {month}. Use YYYY-MM."
        except Exception as e:
            return f"Error: {e}"

    def calculate_balance(self, month=None, currency_symbol="₹"):
        exp_result = self.show_total_expenses(month, currency_symbol)
        rec_result = self.show_total_received(month, currency_symbol)
        self.account_balance = self.total_received - self.total_expenses
        self.amount_left = max(0, self.account_balance)
        self.amount_needed = max(0, -self.account_balance)
        return {
            'expenses': exp_result,
            'received': rec_result,
            'balance': f"Account Balance: {currency_symbol}{self.account_balance:.2f}",
            'left': f"Amount Left: {currency_symbol}{self.amount_left:.2f}",
            'needed': f"Amount Needed: {currency_symbol}{self.amount_needed:.2f}" if self.amount_needed > 0 else None
        }

    def save_to_csv_by_month(self):
        try:
            # Expenses
            expenses_df = pd.DataFrame({
                "Category": self.category,
                "Amount": self.amountspent,
                "Date": pd.to_datetime(self.datespent),
                "Place of Spending": self.placeofspending,
                "Auto-Pay": self.autopay
            })
            messages = []
            if not expenses_df.empty:
                expenses_df['Month'] = expenses_df['Date'].dt.strftime('%Y_%m')
                for month, group in expenses_df.groupby('Month'):
                    filename = f"expenses_{month}.csv"
                    group[['Category', 'Amount', 'Date', 'Place of Spending', 'Auto-Pay']].to_csv(filename, index=False)
                    messages.append(f"Saved expenses for {month} to '{filename}'")

            # Received
            received_df = pd.DataFrame({
                "Sender": self.sender,
                "Amount": self.amount_received,
                "Date": pd.to_datetime(self.dateofreceiving)
            })
            if not received_df.empty:
                received_df['Month'] = received_df['Date'].dt.strftime('%Y_%m')
                for month, group in received_df.groupby('Month'):
                    filename = f"received_{month}.csv"
                    group[['Sender', 'Amount', 'Date']].to_csv(filename, index=False)
                    messages.append(f"Saved received amounts for {month} to '{filename}'")

            if not messages:
                messages.append("No data to save.")
            messages.append("Data saved to monthly CSV files successfully.")
            return messages
        except Exception as e:
            return [f"Error saving to CSV: {e}"]

# Global instance (in-memory, resets on rerun)
if 'tracker' not in st.session_state:
    st.session_state.tracker = Expenses()

tracker = st.session_state.tracker

# Sidebar navigation with currency selector
st.sidebar.title("Expense Tracker")
currency = st.sidebar.selectbox("Currency", ["₹ (INR)", "$ (USD)", "€ (EUR)"], index=0)
currency_symbol = currency.split()[0]  # Extracts ₹, $, or €

page = st.sidebar.selectbox("Choose an option", [
    "Home",
    "Enter Expenses",
    "Enter Received",
    "View Expenses",
    "View Received",
    "Totals & Balance",
    "Save to Monthly CSVs"
])

# Main app logic
if page == "Home":
    st.title("Welcome to Your Personal Expense Tracker")
    st.write("Use the sidebar to manage your finances.")

elif page == "Enter Expenses":
    st.header("Enter Expenses")
    with st.form(key='expense_form'):
        category = st.text_input("Category", "")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date")
        place = st.text_input("Place", "")
        autopay = st.checkbox("Auto-Pay")
        submit = st.form_submit_button("Add Expense")
        if submit:
            message = tracker.enter_expenses(category, amount, str(date), place, autopay, currency_symbol)
            if "Error" in message:
                st.error(message)
            else:
                st.success(message)

elif page == "Enter Received":
    st.header("Enter Received")
    with st.form(key='received_form'):
        sender = st.text_input("Sender", "")
        amount = st.number_input("Amount", min_value=0.0, step=0.01)
        date = st.date_input("Date")
        submit = st.form_submit_button("Add Received")
        if submit:
            message = tracker.enter_receiving(sender, amount, str(date), currency_symbol)
            if "Error" in message:
                st.error(message)
            else:
                st.success(message)

elif page == "View Expenses":
    st.header("View Expenses")
    with st.form(key='view_expenses_form'):
        date_start = st.date_input("Start Date", None)
        date_end = st.date_input("End Date", None)
        category = st.text_input("Category", "")
        plot = st.checkbox("Generate Plot")
        submit = st.form_submit_button("Filter")
        if submit:
            df = tracker.filter_data(
                "expenses",
                date_start=str(date_start) if date_start else None,
                date_end=str(date_end) if date_end else None,
                key="category" if category else None,
                value=category
            )
            if df.empty:
                st.warning("No expenses match the filter.")
            else:
                df = df.rename(columns={
                    "date": "Date",
                    "amount": "Amount",
                    "category": "Category",
                    "place": "Place",
                    "autopay": "Auto-Pay"
                })
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(df[["Date", "Amount", "Category", "Place", "Auto-Pay"]])
                if plot:
                    fig, ax = plt.subplots(figsize=(10, 6))
                    sns.barplot(x='Category', y='Amount', data=df, estimator=sum, palette='muted', ax=ax)
                    ax.set_title(f"Expenses by Category ({date_start or 'Start'} to {date_end or 'End'})")
                    ax.set_xlabel("Category")
                    ax.set_ylabel(f"Total Amount ({currency_symbol})")
                    plt.xticks(rotation=45)
                    st.pyplot(fig)

elif page == "View Received":
    st.header("View Received")
    with st.form(key='view_received_form'):
        date_start = st.date_input("Start Date", None)
        date_end = st.date_input("End Date", None)
        sender = st.text_input("Sender", "")
        submit = st.form_submit_button("Filter")
        if submit:
            df = tracker.filter_data(
                "received",
                date_start=str(date_start) if date_start else None,
                date_end=str(date_end) if date_end else None,
                key="sender" if sender else None,
                value=sender
            )
            if df.empty:
                st.warning("No received amounts match the filter.")
            else:
                df = df.rename(columns={
                    "date": "Date",
                    "amount": "Amount",
                    "sender": "Sender"
                })
                df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
                st.dataframe(df[["Date", "Amount", "Sender"]])

elif page == "Totals & Balance":
    st.header("Totals & Balance")
    with st.form(key='totals_form'):
        month = st.text_input("Month (YYYY-MM)", "")
        plot = st.checkbox("Generate Plot")
        submit = st.form_submit_button("Calculate")
        if submit:
            month = month if month else None
            results = tracker.calculate_balance(month, currency_symbol)
            st.write(results['expenses'])
            st.write(results['received'])
            st.write(results['balance'])
            st.write(results['left'])
            if results['needed']:
                st.write(results['needed'])
            if plot:
                fig, ax = plt.subplots(figsize=(6, 6))
                balance_data = pd.DataFrame({
                    'Type': ['Expenses', 'Received'],
                    'Amount': [tracker.total_expenses, tracker.total_received]
                })
                sns.barplot(x='Type', y='Amount', data=balance_data, palette='Set2', ax=ax)
                month_str = f" for {month}" if month else ""
                ax.set_title(f"Expenses vs Received{month_str}")
                ax.set_ylabel(f"Amount ({currency_symbol})")
                st.pyplot(fig)

elif page == "Save to Monthly CSVs":
    st.header("Save to Monthly CSVs")
    if st.button("Save"):
        messages = tracker.save_to_csv_by_month()
        for message in messages:
            if "Error" in message:
                st.error(message)
            else:
                st.success(message)

if __name__ == "__main__":
    st.write("Made by Rananjay Singh 'RJ' Chauhan")

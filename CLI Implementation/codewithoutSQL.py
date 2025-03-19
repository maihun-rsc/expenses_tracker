# Expense-Tracker (No SQL)
# Created by Rananjay Singh Chauhan on 19/03/25, refined with Grok's help
# CLI implementation with CSV and Graphs, no SQLite

import pandas as pd
import matplotlib.pyplot as plt
import csv

class Expenses:
    def __init__(self):
        """Initialize the expense tracker with in-memory storage."""
        self.expenses = {}
        self.category = []
        self.amountspent = []
        self.datespent = []
        self.placeofspending = []
        self.autopay = []
        self.load_from_csv()

    def load_from_csv(self):
        """Load expenses from CSV into memory if it exists."""
        try:
            with open("expenses.csv", "r") as f:
                reader = csv.reader(f)
                next(reader)  # Skip header
                for row in reader:
                    self.datespent.append(row[0])
                    self.amountspent.append(float(row[1]))
                    self.category.append(row[2])
                    self.placeofspending.append(row[3])
                    self.autopay.append(bool(int(row[4])))
            self.update_expenses_dict()
        except FileNotFoundError:
            pass

    def update_expenses_dict(self):
        """Update the expenses dictionary from lists."""
        self.expenses["Date"] = self.datespent
        self.expenses["Amount Spent"] = self.amountspent
        self.expenses["Category"] = self.category
        self.expenses["Place"] = self.placeofspending
        self.expenses["Autopay"] = self.autopay

    def enter_expenses(self):
        """Enter new expenses and save to CSV."""
        try:
            x = int(input("Enter the number of expenses to add: "))
            for _ in range(x):
                category = input("Enter category: ")
                amount = float(input("Enter amount spent: "))
                if amount < 0:
                    raise ValueError("Amount cannot be negative.")
                date = input("Date of spending (DD-MM-YYYY): ")
                place = input("Enter place of spending: ")
                autopay = input("Auto-pay? (True/False): ").lower() == 'true'
                self.category.append(category)
                self.amountspent.append(amount)
                self.datespent.append(date)
                self.placeofspending.append(place)
                self.autopay.append(autopay)
            self.update_expenses_dict()
            self.save_to_csv()
            print("Expenses added. Enter 1 to view, 0 to continue.")
            if int(input()) == 1:
                self.view_expenses()
        except ValueError as e:
            print(f"Error: {e}. Try again.")

    def view_expenses(self):
        """View expenses and save to CSV."""
        if not self.datespent:
            print("No expenses found.")
            return
        print("\n=== Expenses ===")
        for i in range(len(self.datespent)):
            print(f"{self.datespent[i]} | ${self.amountspent[i]:.2f} | {self.category[i]} | {self.placeofspending[i]} | Autopay: {self.autopay[i]}")
        self.save_to_csv()

    def total_expense(self):
        """Calculate total expenses."""
        return sum(self.amountspent)

    def save_to_csv(self):
        """Save expenses to CSV."""
        with open("expenses.csv", "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Date", "Amount Spent", "Category", "Place", "Autopay"])
            writer.writerows(zip(self.datespent, self.amountspent, self.category, self.placeofspending, [int(a) for a in self.autopay]))
        print("Saved to 'expenses.csv'")

    def generate_graphs(self):
        """Generate basic spending graphs."""
        df = pd.DataFrame(self.expenses)
        if df.empty:
            print("No data to graph.")
            return
        df['Date'] = pd.to_datetime(df['Date'], format='%d-%m-%Y')

        # Bar Chart: Spending by Category
        category_totals = df.groupby("Category")["Amount Spent"].sum()
        plt.figure(figsize=(10, 6))
        category_totals.plot(kind='bar', color='skyblue')
        plt.title("Spending by Category")
        plt.xlabel("Category")
        plt.ylabel("Total Amount ($)")
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig("spending_by_category.png")
        plt.close()
        print("Bar chart saved as 'spending_by_category.png'")

        # Pie Chart: Category Distribution
        plt.figure(figsize=(8, 8))
        category_totals.plot(kind='pie', autopct='%1.1f%%', startangle=90)
        plt.title("Spending Distribution by Category")
        plt.ylabel("")
        plt.tight_layout()
        plt.savefig("category_distribution.png")
        plt.close()
        print("Pie chart saved as 'category_distribution.png'")

def main():
    """Run the expense tracker CLI."""
    print("Welcome to Your Personal Expense Tracker")
    id = input("Enter ID: ")
    password = input("Enter Password: ")
    if id == "1234" and password == "":
        tracker = Expenses()
        while True:
            print("\n=== Menu ===")
            print("1. Add Expense")
            print("2. View Expenses")
            print("3. Total Expenses")
            print("4. Generate Graphs")
            print("5. Exit")
            choice = input("Choose an option: ")
            if choice == "1":
                tracker.enter_expenses()
            elif choice == "2":
                tracker.view_expenses()
            elif choice == "3":
                print(f"Total Expenses: ${tracker.total_expense():.2f}")
            elif choice == "4":
                tracker.generate_graphs()
            elif choice == "5":
                print("Goodbye!")
                break
            else:
                print("Invalid option, try again.")
    else:
        print("Invalid ID or Password.")

if __name__ == "__main__":
    main()

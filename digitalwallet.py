import sqlite3
from datetime import datetime
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView

# Database setup (create expenses table if it doesn't exist)
def setup_database():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            amount REAL,
            category TEXT,
            description TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

# Function to save expense data to the database
def save_expense(amount, category, description):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        INSERT INTO expenses (amount, category, description, date) 
        VALUES (?, ?, ?, ?)
    ''', (amount, category, description, date))
    conn.commit()
    conn.close()

# Function to view all expenses from the database
def get_expenses():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM expenses")
    expenses = cursor.fetchall()
    conn.close()
    return expenses

# Function to edit an expense
def edit_expense(expense_id, new_amount, new_category, new_description):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE expenses
        SET amount = ?, category = ?, description = ?, date = ?
        WHERE id = ?
    ''', (new_amount, new_category, new_description, date, expense_id))
    conn.commit()
    conn.close()

# Function to delete an expense
def delete_expense(expense_id):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

# Main application class
class ExpenseApp(App):
    def build(self):
        self.title = "Expense Tracker"
        self.setup_ui()
        setup_database()  # Ensure the database is ready

    def setup_ui(self):
        # Create the root layout
        self.root = BoxLayout(orientation='vertical')

        # Create an input form for adding expenses
        self.amount_input = TextInput(hint_text="Enter amount", multiline=False, input_filter='float')
        self.category_spinner = Spinner(text="Select Category", values=["Food", "Bills", "Travel", "Others"])
        self.description_input = TextInput(hint_text="Enter description", multiline=False)

        save_button = Button(text="Save Expense")
        save_button.bind(on_release=self.save_expense)

        # Add input fields to the layout
        form_layout = BoxLayout(orientation='vertical', padding=10)
        form_layout.add_widget(self.amount_input)
        form_layout.add_widget(self.category_spinner)
        form_layout.add_widget(self.description_input)
        form_layout.add_widget(save_button)

        # Create a button to view the expenses
        view_button = Button(text="View Expenses")
        view_button.bind(on_release=self.show_expenses)

        # Add form and view button to the root layout
        self.root.add_widget(form_layout)
        self.root.add_widget(view_button)

        return self.root

    def save_expense(self, instance):
        try:
            amount = float(self.amount_input.text)
            category = self.category_spinner.text
            description = self.description_input.text
            save_expense(amount, category, description)

            # Reset the inputs after saving
            self.amount_input.text = ''
            self.category_spinner.text = 'Select Category'
            self.description_input.text = ''

            self.show_popup("Success", "Expense saved successfully!")
        except ValueError:
            self.show_popup("Error", "Invalid input. Please enter valid amount and description.")

    def show_expenses(self, instance):
        expenses = get_expenses()
        if not expenses:
            self.show_popup("No Data", "No expenses recorded yet.")
            return

        # Create a layout to display expenses
        layout = GridLayout(cols=4, padding=10, spacing=10)
        layout.add_widget(Label(text="Amount"))
        layout.add_widget(Label(text="Category"))
        layout.add_widget(Label(text="Description"))
        layout.add_widget(Label(text="Actions"))

        for expense in expenses:
            layout.add_widget(Label(text=str(expense[1])))
            layout.add_widget(Label(text=expense[2]))
            layout.add_widget(Label(text=expense[3]))
            action_button = Button(text="Edit/Delete")
            action_button.bind(on_release=lambda btn, expense_id=expense[0]: self.edit_delete_expense(expense_id))
            layout.add_widget(action_button)

        # Create scrollable view to display expenses
        scroll_view = ScrollView()
        scroll_view.add_widget(layout)

        # Create a popup to show the expenses
        popup = Popup(title="Expenses", content=scroll_view, size_hint=(0.9, 0.9))
        popup.open()

    def edit_delete_expense(self, expense_id):
        expenses = get_expenses()
        expense = next(exp for exp in expenses if exp[0] == expense_id)
        self.show_edit_delete_popup(expense_id, expense[1], expense[2], expense[3])

    def show_edit_delete_popup(self, expense_id, amount, category, description):
        # Create a layout for editing or deleting the expense
        popup_layout = BoxLayout(orientation='vertical')

        amount_input = TextInput(hint_text="Enter amount", text=str(amount), multiline=False, input_filter='float')
        category_spinner = Spinner(text=category, values=["Food", "Bills", "Travel", "Others"])
        description_input = TextInput(hint_text="Enter description", text=description, multiline=False)

        def update_expense(instance):
            new_amount = float(amount_input.text)
            new_category = category_spinner.text
            new_description = description_input.text
            edit_expense(expense_id, new_amount, new_category, new_description)
            self.show_popup("Success", "Expense updated successfully!")

        def delete_expense(instance):
            delete_expense(expense_id)
            self.show_popup("Success", "Expense deleted successfully!")

        update_button = Button(text="Update Expense")
        update_button.bind(on_release=update_expense)

        delete_button = Button(text="Delete Expense")
        delete_button.bind(on_release=delete_expense)

        popup_layout.add_widget(amount_input)
        popup_layout.add_widget(category_spinner)
        popup_layout.add_widget(description_input)
        popup_layout.add_widget(update_button)
        popup_layout.add_widget(delete_button)

        popup = Popup(title="Edit/Delete Expense", content=popup_layout, size_hint=(0.9, 0.9))
        popup.open()

    def show_popup(self, title, message):
        popup = Popup(title=title, content=Label(text=message), size_hint=(0.6, 0.4))
        popup.open()

if __name__ == "__main__":
    ExpenseApp().run()

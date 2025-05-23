from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.core.window import Window
import sqlite3
from datetime import datetime

# ------------------ Database ------------------

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

def save_expense_to_db(amount, category, description):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)',
                   (amount, category, description, date))
    conn.commit()
    conn.close()

def get_recent_expenses(limit=50):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM expenses ORDER BY date DESC LIMIT ?', (limit,))
    data = cursor.fetchall()
    conn.close()
    return data

def edit_expense_in_db(expense_id, amount, category, description):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
        UPDATE expenses
        SET amount = ?, category = ?, description = ?, date = ?
        WHERE id = ?
    ''', (amount, category, description, date, expense_id))
    conn.commit()
    conn.close()

def delete_expense_from_db(expense_id):
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
    conn.commit()
    conn.close()

# ------------------ Screens ------------------

class AddExpenseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Labels with * for mandatory fields
        amount_label = Label(text='Amount *', size_hint_y=None, height=25)
        self.amount_input = TextInput(multiline=False, input_filter='float', size_hint_y=None, height=40)

        category_label = Label(text='Category *', size_hint_y=None, height=25)
        self.category_input = Spinner(text="Select Category", values=["Food", "Bills", "Travel", "Others"], size_hint_y=None, height=40)

        description_label = Label(text='Description *', size_hint_y=None, height=25)
        self.description_input = TextInput(multiline=False, size_hint_y=None, height=40)

        save_button = Button(text="Save Expense", size_hint_y=None, height=40)
        save_button.bind(on_release=self.save_expense)

        view_button = Button(text="View Expenses", size_hint_y=None, height=40)
        view_button.bind(on_release=self.go_to_view)

        close_button = Button(text="Close App", size_hint_y=None, height=40)
        close_button.bind(on_release=self.close_app)

        # Add widgets to layout
        layout.add_widget(amount_label)
        layout.add_widget(self.amount_input)
        layout.add_widget(category_label)
        layout.add_widget(self.category_input)
        layout.add_widget(description_label)
        layout.add_widget(self.description_input)
        layout.add_widget(save_button)
        layout.add_widget(view_button)
        layout.add_widget(close_button)

        self.add_widget(layout)

    def save_expense(self, instance):
        try:
            amount_text = self.amount_input.text.strip()
            category = self.category_input.text
            description = self.description_input.text.strip()

            if not amount_text or category == "Select Category" or not description:
                raise ValueError("Please fill in all mandatory fields.")

            amount = float(amount_text)
            save_expense_to_db(amount, category, description)
            self.amount_input.text = ''
            self.category_input.text = 'Select Category'
            self.description_input.text = ''
            self.show_popup("Success", "Expense saved successfully.")
        except ValueError as e:
            self.show_popup("Error", str(e))

    def go_to_view(self, instance):
        self.manager.get_screen('view').load_expenses()
        self.manager.current = 'view'

    def close_app(self, instance):
        App.get_running_app().stop()
        Window.close()

    def show_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg), size_hint=(0.6, 0.4))
        popup.open()

class ViewExpensesScreen(Screen):
    def load_expenses(self):
        self.clear_widgets()
        layout = BoxLayout(orientation='vertical')
        scroll = ScrollView()

        grid = GridLayout(cols=5, size_hint_y=None, spacing=10, padding=10)
        grid.bind(minimum_height=grid.setter('height'))

        # Headers
        grid.add_widget(Label(text="Amount"))
        grid.add_widget(Label(text="Category"))
        grid.add_widget(Label(text="Description"))
        grid.add_widget(Label(text="Edit"))
        grid.add_widget(Label(text="Delete"))

        total = 0
        expenses = get_recent_expenses()
        for exp in expenses:
            exp_id, amt, cat, desc, _ = exp
            total += amt
            grid.add_widget(Label(text=f"₹{amt:.2f}"))
            grid.add_widget(Label(text=cat))
            grid.add_widget(Label(text=desc))

            edit_btn = Button(text="Edit", size_hint_y=None, height=30)
            edit_btn.bind(on_release=lambda btn, eid=exp_id: self.edit_expense_popup(eid))
            grid.add_widget(edit_btn)

            del_btn = Button(text="Delete", size_hint_y=None, height=30)
            del_btn.bind(on_release=lambda btn, eid=exp_id: self.delete_expense(eid))
            grid.add_widget(del_btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        total_label = Label(text=f"Total: ₹{total:.2f}", size_hint_y=None, height=40)
        layout.add_widget(total_label)

        back_btn = Button(text="Back", size_hint_y=None, height=40)
        back_btn.bind(on_release=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    def edit_expense_popup(self, expense_id):
        # Fetch expense data
        expense = next(exp for exp in get_recent_expenses() if exp[0] == expense_id)

        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        amount_label = Label(text='Amount *', size_hint_y=None, height=25)
        amount_input = TextInput(text=str(expense[1]), multiline=False, input_filter='float', size_hint_y=None, height=40)

        category_label = Label(text='Category *', size_hint_y=None, height=25)
        category_spinner = Spinner(text=expense[2], values=["Food", "Bills", "Travel", "Others"], size_hint_y=None, height=40)

        description_label = Label(text='Description *', size_hint_y=None, height=25)
        description_input = TextInput(text=expense[3], multiline=False, size_hint_y=None, height=40)

        def update_expense(instance):
            try:
                amt_text = amount_input.text.strip()
                cat = category_spinner.text
                desc = description_input.text.strip()
                if not amt_text or cat == "Select Category" or not desc:
                    raise ValueError("Please fill in all mandatory fields.")
                amt = float(amt_text)
                edit_expense_in_db(expense_id, amt, cat, desc)
                self.show_popup("Success", "Expense updated.")
                popup.dismiss()
                self.load_expenses()
            except ValueError as e:
                self.show_popup("Error", str(e))

        def delete_expense(instance):
            delete_expense_from_db(expense_id)
            self.show_popup("Success", "Expense deleted.")
            popup.dismiss()
            self.load_expenses()

        update_btn = Button(text="Update", size_hint_y=None, height=40)
        update_btn.bind(on_release=update_expense)

        delete_btn = Button(text="Delete", size_hint_y=None, height=40)
        delete_btn.bind(on_release=delete_expense)

        popup_layout.add_widget(amount_label)
        popup_layout.add_widget(amount_input)
        popup_layout.add_widget(category_label)
        popup_layout.add_widget(category_spinner)
        popup_layout.add_widget(description_label)
        popup_layout.add_widget(description_input)
        popup_layout.add_widget(update_btn)
        popup_layout.add_widget(delete_btn)

        popup = Popup(title="Edit/Delete Expense", content=popup_layout, size_hint=(0.9, 0.9))
        popup.open()

    def delete_expense(self, expense_id):
        delete_expense_from_db(expense_id)
        self.load_expenses()

    def go_back(self, instance):
        self.manager.current = 'add'

    def show_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg), size_hint=(0.6, 0.4))
        popup.open()

# ------------------ App ------------------

class ExpenseTrackerApp(App):
    def build(self):
        setup_database()
        sm = ScreenManager()
        sm.add_widget(AddExpenseScreen(name='add'))
        sm.add_widget(ViewExpensesScreen(name='view'))
        return sm

if __name__ == '__main__':
    ExpenseTrackerApp().run()

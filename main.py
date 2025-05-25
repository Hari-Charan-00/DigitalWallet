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
import requests
import json
from datetime import datetime
from kivy.storage.jsonstore import JsonStore

# ------------------ Configuration ------------------
API_BASE_URL = "http://localhost:9000"  # Make sure this matches your API server
store = JsonStore('user_data.json')  # For storing tokens locally

# ------------------ API Client ------------------
class APIClient:
    def __init__(self):
        self.base_url = API_BASE_URL
        self.access_token = None
        self.refresh_token = None
        self.load_tokens()

    def load_tokens(self):
        """Load tokens from local storage"""
        if store.exists('auth'):
            auth_data = store.get('auth')
            self.access_token = auth_data.get('access_token')
            self.refresh_token = auth_data.get('refresh_token')

    def save_tokens(self, access_token, refresh_token):
        """Save tokens to local storage"""
        self.access_token = access_token
        self.refresh_token = refresh_token
        store.put('auth', access_token=access_token, refresh_token=refresh_token)

    def clear_tokens(self):
        """Clear tokens from memory and storage"""
        self.access_token = None
        self.refresh_token = None
        if store.exists('auth'):
            store.delete('auth')

    def get_headers(self):
        """Get headers with authorization token"""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def refresh_access_token(self):
        """Refresh access token using refresh token"""
        if not self.refresh_token:
            return False
        
        try:
            response = requests.post(f"{self.base_url}/refresh", 
                                   json={"refresh_token": self.refresh_token},
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.save_tokens(data['access_token'], data['refresh_token'])
                return True
        except Exception as e:
            print(f"Token refresh failed: {e}")
        return False

    def make_request(self, method, endpoint, **kwargs):
        """Make authenticated API request with automatic token refresh"""
        url = f"{self.base_url}{endpoint}"
        headers = self.get_headers()
        
        # Merge provided headers with auth headers
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        kwargs['timeout'] = 10  # Add timeout

        try:
            response = requests.request(method, url, **kwargs)
            
            # If unauthorized, try to refresh token and retry once
            if response.status_code == 401 and self.refresh_access_token():
                kwargs['headers'] = self.get_headers()
                response = requests.request(method, url, **kwargs)
                
            return response
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return None

    def register(self, username, password):
        """Register new user"""
        try:
            response = requests.post(f"{self.base_url}/register", 
                                   json={"username": username, "password": password},
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            return response
        except requests.exceptions.RequestException as e:
            print(f"Registration failed: {e}")
            return None

    def login(self, username, password):
        """Login user and save tokens"""
        try:
            response = requests.post(f"{self.base_url}/login", 
                                   json={"username": username, "password": password},
                                   headers={"Content-Type": "application/json"},
                                   timeout=10)
            if response and response.status_code == 200:
                data = response.json()
                self.save_tokens(data['access_token'], data['refresh_token'])
            return response
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return None

    def get_expenses(self):
        """Get user expenses"""
        response = self.make_request('GET', '/expenses/')
        if response and response.status_code == 200:
            return response.json()
        return []

    def add_expense(self, title, amount, category, description):
        """Add new expense"""
        data = {
            "title": title,
            "amount": amount,
            "category": category,
            "description": description
        }
        response = self.make_request('POST', '/expenses/', json=data)
        return response

    def update_expense(self, expense_id, title, amount, category, description):
        """Update existing expense"""
        data = {
            "title": title,
            "amount": amount,
            "category": category,
            "description": description
        }
        response = self.make_request('PUT', f'/expenses/{expense_id}', json=data)
        return response

    def delete_expense(self, expense_id):
        """Delete expense"""
        response = self.make_request('DELETE', f'/expenses/{expense_id}')
        return response

    def is_authenticated(self):
        """Check if user is authenticated"""
        return self.access_token is not None

# Global API client instance
api_client = APIClient()

# ------------------ Screens ------------------

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title = Label(text='Expense Tracker - Login', size_hint_y=None, height=50, 
                     font_size='20sp')
        
        username_label = Label(text='Username *', size_hint_y=None, height=30)
        self.username_input = TextInput(multiline=False, size_hint_y=None, height=40)

        password_label = Label(text='Password *', size_hint_y=None, height=30)
        self.password_input = TextInput(multiline=False, password=True, size_hint_y=None, height=40)

        login_button = Button(text="Login", size_hint_y=None, height=50)
        login_button.bind(on_release=self.login)

        register_button = Button(text="Register New Account", size_hint_y=None, height=50)
        register_button.bind(on_release=self.go_to_register)

        layout.add_widget(title)
        layout.add_widget(username_label)
        layout.add_widget(self.username_input)
        layout.add_widget(password_label)
        layout.add_widget(self.password_input)
        layout.add_widget(login_button)
        layout.add_widget(register_button)

        self.add_widget(layout)

    def login(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.show_popup("Error", "Please fill in all fields")
            return

        response = api_client.login(username, password)
        if response is None:
            self.show_popup("Error", "Connection failed. Please check if the API server is running on http://localhost:9000")
            return

        if response.status_code == 200:
            self.show_popup("Success", "Login successful!")
            self.manager.current = 'add'
            # Clear input fields
            self.username_input.text = ''
            self.password_input.text = ''
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', 'Invalid credentials')
            except:
                error_msg = "Invalid credentials"
            self.show_popup("Error", error_msg)

    def go_to_register(self, instance):
        self.manager.current = 'register'

    def show_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg), size_hint=(0.6, 0.4))
        popup.open()

class RegisterScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=15)

        title = Label(text='Create New Account', size_hint_y=None, height=50, 
                     font_size='20sp')
        
        username_label = Label(text='Username *', size_hint_y=None, height=30)
        self.username_input = TextInput(multiline=False, size_hint_y=None, height=40)

        password_label = Label(text='Password *', size_hint_y=None, height=30)
        self.password_input = TextInput(multiline=False, password=True, size_hint_y=None, height=40)

        confirm_password_label = Label(text='Confirm Password *', size_hint_y=None, height=30)
        self.confirm_password_input = TextInput(multiline=False, password=True, size_hint_y=None, height=40)

        register_button = Button(text="Register", size_hint_y=None, height=50)
        register_button.bind(on_release=self.register)

        back_button = Button(text="Back to Login", size_hint_y=None, height=50)
        back_button.bind(on_release=self.go_to_login)

        layout.add_widget(title)
        layout.add_widget(username_label)
        layout.add_widget(self.username_input)
        layout.add_widget(password_label)
        layout.add_widget(self.password_input)
        layout.add_widget(confirm_password_label)
        layout.add_widget(self.confirm_password_input)
        layout.add_widget(register_button)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def register(self, instance):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        confirm_password = self.confirm_password_input.text.strip()

        if not username or not password or not confirm_password:
            self.show_popup("Error", "Please fill in all fields")
            return

        if password != confirm_password:
            self.show_popup("Error", "Passwords do not match")
            return

        if len(password) < 6:
            self.show_popup("Error", "Password must be at least 6 characters")
            return

        response = api_client.register(username, password)
        if response is None:
            self.show_popup("Error", "Connection failed. Please check if the API server is running on http://localhost:9000")
            return

        if response.status_code == 200:
            self.show_popup("Success", "Registration successful! Please login.")
            self.manager.current = 'login'
            # Clear input fields
            self.username_input.text = ''
            self.password_input.text = ''
            self.confirm_password_input.text = ''
        else:
            error_msg = "Registration failed"
            try:
                error_data = response.json()
                error_msg = error_data.get('detail', error_msg)
            except:
                pass
            self.show_popup("Error", error_msg)

    def go_to_login(self, instance):
        self.manager.current = 'login'

    def show_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg), size_hint=(0.6, 0.4))
        popup.open()

class AddExpenseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title field (using title instead of description as primary field)
        title_label = Label(text='Title *', size_hint_y=None, height=25)
        self.title_input = TextInput(multiline=False, size_hint_y=None, height=40)

        # Amount field
        amount_label = Label(text='Amount *', size_hint_y=None, height=25)
        self.amount_input = TextInput(multiline=False, input_filter='float', size_hint_y=None, height=40)

        # Category field
        category_label = Label(text='Category *', size_hint_y=None, height=25)
        self.category_input = Spinner(text="Select Category", values=["Food", "Bills", "Travel", "Others"], size_hint_y=None, height=40)

        # Description field
        description_label = Label(text='Description', size_hint_y=None, height=25)
        self.description_input = TextInput(multiline=False, size_hint_y=None, height=40)

        save_button = Button(text="Save Expense", size_hint_y=None, height=40)
        save_button.bind(on_release=self.save_expense)

        view_button = Button(text="View Expenses", size_hint_y=None, height=40)
        view_button.bind(on_release=self.go_to_view)

        logout_button = Button(text="Logout", size_hint_y=None, height=40)
        logout_button.bind(on_release=self.logout)

        close_button = Button(text="Close App", size_hint_y=None, height=40)
        close_button.bind(on_release=self.close_app)

        layout.add_widget(title_label)
        layout.add_widget(self.title_input)
        layout.add_widget(amount_label)
        layout.add_widget(self.amount_input)
        layout.add_widget(category_label)
        layout.add_widget(self.category_input)
        layout.add_widget(description_label)
        layout.add_widget(self.description_input)
        layout.add_widget(save_button)
        layout.add_widget(view_button)
        layout.add_widget(logout_button)
        layout.add_widget(close_button)

        self.add_widget(layout)

    def save_expense(self, instance):
        try:
            title = self.title_input.text.strip()
            amount_text = self.amount_input.text.strip()
            category = self.category_input.text
            description = self.description_input.text.strip()

            if not title or not amount_text or category == "Select Category":
                raise ValueError("Please fill in all mandatory fields.")

            amount = float(amount_text)
            
            response = api_client.add_expense(title, amount, category, description)
            
            if response is None:
                self.show_popup("Error", "Connection failed. Please check if the API server is running.")
                return

            if response.status_code == 200:
                # Clear input fields
                self.title_input.text = ''
                self.amount_input.text = ''
                self.category_input.text = 'Select Category'
                self.description_input.text = ''
                self.show_popup("Success", "Expense saved successfully.")
            elif response.status_code == 401:
                self.show_popup("Error", "Session expired. Please login again.")
                self.logout(None)
            else:
                self.show_popup("Error", "Failed to save expense.")
                
        except ValueError as e:
            self.show_popup("Error", str(e))

    def go_to_view(self, instance):
        self.manager.get_screen('view').load_expenses()
        self.manager.current = 'view'

    def logout(self, instance):
        api_client.clear_tokens()
        self.manager.current = 'login'

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
        
        # Check authentication first
        if not api_client.is_authenticated():
            self.manager.current = 'login'
            return

        expenses = api_client.get_expenses()
        
        if expenses is None:
            # Handle connection error
            error_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
            error_layout.add_widget(Label(text="Connection failed. Please check if the API server is running."))
            back_btn = Button(text="Back", size_hint_y=None, height=40)
            back_btn.bind(on_release=self.go_back)
            error_layout.add_widget(back_btn)
            layout.add_widget(error_layout)
            self.add_widget(layout)
            return

        scroll = ScrollView()
        grid = GridLayout(cols=5, size_hint_y=None, spacing=10, padding=10)
        grid.bind(minimum_height=grid.setter('height'))

        # Headers
        grid.add_widget(Label(text="Title", text_size=(None, None), halign="center"))
        grid.add_widget(Label(text="Amount", text_size=(None, None), halign="center"))
        grid.add_widget(Label(text="Category", text_size=(None, None), halign="center"))
        grid.add_widget(Label(text="Edit", text_size=(None, None), halign="center"))
        grid.add_widget(Label(text="Delete", text_size=(None, None), halign="center"))

        total = 0
        for exp in expenses:
            total += exp['amount']
            
            # Title (truncate if too long)
            title_text = exp['title'][:20] + "..." if len(exp['title']) > 20 else exp['title']
            grid.add_widget(Label(text=title_text, text_size=(None, None), halign="center"))
            
            grid.add_widget(Label(text=f"₹{exp['amount']:.2f}", text_size=(None, None), halign="center"))
            grid.add_widget(Label(text=exp['category'], text_size=(None, None), halign="center"))

            edit_btn = Button(text="Edit", size_hint_y=None, height=30)
            edit_btn.bind(on_release=lambda btn, expense=exp: self.edit_expense_popup(expense))
            grid.add_widget(edit_btn)

            del_btn = Button(text="Delete", size_hint_y=None, height=30)
            del_btn.bind(on_release=lambda btn, expense_id=exp['id']: self.delete_expense(expense_id))
            grid.add_widget(del_btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)

        total_label = Label(text=f"Total: ₹{total:.2f}", size_hint_y=None, height=40)
        layout.add_widget(total_label)

        back_btn = Button(text="Back", size_hint_y=None, height=40)
        back_btn.bind(on_release=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)

    # ... keep existing code (edit_expense_popup, delete_expense, go_back, show_popup methods)

    def edit_expense_popup(self, expense):
        popup_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        title_label = Label(text='Title *', size_hint_y=None, height=25)
        title_input = TextInput(text=expense['title'], multiline=False, size_hint_y=None, height=40)

        amount_label = Label(text='Amount *', size_hint_y=None, height=25)
        amount_input = TextInput(text=str(expense['amount']), multiline=False, input_filter='float', size_hint_y=None, height=40)

        category_label = Label(text='Category *', size_hint_y=None, height=25)
        category_spinner = Spinner(text=expense['category'], values=["Food", "Bills", "Travel", "Others"], size_hint_y=None, height=40)

        description_label = Label(text='Description', size_hint_y=None, height=25)
        description_input = TextInput(text=expense.get('description', ''), multiline=False, size_hint_y=None, height=40)

        def update_expense(instance):
            try:
                title = title_input.text.strip()
                amt_text = amount_input.text.strip()
                cat = category_spinner.text
                desc = description_input.text.strip()
                
                if not title or not amt_text or cat == "Select Category":
                    raise ValueError("Please fill in all mandatory fields.")
                    
                amt = float(amt_text)
                
                response = api_client.update_expense(expense['id'], title, amt, cat, desc)
                
                if response and response.status_code == 200:
                    self.show_popup("Success", "Expense updated.")
                    popup.dismiss()
                    self.load_expenses()
                elif response and response.status_code == 401:
                    self.show_popup("Error", "Session expired. Please login again.")
                    popup.dismiss()
                    self.manager.current = 'login'
                else:
                    self.show_popup("Error", "Failed to update expense.")
                    
            except ValueError as e:
                self.show_popup("Error", str(e))

        update_btn = Button(text="Update", size_hint_y=None, height=40)
        update_btn.bind(on_release=update_expense)

        cancel_btn = Button(text="Cancel", size_hint_y=None, height=40)
        cancel_btn.bind(on_release=lambda x: popup.dismiss())

        popup_layout.add_widget(title_label)
        popup_layout.add_widget(title_input)
        popup_layout.add_widget(amount_label)
        popup_layout.add_widget(amount_input)
        popup_layout.add_widget(category_label)
        popup_layout.add_widget(category_spinner)
        popup_layout.add_widget(description_label)
        popup_layout.add_widget(description_input)
        popup_layout.add_widget(update_btn)
        popup_layout.add_widget(cancel_btn)

        popup = Popup(title="Edit Expense", content=popup_layout, size_hint=(0.9, 0.9))
        popup.open()

    def delete_expense(self, expense_id):
        response = api_client.delete_expense(expense_id)
        if response and response.status_code == 200:
            self.show_popup("Success", "Expense deleted.")
            self.load_expenses()
        elif response and response.status_code == 401:
            self.show_popup("Error", "Session expired. Please login again.")
            self.manager.current = 'login'
        else:
            self.show_popup("Error", "Failed to delete expense.")

    def go_back(self, instance):
        self.manager.current = 'add'

    def show_popup(self, title, msg):
        popup = Popup(title=title, content=Label(text=msg), size_hint=(0.6, 0.4))
        popup.open()

# ------------------ App ------------------

class ExpenseTrackerApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegisterScreen(name='register'))
        sm.add_widget(AddExpenseScreen(name='add'))
        sm.add_widget(ViewExpensesScreen(name='view'))
        
        # Start with login screen or main screen if already authenticated
        if api_client.is_authenticated():
            sm.current = 'add'
        else:
            sm.current = 'login'
            
        return sm

if __name__ == '__main__':
    ExpenseTrackerApp().run()

A digital tracker that help in money savings
I'll update this README.md

📌 Phase 1 – Planning the MVP
🔹 1. Core Features for MVP
✅ Add expenses manually (amount, category, description)

✅ View expense history

✅ See weekly/monthly summaries

✅ Identify overspending habits (e.g., category trends)

🔹 2. Optional Add-ons (later)
SMS parsing (bank transaction alerts)

Receipt OCR

AI nudges or goal tracking

Budget alerts

🔹 3. Tech Stack
Layer	Tech	Notes
Backend API	FastAPI (Python)	Fast, modern, async-ready
Database	SQLite (start simple) → PostgreSQL	SQLite good for local dev
Frontend	Optional now, or simple HTML + JS / React later	Can start with Postman or Swagger
Auth	JWT (optional)	If you want multi-user login
Hosting	Local first → then Render, Railway, or Heroku	

🔹 4. Data Model Example
python
Copy
Edit
User
- id
- name
- email
- password_hash (if login enabled)

Expense
- id
- user_id
- amount
- category (e.g., Food, Travel)
- description
- timestamp
🔹 5. Basic API Endpoints
Endpoint	Method	Description
/expenses/	GET	List all expenses
/expenses/	POST	Add a new expense
/expenses/{id}	DELETE	Delete an expense
/summary/weekly	GET	Get this week's spending summary
/habits/trends	GET	Analyze patterns in spending

🏗️ Let's Start Building the APK
Here’s the plan for the next steps:

🔹 Step 1: Build the Kivy UI for adding expenses
🔹 Step 2: Save the expenses to a local SQLite database
🔹 Step 3: Show a list of recent expenses
🔹 Step 4: Generate weekly/monthly summaries
🔹 Step 5: Parse SMS for bank transaction detection

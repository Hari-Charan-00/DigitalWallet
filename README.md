# Digital Wallet - Expense Tracker

A simple Digital Wallet app focusing on expense tracking and savings. This project is designed step-by-step to build a real-world application with full stack capabilities, from UI to backend APIs and deployment.

---

## 📌 Project Overview

The goal is to create a **Digital Expense Tracker** that allows users to add, view, edit, and delete expenses, while later adding advanced features like SMS parsing, AI nudges, and budget alerts.

---

## 🚀 Current Progress: Step 1 & Step 2 Complete

### Step 1 - Kivy-based Desktop App (Local SQLite)
- Built a basic UI with Kivy for manual expense entry.
- Implemented expense storage using a local SQLite database.
- Features include adding, editing, deleting, and viewing expenses.
- Basic popup notifications for success/error messages.
- UI improvements are planned for better usability.

### Step 2 - Backend API with FastAPI
- Created a RESTful API backend with FastAPI to handle expenses.
- API supports CRUD operations on expenses.
- Used SQLite for persistent data storage.
- Server runs locally, ready for integration with frontend/mobile app.
- Tested using uvicorn with live reload support.

---

## 🔧 Tech Stack

- **Frontend:** Kivy (Python)
- **Backend:** FastAPI (Python)
- **Database:** SQLite (local for dev)
- **API Testing:** Postman / Swagger UI

---

## 📂 Project Structure

- `main.py` — Kivy UI app for Step 1
- `DigiApi.py` — FastAPI backend server for Step 2
- `expenses.db` — SQLite database file
- Other scripts/tools as required

---

## 🔜 Next Steps

- Step 3: Test backend API thoroughly using Postman and Swagger UI.
- Step 4: Integrate Kivy frontend with FastAPI backend via HTTP requests.
- Step 5: Enhance UI/UX with better navigation, scrolling, and notifications.
- Step 6: Deployment planning with Docker, Kubernetes, Terraform, CI/CD pipeline (DevOps focus).
- Step 7: Optional advanced features (SMS parsing, AI nudges, etc.)

---

## 📌 How to Run

### FastAPI Backend
```bash
pip install fastapi uvicorn
python -m uvicorn DigiApi:app --reload --port 9000
pip install kivy
python main.py

We have the source code and the REST APIs


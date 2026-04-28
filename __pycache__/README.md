### 📄 README.md for "Travel Agent" Project

Create a file called `README.md` in your `ticket-agent` folder:


# ✈️ AI Travel Agent - Smart Flight Search & Alerts

## 🎯 What is this?
An intelligent travel agent that searches **real flight routes**, finds **direct and connecting flights**, and sends deals to your email. Uses live AirLabs API data.

## ✨ Features
- 🔍 Search real flight routes (Moscow → Istanbul → Cairo)
- 🛫 Shows DIRECT flights (non-stop)
- 🔄 Shows CONNECTING flights (with layovers)
- 📅 Natural language date parsing ("19 June 2026")
- 📧 Email flight deals to yourself
- 🌍 Supports major airports worldwide
- 🚫 No API key required for basic use (mock data fallback)

## 🛠️ Technologies Used
| Technology | Purpose |
|------------|---------|
| **Python** | Core logic |
| **AirLabs API** | Real-time flight routes |
| **Regex** | Natural language parsing |
| **SMTP (Gmail)** | Email notifications |
| **Requests** | HTTP API calls |
| **python-dotenv** | Secure credential management |

## 📁 Project Structure
ticket-agent/
├── agent.py # Main agent & UI logic
├── airlabs_tools.py # API integration & flight search
├── email_sender.py # Email notifications
├── .env # API keys & credentials
└── flight_database.csv # Fallback data



## 🚀 How to Run

### Prerequisites

# Get free API key from https://airlabs.co
# (Optional) Setup Gmail App Password for email
Installation

cd ticket-agent
pip install requests python-dotenv
Configuration
Create .env file:

env
AIRLABS_API_KEY=your_api_key_here
EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
Run

python agent.py
# Choose mode: 1 (Smart) or 2 (Quick)
📸 Usage Examples
Smart Mode (Step-by-step)
text
💬 You: Moscow to Cairo
📍 Departure city: Moscow
🎯 Destination city: Cairo
📅 Travel date: 19 June 2026

🔍 Searching flights...
✈️ BEST DEAL: Aeroflot → EgyptAir via Istanbul (350 USD)
Quick Mode (One line)
text
💬 You: Moscow to Istanbul on 2026-07-15 anas@email.com
🔍 Searching... ✅ Found 16 real routes!
📧 Email sent!
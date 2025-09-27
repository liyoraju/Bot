# 📚 Library Research Assistant (AI-Powered)

An AI-powered **Library Research Assistant** that helps users find academic papers and research materials.  
It uses the **OpenAlex API** for scholarly data and **OpenRouter (LLaMA model)** for natural language understanding and summarization.  
The project runs as a **single Flask app** deployed on **Render** — serving both the **frontend UI** and the **backend API**.

---

## 🚀 Features
- 🔎 Extracts **academic keywords** from user queries.
- 📖 Searches scholarly works via the **OpenAlex API**.
- 📝 Generates structured **AI-powered summaries** of research papers.
- 🌐 Beautiful **chat-style web interface**.
- ⚡ Parallel execution for faster results.


---

## 🗂️ Project Structure
.
├── backend.py 
├── flask_api_server.py 
├── templates/
│ └── index.html 
├── requirements.txt 
└── README.md 

---

## ⚙️ Local Development Setup

### 1️⃣ Clone Repository

git clone https://github.com/liyoraju/Library_ChatBot.git

cd Library_ChatBot

### 2️⃣ Create Virtual Environment

python -m venv venv

source venv/bin/activate   # Linux/Mac

venv\Scripts\activate      # Windows

### 3️⃣ Install Dependencies

pip install -r requirements.txt

### 4️⃣ Configure API Key

Create a .env file in the project root:
env

API=your_openrouter_api_key_here

### 5️⃣ Run Locally

python flask_api_server.py

App will be available at:
👉 http://localhost:5000

### ☁️ Deploying to Render

Push this repo to GitHub.

Go to Render → New Web Service.

Connect your GitHub repo.

Configure:
Runtime: Python 3

Build Command:
pip install -r requirements.txt

Start Command:
python flask_api_server.py

Add Environment Variable in Render Dashboard:
API=your_openrouter_api_key_here

### Deploy 🚀

Render will give you a URL like:

https://your-app.onrender.com

Visit / → loads frontend UI.

Visit /api/research → handles API requests.

Visit /api/health → health check.


### 📖 Usage
Open the deployed Render URL in your browser.

Enter your research query in the input box.

System fetches relevant papers from OpenAlex.

AI summarizes findings in an academic style.

Sources, abstracts, and PDF links are displayed in chat interface.

### 📌 Future Improvements
🔐 User authentication system

📊 Visualization of research trends

🌍 Support for multi-cloud deployment

🧠 Add support for more LLMs

### 👨‍💻 Author
Liyo C Raju
🚀 Data Science Enthusiast | AI & ML Developer

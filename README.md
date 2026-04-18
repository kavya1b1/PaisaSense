# 💸 PaisaSense AI  
### AI-Powered Financial Behavior Analyzer for India’s Digital-First Generation

Upload your bank statement (CSV or PDF) and get **instant spending insights, behavioral patterns, risk alerts, and AI-generated advice** — in **Hindi, Hinglish, or English**.

---

## 🚀 Features

### 📊 Smart Financial Insights
- Category-wise breakdown (Food, Travel, Shopping, Bills, etc.)
- Budget vs Actual comparison (50/30/20 rule)
- Daily & monthly spending trends

### 🧠 Behavioral Analysis
- Weekend overspending detection  
- Micro-transaction leaks  
- Impulse spending patterns  

### ⚠️ Risk Alerts
- Burn rate warnings  
- Spending anomaly detection  

### 📺 Subscription Detection
- Finds recurring payments you may have forgotten  

### 🤖 AI-Powered Insights
- Gemini AI (primary)
- OpenRouter GPT fallback
- Rule-based fallback if APIs unavailable  

### 🎤 Voice Interaction
- Ask questions in Hindi/English  
- Get spoken AI responses  

---

## 🗂️ Project Structure

paisasense/

├── app.py
|
├── categorizer.py
├── parser.py
├── analyzer.py
├── ai_engine.py
├── requirements.txt
│
├── templates/
│   ├── index.html
│   └── dashboard.html
│
└── static/
    ├── css/
    └── js/


---

## ⚙️ Setup

```bash
git clone https://github.com/yourname/paisasense-ai.git
cd paisasense-ai

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -r requirements.txt
python app.py
```
👉 Open: http://127.0.0.1:5000

🔑 API Keys (Optional)
```
export GEMINI_API_KEY="your_key"
export OPENROUTER_API_KEY="your_key"
```
Fallback works without keys

## 📂 Supported Formats
CSV (recommended)
PDF (via pdfplumber)

## 🌐 API Endpoints
Method	Endpoint
GET	/
POST	/upload
POST	/ai-analysis
POST	/voice-query

## 🌍 Language Support
EN (English)
HI (Hindi)
HI-EN (Hinglish)

## 🔒 Privacy
No data stored
No login required
Session-based processing

## 🚀 Deployment 

pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app

## 🧰 Tech Stack

Flask • Pandas • pdfplumber • Chart.js • Gemini AI • OpenRouter • Web Speech API

📄 License

MIT License

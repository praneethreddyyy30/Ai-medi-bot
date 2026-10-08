# 🤖 Medi AI — Intelligent Health Companion

Medi AI is a smart, AI-powered medical symptom analyzer web application. It uses a trained **XGBoost machine learning classifier** to predict likely diseases based on user-inputted symptoms, and integrates the **Google Gemini API** to provide conversational health guidance, safe home remedies, and doctor consultation recommendations.

> ⚠️ **Disclaimer**: Medi AI is **not** a substitute for professional medical advice, diagnosis, or treatment. Always consult a licensed doctor for proper guidance.

---

## 🌐 Live Demo

👉 **[https://ai-medi-bot.onrender.com](https://ai-medi-bot.onrender.com)**

---

## ✨ Features

- 🩺 **Disease Prediction** — XGBoost classifier trained on 45 infectious diseases and 30 symptom features, showing top-3 disease matches with confidence progress bars.
- 💬 **Conversational AI** — Google Gemini API powers natural medical conversations, answering health-related queries in real time.
- 🌱 **Home Remedies** — After each prediction, the bot suggests safe, non-side-effect home care tips (hydration, rest, steam, ORS, etc.) and always recommends consulting a doctor.
- 🔍 **Fuzzy Symptom Matching** — Automatically corrects common typos (e.g. `headche` → `headache`, `fevr` → `fever`) using Python's `difflib`.
- 🏷️ **Symptom Tag Grid** — Click symptom tags at the top to select symptoms, which sync automatically to the chat input box.
- 🚫 **Medical-Only Filter** — The bot strictly refuses non-medical queries (e.g. general knowledge, celebrities, programming) and politely stays on-topic.
- 📱 **Fully Responsive** — Optimized for both desktop and mobile screens with a modern glassmorphic UI design.
- 🚑 **Emergency Contacts** — Emergency, Poison Control, and Mental Health helplines are always visible at the bottom.

---

## 🖼️ Screenshots

| Desktop View | Mobile View |
|---|---|
| Full-width glassmorphic layout with chat, tags, and progress bars | Stacked single-column layout with optimized tap targets |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Backend** | Python 3.12, Flask |
| **ML Model** | XGBoost Classifier (scikit-learn pipeline) |
| **AI Chat** | Google Gemini API (`gemini-3.1-flash-lite`) |
| **Frontend** | HTML5, CSS3, Vanilla JavaScript |
| **Deployment** | Render (Free Tier) |
| **Environment** | python-dotenv |

---

## 🚀 Getting Started (Run Locally)

### 1. Clone the Repository
```bash
git clone https://github.com/praneethreddyyy30/Ai-medi-bot.git
cd Ai-medi-bot
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Set Up the Gemini API Key
Create a `.env` file in the project root:
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```
> Get a free API key from [Google AI Studio](https://aistudio.google.com/)

### 4. Train the ML Model (first time only)
```bash
python train_test_final.py
```
This generates `disease_predictor.pkl` and `features.json`.

### 5. Run the App
```bash
python app.py
```
Visit **[http://127.0.0.1:5000](http://127.0.0.1:5000)** in your browser.

---

## 📁 Project Structure

```
Ai-medi-bot/
├── app.py                  # Flask backend — routes, prediction engine, Gemini integration
├── train_test_final.py     # XGBoost model training script
├── index.html              # Frontend HTML template
├── style.css               # Glassmorphic responsive CSS design
├── script.js               # Frontend JavaScript — chat, symptom tags, progress bars
├── features.json           # List of 30 canonical symptom features
├── disease_predictor.pkl   # Pre-trained XGBoost ML model
├── realistic_infectious_disease_dataset_45.csv  # Training dataset (45 diseases)
├── accuracy_plot.png       # Model accuracy visualization
├── requirements.txt        # Python dependencies
├── .gitignore              # Excludes .env and cache files
└── README.md               # This file
```

---

## 🧠 How It Works

```
User types symptoms (or clicks tags)
            ↓
detect_symptoms() → fuzzy matches via difflib
            ↓
predict_diseases() → XGBoost model returns top 3 predictions with confidence %
            ↓
gemini_reply() → Gemini API generates home remedies & consult-doctor tip
            ↓
Frontend renders: chat message + progress bars + active symptom pills
```

### Routing Logic:
- **Greetings** (`hii`, `hello`, `heyy`, etc.) → Friendly greeting response
- **Goodbye** (`bye`, `take care`, etc.) → Farewell message
- **Symptoms detected in message** → Classifier prediction + Gemini advice
- **Medical questions** → Gemini answers conversationally
- **Non-medical queries** → Politely refused by the medical-only filter

---

## 🌿 Supported Diseases (45 total)

Includes: Common Cold, Influenza, COVID-19, Dengue, Malaria, Typhoid Fever, Cholera, Chickenpox, Measles, Rubella, Tetanus, Tuberculosis, Chikungunya, Hepatitis A/B, Rabies, Plague, Ebola, SARS, Zika, and more.

---

## 🔑 Environment Variables

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Your Google AI Studio API key for conversational AI features |

> If the key is not set or rate-limited, the app gracefully falls back to local offline remedies and template replies.

---

## 📦 Deployment on Render

1. Push the project to GitHub.
2. Create a new **Web Service** on [Render.com](https://render.com).
3. Set **Build Command**: `pip install -r requirements.txt`
4. Set **Start Command**: `gunicorn app:app`
5. Add Environment Variable: `GEMINI_API_KEY = your_key_here`
6. Deploy! 🚀

---

## 👨‍💻 Author

**Praneeth Reddy**
- GitHub: [@praneethreddyyy30](https://github.com/praneethreddyyy30)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

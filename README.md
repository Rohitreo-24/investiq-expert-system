# InvestIQ — AI Powered Investment Decision System

InvestIQ is a **Frame-Based + First Order Logic (FOL) Expert System** that recommends investment instruments based on user profile and explains them using AI.

It combines:

* Frame based profiling
* FOL forward chaining rule engine
* AI explanation for each instrument
* Flask backend + modern UI

---

## 🚀 Features

* Age, income, risk, duration, goal based reasoning
* 30+ FOL rules with AND/OR logic
* Instrument filtering engine
* AI explanation for each investment instrument
* Streaming AI portfolio explanation
* Clean UI for demo/presentation

---

## 🛠 Tech Stack

* Python Flask
* Groq AI API
* HTML/CSS/JS
* FOL Rule Engine

---

## ⚙️ Setup Instructions (Local Run)

### 1. Clone repository

```bash
git clone https://github.com/YOUR_USERNAME/investiq.git
cd investiq
```

---

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Set Environment Variable (IMPORTANT)

This project uses **Groq API**.

You must set your own key.

#### ▶ Windows (PowerShell)

```powershell
setx GROQ_API_KEY "your_key_here"
```

Restart terminal after running this.

---

#### ▶ Mac/Linux

```bash
export GROQ_API_KEY="your_key_here"
```

---

### 4. Run the app

```bash
python app.py
```

Open browser:

```
http://127.0.0.1:5000
```

---

## 🧠 How It Works

1. User enters profile
2. Frame is created
3. FOL rules fire
4. Instruments removed step-by-step
5. Final array shown
6. Clicking instrument → AI explanation

---

## 🔐 API Key Safety

This repo does **NOT** store any API key.

Each user must set their own:

```
GROQ_API_KEY
```

## 🌐 Deployment

To deploy on Render:

1. Add environment variable:

```
GROQ_API_KEY = your_key
```

2. Start command:

```
python app.py
```

---

## 📁 Project Structure

```
investiq/
│
├── app.py
├── requirements.txt
├── README.md
└── templates/
    └── index.html
```

---

## 🎓 Project Type

AI Expert System using:

* Frames
* FOL rules
* Forward chaining
* AI reasoning

Built for academic purposes.

---

## 👨‍💻 Author

Dhatchana Moorthy R
AI + Expert Systems Project

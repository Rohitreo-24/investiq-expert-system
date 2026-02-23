import json
import os
import logging
from flask import Flask, render_template, request, jsonify, Response, stream_with_context
from groq import Groq
from dotenv import load_dotenv

TEST_MODE = False
load_dotenv()

app = Flask(__name__)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)

# ───────── FRAME ─────────
class UserFrame:
    def __init__(self, age, income, risk, duration, goal):
        self.age = int(age)
        self.income = income
        self.risk = risk
        self.duration = duration
        self.goal = goal

    def to_dict(self):
        return vars(self)

# ───────── RULE ─────────
class Rule:
    def __init__(self, rule_id, conditions, remove_list, fol, explanation, icon, priority=1):
        self.rule_id = rule_id
        self.conditions = conditions
        self.remove_list = remove_list
        self.fol = fol
        self.explanation = explanation
        self.icon = icon
        self.priority = priority

    def evaluate(self, frame):
        f = frame.to_dict()
        for attr, op, val in self.conditions:
            fv = f.get(attr)
            if op == "==" and fv != val: return False
            if op == ">" and not fv > val: return False
            if op == "<" and not fv < val: return False
            if op == ">=" and not fv >= val: return False
            if op == "<=" and not fv <= val: return False
        return True

# ───────── INSTRUMENT UNIVERSE ─────────
INSTRUMENTS = [
"Equity Stocks","Index Funds","Equity Mutual Funds","Debt Mutual Funds",
"Hybrid Mutual Funds","Government Bonds","FD","PPF",
"Gold ETF",
"Real Estate","Cryptocurrency","Liquid Funds","Arbitrage Funds","Venture Capital"
]

# ───────── RULE BASE ─────────
def build_rules():
    return [

# =========================
# DURATION RULES
# =========================

Rule("D1",[("duration","==","short")],
["Real Estate","PPF","Venture Capital","Cryptocurrency","Equity Stocks"],
"Duration(x,short) → remove(x,Illiquid)",
"Short duration cannot hold long lock-in assets",
"⏳",5),

Rule("D2",[("duration","==","medium")],
["Venture Capital","Real Estate"],
"Duration(x,medium) → remove(x,VC)",
"VC unsuitable for medium term",
"📆",5),

Rule("D3",[("duration","==","long"),("risk","==","low")],
["Cryptocurrency","Venture Capital"],
"Duration(x,long) ∧ Risk(x,low) → remove(x,Speculative)",
"Long-term low risk avoids speculation",
"🛡️",5),

# =========================
# RISK RULES
# =========================

Rule("R1",[("risk","==","low"),("duration","!=","long")],
["Equity Stocks","Cryptocurrency","Venture Capital"],
"Risk(x,low) ∧ Duration(x,long)  → remove(x,HighVolatile)",
"Low risk avoids volatile assets",
"🛑",4),

Rule("R2",[("risk","==","medium")],
["Cryptocurrency","Venture Capital"],
"Risk(x,medium) → remove(x,ExtremeRisk)",
"Medium risk avoids extreme assets",
"⚖️",4),

Rule("R3",[("risk","==","high"),("duration","==","short")],
["PPF","Government Bonds","FD"],
"Risk(x,high) ∧ Duration(x,short) → remove(x,Conservative)",
"High risk short term avoids conservative",
"🔥",4),

# =========================
# AGE RULES
# =========================

Rule("A1",[("age",">",55)],
["Cryptocurrency","Venture Capital"],
"Age(x)>55 → remove(x,Speculative)",
"Senior investors avoid speculation",
"👴",3),

Rule("A2",[("age",">",60)],
["Equity Stocks"],
"Age(x)>60 → remove(x,HighVolatility)",
"Reduce equity volatility after 60",
"🏦",3),

Rule("A3",[("age","<",25),("risk","==","high")],
["FD","Government Bonds"],
"Age(x)<25 ∧ Risk(x,high)",
"Young high-risk avoids conservative",
"🚀",3),

Rule("A4",[("age","<",25),("risk","==","low")],
["Cryptocurrency","Venture Capital"],
"Age(x)<25 ∧ Risk(x,low)",
"Young low risk avoids speculation",
"📚",3),

# =========================
# GOAL SHORT TERM
# =========================

Rule("G1",[("goal","==","short_term")],
["Real Estate","PPF","Venture Capital","FD"],
"Goal(x,short_term) → remove(x,Lockin)",
"Short term needs liquidity",
"🎯",5),

Rule("G2",[("goal","==","short_term"),("risk","==","high")],
["PPF","Government Bonds"],
"Goal(x,short_term) ∧ Risk(x,high)",
"High risk short term avoids locked safe assets",
"⚡",5),

# =========================
# GOAL WEALTH
# =========================

Rule("G3",[("goal","==","wealth"),("risk","==","low")],
["Cryptocurrency","Venture Capital"],
"Goal(x,wealth) ∧ Risk(x,low)",
"Low risk wealth avoids speculation",
"💰",5),

Rule("G4",[("goal","==","wealth"),("duration","==","short")],
["PPF","Real Estate"],
"Goal(x,wealth) ∧ Duration(x,short)",
"Short wealth avoids lock-in",
"📉",5),

Rule("G5",[("goal","==","wealth"),("duration","==","medium"),("risk","==","high")],
["FD","Government Bonds"],
"Goal(x,wealth) ∧ Duration(x,medium) ∧ Risk(x,high)",
"Growth investor avoids conservative",
"📈",5),

Rule("G6",[("goal","==","wealth"),("duration","==","long")],
["Cryptocurrency","Venture Capital"],
"Goal(x,wealth) ∧ Duration(x,long) ∧ Risk(x,low)",
"Low risk long avoids speculation",
"🧱",5),

Rule("G10",[("goal","==","wealth")],
["Cryptocurrency","Arbitrage Funds"],
"Goal(x,wealth)",
"Goal : wealth avoids speculation",
"💰",5),

# =========================
# GOAL RETIRE
# =========================

Rule("G7",[("goal","==","retire"),("age","<",35)],
["Cryptocurrency","Venture Capital"],
"Goal(x,retire) ∧ Age(x)<35",
"Early retirement avoid extreme speculation",
"🏁",5),

Rule("G8",[("goal","==","retire"),("age",">",50)],
["Cryptocurrency","Venture Capital"],
"Goal(x,retire) ∧ Age(x)>50",
"Senior retirement avoids risk",
"🏦",5),

Rule("G9",[("goal","==","retire"),("duration","==","long"),("risk","==","low")],
["Equity Stocks","Cryptocurrency","Venture Capital"],
"Goal(x,retire) ∧ Duration(x,long) ∧ Risk(x,low)",
"Retirement low risk removes equity",
"📊",5),

# =========================
# INCOME RULES
# =========================

Rule("I1",[("income","==","low")],
["Real Estate","Venture Capital"],
"Income(x,low)",
"Low income avoids heavy capital",
"💼",2),

Rule("I2",[("income","==","low"),("risk","==","high")],
["Real Estate","Venture Capital"],
"Income(x,low) ∧ Risk(x,high)",
"Low income cannot take VC",
"📉",2),

Rule("I3",[("income","==","medium"),("risk","==","low")],
["Cryptocurrency","Venture Capital"],
"Income(x,medium) ∧ Risk(x,low)",
"Moderate investors avoid speculation",
"⚖️",2),

Rule("I4",[("income","==","high"),("duration","==","short")],
["PPF","Real Estate"],
"Income(x,high) ∧ Duration(x,short)",
"High income short avoids lock",
"🏢",2),

# =========================
# OR RULES (explicit)
# =========================

Rule("OR1",[("risk","==","low")],
["Cryptocurrency"],
"Risk(x,low) OR Age(x)>60",
"Low risk avoids crypto",
"🛑",3),

Rule("OR2",[("age",">",50)],
["Cryptocurrency"],
"Risk(x,low) OR Age(x)>50",
"Senior avoids crypto",
"👴",3),

Rule("OR3",[("goal","==","short_term")],
["Real Estate"],
"Goal(short) OR Duration(short)",
"Short term avoids real estate",
"🏠",5),

Rule("OR4",[("duration","==","short")],
["Real Estate"],
"Goal(short) OR Duration(short)",
"Short duration avoids real estate",
"🏠",5),

]

# ───────── ENGINE ─────────
class Engine:
    def __init__(self, rules):
        self.rules = rules

    def run(self, frame):

        remaining = set(INSTRUMENTS)
        fired_rules = []

        for rule in sorted(self.rules, key=lambda r: r.priority, reverse=True):
            if rule.evaluate(frame):
                fired_rules.append(rule)

                for inst in rule.remove_list:
                    remaining.discard(inst)

        final_list = sorted(list(remaining))
        return fired_rules, final_list

# ───────── AI FOR INSTRUMENT CLICK ─────────

@app.route("/explain_instrument", methods=["POST"])
def explain_instrument():
    try:
        data = request.json
        instrument = data.get("instrument")
        frame = data.get("frame")

        if not instrument:
            return jsonify({"error": "Missing instrument"}), 400

        # ✅ TEST MODE (no API call)
        if TEST_MODE:
            return jsonify({
                "instrument": instrument,
                "explanation": f"""
1. What is {instrument}?
{instrument} is a financial instrument used for portfolio diversification.

2. Risk Level:
Based on your profile, this instrument fits your risk appetite.

3. Returns:
Returns vary depending on market conditions.

4. Why Recommended:
It survived rule-based elimination and aligns with your investment goal.
""",
                "status": "success"
            })

        # ✅ REAL AI MODE
        prompt = f"""
Explain the investment instrument "{instrument}" for this user profile:

{frame}

Keep it clear and structured.
"""

        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        explanation = res.choices[0].message.content

        return jsonify({
            "instrument": instrument,
            "explanation": explanation,
            "status": "success"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# ───────── AI STREAM (PORTFOLIO) ─────────
def ask_ai(frame, recs, fired):

    if TEST_MODE:
        yield "TEST MODE\nFinal Instruments:\n"
        for r in recs:
            yield f"{r}\n"
        return

    prompt = f"profile {frame} instruments {recs}"

    res = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role":"user","content":prompt}],
        stream=True
    )

    for chunk in res:
        if chunk.choices[0].delta.content:
            yield chunk.choices[0].delta.content

# ───────── ROUTES ─────────
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/analyze",methods=["POST"])
def analyze():

    data=request.json

    frame=UserFrame(
        data["age"],
        data["income"],
        data["risk"],
        data["duration"],
        data["goal"]
    )

    fired,recs=Engine(build_rules()).run(frame)

    return jsonify({
        "frame": frame.to_dict(),
        "recommendations": recs,
        "fired_rules": [
            {
                "rule_id": r.rule_id,
                "fol": r.fol,
                "explanation": r.explanation,
                "icon": r.icon,
                "recommendation": ", ".join(r.remove_list)
            } for r in fired
        ]
    })

# ───────── INSTRUMENT CLICK ROUTE ─────────
@app.route("/instrument_info", methods=["POST"])
def instrument_info():

    data = request.json
    instrument = data["instrument"]
    frame = data["frame"]

    explanation = explain_instrument_ai(instrument, frame)

    return jsonify({
        "instrument": instrument,
        "explanation": explanation
    })

# ───────── STREAM ROUTE ─────────
@app.route("/stream_allocation", methods=["POST"])
def stream_allocation():
    data = request.json

    def generate():
        for text in ask_ai(data["frame"], data["recommendations"], data["fired_rules"]):
            yield f"data: {json.dumps({'text': text})}\n\n"
        yield "data: [DONE]\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

@app.route("/ai_explain", methods=["POST"])
def ai_explain():
    data = request.json
    full=""
    for t in ask_ai(data["frame"], data["recommendations"], data["fired_rules"]):
        full+=t
    return jsonify({"explanation":full})

# ───────── RUN ─────────
if __name__=="__main__":
    app.run(debug=True)
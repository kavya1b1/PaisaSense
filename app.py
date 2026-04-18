"""
PaisaSense AI — Flask Application
Analyzes CSV + PDF transaction data and provides behavioral + AI-powered financial insights.
"""

from flask import Flask, request, jsonify, render_template
from parser import parse_file
from analyzer import process_dataframe, process_transactions
from ai_engine import (
    get_ai_response,
    build_analysis_prompt,
    build_voice_prompt,
    fallback_analysis,
    fallback_voice,
)

app = Flask(__name__)


# ── Demo Data ──────────────────────────────────────────────────────────────────

DEMO_CSV = """Date,Amount,Merchant
2024-01-01,450,Swiggy
2024-01-02,1200,Amazon
2024-01-03,350,Uber
2024-01-04,850,Zomato
2024-01-05,12000,Rent
2024-01-06,320,Swiggy
2024-01-07,180,Auto Rickshaw
2024-01-08,2400,Flipkart
2024-01-09,600,Ola
2024-01-10,750,Zomato
2024-01-11,150,Tea Stall
2024-01-12,950,Swiggy
2024-01-13,3200,Amazon
2024-01-14,450,Uber
2024-01-15,1800,Electricity Bill
2024-01-16,280,Swiggy
2024-01-17,5500,Flipkart
2024-01-18,420,Ola
2024-01-19,900,Zomato
2024-01-20,120,Chai Point
2024-01-21,2100,Amazon
2024-01-22,650,Swiggy
2024-01-23,380,Uber
2024-01-24,4800,Rent
2024-01-25,190,Auto Rickshaw
2024-01-26,730,Zomato
2024-01-27,1400,Flipkart
2024-01-28,560,Swiggy
2024-01-29,310,Ola
2024-01-30,2200,Amazon
"""


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")


@app.route("/upload", methods=["POST"])
def upload():
    """Handle CSV/PDF upload or demo data request."""
    try:
        if request.form.get("use_demo"):
            result = process_transactions(DEMO_CSV)
        elif "file" in request.files:
            f = request.files["file"]
            if not f.filename:
                return jsonify({"error": "No file selected"}), 400
            df = parse_file(f)
            result = process_dataframe(df)
        else:
            return jsonify({"error": "No file or demo flag provided"}), 400

        return jsonify(result)

    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Processing error: {str(e)}"}), 500


@app.route("/ai-analysis", methods=["POST"])
def ai_analysis():
    """Generate AI explanation from processed insights."""
    try:
        body = request.get_json()
        if not body:
            return jsonify({"error": "No insights data provided"}), 400

        insights   = body.get("insights", body)
        language   = body.get("language", "en")
        prompt     = build_analysis_prompt(insights, language)
        text, source = get_ai_response(prompt)

        if not text:
            text   = fallback_analysis(insights, language)
            source = "fallback"

        return jsonify({"analysis": text, "ai_source": source})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/voice-query", methods=["POST"])
def voice_query():
    """Answer a specific voice question using the user's actual spending data."""
    try:
        body       = request.get_json()
        user_query = body.get("query", "").strip()
        language   = body.get("language", "en")
        context    = body.get("context", {})

        if not user_query:
            return jsonify({"error": "No query provided"}), 400

        prompt       = build_voice_prompt(user_query, context, language)
        answer, source = get_ai_response(prompt)

        if not answer:
            answer = fallback_voice(language)

        return jsonify({"answer": answer, "ai_source": source})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/demo-csv")
def demo_csv():
    return DEMO_CSV, 200, {
        "Content-Type": "text/csv",
        "Content-Disposition": "attachment; filename=demo_transactions.csv",
    }


if __name__ == "__main__":
    app.run(debug=True, port=5000)

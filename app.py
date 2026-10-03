from flask import Flask, jsonify, render_template
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

BOC_RATES_URL = "https://www.bankofcanada.ca/valet/observations/V39078,V39079/json"

# Fixed Bank of Canada 2026 Scheduled Announcement Dates
BOC_2026_SCHEDULE = [
    "2026-01-28", "2026-03-18", "2026-04-29", "2026-06-10",
    "2026-07-15", "2026-09-02", "2026-10-28", "2026-12-09"
]

def get_upcoming_release(latest_date_str):
    try:
        latest_dt = datetime.strptime(latest_date_str, "%Y-%m-%d")
        for date_str in BOC_2026_SCHEDULE:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            if dt > latest_dt:
                return dt.strftime("%B %d, %Y")
    except Exception:
        pass
    return "October 28, 2026" # Fallback default

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/interest-rates", methods=["GET"])
def get_interest_rates():
    try:
        response = requests.get(BOC_RATES_URL, timeout=10)
        response.raise_for_status()
        data = response.json()

        series_details = data.get("seriesDetails", {})
        observations = data.get("observations", [])

        if not observations:
            return jsonify({"success": False, "error": "Empty observations payload from Bank of Canada API."}), 500

        formatted_obs = []
        latest_bank_rate = None
        latest_overnight_rate = None
        latest_date = None

        for obs in observations:
            date_val = obs.get("d")
            bank_rate_obj = obs.get("V39078", {})
            overnight_obj = obs.get("V39079", {})

            bank_rate = None
            overnight_rate = None

            if isinstance(bank_rate_obj, dict) and "v" in bank_rate_obj:
                try:
                    bank_rate = float(bank_rate_obj["v"])
                except (ValueError, TypeError):
                    pass

            if isinstance(overnight_obj, dict) and "v" in overnight_obj:
                try:
                    overnight_rate = float(overnight_obj["v"])
                except (ValueError, TypeError):
                    pass

            if overnight_rate is not None:
                latest_overnight_rate = overnight_rate
                latest_bank_rate = bank_rate
                latest_date = date_val

            formatted_obs.append({
                "date": date_val,
                "bank_rate": bank_rate,
                "overnight_rate": overnight_rate,
                "is_forecast": False
            })

        upcoming_release = get_upcoming_release(latest_date) if latest_date else "October 28, 2026"

        forecast_obs = []
        if latest_overnight_rate is not None and latest_bank_rate is not None:
            forecast_obs = [
                {"date": "2026-11-01", "bank_rate": latest_bank_rate, "overnight_rate": latest_overnight_rate, "is_forecast": True},
                {"date": "2026-12-01", "bank_rate": latest_bank_rate, "overnight_rate": latest_overnight_rate, "is_forecast": True},
                {"date": "2027-01-01", "bank_rate": latest_bank_rate, "overnight_rate": latest_overnight_rate, "is_forecast": True}
            ]

        return jsonify({
            "success": True,
            "metadata": {
                "latest_bank_rate": latest_bank_rate,
                "latest_overnight_rate": latest_overnight_rate,
                "latest_date": latest_date,
                "upcoming_release": upcoming_release
            },
            "data": formatted_obs,
            "forecast": forecast_obs
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch interest rates: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=9045)
from flask import Flask, jsonify, render_template
import requests

app = Flask(__name__)

# Bank of Canada Valet API endpoint for Bank Rate (V39078) and Target for the Overnight Rate (V39079)
BOC_RATES_URL = "https://www.bankofcanada.ca/valet/observations/V39078,V39079/json"

@app.route("/")
def index():
    """Renders the frontend dashboard."""
    return render_template("index.html")

@app.route("/api/interest-rates", methods=["GET"])
def get_interest_rates():
    """Fetches historical Bank Rate and Target for the Overnight Rate data along with forecasts."""
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

        # Append analytical forecast points for upcoming scheduled meetings (simulated hold/trend projection)
        forecast_obs = []
        if latest_overnight_rate is not None and latest_bank_rate is not None:
            forecast_obs = [
                {
                    "date": "2026-11-01", 
                    "bank_rate": latest_bank_rate, 
                    "overnight_rate": latest_overnight_rate, 
                    "is_forecast": True
                },
                {
                    "date": "2026-12-01", 
                    "bank_rate": latest_bank_rate, 
                    "overnight_rate": latest_overnight_rate, 
                    "is_forecast": True
                },
                {
                    "date": "2027-01-01", 
                    "bank_rate": latest_bank_rate, 
                    "overnight_rate": latest_overnight_rate, 
                    "is_forecast": True
                }
            ]

        return jsonify({
            "success": True,
            "metadata": {
                "bank_rate_label": series_details.get("V39078", {}).get("label", "Bank Rate"),
                "overnight_rate_label": series_details.get("V39079", {}).get("label", "Target for the Overnight Rate"),
                "latest_bank_rate": latest_bank_rate,
                "latest_overnight_rate": latest_overnight_rate,
                "latest_date": latest_date
            },
            "data": formatted_obs,
            "forecast": forecast_obs
        })

    except requests.exceptions.RequestException as e:
        return jsonify({"success": False, "error": f"Failed to fetch interest rates: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=9045)
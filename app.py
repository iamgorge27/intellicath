import ssl
import math
import pickle
import pymysql
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from datetime import datetime

app = Flask(__name__)
CORS(app)  

model = pickle.load(open("models/model_1.pkl", "rb"))
poly = pickle.load(open("models/polynomial_features.pkl", "rb"))
scaler = pickle.load(open("models/scaler.pkl", "rb"))

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "",
    "database": "intellicath",
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db_connection():
    """Establish a MySQL database connection."""
    try:
        return pymysql.connect(**DB_CONFIG)
    except pymysql.MySQLError as e:
        print(f"[ERROR] Database Connection Failed: {e}")
        return None

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/predict-post", methods=["POST"])
def predict():
    """Receives data from ESP32, processes it, and stores predictions in MySQL."""
    data = request.get_json()

    if not data:
        return jsonify({"error": "No data received"}), 400

    try:
        urine_output = data.get("urine_output")
        urine_flow_rate = data.get("urine_flow_rate")
        catheter_bag_volume = data.get("catheter_bag_volume")
        remaining_volume = data.get("remaining_volume")

        if None in [urine_output, urine_flow_rate, catheter_bag_volume, remaining_volume]:
            return jsonify({"error": "Incomplete data provided"}), 400

        features = np.array([[urine_output, urine_flow_rate, catheter_bag_volume, remaining_volume]])
        features_scaled = scaler.transform(poly.transform(features))

        if catheter_bag_volume == 0 and urine_output == 0:
            predicted_time = "N/A"
        else:
            predicted_time_minutes = model.predict(features_scaled)[0]
            hours = math.floor(predicted_time_minutes)
            minutes = round((predicted_time_minutes - hours) * 60)
            predicted_time = f"{int(hours):02} hours and {int(minutes):02} minutes"

        actual_time = None
        if catheter_bag_volume >= 800:
            actual_time = datetime.now().strftime("%H:%M %p") 

        save_data_to_db({
            "urine_output": urine_output,
            "urine_flow_rate": urine_flow_rate,
            "catheter_bag_volume": catheter_bag_volume,
            "remaining_volume": remaining_volume,
            "predicted_time": predicted_time,
            "actual_time": actual_time  
        })

        return jsonify({"status": "success", "message": "Data processed successfully"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

def save_data_to_db(data):
    """Saves processed data to MySQL only if there is a significant change."""
    try:
        connection = get_db_connection()
        if connection is None:
            return

        with connection.cursor() as cursor:
            last_query = "SELECT * FROM intellicath_data ORDER BY id DESC LIMIT 1"
            cursor.execute(last_query)
            last_entry = cursor.fetchone()

            if last_entry:
                if abs(last_entry["urine_output"] - data["urine_output"]) <= 2 and \
                   abs(last_entry["urine_flow_rate"] - data["urine_flow_rate"]) <= 0.1 and \
                   abs(last_entry["catheter_bag_volume"] - data["catheter_bag_volume"]) <= 2:
                    print("[INFO] No significant change in data. Skipping insert.")
                    return  

            sql = """
            INSERT INTO intellicath_data (urine_output, urine_flow_rate, catheter_bag_volume, remaining_volume, predicted_time, actual_time)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data["urine_output"], 
                data["urine_flow_rate"], 
                data["catheter_bag_volume"], 
                data["remaining_volume"], 
                data["predicted_time"],
                data["actual_time"] 
            ))
            connection.commit()
            print("[✅] Data inserted into database successfully.")

        connection.close()

    except pymysql.MySQLError as e:
        print(f"[ERROR] MySQL Insert Failed: {e}")

if __name__ == "__main__":
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain(certfile="localhost.pem", keyfile="localhost-key.pem")
    app.run(debug=True, host="0.0.0.0", port=5001, ssl_context=context)

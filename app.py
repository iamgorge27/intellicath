
from flask import Flask, request, jsonify
import pickle

app = Flask(__name__)

# Load your trained model and preprocessors
model = pickle.load(open('models/model_1.pkl', 'rb'))
poly = pickle.load(open('models/polynomial_features.pkl', 'rb'))
scaler = pickle.load(open('models/scaler.pkl', 'rb'))

@app.route("/predict", methods=["POST"])
def predict():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data received"}), 400
    try:
        # Extract features from incoming data
        urine_output = data.get("urine_output")
        urine_flow_rate = data.get("urine_flow_rate")
        catheter_bag_volume = data.get("catheter_bag_volume")
        remaining_volume = data.get("remaining_volume")

        if None in [urine_output, urine_flow_rate, catheter_bag_volume, remaining_volume]:
            return jsonify({"error": "Incomplete data provided"}), 400

        # Prepare features for prediction
        features = [
            urine_output,
            urine_flow_rate,
            catheter_bag_volume,
            remaining_volume
        ]

        # Transform and scale features
        features_scaled = scaler.transform(poly.transform([features]))
        predicted_time = model.predict(features_scaled)[0]

        # Build response
        response = {
            "urine_output": urine_output,
            "urine_flow_rate": urine_flow_rate,
            "catheter_bag_volume": catheter_bag_volume,
            "remaining_volume": remaining_volume,
            "predicted_time": round(predicted_time, 2)
        }

        return jsonify(response)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
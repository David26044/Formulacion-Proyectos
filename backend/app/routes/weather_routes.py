# app/routes/weather_routes.py
from flask import Blueprint, jsonify
import requests
from datetime import datetime
from app.models import RainForecast, db
from flask_jwt_extended import jwt_required
import os

weather_bp = Blueprint('weather', __name__)

@weather_bp.route('/weather/update', methods=['POST'])
@jwt_required()
def update_weather():
    api_key = os.getenv('OPENWEATHER_API_KEY')
    lat = 4.72
    lon = -73.97
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units=metric"

    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        # 🧹 Eliminar pronósticos anteriores
        db.session.query(RainForecast).delete()
        db.session.commit()

        forecasts = data.get('list', [])
        for f in forecasts:
            dt_txt = f['dt_txt']
            forecast_time = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S")

            rain_mm = f.get('rain', {}).get('3h', 0)
            # Definir nivel de riesgo según tu criterio
            if rain_mm >= 5:
                risk_level = 1  # Amarillo
            elif rain_mm >= 10:
                risk_level = 2  # Rojo
            else:
                risk_level = 0  # Verde

            forecast = RainForecast(
                forecast_time=forecast_time,
                rain_mm=rain_mm,
                risk_level=risk_level
            )
            db.session.add(forecast)

        db.session.commit()

        return jsonify({
            "message": f"Se guardaron {len(forecasts)} pronósticos correctamente."
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500
    
@weather_bp.route('/weather/forecasts', methods=['GET'])
@jwt_required()
def get_forecasts():
    forecasts = RainForecast.query.order_by(RainForecast.forecast_time).all()
    result = [
        {
            "forecast_time": f.forecast_time.isoformat(),
            "rain_mm": f.rain_mm,
            "risk_level": f.risk_level
        } for f in forecasts
    ]
    return jsonify(result), 200


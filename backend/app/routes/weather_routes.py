# app/routes/weather_routes.py
from flask import Blueprint, jsonify
import requests
from datetime import datetime
from app.models import RainForecast, db
from flask_jwt_extended import jwt_required
import os
from app.models import RainForecast, db, AlertConfig
from app.mail_utils import send_email_alert


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

            rain_mm = f.get('rain', {}).get('3h', 0.0)

            # OJO: esta lógica ya no se usa para el riesgo,
            # solo para mostrar algo en /forecasts si lo necesitaras
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

        # === Cálculo rápido de riesgo global para ALERTAS ===
        all_forecasts = RainForecast.query.order_by(RainForecast.forecast_time).all()
        if not all_forecasts:
            return jsonify({
                "message": "Se guardaron 0 pronósticos, no hay datos para calcular riesgo."
            }), 200

        # Construir serie simple
        series = [
            {
                "time": f.forecast_time,
                "rain_mm": f.rain_mm
            }
            for f in all_forecasts
        ]

        # 1) Intensidad actual (I_now) = primer bloque 3h / 3
        first = series[0]
        rain_3h = first["rain_mm"]
        intensidad_mm_h = rain_3h / 3.0

        if intensidad_mm_h == 0:
            peso_I = 0
        elif intensidad_mm_h < 3:
            peso_I = 1
        elif intensidad_mm_h < 10:
            peso_I = 2
        elif intensidad_mm_h < 20:
            peso_I = 3
        else:
            peso_I = 4

        # 2) P_24h = suma próximas 24h (8 bloques de 3h)
        P_24h = 0.0
        for item in series[:8]:
            P_24h += item["rain_mm"]

        if P_24h < 30:
            peso_P24 = 0
        elif P_24h < 70:
            peso_P24 = 1
        elif P_24h < 120:
            peso_P24 = 2
        else:
            peso_P24 = 3

        # 3) P_48h = suma próximas 48h (16 bloques de 3h)
        P_48h = 0.0
        for item in series[:16]:
            P_48h += item["rain_mm"]

        if P_48h < 60:
            peso_P48 = 0
        elif P_48h < 120:
            peso_P48 = 1
        else:
            peso_P48 = 2

        # 4) Score y nivel de riesgo (MISMA lógica que en /summary)
        score = peso_I + peso_P24 + peso_P48

        if score <= 2:
            risk_level_label = "BAJO"
            risk_color = "green"
            risk_message = "Flujo estable, el disipador opera en condiciones normales."
        elif score <= 4:
            risk_level_label = "MODERADO"
            risk_color = "yellow"
            risk_message = "El disipador disipa más energía, pero el riesgo es controlado."
        elif score <= 6:
            risk_level_label = "ALTO"
            risk_color = "orange"
            risk_message = "El disipador está cerca de su capacidad de diseño; aumenta el riesgo de erosión."
        else:
            risk_level_label = "MUY ALTO"
            risk_color = "red"
            risk_message = "Condiciones extremas: el flujo podría superar la capacidad del disipador y comprometer el talud."

        # === ALERTAS POR CORREO SEGÚN NIVEL DE RIESGO ===

        # Solo mandamos correos si el nivel es ALTO o MUY ALTO
        if risk_level_label in ("ALTO", "MUY ALTO"):
            # Buscar configuraciones de usuario que quieran recibir ese nivel
            configs_query = AlertConfig.query

            if risk_level_label == "ALTO":
                configs_query = configs_query.filter_by(notify_on_high=True)
            elif risk_level_label == "MUY ALTO":
                configs_query = configs_query.filter_by(notify_on_very_high=True)

            alert_configs = configs_query.all()

            subject = f"Alerta de riesgo hidráulico: {risk_level_label}"
            body = (
                f"Nivel de riesgo actual: {risk_level_label}\n"
                f"Mensaje: {risk_message}\n\n"
                f"Datos de lluvia estimados:\n"
                f"- Intensidad actual: {intensidad_mm_h:.2f} mm/h\n"
                f"- Lluvia acumulada 24h: {P_24h:.1f} mm\n"
                f"- Lluvia acumulada 48h: {P_48h:.1f} mm\n\n"
                "Este mensaje ha sido generado automáticamente por el sistema de "
                "monitoreo del disipador hidráulico en La Calera."
            )

            for config in alert_configs:
                send_email_alert(config.email, subject, body)

        return jsonify({
            "message": f"Se guardaron {len(forecasts)} pronósticos correctamente.",
            "risk": {
                "level": risk_level_label,
                "color": risk_color,
                "score": score,
                "message": risk_message,
                "debug": {
                    "I_now_mm_h": round(intensidad_mm_h, 2),
                    "P_24h_mm": round(P_24h, 1),
                    "P_48h_mm": round(P_48h, 1),
                    "peso_I": peso_I,
                    "peso_P24": peso_P24,
                    "peso_P48": peso_P48
                }
            }
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

@weather_bp.route('/weather/summary', methods=['GET'])
def weather_summary():
    """
    Resume el estado hidrológico para la maqueta:
    - Lluvia actual (intensidad mm/h + etiqueta)
    - Riesgo hidráulico actual (BAJO/MODERADO/ALTO/MUY ALTO)
    usando:
      * Intensidad actual (I_now)
      * Lluvia acumulada 24h (P_24h)
      * Lluvia acumulada 48h (P_48h)
    """

    # 1. Obtener registros desde la BD
    forecasts = RainForecast.query.order_by(RainForecast.forecast_time).all()

    # 2. Validar que existan datos
    if not forecasts:
        return jsonify({"error": "No hay pronósticos guardados. Ejecuta /weather/update primero."}), 400

    # 3. Preparar lista simple con lluvia y fecha
    series = [
        {
            "time": f.forecast_time,
            "rain_mm": f.rain_mm
        }
        for f in forecasts
    ]

    # === A) LLUVIA ACTUAL (current_rain) ===

    # Primer pronóstico (próximas 3h)
    first = series[0]
    rain_3h = first["rain_mm"]

    # Convertir a intensidad (mm/h)
    intensidad_mm_h = rain_3h / 3.0

    # Clasificar intensidad y peso para el riesgo
    # Modelo ajustado por disipador:
    # 0       -> sin lluvia (0)
    # 0-3     -> ligera (1)
    # 3-10    -> moderada (2)
    # 10-20   -> fuerte (3)
    # >=20    -> muy fuerte (4)
    if intensidad_mm_h == 0:
        rain_label = "Sin lluvia"
        peso_I = 0
    elif intensidad_mm_h < 3:
        rain_label = "Lluvia ligera"
        peso_I = 1
    elif intensidad_mm_h < 10:
        rain_label = "Lluvia moderada"
        peso_I = 2
    elif intensidad_mm_h < 20:
        rain_label = "Lluvia fuerte"
        peso_I = 3
    else:
        rain_label = "Lluvia muy fuerte"
        peso_I = 4

    current_rain = {
        "intensity_mm_h": round(intensidad_mm_h, 2),
        "label": rain_label
    }

    # === B) ACUMULADOS P_24h y P_48h ===

    # P_24h: suma de las próximas 24 horas (8 bloques de 3h)
    P_24h = 0.0
    for item in series[:8]:  # si hay menos de 8, usa los que haya
        P_24h += item["rain_mm"]

    # P_48h: suma de las próximas 48 horas (16 bloques de 3h)
    P_48h = 0.0
    for item in series[:16]:  # si hay menos de 16, usa los que haya
        P_48h += item["rain_mm"]

    # Clasificación de P_24h (ajustada por disipador)
    # <30      -> peso 0
    # 30-70    -> peso 1
    # 70-120   -> peso 2
    # >120     -> peso 3
    if P_24h < 30:
        peso_P24 = 0
    elif P_24h < 70:
        peso_P24 = 1
    elif P_24h < 120:
        peso_P24 = 2
    else:
        peso_P24 = 3

    # Clasificación de P_48h (saturación de suelos "2 días")
    # <60      -> peso 0
    # 60-120   -> peso 1
    # >120     -> peso 2
    if P_48h < 60:
        peso_P48 = 0
    elif P_48h < 120:
        peso_P48 = 1
    else:
        peso_P48 = 2

    # === C) SCORE DE RIESGO Y NIVEL ===

    score = peso_I + peso_P24 + peso_P48

    # Mapeo del score a nivel de riesgo
    # 0-2   -> BAJO
    # 3-4   -> MODERADO
    # 5-6   -> ALTO
    # >=7   -> MUY ALTO
    if score <= 2:
        risk_level = "BAJO"
        risk_color = "green"
        risk_message = "Flujo estable, el disipador opera en condiciones normales."
    elif score <= 4:
        risk_level = "MODERADO"
        risk_color = "yellow"
        risk_message = "El disipador disipa más energía, pero el riesgo es controlado."
    elif score <= 6:
        risk_level = "ALTO"
        risk_color = "orange"
        risk_message = "El disipador está cerca de su capacidad de diseño; aumenta el riesgo de erosión."
    else:
        risk_level = "MUY ALTO"
        risk_color = "red"
        risk_message = "Condiciones extremas: el flujo podría superar la capacidad del disipador y comprometer el talud."

    current_risk = {
        "level": risk_level,
        "score": score,
        "color": risk_color,
        "message": risk_message,
        "debug": {
            "I_now_mm_h": round(intensidad_mm_h, 2),
            "P_24h_mm": round(P_24h, 1),
            "P_48h_mm": round(P_48h, 1),
            "peso_I": peso_I,
            "peso_P24": peso_P24,
            "peso_P48": peso_P48
        }
    }

        # === E) PRÓXIMAS HORAS (next_hours) ===
    # Usamos las próximas 6h (2 bloques de 3h)
    P_6h = 0.0
    for item in series[:2]:  # si no hay 2, suma los que haya
        P_6h += item["rain_mm"]

    # Clasificación muy simple para la maqueta
    # <1 mm      -> Seco (1 barra)
    # 1-10 mm    -> Moderado (2 barras)
    # >=10 mm    -> Fuerte (3 barras)
    if P_6h < 1:
        nh_level = "Seco"
        nh_bars = 1
    elif P_6h < 10:
        nh_level = "Moderado"
        nh_bars = 2
    else:
        nh_level = "Fuerte"
        nh_bars = 3

    next_hours = {
        "window_hours": 6,
        "accumulated_mm": round(P_6h, 1),
        "level": nh_level,
        "bars": nh_bars
    }


    # === D) Por ahora devolvemos lluvia actual + riesgo actual ===

    response = {
        "current_rain": current_rain,
        "current_risk": current_risk,
        "next_hours": next_hours
    }

    return jsonify(response), 200
@weather_bp.route('/weather/history', methods=['GET'])
@jwt_required()
def get_weather_history():
    """
    Devuelve un 'historial' de pronósticos:
    - Cada franja de 3h con lluvia (mm/3h)
    - Intensidad equivalente (mm/h)
    - Categoría de riesgo por franja
    - Resumen: máxima intensidad, total 24h, total 48h
    """
    forecasts = RainForecast.query.order_by(RainForecast.forecast_time).all()
    if not forecasts:
        return jsonify({
            "entries": [],
            "summary": {
                "max_intensity_mm_h": 0.0,
                "max_intensity_time": None,
                "total_24h_mm": 0.0,
                "total_48h_mm": 0.0
            }
        }), 200

    entries = []
    max_intensity = -1.0
    max_intensity_time = None

    # lluvia acumulada en 24h (8 bloques de 3h) y 48h (16 bloques)
    total_24h = 0.0
    total_48h = 0.0

    for idx, f in enumerate(forecasts):
        rain_3h = f.rain_mm or 0.0
        intensity_mm_h = rain_3h / 3.0

        # Acumulados para 24h y 48h
        if idx < 8:
            total_24h += rain_3h
        if idx < 16:
            total_48h += rain_3h

        # Categoría de riesgo por franja según intensidad
        if intensity_mm_h == 0:
            slot_risk = "SIN LLUVIA"
        elif intensity_mm_h < 3:
            slot_risk = "BAJO"
        elif intensity_mm_h < 10:
            slot_risk = "MODERADO"
        elif intensity_mm_h < 20:
            slot_risk = "ALTO"
        else:
            slot_risk = "MUY ALTO"

        # Track máximo
        if intensity_mm_h > max_intensity:
            max_intensity = intensity_mm_h
            max_intensity_time = f.forecast_time

        entries.append({
            "time": f.forecast_time.isoformat(),
            "rain_3h_mm": round(rain_3h, 2),
            "intensity_mm_h": round(intensity_mm_h, 2),
            "slot_risk": slot_risk
        })

    summary = {
        "max_intensity_mm_h": round(max_intensity, 2),
        "max_intensity_time": max_intensity_time.isoformat() if max_intensity_time else None,
        "total_24h_mm": round(total_24h, 1),
        "total_48h_mm": round(total_48h, 1)
    }

    return jsonify({
        "entries": entries,
        "summary": summary
    }), 200






from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt
from app.models import db, User, AlertConfig
from app.mail_utils import send_email_alert


alerts_bp = Blueprint('alerts', __name__, url_prefix='/alerts')


def serialize_config(config: AlertConfig):
    return {
        "email": config.email,
        "notify_on_high": config.notify_on_high,
        "notify_on_very_high": config.notify_on_very_high
    }


@alerts_bp.route('/config', methods=['GET'])
@jwt_required()
def get_my_alert_config():
    """
    Devuelve la configuración de alertas del usuario autenticado.
    Si no existe, la crea con valores por defecto (usar correo del usuario).
    """
    claims = get_jwt()
    user_id = claims.get("id")

    config = AlertConfig.query.filter_by(user_id=user_id).first()

    if not config:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        # Crear config por defecto
        config = AlertConfig(
            user_id=user_id,
            email=user.email,
            notify_on_high=True,
            notify_on_very_high=True
        )
        db.session.add(config)
        db.session.commit()

    return jsonify(serialize_config(config)), 200


@alerts_bp.route('/config', methods=['PUT'])
@jwt_required()
def update_my_alert_config():
    """
    Permite actualizar el correo y las banderas de notificación
    del usuario autenticado.
    """
    claims = get_jwt()
    user_id = claims.get("id")

    config = AlertConfig.query.filter_by(user_id=user_id).first()

    if not config:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "Usuario no encontrado"}), 404

        config = AlertConfig(
            user_id=user_id,
            email=user.email
        )
        db.session.add(config)

    data = request.get_json() or {}

    # Actualizar email si viene
    new_email = data.get("email")
    if new_email:
        config.email = new_email

    # Actualizar flags si vienen
    if "notify_on_high" in data:
        config.notify_on_high = bool(data["notify_on_high"])

    if "notify_on_very_high" in data:
        config.notify_on_very_high = bool(data["notify_on_very_high"])

    db.session.commit()

    return jsonify(serialize_config(config)), 200

@alerts_bp.route('/test-email', methods=['POST'])
@jwt_required()
def send_test_email():
    """
    Envía un correo de prueba al email configurado en las alertas
    del usuario autenticado.
    """
    claims = get_jwt()
    user_id = claims.get("id")

    config = AlertConfig.query.filter_by(user_id=user_id).first()
    if not config:
        return jsonify({"error": "No hay configuración de alertas para este usuario."}), 404

    subject = "Prueba de alertas - Disipador hidráulico"
    body = (
        "Este es un correo de prueba del sistema de monitoreo del disipador hidráulico.\n\n"
        "Si recibes este mensaje, la configuración SMTP está funcionando correctamente."
    )

    send_email_alert(config.email, subject, body)

    return jsonify({"message": f"Correo de prueba enviado a {config.email}"}), 200
from flask import Blueprint, request, jsonify
from app.models import User, db
from flask_jwt_extended import create_access_token
from datetime import timedelta
from flask_jwt_extended import jwt_required, get_jwt

#Definimos un Blueprint para agrupar las rutas de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


#Registro de usuarios
@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    # Validar que vengan todos los campos
    if not name or not email or not password:
        return jsonify({"message": "Faltan datos"}), 400

    # Verificar si ya existe el usuario
    if User.query.filter_by(email=email).first():
        return jsonify({"message": "El correo ya está registrado"}), 409

    # Crear el nuevo usuario
    user = User(name=name, email=email)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    return jsonify({"message": "Usuario registrado correctamente"}), 201


#Login
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Faltan datos"}), 400

    user = User.query.filter_by(email=email).first()

    # Verificar credenciales
    if not user or not user.check_password(password):
        return jsonify({"message": "Credenciales inválidas"}), 401

    # 👇 Información adicional para incluir en el token JWT
    additional_claims = {
        "id": user.id,
        "name": user.name,
        "email": user.email
    }

    # Generar token con claims personalizados
    access_token = create_access_token(
        identity=str(user.id),
        additional_claims=additional_claims,
        expires_delta=timedelta(hours=2)  # opcional: duración del token
    )

    return jsonify({
        "message": "Inicio de sesión exitoso",
        "token": access_token,
    }), 200


# Ruta protegida para obtener la info del usuario autenticado
@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def me():
    #get_jwt() devuelve todo el payload (claims) del token JWT actual
    claims = get_jwt()

    # Extraemos lo que necesitamos (puedes usar directamente claims si quieres)
    user_data = {
        "id": claims.get("id"),
        "name": claims.get("name"),
        "email": claims.get("email")
    }

    return jsonify({
        "message": "Usuario autenticado correctamente",
        "user": user_data
    }), 200

from datetime import datetime
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password_plain):
        """Encripta la contraseña en texto plano."""
        self.password = generate_password_hash(password_plain)

    def check_password(self, password_plain):
        """Verifica si la contraseña coincide."""
        return check_password_hash(self.password, password_plain)

    def __repr__(self):
        return f"<User {self.email}>"
    
class RainForecast(db.Model):
    __tablename__ = "rain_forecasts"

    id = db.Column(db.Integer, primary_key=True)
    forecast_time = db.Column(db.DateTime, nullable=False)  # ✅ nombre cambiado
    rain_mm = db.Column(db.Float, nullable=False)
    risk_level = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<RainForecast {self.forecast_time} - {self.rain_mm} mm - Risk {self.risk_level}>"
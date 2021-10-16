from flask import Flask
from flask_qrcode import QRcode
import os
from datetime import timedelta
from login.routes import login
from usuarios.routes import usuarios
from main.routes import main
from eventos.routes import eventos
from comunicados.routes import comunicados
from qr.routes import qr
from domicilios.routes import domicilios
from cobros.routes import cobros
from ventas.routes import ventas


application = app = Flask(__name__, template_folder='templates')
qrcode = QRcode(app)


# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15000)



app.register_blueprint(login)
app.register_blueprint(usuarios)
app.register_blueprint(main)
app.register_blueprint(comunicados)
app.register_blueprint(eventos)
app.register_blueprint(qr)
app.register_blueprint(domicilios)
app.register_blueprint(cobros)
app.register_blueprint(ventas)



if __name__ == '__main__':
    app.run(debug=True)

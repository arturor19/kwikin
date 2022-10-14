from flask import render_template, flash, redirect, url_for, session, request, Blueprint, Flask
from enviar_email import enviar_correo
import bcrypt
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
import secrets
import json
from config import db, oauth

login = Blueprint('login', __name__, template_folder='templates', static_folder='Kwikin/static')

@login.route('/loging')
def loging():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('login.authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@login.route('/login', methods=['POST', 'GET'])
def logineng():
    '''comentarios'''
    try:
        usuario = db.usuarios  #nombre variable de base de datos
        correo = request.form['logincorreo'] #obtiene el correo de la forma de pagina login
        usuario_login = usuario.find_one({'correo':correo})  #Con el correo, busca_todo el json en base de datos
        inte = usuario.find_one({'correo': correo}, {'_id': 0,'intentos':1}) #contador que incrementa los intentos
        intento = json.dumps(inte, default=str)
        info_bd = json.loads(intento)
        intentos = (info_bd['intentos'])
        if usuario_login and usuario_login['password_temporal'] == True: #si el password es temporal lo manda a configuracion
           if request.form['loginpassword'] == usuario_login['passwordt']:
               usuario_login_session = usuario.find_one({'correo': correo},
                                                {'_id': 1, 'correo': 1, 'nombre': 1, 'apellido': 1, 'terminos_condiciones':1, 'password_temporal':1,
                                                 'picture':1})
               usuario_login_session = json.dumps(usuario_login_session, default=str)
               session['profile'] = usuario_login_session
               session.permanent = True
               return redirect(url_for('usuarios.configuracion_usuario'))
           elif intentos >= 4:
                correo = request.form['logincorreo']
                return redirect(url_for('login.resetpasstemp', correo=correo))
           else:
               usuario.update_one({"correo": correo}, {'$inc': {"intentos": 1}})
               flash(f'Revisa tus credenciales, Intentos {intentos+1}', 'danger')
               return render_template('login/login.html')
        elif usuario_login:
            if bcrypt.checkpw(request.form['loginpassword'].encode('utf-8'), usuario_login['password']):
                usuario_login_session = usuario.find_one({'correo': correo},
                                                         {'_id': 1, 'correo': 1, 'nombre': 1, 'apellido': 1,
                                                          'terminos_condiciones': 1, 'password_temporal':1, 'picture':1})
                usuario_login_session = json.dumps(usuario_login_session, default=str)
                session['profile'] = usuario_login_session
                usuario.update_one({"correo": correo},
                                   {"$set": {"intentos": 0}})
                return redirect(url_for('login.bienvenida'))
            elif intentos >= 4:
                correo = request.form['logincorreo']
                return redirect(url_for('login.resetpasstemp', correo=correo))
            else:
                print(correo)
                usuario.update_one({"correo": correo }, {'$inc': {"intentos": 1}})
                flash(f'Revisa tus credenciales, Intentos {intentos +1}', 'danger')
                return render_template('login/login.html')
        flash(f'Revisa tus credenciales, intento {intento}', 'danger')
        return render_template('login/login.html')
    except:
        return render_template('login/login.html')
    return render_template('login/login.html')


@login.route('/recupera', methods=['POST', 'GET'])
def recupera():
    correo = request.form['correorecuperar']
    usuario = db.usuarios
    usuario_login = usuario.find_one({'correo':correo})
    if usuario_login:
        return redirect(url_for('login.resetpasstemp', correo=correo))
    else:
        flash(f'Correo no reistrado', 'danger')
        return render_template('login/login.html')
    return render_template('login/login.html')


@login.route('/resetpasstemp/<correo>', methods=['POST', 'GET'])
def resetpasstemp(correo):
    usuario = db.usuarios
    passwordt = secrets.token_urlsafe(10)
    usuario.update_one({"correo": correo}, {'$set': {"passwordt": passwordt, "password": "", "password_temporal": True,
                                 "intentos": 0}})
    attach = "test"
    subject = "Nuevo Password temporal"
    body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                                <body><p>Estimado usuario,</p><p>Por favor usa <b>{passwordt}<b> como password temporal</p>
                                                <p>Una vez en la plataforma, necesitarás actualizarlo</p><p>Gracias.</p>
                                                </body></html>"""
    #enviar_correo('root@kwikin.mx', correo, body, attach, subject) Envio de correo comentado por lo pronto
    flash('Password temporal creado, revisa tu correo', 'danger')
    return render_template('login/login.html')


@login.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    usuario_login = json.dumps(user_info, default=str)
    info_google = json.loads(usuario_login)
    print(info_google)
    correo = (info_google['email'])
    nombre = (info_google['given_name'])
    apellido = (info_google['family_name'])
    picture = (info_google['picture'])
    usuario = db.usuarios
    usuario.update_one({'correo': correo},{"$set": {'nombre': nombre, 'picture': picture, 'apellido':apellido}})
    usuario_login_session = usuario.find_one({'correo': correo},
                                             {'_id': 1, 'correo': 1, 'nombre': 1, 'apellido': 1,
                                              'terminos_condiciones': 1, 'picture': 1, 'password_temporal': 1})
    usuario_login_session = json.dumps(usuario_login_session, default=str)
    session['profile'] = usuario_login_session
    usuario.update_one({"correo": correo},
                       {"$set": {"intentos": 0}})
    return redirect(url_for('login.bienvenida'))

@login.route('/bienvenida', methods=["GET", "POST"])
@is_logged_in
def bienvenida(**kws):
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    array_grupos = (usuario.find_one({'correo':correo},{'_id':0, 'grupos':1}))
    if request.method == 'POST':
        coto = request.form.get('coto')
        resp.update({'coto': coto})
        resp = json.dumps(resp, default=str)
        session['profile'] = resp
        print(session['profile'])
        return redirect(url_for('login.bienvenida_'))
    return render_template('login/bienvenida.html', grupos=array_grupos)

@login.route('/bienvenida_', methods=["GET", "POST"])

@is_logged_in
def bienvenida_(**kws):
    usuario = db.usuarios
    grupos = usuario.grupos
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    coto = (resp['coto'])
    grup = (usuario.find_one({'correo':correo}))
    usuario_login = json.dumps(grup, default=str)
    test = json.loads(usuario_login)
    grupos = (test['grupos'][coto])
    if request.method == 'POST':
        grupo = request.form.get('grupo')
        resp.update({'grupo': grupo})
        resp = json.dumps(resp, default=str)
        session['profile'] = resp
        return redirect(url_for('main.dashboard'))
    return render_template('login/bienvenida_.html', grupos=grupos)

@login.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return render_template('login/login.html')

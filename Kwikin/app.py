from flask import Flask, Markup, render_template, flash, redirect, url_for, session, request, logging, send_file, \
    send_from_directory, jsonify
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, SelectField, IntegerField, \
    HiddenField
from authlib.integrations.flask_client import OAuth
from auth_decorator import is_logged_in, is_user, db_execute, usuario_notificaciones
import os
import json
import pandas as pd
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Email, DataRequired
from functools import wraps
import sqlite3
from Cryptodome.Cipher import AES
import base64
from datetime import timedelta, datetime
import time
from flask_qrcode import QRcode
import io
import pytz
import pymysql

# ../templates', static_folder='../static'
application = app = Flask(__name__, template_folder='templates', static_folder='static')
qrcode = QRcode(app)

# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15000)
cipher = AES.new("1234567890123456".encode("utf8"), AES.MODE_ECB)

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/userinfo/v2/me',
    # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)


@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)


@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    print(user_info)
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    email = dict(session)['profile']['email']
    termycon = db_execute(f"SELECT termycon FROM usuarios WHERE email = '{email}'")[0]['termycon']
    print(termycon)
    if termycon == "Acepto": #Agregado para asegurarnos que solo las personas que acepten nuestros terminos y condiciones junto con y aviso de privacidad puedan usar nuestra herramienta"""
        return redirect(url_for('dashboard'))
    return redirect(url_for('terminosycondiciones'))

@app.route('/avisodeprivacidad', methods=['GET', 'POST', 'UPDATE'])
def avisodeprivacidad():
    return render_template('avisodeprivacidad.html')

@app.route('/terminosycondiciones', methods=['GET', 'POST', 'UPDATE'])
@is_logged_in
def terminosycondiciones():
    email = dict(session)['profile']['email']
    termycon = db_execute(f"SELECT termycon FROM usuarios WHERE email = '{email}'")[0]['termycon']
    try:
        if request.method == 'POST':
            db_execute(f"UPDATE usuarios SET termycon = 'Acepto' WHERE email = '{email}'")
            return redirect(url_for('dashboard'))
        return render_template('terminosycondiciones.html')
    except:
        email = None
        termycon = None
        return render_template('terminosycondiciones.html', email=email, termycon=termycon)
    return render_template('terminosycondiciones.html', email=email, termycon=termycon)

# Index
@app.route('/')
def index():
    return render_template('login.html')


@app.route('/ayudabulk', methods=["GET", "POST"])
@usuario_notificaciones
@is_user
@is_logged_in
def ayudabulk(**kws):
    name = session['profile']['name']
    picture = session['profile']['picture']
    return render_template('ayudabulk.html', cont=kws['cont'], com=kws['com'])


@app.route('/dashboard')
@usuario_notificaciones
@is_user
@is_logged_in
def dashboard(**kws):
    return render_template('dashboard.html', cont=kws['cont'], com=kws['com'])


@app.route('/scannerqr')
@usuario_notificaciones
@is_user
@is_logged_in
def scannerqr(**kws):
    return render_template('scannerqr.html', cont=kws['cont'], com=kws['com'])


@app.route('/scannerqrs')
@usuario_notificaciones
@is_user
@is_logged_in
def scannerqrs(**kws):
    return render_template('scannerqrs.html', cont=kws['cont'], com=kws['com'])


@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return render_template('login.html')


@app.route('/crearqr', methods=['GET', 'POST'])
@usuario_notificaciones
@is_user
@is_logged_in
def peticionqr(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    email = session['profile']['email']
    usuario_id = db_execute(f"SELECT id_usuario FROM usuarios WHERE email = '{email}'")[0]['id_usuario']
    now = ct.strftime("%Y-%m-%d %H:%M")
    array_qr = []
    qr = db_execute(f"""SELECT *, CURRENT_TIMESTAMP from qr q , asoc_qr_usuario aqu 
where 
aqu.id_qr = q.id_qr AND 
aqu.id_usuario = '{usuario_id}' and
q.fin >= '{now}' AND 
q.estado = 'Activo'""")

    for row in qr:
        Nombre = (row['visitante'])
        Entrada = (row['inicio'])
        Salida = (row['fin'])
        email_qr = (row['correo_visitante'])
        placas = (row['placas'])
        entrada_real = (row['inicio_real'])
        fin_real = (row['fin_real'])
        estado = (row['estado'])
        id_qr = (row['id_qr'])
        estado_acceso = (row['estado_acceso'])
        codigo_qr = (row['codigo_qr'])

        array_qr.append({'Nombre': Nombre,
                         'Entrada': Entrada,
                         'Salida': Salida,
                         'entrada_real': entrada_real,
                         'fin_real': fin_real,
                         'estado': estado,
                         'estado_acceso': estado_acceso,
                         'email_qr': email_qr,
                         'placas': placas,
                         'codigo_qr': codigo_qr,
                         'id_qr': id_qr})

    if request.method == 'POST':
        tzone = ct.strftime("%Y-%m-%dT%H:%M")
        qr_ent = str(request.form['dateE'])
        qr_sal = str(request.form['dateS'])
        if qr_ent != '' and qr_sal == '':
            dateent = datetime.strptime(qr_ent, "%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_ent, "%Y-%m-%dT%H:%M") + timedelta(days=1)
        elif qr_ent == '' and qr_sal != '':
            dateent = datetime.strptime(str(tzone), "%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_sal, "%Y-%m-%dT%H:%M")
        elif qr_ent == '' and qr_sal == '':
            dateent = datetime.strptime(str(tzone), "%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(str(tzone), "%Y-%m-%dT%H:%M") + timedelta(days=1)
        elif qr_ent != '' and qr_sal != '':
            dateent = datetime.strptime(qr_ent, "%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_sal, "%Y-%m-%dT%H:%M") + timedelta(days=1)
        if dateent > datesal or datesal < datetime.strptime(str(tzone), "%Y-%m-%dT%H:%M") + timedelta(minutes=1):
            flash('Por favor valida que las fechas sean correctas', 'danger')
        elif datesal - dateent > timedelta(hours=48):
            flash('Recuerda que los accesos se otorgan sólo por 48 horas', 'danger')
        elif request.form['nombreqr'] == "":
            flash('Por favor agrega nombre', 'danger')
        fecha_entrada = dateent
        fecha_salida = datesal
        nombre = request.form['nombreqr']
        placas = request.form['placasqr']
        emailqr = request.form['emailqr']
        tipoqr = request.form['tipoqr']
        timestamp = now
        codigo_qr = hex(int(time.time() * 100))
        qr = qrcode(codigo_qr, mode="raw", start_date=fecha_entrada, end_date=fecha_salida)
        try:
            db_execute(
                "INSERT INTO qr(codigo_qr, visitante, inicio, fin, placas, correo_visitante, timestamp, tipo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
                    codigo_qr, nombre, fecha_entrada, fecha_salida, placas, emailqr, timestamp, tipoqr))
            id_usuario = db_execute(("SELECT id_usuario FROM usuarios WHERE email = '%s';" % email))[0]['id_usuario']
            id_qr = db_execute(("SELECT id_qr FROM qr WHERE codigo_qr = '%s';" % codigo_qr))[0]['id_qr']

            db_execute("INSERT INTO asoc_qr_usuario(id_usuario, id_qr) VALUES (\"%s\", \"%s\")" % (id_usuario, id_qr))

        except:
            flash(f'Codigo no creado correctamente', 'danger')
            return redirect(url_for('peticionqr', qr=array_qr))
        qr_data = send_file(qr, mimetype="image/png")
        return redirect(url_for('codigoqr', qr_data=codigo_qr, start_date=fecha_entrada, end_date=fecha_salida, qr=array_qr))

    return render_template('crearpeticionqr.html', qr=array_qr, now=now,  cont=kws['cont'], com=kws['com'])


@app.route('/codigoqr', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def codigoqr(**kws):
    if request.method == 'GET':
        qr_data = request.args.get('qr_data')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        return render_template('codigoqr.html', qr_data=qr_data, mode="raw", start_date=start_date,
                               end_date=end_date,  cont=kws['cont'], com=kws['com'])


@app.route('/crearInd', methods=['GET', 'POST'])
@is_user
@is_logged_in
def crearInd(**kws):
    if request.method == 'POST':
        domicilio = request.form['direccion']
        email = request.form['correo']
        telefono = request.form['telefono']
        checkguardia = request.form.get('checkguardia')
        checkadmin = request.form.get('checkadmin')
        if checkguardia == 'on' and checkadmin == 'off':
            grupo = 4
        elif checkadmin == 'on' and checkguardia == 'off':
            grupo = 2
        elif checkadmin == 'on' and checkguardia == 'on':
            grupo = ""
            flash(f'{email} no fue dado de alta. Solo puedes seleccionar un tipo de usuario', 'danger')
        else:
            grupo = 3
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        if '@gmail.com' in email:
            if domicilio == "" or email == "" or telefono == "" or grupo == "":
                flash('Por favor revisa que todos los datos esten completos', 'danger')
            else:
                try:
                    cur.execute("INSERT INTO usuarios(domicilio, email, telefono) VALUES(\"%s\", \"%s\", \"%s\")" % (
                        domicilio, email, telefono))
                    cur.execute(
                        f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
                    flash(f'Usuario {email} agregado correctamente', 'success')
                    mysql.commit()
                except:
                    flash(f'Correo {email} ya existe', 'danger')
        else:
            flash(f'El correo {email} es incorrecto, por favor valida que sea Gmail', 'danger')
        cur.close()
    return redirect(url_for('gestionusuarios'))


@app.route('/crearBulk', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def upload(**kws):
    if request.method == 'POST':
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        try:
            df = pd.read_csv(request.files.get('file'))
            for index, row in df.iterrows():
                email = row['Email']
                domicilio = row['Direccion']
                telefono = row['Telefono']
                if '@gmail.com' in email:
                    try:
                        cur.execute(
                            f"INSERT INTO usuarios(domicilio, email, telefono) VALUES('{domicilio}','{email}','{telefono}')")
                        cur.execute(
                            f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values (3, (SELECT id_usuario FROM "
                            f"usuarios WHERE email = '{email}'))")
                        flash(f'{email} agregado correctamente', 'success')
                    except:
                        flash(f'El correo {email} ya existe', 'danger')
                    mysql.commit()
                else:
                    flash(f'El correo {email} es incorrecto, por favor valida que sea Gmail', 'danger')
            cur.close()
        except:
            flash(f"El formato no es valido o el archivo no existe", "danger")
        return render_template('crearbulk.html',  cont=kws['cont'], com=kws['com'])
    return render_template('crearbulk.html',  cont=kws['cont'], com=kws['com'])


@app.route('/gestionusuarios', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestionusuarios(**kws):
    lista_usuarios_grupos = (db_execute("select u2.*, g2.nombre_grupo as 'nombre_grupo' from asoc_usuario_grupo aug, usuarios u2, grupos g2 where u2.id_usuario = aug.id_usuario and aug.id_grupo = g2.id_grupo"))
    dict_usuarios = {}
    for usuari in lista_usuarios_grupos:

        if usuari["email"] not in dict_usuarios.keys():
            dict_usuarios.update({usuari["email"]: {"grupos": [usuari["nombre_grupo"]]}})
        else:
            dict_usuarios[usuari["email"]]["grupos"].append(usuari["nombre_grupo"])

    print(dict_usuarios)
    usuarios = db_execute("SELECT * FROM  usuarios")
    print(usuarios)
    array = []
    for row in usuarios:
        id_usuario = (row['id_usuario'])
        status = (row['status'])
        email = (row['email'])
        grupo = db_execute(
            f"SELECT  GROUP_CONCAT(asoc_usuario_grupo.id_grupo) as grupo FROM usuarios JOIN asoc_usuario_grupo ON usuarios.id_usuario = asoc_usuario_grupo.id_usuario WHERE usuarios.email = '{email}'")[0]['grupo']
        nombre = (row['nombre'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])


        array.append({'status': (status),
                      'id_usuario': id_usuario,
                      'email': email,
                      'nombre': nombre,
                      'telefono': telefono,
                      'grupo' : grupo,
                      'domicilio': domicilio})
    print(array)
    if len(usuarios) > 0:
        return render_template('gestionusuarios.html', usuarios=array, dict_usuarios=dict_usuarios, cont=kws['cont'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('gestionusuarios.html', usuarios=array, dict_usuarios=dict_usuarios, cont=kws['cont'], com=kws['com'])

@app.route('/actgrupousuario', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actgrupousuario():
    idsg = None
    if request.method == "POST":
        idsg = request.form['data']
        valida_admin = db_execute(f"SELECT * FROM asoc_usuario_grupo WHERE id_usuario = '{idsg}' AND id_grupo = 2")
        if len(valida_admin) > 0:
            db_execute(f"DELETE FROM asoc_usuario_grupo WHERE id_usuario = '{idsg}' AND id_grupo = 2")
            flash(f'Usuario configurado como solo residente', 'Success')
        else:
            db_execute(f"INSERT INTO asoc_usuario_grupo(id_usuario, id_grupo) VALUES ('{idsg}', 2)")
            flash(f'Usuario configurado como administrador', 'Success')
        print(idsg)

    return redirect(url_for('gestionusuarios'))


@app.route('/actusuarioinfo', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actusuarioinfo():
    if request.method == "POST":
        if request.form['actusuarioinfo'] == 'actu':
            idusuario = request.form['idusuariohidden']
            domicilio_usuario = request.form['domiciliousuario']
            telefono_usuario = request.form['telefonousuario']
            try:
                db_execute(f"UPDATE usuarios SET  domicilio = '{domicilio_usuario}', telefono = '{telefono_usuario}' WHERE id_usuario = '{idusuario}'")
                return redirect(url_for('gestionusuarios'))
            except:
                flash(f'No se pudo actualizar el registro', 'danger')
                return redirect(url_for('gestionusuarios'))
        elif request.form['actusuarioinfo'] == 'elim':
            if request.method == 'POST':
                try:
                    idusuario = request.form['idusuariohidden']
                    db_execute(f"DELETE FROM usuarios WHERE id_usuario = '{idusuario}' ")
                    return redirect(url_for('gestionusuarios'))
                except:
                    flash(f'No se pudo eliminar el registro', 'danger')
                    return redirect(url_for('gestionusuarios'))
    return redirect(url_for('gestionusuarios'))

@app.route('/actestadoqr', methods=['POST'])
@is_user
@is_logged_in
def actestadoqr():
    ids = None
    if request.method == "POST":
        ids = request.form['data']
        print(ids)
        result = db_execute("SELECT estado FROM qr WHERE id_qr = '%s';" % ids)[0]['estado']
        print(result)
        if str(result) == "Activo":
            db_execute("UPDATE qr SET estado = 'Inactivo' WHERE id_qr = '%s';" % ids)
            return redirect(url_for('peticionqr'))
        elif str(result) == "Inactivo":
            db_execute("UPDATE qr SET estado = 'Activo' WHERE id_qr = '%s';" % ids)
            return redirect(url_for('peticionqr'))
    return redirect(url_for('peticionqr'))

@app.route('/actestadoaccesoqr', methods=['POST'])
@is_user
@is_logged_in
def actestadoaccesoqr():
    ids = None
    if request.method == "POST":
        ids = request.form['data']
        print(ids)
        result = db_execute("SELECT estado_acceso FROM qr WHERE id_qr = '%s';" % ids)[0]['estado_acceso']
        print(result)
        if str(result) == "Entro":
            db_execute("UPDATE qr SET estado_acceso = 'Salio' WHERE id_qr = '%s';" % ids)
            return redirect(url_for('peticionqr'))
        elif str(result) == "Salio":
            db_execute("UPDATE qr SET estado_acceso = 'Entro' WHERE id_qr = '%s';" % ids)
            return redirect(url_for('peticionqr'))
    return redirect(url_for('peticionqr'))

@app.route('/actusuario', methods=['POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def actusuario(**kws):
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    ids = None
    if request.method == "POST":
        ids = request.form['data']
        result = cur.execute("SELECT status FROM usuarios WHERE email = '%s';" % ids)
        result = cur.fetchone()
        if str(result) == "('Activo',)":
            cur.execute("UPDATE usuarios SET status = 'Inactivo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html',  cont=kws['cont'], com=kws['com'])
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html',  cont=kws['cont'], com=kws['com'])
    cur.close()
    return render_template('gestionusuarios.html',  cont=kws['cont'], com=kws['com'])


@app.route('/actdom', methods=['POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def actdom(**kws):
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    ids = None
    if request.method == "POST":
        ids = request.form['data']
        result = cur.execute("SELECT status FROM usuarios WHERE email = '%s';" % ids)
        result = cur.fetchone()
        if str(result) == "('Activo',)":
            cur.execute("UPDATE usuarios SET status = 'Inactivo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestiondimicilios.html',  cont=kws['cont'], com=kws['com'])
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestiondimicilios.html', cont=kws['cont'], com=kws['com'])
    cur.close()
    return render_template('gestiondimicilios.html', cont=kws['cont'], com=kws['com'])

@app.route('/gestionqrhistorico', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestionqrhistorico(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    now = ct
    usuario_id = db_execute(f"SELECT id_usuario FROM usuarios WHERE email = '{email}'")[0]['id_usuario']
    now = str(now)
    array_qrh = []
    qrh = db_execute(f"""SELECT * from qr q , asoc_qr_usuario aqu 
    where 
    (aqu.id_qr = q.id_qr AND
    aqu.id_usuario = '{usuario_id}' AND
    q.fin <= '{now}') or 
    (aqu.id_qr = q.id_qr AND 
    aqu.id_usuario = '{usuario_id}' AND
    q.estado = 'Inactivo')""")

    for row in qrh:
        Nombre = (row['visitante'])
        Entrada = (row['inicio'])
        Salida = (row['fin'])
        email_qr = (row['correo_visitante'])
        placas = (row['placas'])
        entrada_real = (row['inicio_real'])
        fin_real = (row['fin_real'])
        estado = (row['estado'])
        id_qr = (row['id_qr'])
        codigo_qr = (row['codigo_qr'])
        estado_acceso = (row['estado_acceso'])
        array_qrh.append({'Nombre': Nombre,
                         'Entrada': Entrada,
                         'Salida': Salida,
                         'entrada_real': entrada_real,
                         'fin_real': fin_real,
                         'estado': estado,
                         'email_qr': email_qr,
                         'placas': placas,
                         'estado_acceso': estado_acceso,
                         'codigo_qr': codigo_qr,
                         'id_qr': id_qr})
    return render_template('crearpeticionqrhistorico.html', qrh=array_qrh, now=now, cont=kws['cont'], com=kws['com'])

@app.route('/actqr', methods=['POST','GET'])
@is_user
@is_logged_in
def actqr():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    usuario_id = db_execute(f"SELECT id_usuario FROM usuarios WHERE email = '{email}'")[0]['id_usuario']
    now = ct
    now = str(now)
    array_qrh = []
    qrh = db_execute(f"""SELECT *, CURRENT_TIMESTAMP from qr q , asoc_qr_usuario aqu  
    where 
    aqu.id_qr = q.id_qr AND 
    aqu.id_usuario = '{usuario_id}' AND
    q.fin >= '{now}' AND 
    q.estado = 'Activo'""")
    for row in qrh:
        Nombre = (row['visitante'])
        Entrada = (row['inicio'])
        Salida = (row['fin'])
        email_qr = (row['correo_visitante'])
        placas = (row['placas'])
        entrada_real = (row['inicio_real'])
        fin_real = (row['fin_real'])
        estado = (row['estado'])
        id_qr = (row['id_qr'])
        codigo_qr = (row['codigo_qr'])
        estado_acceso = (row['estado_acceso'])
        array_qrh.append({'Nombre': Nombre,
                         'Entrada': Entrada,
                         'Salida': Salida,
                         'entrada_real': entrada_real,
                         'fin_real': fin_real,
                         'estado': estado,
                         'email_qr': email_qr,
                         'placas': placas,
                         'estado_acceso': estado_acceso,
                         'codigo_qr': codigo_qr,
                         'id_qr': id_qr})
    print(array_qrh)
    if request.method == "POST":
        if request.form['actqr'] == 'act':
            qrid = request.form['idqrhidden']
            visitante = request.form['codigovisitante']
            correo_visitante = request.form['codigoemailvisitante']
            placas_visitante = request.form['codigoplacas']
            entrada_visitante = request.form['codigoEntrada']
            salida_visitante = request.form['codigoSalida']

            try:
                db_execute(f"UPDATE qr SET  visitante = '{visitante}', correo_visitante = '{correo_visitante}', placas = '{placas_visitante }', inicio = '{entrada_visitante}', fin = '{salida_visitante}'  WHERE id_qr = '{qrid}'")
                return redirect(url_for('peticionqr', qr=array_qrh))
            except:
                flash(f'No se pudo actualizar el registro', 'danger')
                return redirect(url_for('peticionqr', qr=array_qrh))
        elif request.form['actqr'] == 'ver':
            if request.method == 'POST':
                codigo_qr = request.form['qrhidden']
                fecha_entrada = request.form['starthidden']
                fecha_salida = request.form['endhidden']
                return redirect(
                    url_for('codigoqr', qr_data=codigo_qr, start_date=fecha_entrada, end_date=fecha_salida))
    return redirect(url_for('peticionqr', qr=array_qrh))


@app.route('/ventas', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def ventas(**kws):
    if request.method == 'POST':
        domicilio = request.form['direccion']
        email = request.form['correo']
        checkguardia = request.form.get('checkguardia')
        if checkguardia == 'on':
            grupo = 4
        else:
            grupo = 3
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        try:
            cur.execute("INSERT INTO usuarios(domicilio, email) VALUES(\"%s\", \"%s\")" % (
                domicilio, email))
            flash('Usuario agregado correctamente', 'success')
            mysql.commit()

        except:
            flash('Correo ya existe', 'danger')
        try:
            cur.execute(
                f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
            mysql.commit()
        except:
            flash(f'El correo {email} no pudo asociar un grupo, contacta un administrador', 'danger')
        cur.close()
    return render_template('ventas.html', cont=kws['cont'], com=kws['com'])


@app.route('/crearventa', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def crearventa(**kws):
    Cotopy = request.form['Coto']
    CotoDirpy = request.form['CotoDir']
    CotoCPpy = request.form['CotoCP']
    correopy = request.form['correo']
    teladminpy = request.form['teladmin']
    vendedorpy = dict(session)['profile']['email']  # esta variable sirve para saber quien creo el coto y poder mapearlo
    print(Cotopy, CotoDirpy, CotoCPpy, correopy, teladminpy, vendedorpy)
    return render_template("ventas.html", cont=kws['cont'], com=kws['com'])
    '''db.execute(
        "INSERT INTO events (user_id, title, description, place, start, end) VALUES (:user, :title, :description, :place, :start, :end)",
        user=session["user_id"], title=title, description=description, place=place, start=start, end=end)'''


@app.route('/validarqr', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def validarqr(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    if request.method == 'GET':
        qrval = request.args.get('qr')
        print(qrval)
        result = cur.execute("SELECT * FROM qr WHERE codigo_qr = '%s';" % qrval)
        qrinfo = cur.fetchall()
        print(qrinfo[0])
        try:
            qrid = int(qrinfo[0][0])
        except:
            return render_template("noaprobado.html", cont=kws['cont'], com=kws['com'])
        fecha_inicio = qrinfo[0][2]
        fecha_fin = qrinfo[0][3]
        nombre = qrinfo[0][4]
        estado = qrinfo[0][7]
        timestamp = tzone.strftime("%Y-%m-%dT%H:%M:%SZ")
        tipo = "E"
        if len(qrinfo[0][1]) > 0:
            if fecha_inicio < tzone.strftime("%Y-%m-%dT%H:%M:%SZ") and fecha_fin > tzone.strftime("%Y-%m-%dT%H:%M:%SZ"):
                print("fecha")
                if estado == "Activo":
                    print("estado")
                    flash(f'Adelante {nombre}', 'success')
                    cur.execute(
                        "INSERT INTO asoc_qr_registro (id_qr, timestamp, type) VALUES(\"%s\", \"%s\", \"%s\")" % (
                            qrid, timestamp, tipo))
                    mysql.commit()
                    cur.close()
                    return render_template("aprobado.html",  cont=kws['cont'], com=kws['com'])
                else:
                    flash(f'el código ha sido cancelado', 'danger')
                    return render_template("noaprobado.html",  cont=kws['cont'], com=kws['com'])
            else:
                flash(f'Las fechas no son validas', 'danger')
                return render_template("noaprobado.html",  cont=kws['cont'], com=kws['com'])
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("noaprobado.html",  cont=kws['cont'], com=kws['com'])


@app.route('/validarqrs', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def validarqrs(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    if request.method == 'GET':
        qrval = request.args.get('qrs')
        result = cur.execute("SELECT * FROM qr WHERE codigo_qr = '%s';" % qrval)
        qrinfo = cur.fetchall()
        try:
            qrid = int(qrinfo[0][0])
        except:
            return render_template("noaprobado.html", cont=kws['cont'], com=kws['com'])
        fecha_inicio = qrinfo[0][2]
        fecha_fin = qrinfo[0][3]
        nombre = qrinfo[0][4]
        estado = qrinfo[0][7]
        timestamp = tzone.strftime("%Y-%m-%dT%H:%M:%SZ")
        tipo = "S"
        if len(qrinfo[0][1]) > 0:
            flash(f'Hasta Luego {nombre}', 'success')
            cur.execute("INSERT INTO asoc_qr_registro (id_qr, timestamp, type) VALUES(\"%s\", \"%s\", \"%s\")" % (
                qrid, timestamp, tipo))
            mysql.commit()
            cur.close()
            return render_template("aprobado.html", cont=kws['cont'], com=kws['com'])
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("noaprobado.html",  cont=kws['cont'], com=kws['com'])
    return render_template("dashboard.html",  cont=kws['cont'], com=kws['com'])


@app.route('/calendar-events')
@is_user
@is_logged_in
@usuario_notificaciones
def calendar_events(**kws):
    arr_terr = db_execute('select * from terrazas')
    try:
        rows = db_execute("SELECT id, titulo, casa, UNIX_TIMESTAMP(start_date)*1000 as start, UNIX_TIMESTAMP("
                          "end_date)*1000 as end FROM event FROM eventos")
        resp = jsonify({'success': 1, 'result': rows})
        print(rows)
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    return render_template('calendar_events.html', rows=rows, terrazas=arr_terr, cont=kws['cont'], com=kws['com'])


@app.route('/calendario')
@is_user
@is_logged_in
@usuario_notificaciones
def calendario(**kws):
    arr_terr = db_execute('select * from terrazas')
    return render_template('calendar_events.html',  cont=kws['cont'], com=kws['com'], terrazas=arr_terr)

@app.route('/calendario_ini/remote')
@is_user
@is_logged_in
def calendario_ini():
    test_cal = ''
    if request.method == 'GET':
        callback = request.args.get('callback')
        print(callback)
    if callback in "in mbsc_jsonp_comp_demo-responsive-month-view":
        test_cal = '''try { window['mbsc_jsonp_comp_demo-responsive-month-view']('{"calendar":{},"datetime":{"wheels":[[{"cssClass":"mbsc-dt-whl-d","label":"Día","data":[{"value":1,"display":"1"},{"value":2,"display":"2"},{"value":3,"display":"3"},{"value":4,"display":"4"},{"value":5,"display":"5"},{"value":6,"display":"6"},{"value":7,"display":"7"},{"value":8,"display":"8"},{"value":9,"display":"9"},{"value":10,"display":"10"},{"value":11,"display":"11"},{"value":12,"display":"12"},{"value":13,"display":"13"},{"value":14,"display":"14"},{"value":15,"display":"15"},{"value":16,"display":"16"},{"value":17,"display":"17"},{"value":18,"display":"18"},{"value":19,"display":"19"},{"value":20,"display":"20"},{"value":21,"display":"21"},{"value":22,"display":"22"},{"value":23,"display":"23"},{"value":24,"display":"24"},{"value":25,"display":"25"},{"value":26,"display":"26"},{"value":27,"display":"27"},{"value":28,"display":"28"},{"value":29,"display":"29"},{"value":30,"display":"30"},{"value":31,"display":"31"}]},{"cssClass":"mbsc-dt-whl-m","label":"Mes","data":[{"value":0,"display":"<span class=\\\\"mbsc-dt-month\\\\">Enero</span>"},{"value":1,"display":"<span class=\\\\"mbsc-dt-month\\\\">Febrero</span>"},{"value":2,"display":"<span class=\\\\"mbsc-dt-month\\\\">Marzo</span>"},{"value":3,"display":"<span class=\\\\"mbsc-dt-month\\\\">Abril</span>"},{"value":4,"display":"<span class=\\\\"mbsc-dt-month\\\\">Mayo</span>"},{"value":5,"display":"<span class=\\\\"mbsc-dt-month\\\\">Junio</span>"},{"value":6,"display":"<span class=\\\\"mbsc-dt-month\\\\">Julio</span>"},{"value":7,"display":"<span class=\\\\"mbsc-dt-month\\\\">Agosto</span>"},{"value":8,"display":"<span class=\\\\"mbsc-dt-month\\\\">Septiembre</span>"},{"value":9,"display":"<span class=\\\\"mbsc-dt-month\\\\">Octubre</span>"},{"value":10,"display":"<span class=\\\\"mbsc-dt-month\\\\">Noviembre</span>"},{"value":11,"display":"<span class=\\\\"mbsc-dt-month\\\\">Diciembre</span>"}]},{"cssClass":"mbsc-dt-whl-y","label":"A&ntilde;o","data":"function getYearValue(i, inst) {\\\\r\\\\n    var s = inst.settings;\\\\r\\\\n    return {\\\\r\\\\n      value: i,\\\\r\\\\n      display: (/yy/i.test(s.dateDisplay) ? i : (i + \\'\\').substr(2, 2)) + (s.yearSuffix || \\'\\')\\\\r\\\\n    };\\\\r\\\\n  }","getIndex":"function getYearIndex(v) {\\\\r\\\\n    return v;\\\\r\\\\n  }"}]],"wheelOrder":{"d":0,"m":1,"y":2},"isoParts":{"y":1,"m":1,"d":1}},"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div>"}'); } catch (ex) {}'''
    elif "mbsc_jsonp_comp_" in callback:
        id_num_cal = str(callback).replace("mbsc_jsonp_comp_", '')
        head_cal = ("try { window['mbsc_jsonp_comp_" + id_num_cal + "']")
        tail_cal = '''('{"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-persp\\\\"><div role=\\\\"dialog\\\\" class=\\\\"mbsc-fr-scroll\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-focus\\\\" tabindex=\\\\"-1\\\\"></div><div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div></div></div>"}'); } catch (ex) {}'''
        test_cal = head_cal + tail_cal
    return test_cal

@app.route('/calendario_data')
@is_user
@is_logged_in
def test_calendario():
    colores = {}
    for v in (db_execute("select id_terrazas, colores_terraza from terrazas;")):
        colores.update({v["id_terrazas"]: v["colores_terraza"]})
    arr_evetos_aprobados = db_execute("select t2.id_terrazas, t2.terraza, e.dia from eventos e, terrazas t2 where "
                                      "e.estado = 'Aprobado' and t2.terraza = e.terraza")
    arr_cal = []
    for event in arr_evetos_aprobados:
        start = event['dia']
        text = event['terraza']
        color = colores[event['id_terrazas']]
        arr_cal.append({"start": start, "text": text, "color": color})
    events_json = json.dumps(arr_cal, indent=4)
    info_calendario = 'try {mbscjsonp1(' + events_json + ');' + '} catch (ex) {}'
    return info_calendario


#@app.route('/avisodeprivacidad')
#def avisodeprivacidad():
#    return render_template('avisodeprivacidad.html')


@app.route('/crearevento', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def peticionevento(**kws):
    arr_terr = db_execute('select * from terrazas')
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = session['profile']['email']
    name = session['profile']['name']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = str(now)

    if request.method == 'POST':
        try:
            fechaevento = request.form['fechaevento']
            terraza = request.form['terraza']

            if fechaevento < now:
                flash('Por favor valida que las fechas sean correctas', 'danger')
            elif terraza == 'Selecciona terraza':
                flash('Por favor selecciona una terraza del listado', 'danger')
            else:
                try:
                    existe_evento = db_execute(f"select * from eventos where terraza='{terraza}' and nombre_eventos='{name}' and correo='{email}' and dia='{fechaevento}'")
                    valor_evento = (len(existe_evento))
                    if valor_evento == 1:
                        pass
                    else:
                        db_execute(
                        "INSERT INTO eventos(terraza, nombre_eventos, correo, dia) VALUES(\"%s\", \"%s\", \"%s\", \"%s\")" % (
                            terraza, name, email, fechaevento))

                    flash(f'Evento guardado correctamente, recibiras un correo cuando el administrador lo apruebe',
                          'success')
                    # insert_asoc_qr_usuario = f"""INSERT INTO asoc_qr_usuario(id_usuario, id_qr, id_coto) VALUES
                    #  (
                    #  (SELECT id_usuario FROM usuarios where email = '{email}'),
                    # (SELECT id_qr FROM qr where codigo_qr = '{codigo_qr}'),
                    #  (SELECT id_coto FROM asoc_usuario_coto where id_usuario = (SELECT id_usuario FROM usuarios where email = '{email}'))
                    #  );"""
                    #                cur.execute(insert_asoc_qr_usuario)
                    #                mysql.commit()
                    cur.close()
                except:
                    flash(f'Evento no creado correctamente', 'danger')
                    return render_template('calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now,
                                           terrazas=arr_terr)
                return render_template('calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)
        except:
            flash(f'Revisa todos los campos', 'danger')
            return render_template('calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)

    return render_template('calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)


@app.route('/gestioneventos', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioneventos(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = session['profile']['email']
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia >= '%s';" % now)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        email = (row['correo'])
        nombre = (row['nombre_eventos'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])
        id_eventos = (row['id_eventos'])

        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'email': email,
                              'nombre': nombre,
                              'terraza': terraza,
                              'domicilio': domicilio,
                              'telefono': telefono,
                              'dia': dia})

    if len(eventos) > 0:
        return render_template('gestioneventos.html', eventos=array_eventos, cont=kws['cont'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('gestioneventos.html', eventos=array_eventos, msg=msg, cont=kws['cont'], com=kws['com'])


@app.route('/acteventos', methods=['POST'])
@is_user
@is_logged_in
def acteventos():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia >= '%s';" % now)
    array_eventos = []
    if request.method == 'POST':
        eventsvalue = request.form['mycheckboxE']
        eventsid = request.form['idhidden']
        terraza = request.form['terrazahidden']
        print(eventsvalue, eventsid, terraza)
        dia = db_execute("SELECT dia FROM eventos WHERE id_eventos = '%s';" % eventsid)[0]['dia']
        print(eventsvalue)
        print(eventsid)
        print(terraza)
        print(dia)
        print(f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia}' AND estado = 'Aprobado'")
        validador = db_execute(
            f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia}' AND estado = 'Aprobado'")
        print(validador)
        if len(validador) > 0 and eventsvalue == 'Aprobado':
            flash(f'La terraza {terraza} ya esta apartada el dia {dia}, revisa fecha', 'danger')
            return redirect(url_for('gestioneventos'))
        else:
            db_execute("UPDATE eventos SET estado =\"%s\"  WHERE id_eventos =\"%s\";" % (eventsvalue, eventsid))
            db_execute(
                "SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia >= '%s';" % now)
            flash(f'La terraza {terraza} fue  cambiada a {eventsvalue} el dia {dia} con éxito', 'success')
            return redirect(url_for('gestioneventos'))

        return redirect(url_for('gestioneventos'))

    return redirect(url_for('gestioneventos'))


@app.route('/gestioneventoshistorico', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioneventoshistorico(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    now = ct
    now = str(now)
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia < '%s';" % now)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        email = (row['correo'])
        nombre = (row['nombre_eventos'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])
        id_eventos = (row['id_eventos'])

        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'email': email,
                              'nombre': nombre,
                              'terraza': terraza,
                              'domicilio': domicilio,
                              'telefono': telefono,
                              'dia': dia})
    if len(eventos) > 0:
        return render_template('gestioneventoshistorico.html',  cont=kws['cont'], com=kws['com'], eventos=array_eventos)
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('gestioneventoshistorico.html',  cont=kws['cont'], com=kws['com'],
                               eventos=array_eventos, msg=msg)
    cur.close()


@app.route('/comunicados', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def comunicados(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    creador = dict(session)['profile']['email']
    id_mensaje = ""
    array_comunica = []
    comunica = db_execute("SELECT DISTINCT idmultiple_mensaje, fecha, titulo, mensaje, id_usuario_emisor, tipo from comunicados")
    for row in comunica:
        id_mensaje = (row['idmultiple_mensaje'])
        fecha = (row['fecha'])
        titulo = (row['titulo'])
        mensaje = (row['mensaje'])
        creador = (row['id_usuario_emisor'])
        tipo = (row['tipo'])
        id_mensaje = (row['idmultiple_mensaje'])
        array_comunica.append({'idmultiple_mensaje' : id_mensaje,
                             'fecha': fecha,
                             'titulo': titulo,
                             'mensaje': mensaje,
                             'id_mensaje': id_mensaje,
                             'tipo': tipo,
                             'creador': creador})
        print(array_comunica)
    array_allemails = []
    allemails = db_execute("SELECT * FROM usuarios ")
    for row in allemails:
        email = (row['email'])
        array_allemails.append({'email': email})
    print(array_allemails)

    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = hex(int(time.time()))
        titulo = request.form['titulocom']
        mensaje = request.form['commensaje']
        email_usuario_receptor = request.form['comdirigido']
        if email_usuario_receptor == "Todos":
            for entry in array_allemails:
                db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
                timestamp, titulo, mensaje, idmultmensaje, entry['email'], creador, 0, "Comunicado"))
            return redirect(url_for('comunicados'))
        else:
            db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            timestamp, titulo, mensaje, idmultmensaje, email_usuario_receptor, creador, 0, "Comunicado"))
            return redirect(url_for('comunicados'))
        return render_template('comunicados.html', comuni=array_comunica, cont=kws['cont'], com=kws['com'],
                               allemails=array_allemails, id_mensaje=id_mensaje)
    return render_template('comunicados.html',  cont=kws['cont'], com=kws['com'], comuni=array_comunica,
                           allemails=array_allemails, id_mensaje=id_mensaje)


@app.route('/entregadoact/<id_mensaje>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoact(id_mensaje, **kws):
    usuario = dict(session)['profile']['email']
    id_usuario = db_execute(f"SELECT id_usuario FROM usuarios WHERE email = '{usuario}'")[0]['id_usuario']
    valida = db_execute(f"SELECT id_grupo FROM asoc_usuario_grupo WHERE id_usuario = '{id_usuario}'")[0]['id_grupo']
    if valida == 1 or valida == 2 or valida == 3:
        if request.method == 'GET':
            titulo = db_execute(f"SELECT titulo FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['titulo']
            mensaje = db_execute(f"SELECT mensaje FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['mensaje']
            tipo = db_execute(f"SELECT tipo FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['tipo']
            resp_a = db_execute(f"SELECT opcion_a FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_a']
            resp_b = db_execute(f"SELECT opcion_b FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_b']
            resp_c = db_execute(f"SELECT opcion_c FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_c']
            resp_d = db_execute(f"SELECT opcion_d FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_d']
            array_leido = []
            leido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido != 0 and idmultiple_mensaje = '{id_mensaje}'")
            contleidopor = len(leido)
            array_noleido = []
            noleido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido = 0 and idmultiple_mensaje = '{id_mensaje}'")
            contnoleidopor = len(noleido)
            try:
                opcion_a = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'A'")
                contopa = len(opcion_a)
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'B'")
                contopb = len(opcion_b)
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'C'")
                contopc = len(opcion_c)
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'D'")
                contopd = len(opcion_d)
            except:
                opcion_d = ""
                contopd = 0
            if tipo == "Comunicado":
                labels = ["Leido","No leido"]
                values = [contleidopor, contnoleidopor]
                colors = ["#1cc88a", "#e74a3b"]
            else:
                labels = ["Opcion A", "Opcion B", "Opcion C", "Opcion D"]
                values = [contopa, contopb, contopc, contopd]
                colors = ["#4e73df", "#858796", "#1cc88a", "#36b9cc"]
            array_opa = []
            array_opb = []
            array_opc = []
            array_opd = []
            for row in noleido:
                noleidopor =  (row['email_usuario_receptor'])
                array_noleido.append({'noleidopor':noleidopor})
            for rows in leido:
                leidopor =  (rows['email_usuario_receptor'])
                array_leido.append({'leidopor':leidopor})
            for row in opcion_a:
                opa = (row['email_usuario_receptor'])
                array_opa.append({'opa':opa})
            for row in opcion_b:
                opb = (row['email_usuario_receptor'])
                array_opb.append({'opb':opb})
            for row in opcion_c:
                opc = (row['email_usuario_receptor'])
                array_opc.append({'opc':opc})
            for row in opcion_d:
                opd = (row['email_usuario_receptor'])
                array_opd.append({'opd':opd})
        return render_template('detallescomunicado.html', contopa=contopa, contopb=contopb, contopc=contopc,
                               contopd=contopd, opa=array_opa, opb=array_opb, opc=array_opc, opd=array_opd,
                               leidopor=array_leido, tipo=tipo, titulo=titulo, mensaje=mensaje, noleidopor=array_noleido,
                               contleidopor=contleidopor, contnoleidopor=contnoleidopor, resp_a=resp_a, resp_b=resp_b,
                               resp_c=resp_c, resp_d=resp_d, set=zip(values, labels, colors),
                               cont=kws['cont'], com=kws['com'])
    else:
        return redirect(url_for('dashboard'))

@app.route('/entregadoactres/eliminarres', methods=['GET','POST'])
@is_user
@is_logged_in
def eliminarres():
    if request.method == 'POST':
        id_mensajes =  request.form['elim']
        db_execute("UPDATE comunicados SET leido =\"%s\"  WHERE id_notificaciones =\"%s\";" % (2, id_mensajes))
        return redirect(url_for('comunicadosres'))
    return redirect(url_for('dashboard'))

@app.route('/entregadoactres/contestarenc', methods=['GET','POST'])
@is_user
@is_logged_in
def contestarenc():
    if request.method == 'POST':
        id_mensajes = request.form['residhidden']
        resultado =  request.form['contestarenc']
        db_execute("UPDATE comunicados SET resultado =\"%s\"  WHERE id_notificaciones =\"%s\";" % (resultado, id_mensajes))
        return redirect(url_for('comunicadosres'))
    return redirect(url_for('dashboard'))

@app.route('/entregadoactres/<id_mensajes>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoactres(id_mensajes, **kws):
    id_mensajes = id_mensajes
    usuario = dict(session)['profile']['email']
    resultado_var = db_execute(f"SELECT resultado FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0][
        'resultado']  # para validar cual es la variable de leido
    valida = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['email_usuario_receptor']
    try:
        if request.method == 'GET' and usuario == valida:
            db_execute("UPDATE comunicados SET leido =\"%s\"  WHERE id_notificaciones =\"%s\";" % (1, id_mensajes))
            titulo = db_execute(f"SELECT titulo FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['titulo']
            mensaje = db_execute(f"SELECT mensaje FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['mensaje']
            tipo = db_execute(f"SELECT tipo FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['tipo']
            resp_a = db_execute(f"SELECT opcion_a FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_a']
            resp_b = db_execute(f"SELECT opcion_b FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_b']
            resp_c = db_execute(f"SELECT opcion_c FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_c']
            resp_d = db_execute(f"SELECT opcion_d FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_d']
            array_leido = []
            leido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido != 0 and id_notificaciones = '{id_mensajes}'")
            contleidopor = len(leido)
            array_noleido = []
            noleido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido = 0 and id_notificaciones = '{id_mensajes}'")
            contnoleidopor = len(noleido)
            try:
                opcion_a = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'A'")
                contopa = len(opcion_a)
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'B'")
                contopb = len(opcion_b)
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'C'")
                contopc = len(opcion_c)
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'D'")
                contopd = len(opcion_d)
            except:
                opcion_d = ""
                contopd = 0
            if tipo == "Comunicado":
                labels = ["Leido","No leido"]
                values = [contleidopor, contnoleidopor]
                colors = ["#1cc88a", "#e74a3b"]
            else:
                labels = ["Opcion A", "Opcion B", "Opcion C", "Opcion D"]
                values = [contopa, contopb, contopc, contopd]
                colors = ["#4e73df", "#858796", "#1cc88a", "#36b9cc"]
            array_opa = []
            array_opb = []
            array_opc = []
            array_opd = []
            for row in noleido:
                noleidopor =  (row['email_usuario_receptor'])
                array_noleido.append({'noleidopor':noleidopor})
            for rows in leido:
                leidopor =  (rows['email_usuario_receptor'])
                array_leido.append({'leidopor':leidopor})
            for row in opcion_a:
                opa = (row['email_usuario_receptor'])
                array_opa.append({'opa':opa})
            for row in opcion_b:
                opb = (row['email_usuario_receptor'])
                array_opb.append({'opb':opb})
            for row in opcion_c:
                opc = (row['email_usuario_receptor'])
                array_opc.append({'opc':opc})
            for row in opcion_d:
                opd = (row['email_usuario_receptor'])
                array_opd.append({'opd':opd})
        return render_template('detallescomunicadores.html', contopa=contopa, contopb=contopb, contopc=contopc,
                               contopd=contopd, opa=array_opa, opb=array_opb, opc=array_opc, opd=array_opd, resultado_var=resultado_var,
                               leidopor=array_leido, tipo=tipo, titulo=titulo, mensaje=mensaje, noleidopor=array_noleido,
                               contleidopor=contleidopor, contnoleidopor=contnoleidopor, resp_a=resp_a, resp_b=resp_b,
                               resp_c=resp_c, resp_d=resp_d, set=zip(values, labels, colors),
                               cont=kws['cont'], com=kws['com'], id_mensajes=id_mensajes)
    except:
        return redirect(url_for('comunicadosres'))


@app.route('/encuesta', methods=['GET', 'POST'])
@is_user
@is_logged_in
def encuesta():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    creador = dict(session)['profile']['email']
    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = hex(int(time.time()))
        titulo = request.form['enctitulo']
        mensaje = request.form['encmensaje']
        email_usuario_receptor = request.form['encdirigido']
        opcion_a =  request.form['enca']
        opcion_b = request.form['encb']
        opcion_c = request.form['encc']
        opcion_d = request.form['encd']
        array_allemails = []
        allemails = db_execute("SELECT * FROM usuarios ")
        for row in allemails:
            email = (row['email'])
            array_allemails.append({'email': email})
        if email_usuario_receptor == "Todos":
            for entry in array_allemails:
                db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo, opcion_a, opcion_b, opcion_c, opcion_d) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
                timestamp, titulo, mensaje, idmultmensaje, entry['email'], creador, 0, "Encuesta", opcion_a, opcion_b, opcion_c, opcion_d))
            return redirect(url_for('comunicados'))
        else:
            db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo, opcion_a, opcion_b, opcion_c, opcion_d) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            timestamp, titulo, mensaje, idmultmensaje, email_usuario_receptor, creador, 0, "Encuesta", opcion_a, opcion_b, opcion_c, opcion_d))
            return redirect(url_for('comunicados'))


        return redirect(url_for('comunicados'))
    return redirect(url_for('comunicados'))


@app.route('/comunicadosres', methods=['GET', 'POST'])
@usuario_notificaciones
@is_user
@is_logged_in
def comunicadosres(**kws):
    email = dict(session)['profile']['email']
    conta = db_execute(f"SELECT * FROM comunicados WHERE leido = 0 AND email_usuario_receptor = '{email}'")
    conti = len(conta)
    comuni = db_execute(f"SELECT * FROM comunicados WHERE email_usuario_receptor = '{email}' AND (leido != 2) ")
    array_comuni = []
    for row in comuni:
        id_notificaciones = (row['id_notificaciones'])
        fecha = (row['fecha'])
        titulo = (row['titulo'])
        tipo = (row['tipo'])
        mensaje = (row['mensaje'])
        leido = (row['leido'])
        array_comuni.append({'id_notificaciones': (id_notificaciones),
                          'fecha': fecha,
                          'tipo': tipo,
                          'titulo': titulo,
                          'mensaje': mensaje,
                          'leido': leido})
    return render_template('comunicadosres.html', cont=kws['cont'], com=kws['com'], comuni=array_comuni)

@app.route('/configuracion', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def configuracion(**kws):
    configuracion = db_execute("SELECT * FROM  terrazas")
    print(configuracion)
    mensualidad = int(db_execute("SELECT mensualidad FROM configuracion")[0]['mensualidad'])
    dia_de_corte = int(db_execute("SELECT dia_de_corte FROM configuracion")[0]['dia_de_corte'])
    dias_de_gracia = int(db_execute("SELECT dias_de_gracia FROM configuracion")[0]['dias_de_gracia'])
    max_tpo_qr_unico = int(db_execute("SELECT max_tpo_qr_unico FROM configuracion")[0]['max_tpo_qr_unico'])
    num_estacionamiento = int(db_execute("SELECT num_estacionamiento FROM configuracion")[0]['num_estacionamiento'])
    terrazas = int(db_execute("SELECT terrazas FROM configuracion")[0]['terrazas'])
    activa_cobros = int(db_execute("SELECT activa_cobros FROM configuracion")[0]['activa_cobros'])
    activa_terraza = int(db_execute("SELECT activa_terraza FROM configuracion")[0]['activa_terraza'])
    activa_estacionamientos = int(db_execute("SELECT activa_estacionamientos FROM configuracion")[0]['activa_estacionamientos'])
    print(terrazas)
    array_conf = []
    for row in configuracion:
        id_terrazas = (row['id_terrazas'])
        colores_terraza = (row['colores_terraza'])
        terrazas = (row['terrazas'])

        array_conf.append({'id_terrazas': id_terrazas,
                           'colores_terraza': colores_terraza,
                           'terrazas': terrazas})
    print(array_conf)
    if len(configuracion) > 0:
        return render_template('configuracion.html', terrazas=terrazas,
                               num_estacionamiento=num_estacionamiento,
                               max_tpo_qr_unico=max_tpo_qr_unico,
                               dias_de_gracia=dias_de_gracia, activa_cobros=activa_cobros,
                               configuracion=array_conf, activa_terraza=activa_terraza,
                               activa_estacionamientos=activa_estacionamientos,
                               dia_de_corte=dia_de_corte, mensualidad=mensualidad,
                               cont=kws['cont'], com=kws['com'])
    else:
        flash('No hay usuarios configuraciones', 'danger')
        return render_template('configuracion.html', configuracion=array_conf,
                               cont=kws['cont'], com=kws['com'])
    return render_template('configuracion.html', cont=kws['cont'], com=kws['com'])

@app.route('/cobros', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def cobros(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = session['profile']['email']
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    cobros = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia >= '%s';" % now)
    array_cobros = []
    for row in cobros:
        estado = (row['estado'])
        email = (row['correo'])
        nombre = (row['nombre'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])
        id_eventos = (row['id_eventos'])

        array_cobros.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'email': email,
                              'nombre': nombre,
                              'terraza': terraza,
                              'domicilio': domicilio,
                              'telefono': telefono,
                              'dia': dia})

    if len(cobros) > 0:
        return render_template('cobros.html', cobros=array_cobros, cont=kws['cont'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados'
        return render_template('cobros.html', cobros=array_cobros, msg=msg, cont=kws['cont'], com=kws['com'])

@app.route('/actconfterraza', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfterraza():
    if request.method == "POST":
        idterraza = request.form['actterrazas']
        db_execute(f"DELETE FROM terrazas WHERE id_terrazas = '{idterraza}' ")
        return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

@app.route('/actconfterraza2', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfterraza2():
    if request.method == "POST":
        agregarterraza = request.form['agregarterraza']
        colorterraza = request.form['colorselector']
        terraza_disponible = len(db_execute(f"""select * from terrazas where colores_terraza == '{colorterraza}'
UNION 
select * from terrazas where terrazas == '{agregarterraza}' 
"""))
        if terraza_disponible == 0:
            db_execute(f"INSERT INTO terrazas (terrazas, colores_terraza) values ('{agregarterraza}', '{colorterraza}')")
            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('configuracion'))
        else:
            flash(f'La terraza o color ya ha sido usado anteriormente', 'danger')
            return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

@app.route('/actconfest', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfest():
    if request.method == "POST":
        num_estacionamiento = request.form['num_estacionamiento']
        db_execute(f"UPDATE configuracion SET num_estacionamiento = '{num_estacionamiento}' ")
        return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

@app.route('/actconfduraccionqr', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfduraccionqr():
    if request.method == "POST":
        max_tpo_qr_unico = request.form['max_tpo_qr_unico']
        db_execute(f"UPDATE configuracion SET max_tpo_qr_unico = '{max_tpo_qr_unico}' ")
        return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

@app.route('/actconfmens', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfmens():
    if request.method == "POST":
        mensualidad = request.form['mensualidad']
        dia_de_corte = request.form['dia_de_corte']
        dias_de_gracia = request.form['dias_de_gracia']
        db_execute(
            f"UPDATE configuracion SET dias_de_gracia = '{dias_de_gracia}', dia_de_corte = '{dia_de_corte}', mensualidad = '{mensualidad}' WHERE id_conf = 1 ")
        return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

@app.route('/actconfcheckbox', methods=['POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def actconfcheckbox(**kws):
    ids = None
    if request.method == "POST":
        nombrecolumna = request.form['data']
        resultconf = (db_execute(f"SELECT {nombrecolumna} FROM configuracion")[0][nombrecolumna])
        if resultconf == 0:
            db_execute(f"UPDATE configuracion SET '{nombrecolumna}' = 1")
            return redirect(url_for('configuracion'))
        elif resultconf == 1:
            db_execute(f"UPDATE configuracion SET '{nombrecolumna}' = 0")
            return redirect(url_for('configuracion'))
    return redirect(url_for('configuracion'))

# De aqui para abajo creo que es basura, pero nos puede servir para ver como insertar en la BD
@app.route('/articles')
def articles():
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if int(result.rowcount) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


# Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)


# unique


@app.route('/unique', methods=['GET', 'POST'])
def unique():
    if request.method == 'POST':
        user = request.form['fingerprint']
    return render_template('unique.html')


# Dashboard
@app.route('/dashboardpaborrar')
@is_logged_in
@is_user
def dashboardpaboorar():
    mysql = sqlite3.connect('qr.db')
    # Create cursor
    cur = mysql.cursor()

    # Get articles
    # result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in
    result = cur.execute("SELECT * FROM articles WHERE author = \"%s\"" % session['username'])

    articles = cur.fetchall()

    array = []
    for row in articles:
        id = (row[0])
        title = (row[1])
        body = (row[2])
        author = (row[3])

        array.append({'id': int(id),
                      'title': title,
                      'body': body,
                      'author': author})

    print(array)

    print(result.rowcount)
    if int(len(array)) > 0:
        return render_template('dashboardpaborrar.html', articles=array)
    else:
        msg = 'No Articles Found'
        return render_template('dashboardpaborrar.html', msg=msg)
    # Close connection
    cur.close()


# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])


# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        mysql = sqlite3.connect('qr.db')
        cur = mysql.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(\"%s\", \"%s\", \"%s\")" % (
        title, body, session['username']))

        # Commit to DB
        mysql.commit()

        # Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get article by id

    article = cur.execute("SELECT * FROM articles WHERE article_id = \"%s\"" % id).fetchall()

    # Get form
    form = ArticleForm(request.form)

    art = []

    print(article)

    for row in article:
        id = (row[0])
        title = (row[1])
        body = (row[2])
        author = (row[3])

        art.append({'id': int(id),
                    'title': title,
                    'body': body,
                    'author': author})

    cur.close()
    # Populate article form fields
    form.title.data = art[0]['title']
    form.body.data = art[0]['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.cursor()
        app.logger.info(title)
        # Execute
        cur.execute("UPDATE articles SET title=\"%s\", body=\"%s\" WHERE article_id=\"%s\"" % (title, body, id))
        # Commit to DB
        mysql.commit()

        # Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)


# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE article_id = \"%s\"" % id)

    # Commit to DB
    mysql.commit()

    # Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

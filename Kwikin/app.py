from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file, send_from_directory, jsonify
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, SelectField, IntegerField, HiddenField
from authlib.integrations.flask_client import OAuth
from auth_decorator import is_logged_in, is_user
import os
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


#../templates', static_folder='../static'
application = app = Flask(__name__, template_folder='templates', static_folder='static')
qrcode = QRcode(app)

# Config MySQL
#obj = AES.new('This is a key123'.encode("utf8"), AES.MODE_CBC, 'This is an IV456'.encode("utf8"))

# init MYSQL
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
    userinfo_endpoint='https://www.googleapis.com/userinfo/v2/me',  # This is only needed if using openId to fetch user info
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
    return redirect(url_for('dashboard'))
# Index
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/ayudabulk', methods=["GET", "POST"])
def ayudabulk():
    name = session['profile']['name']
    picture = session['profile']['picture']
    return render_template('ayudabulk.html', name=name, picture=picture)

@app.route('/dashboard')
@is_user
@is_logged_in
def dashboard():
    name = session['profile']['name']
    picture = session['profile']['picture']
    return render_template('dashboard.html', name=name, picture=picture)


@app.route('/scannerqr')
def scannerqr():
    name = dict(session)['profile']['name']
    email = dict(session)['profile']['email']
    picture = dict(session)['profile']['picture']
    return render_template('scannerqr.html', name=name, picture=picture)

@app.route('/scannerqrs')
def scannerqrs():
    name = dict(session)['profile']['name']
    email = dict(session)['profile']['email']
    picture = dict(session)['profile']['picture']
    return render_template('scannerqrs.html', name=name, picture=picture)

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return render_template('login.html')

@app.route('/crearqr', methods=['GET', 'POST'])
@is_logged_in
def peticionqr():
    name = session['profile']['name']
    picture = session['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    email = session['profile']['email']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = str(now)
    array_qr = []
    result = cur.execute(f"""SELECT * FROM qr WHERE id_qr in (
SELECT id_qr FROM asoc_qr_usuario WHERE id_usuario = (
SELECT id_usuario FROM usuarios where email = '{email}'
));""")
    qr = cur.fetchall()

    for row in qr:
        Nombre = (row[4])
        Entrada = (row[2])
        Salida = (row[3])
        email_qr = (row[5])
        placas = (row[6])
        entrada_real = (row[7])
        fin_real = (row[8])
        estado = (row[9])
        id_qr = (row[1])

        array_qr.append({'Nombre': Nombre,
                    'Entrada': Entrada,
                    'Salida': Salida,
                    'entrada_real': entrada_real,
                    'fin_real': fin_real,
                    'estado': estado,
                    'email': email_qr,
                    'placas': placas,
                    'id_qr': id_qr})

    
    if request.method == 'POST':
        tzone = ct.strftime("%Y-%m-%dT%H:%M")
        qr_ent = str(request.form['dateE'])
        qr_sal = str(request.form['dateS'])
        if qr_ent != '' and qr_sal == '' :
            dateent = datetime.strptime(qr_ent,"%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_ent, "%Y-%m-%dT%H:%M") + timedelta(days=1)
        elif qr_ent == '' and qr_sal != '':
            dateent = datetime.strptime(str(tzone),"%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_sal, "%Y-%m-%dT%H:%M")
        elif qr_ent == '' and qr_sal == '':
            dateent = datetime.strptime(str(tzone),"%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(str(tzone),"%Y-%m-%dT%H:%M") + timedelta(days=1)
        elif qr_ent != '' and qr_sal != '':
            dateent = datetime.strptime(qr_ent,"%Y-%m-%dT%H:%M")
            datesal = datetime.strptime(qr_sal,"%Y-%m-%dT%H:%M") + timedelta(days=1)
        if dateent > datesal or datesal < datetime.strptime(str(tzone),"%Y-%m-%dT%H:%M")+timedelta(minutes=1):
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
        codigo_qr = hex(int(time.time() * 100))
        qr = qrcode(codigo_qr, mode="raw", start_date=fecha_entrada, end_date=fecha_salida)
        try:
            cur.execute("INSERT INTO qr(codigo_qr, visitante, inicio, fin, placas, correo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            codigo_qr, nombre, fecha_entrada, fecha_salida, placas, emailqr))
            mysql.commit()
            insert_asoc_qr_usuario = f"""INSERT INTO asoc_qr_usuario(id_usuario, id_qr) VALUES 
    (
    (SELECT id_usuario FROM usuarios where email = '{email}'),
    (SELECT id_qr FROM qr where codigo_qr = '{codigo_qr}')
    );"""
            cur.execute(insert_asoc_qr_usuario)
            mysql.commit()
            cur.close()
        except:
            flash(f'Codigo no creado correctamente', 'danger')
            return render_template('crearpeticionqr.html', qr=array_qr, name=name, picture=picture, now=now)
        qr_data = send_file(qr, mimetype="image/png")
        return redirect(url_for('codigoqr', qr_data=codigo_qr, start_date=fecha_entrada, end_date=fecha_salida))

    return render_template('crearpeticionqr.html', qr=array_qr, name=name, now=now)


@app.route('/codigoqr', methods=['GET'] )
@is_user
@is_logged_in
def codigoqr():
    picture = session['profile']['picture']
    if request.method == 'GET':
        qr_data = request.args.get('qr_data')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        return render_template('codigoqr.html', qr_data=qr_data, mode="raw", start_date=start_date,
                         end_date=end_date, picture=picture)

@app.route('/crearInd', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def crearInd():
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
                    cur.execute(f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
                    flash(f'Usuario {email} agregado correctamente', 'success')
                    mysql.commit()
                except:
                    flash(f'Correo {email} ya existe','danger')
        else:
            flash(f'El correo {email} es incorrecto, por favor valida que sea Gmail', 'danger')
        cur.close()
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    return redirect(url_for('gestionusuarios', name=name, picture=picture))


@app.route('/crearBulk', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def upload():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
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
                        cur.execute(f"INSERT INTO usuarios(domicilio, email, telefono) VALUES('{domicilio}','{email}','{telefono}')")
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
        return render_template('crearbulk.html', name=name, picture=picture)
    return render_template('crearbulk.html', name=name, picture=picture)

@app.route('/gestionusuarios', methods=['GET', 'POST', 'UPDATE'] )
@is_user
@is_logged_in
def gestionusuarios():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    result = cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()
    array = []
    for row in usuarios:
        status = (row[4])
        email = (row[3])
        nombre = (row[1])
        domicilio = (row[5])

        array.append({'status': (status),
                      'email': email,
                      'nombre': nombre,
                      'domicilio': domicilio})
    if int(result.rowcount) > 0:
        return render_template('gestionusuarios.html', usuarios=array, name=name, picture=picture)
    else:
        msg = 'No hay usuarios asociados al coto'
        return render_template('gestionusuarios.html', usuarios=array, name=name, picture=picture,msg=msg)
    cur.close()

@app.route('/actusuario', methods=['POST'])
@is_user
@is_logged_in
def actusuario():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    ids = None
    if request.method == "POST":
        ids=request.form['data']
        result = cur.execute("SELECT status FROM usuarios WHERE email = '%s';" % ids)
        result = cur.fetchone()
        if str(result) == "('Activo',)":
            cur.execute("UPDATE usuarios SET status = 'Inactivo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html',  name=name, picture=picture)
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html', name=name, picture=picture)
    cur.close()
    return render_template('gestionusuarios.html', name=name, picture=picture)


@app.route('/actdom', methods=['POST'])
@is_user
@is_logged_in
def actdom():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    ids = None
    if request.method == "POST":
        ids=request.form['data']
        result = cur.execute("SELECT status FROM usuarios WHERE email = '%s';" % ids)
        result = cur.fetchone()
        if str(result) == "('Activo',)":
            cur.execute("UPDATE usuarios SET status = 'Inactivo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestiondimicilios.html',  name=name, picture=picture)
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestiondimicilios.html', name=name, picture=picture)
    cur.close()
    return render_template('gestiondimicilios.html', name=name, picture=picture)

@app.route('/actqr', methods=['POST'])
@is_user
@is_logged_in
def actqr():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = str(now)
    array_qr = []
    result = cur.execute(f"""SELECT * FROM qr WHERE id_qr in (
    SELECT id_qr FROM asoc_qr_usuario WHERE id_usuario = (
    SELECT id_usuario FROM usuarios where email = '{email}'
    ));""")
    qr = cur.fetchall()

    for row in qr:
        Nombre = (row[4])
        Entrada = (row[2])
        Salida = (row[3])
        emailvis = (row[5])
        placas = (row[6])
        entrada_real = (row[7])
        fin_real = (row[8])
        estado = (row[9])
        id_qr = (row[1])

        array_qr.append({'Nombre': Nombre,
                         'Entrada': Entrada,
                         'Salida': Salida,
                         'entrada_real': entrada_real,
                         'fin_real': fin_real,
                         'estado': estado,
                         'emailvis': emailvis,
                         'placas': placas,
                         'id_qr': id_qr})

    if request.method == "POST":
        qrid = request.form['dataqr']
        result = cur.execute("SELECT estado FROM qr WHERE codigo_qr = '%s';" % qrid)
        result = cur.fetchone()
        print(qrid)
        try:
            cur.execute("UPDATE qr SET estado = 'Inactivo' WHERE codigo_qr = '%s';" % qrid)
            mysql.commit()
            return render_template('gestionusuarios.html', name=name, picture=picture)
        except:
            flash(f'No se pudo eliminar el registro', 'danger')
            return render_template('gestionusuarios.html', name=name, picture=picture)
    cur.close()
    return render_template('crearpeticionqr.html', name=name, picture=picture)

@app.route('/ventas', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def ventas():
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
            cur.execute(f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
            mysql.commit()
        except:
            flash(f'El correo {email} no pudo asociar un grupo, contacta un administrador', 'danger')
        cur.close()
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    return render_template('ventas.html', name=name, picture=picture)

@app.route('/crearventa', methods=['GET', 'POST'])
@is_user
@is_logged_in
def crearventa():
    Cotopy = request.form['Coto']
    CotoDirpy = request.form['CotoDir']
    CotoCPpy = request.form['CotoCP']
    correopy = request.form['correo']
    teladminpy = request.form['teladmin']
    vendedorpy = dict(session)['profile']['email'] #esta variable sirve para saber quien creo el coto y poder mapearlo
    print(Cotopy, CotoDirpy, CotoCPpy, correopy, teladminpy, vendedorpy)
    return render_template("ventas.html")
    '''db.execute(
        "INSERT INTO events (user_id, title, description, place, start, end) VALUES (:user, :title, :description, :place, :start, :end)",
        user=session["user_id"], title=title, description=description, place=place, start=start, end=end)'''

@app.route('/validarqr', methods=['GET', 'POST'])
@is_user
@is_logged_in
def validarqr():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    if request.method == 'GET':
        qrval = request.args.get('qr')
        result = cur.execute("SELECT * FROM qr WHERE codigo_qr = '%s';" % qrval)
        qrinfo = cur.fetchall()
        print(qrinfo[0])
        qrid = int(qrinfo[0][0])
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
                    cur.execute("INSERT INTO asoc_qr_registro (id_qr, timestamp, type) VALUES(\"%s\", \"%s\", \"%s\")" % (
                        qrid, timestamp, tipo))
                    mysql.commit()
                    cur.close()
                    return render_template("aprobado.html", name=name, picture=picture)
                else:
                    flash(f'el código ha sido cancelado', 'danger')
                    return render_template("noaprobado.html", name=name, picture=picture)
            else:
                flash(f'Las fechas no son validas', 'danger')
                return render_template("noaprobado.html", name=name, picture=picture)
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("noaprobado.html", name=name, picture=picture)


@app.route('/validarqrs', methods=['GET', 'POST'])
@is_user
@is_logged_in
def validarqrs():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    if request.method == 'GET':
        qrval = request.args.get('qrs')
        result = cur.execute("SELECT * FROM qr WHERE codigo_qr = '%s';" % qrval)
        qrinfo = cur.fetchall()
        print(qrinfo[0])
        qrid = int(qrinfo[0][0])
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
            return render_template("aprobado.html", name=name, picture=picture)
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("noaprobado.html", name=name, picture=picture)
    return render_template("dashboard.html", name=name, picture=picture)


@app.route('/calendar-events')
def calendar_events():
    picture = session['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cursor = mysql.cursor()
    try:
        cursor.execute("SELECT id, titulo, casa, UNIX_TIMESTAMP(start_date)*1000 as start, UNIX_TIMESTAMP(end_date)*1000 as end FROM event FROM eventos")
        rows = cursor.fetchall()
        resp = jsonify({'success' : 1, 'result' : rows})
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    finally:
        mysql.commit()
        cursor.close()
    return render_template('calendar_events.html', rows=rows, picture=picture)



@app.route('/calendario')
def calendario():
    picture = session['profile']['picture']
    return render_template('calendar_events.html', picture=picture)


@app.route('/calendario_ini/remote')
def calendario_ini():
    test_cal = ''
    if request.method == 'GET':
        callback = request.args.get('callback')
        print(callback)
    if callback in "in mbsc_jsonp_comp_demo-responsive-month-view":
        test_cal = '''try { window['mbsc_jsonp_comp_demo-responsive-month-view']('{"calendar":{},"datetime":{"wheels":[[{"cssClass":"mbsc-dt-whl-d","label":"Día","data":[{"value":1,"display":"1"},{"value":2,"display":"2"},{"value":3,"display":"3"},{"value":4,"display":"4"},{"value":5,"display":"5"},{"value":6,"display":"6"},{"value":7,"display":"7"},{"value":8,"display":"8"},{"value":9,"display":"9"},{"value":10,"display":"10"},{"value":11,"display":"11"},{"value":12,"display":"12"},{"value":13,"display":"13"},{"value":14,"display":"14"},{"value":15,"display":"15"},{"value":16,"display":"16"},{"value":17,"display":"17"},{"value":18,"display":"18"},{"value":19,"display":"19"},{"value":20,"display":"20"},{"value":21,"display":"21"},{"value":22,"display":"22"},{"value":23,"display":"23"},{"value":24,"display":"24"},{"value":25,"display":"25"},{"value":26,"display":"26"},{"value":27,"display":"27"},{"value":28,"display":"28"},{"value":29,"display":"29"},{"value":30,"display":"30"},{"value":31,"display":"31"}]},{"cssClass":"mbsc-dt-whl-m","label":"Mes","data":[{"value":0,"display":"<span class=\\\\"mbsc-dt-month\\\\">Enero</span>"},{"value":1,"display":"<span class=\\\\"mbsc-dt-month\\\\">Febrero</span>"},{"value":2,"display":"<span class=\\\\"mbsc-dt-month\\\\">Marzo</span>"},{"value":3,"display":"<span class=\\\\"mbsc-dt-month\\\\">Abril</span>"},{"value":4,"display":"<span class=\\\\"mbsc-dt-month\\\\">Mayo</span>"},{"value":5,"display":"<span class=\\\\"mbsc-dt-month\\\\">Junio</span>"},{"value":6,"display":"<span class=\\\\"mbsc-dt-month\\\\">Julio</span>"},{"value":7,"display":"<span class=\\\\"mbsc-dt-month\\\\">Agosto</span>"},{"value":8,"display":"<span class=\\\\"mbsc-dt-month\\\\">Septiembre</span>"},{"value":9,"display":"<span class=\\\\"mbsc-dt-month\\\\">Octubre</span>"},{"value":10,"display":"<span class=\\\\"mbsc-dt-month\\\\">Noviembre</span>"},{"value":11,"display":"<span class=\\\\"mbsc-dt-month\\\\">Diciembre</span>"}]},{"cssClass":"mbsc-dt-whl-y","label":"A&ntilde;o","data":"function getYearValue(i, inst) {\\\\r\\\\n    var s = inst.settings;\\\\r\\\\n    return {\\\\r\\\\n      value: i,\\\\r\\\\n      display: (/yy/i.test(s.dateDisplay) ? i : (i + \\'\\').substr(2, 2)) + (s.yearSuffix || \\'\\')\\\\r\\\\n    };\\\\r\\\\n  }","getIndex":"function getYearIndex(v) {\\\\r\\\\n    return v;\\\\r\\\\n  }"}]],"wheelOrder":{"d":0,"m":1,"y":2},"isoParts":{"y":1,"m":1,"d":1}},"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div>"}'); } catch (ex) {}'''
    elif "mbsc_jsonp_comp_" in callback:
        id_num_cal = str(callback).replace("mbsc_jsonp_comp_",'')
        head_cal = ("try { window['mbsc_jsonp_comp_" + id_num_cal +  "']")
        tail_cal = '''('{"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-persp\\\\"><div role=\\\\"dialog\\\\" class=\\\\"mbsc-fr-scroll\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-focus\\\\" tabindex=\\\\"-1\\\\"></div><div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div></div></div>"}'); } catch (ex) {}'''
        test_cal = head_cal + tail_cal
    return test_cal


@app.route('/calendario_data')
def test_calendario():
    if request.method == 'GET':
        coto = request.args.get('coto')
        print(coto)

    test = '''try {
    mbscjsonp1([{
                "start": "2020-10-12T07:00:00.000Z",
                "end": "2020-10-12T08:00:00.000Z",
                "text": "Area Comun.",
                "color": "#f67944"
            }, {
                "start": "2020-10-13T07:00:00.000Z",
                "end": "2020-10-13T07:15:00.000Z",
                "text": "Terraza Wifi",
                "color": "#6e7f29"
            }, {
                "start": "2020-10-13T07:00:00.000Z",
                "end": "2020-10-13T07:15:00.000Z",
                "text": "Terraza Alberca",
                "color": "#6e7f29"
            }, {
                "start": "2020-10-13T07:00:00.000Z",
                "end": "2020-10-13T07:15:00.000Z",
                "text": "Area Comun",
                "color": "#6e7f29"
            }, {
                "start": "2020-10-12T07:00:00.000Z",
                "end": "2020-10-13T07:15:00.000Z",
                "text": "Terraza Wifi",
                "color": "#6e7f29"
            },
        ]);
} catch (ex) {}'''
    return test

@app.route('/avisodeprivacidad')
def avisodeprivacidad():
    return render_template('avisodeprivacidad.html')

@app.route('/crearevento', methods=['GET', 'POST'])
@is_logged_in
def peticionevento():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
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
                    cur.execute("INSERT INTO eventos(terraza, nombre, correo, dia) VALUES(\"%s\", \"%s\", \"%s\", \"%s\")" % (
                    terraza, name, email, fechaevento))

                    mysql.commit()
                    flash(f'Evento guardado correctamente, recibiras un correo cuando el administrador lo apruebe', 'success')
                    #insert_asoc_qr_usuario = f"""INSERT INTO asoc_qr_usuario(id_usuario, id_qr, id_coto) VALUES
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
                    return render_template('calendar_events.html', name=name, picture=picture, now=now)
                return render_template('calendar_events.html', name=name, picture=picture, now=now)
        except:
            flash(f'Revisa todos los campos', 'danger')
            return render_template('calendar_events.html', name=name, picture=picture, now=now)

    return render_template('calendar_events.html', name=name, picture=picture, now=now)

@app.route('/gestioneventos', methods=['GET', 'POST', 'UPDATE'] )
@is_user
@is_logged_in
def gestioneventos():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = datetime.strftime((now),"%Y-%m-%d")
    result = cur.execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia >= '%s';" % now)
    eventos = cur.fetchall()
    array_eventos = []
    for row in eventos:
        estado = (row[5])
        email = (row[3])
        nombre = (row[2])
        terraza = (row[1])
        dia = (row[4])
        domicilio = (row[11])
        telefono = (row[13])
        id_eventos = (row[0])

        array_eventos.append({'estado': (estado),
                      'id_eventos': id_eventos,
                      'email': email,
                      'nombre': nombre,
                      'terraza': terraza,
                      'domicilio': domicilio,
                      'telefono' : telefono,
                      'dia': dia})

    if int(result.rowcount) > 0:
        return render_template('gestioneventos.html', eventos=array_eventos, name=name, picture=picture)
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('gestioneventos.html', eventos=array_eventos, name=name, picture=picture,msg=msg)

    cur.close()

@app.route('/acteventos', methods=['POST'])
@is_user
@is_logged_in
def acteventos():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    result1 = cur.execute(
        "SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia >= '%s';" % now)
    eventos = cur.fetchall()
    array_eventos = []
    if request.method == "POST":
        eventsvalue = request.form['mycheckboxE']
        eventsid = request.form['idhidden']
        terraza = request.form['terrazahidden']
        cur.execute("SELECT dia FROM eventos WHERE id_eventos = '%s';" % eventsid)
        dia = cur.fetchone()
        print(eventsvalue)
        print(eventsid)
        print(terraza)
        print(dia[0])
        print(f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia[0]}' AND estado = 'Aprobado'")
        validador = cur.execute(f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia[0]}' AND estado = 'Aprobado'").fetchone()
        print(validador)
        if validador != None and eventsvalue == 'Aprobado':
            flash(f'La terraza {terraza} ya esta apartada el dia {dia[0]}, revisa fecha', 'danger')
            return redirect(url_for('gestioneventos'))
        else:
            cur.execute("UPDATE eventos SET estado =\"%s\"  WHERE id_eventos =\"%s\";" % (eventsvalue, eventsid))
            mysql.commit()
            cur.execute(
                "SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia >= '%s';" % now)
            eventos = cur.fetchall()
            flash(f'La terraza {terraza} fue  cambiada a {eventsvalue} el dia {dia[0]} con éxito', 'success')
            array_eventos = []
            cur.close()

            for row in eventos:
                estado = (row[5])
                email = (row[3])
                nombre = (row[2])
                terraza = (row[1])
                dia = (row[4])
                domicilio = (row[11])
                telefono = (row[13])
                id_eventos = (row[0])

                array_eventos.append({'estado': (estado),
                                      'id_eventos': id_eventos,
                                      'email': email,
                                      'nombre': nombre,
                                      'terraza': terraza,
                                      'domicilio': domicilio,
                                      'telefono': telefono,
                                      'dia': dia})
            return render_template('gestioneventos.html', eventos=array_eventos, name=name, picture=picture)
    return render_template('gestioneventos.html', eventos=array_eventos, name=name, picture=picture)


@app.route('/gestioneventoshistorico', methods=['GET', 'POST', 'UPDATE'] )
@is_user
@is_logged_in
def gestioneventoshistorico():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = dict(session)['profile']['email']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = str(now)
    result = cur.execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia < '%s';" % now)
    eventos = cur.fetchall()
    array = []
    for row in eventos:
        estado = (row[5])
        email = (row[3])
        nombre = (row[2])
        terraza = (row[1])
        dia = (row[4])
        domicilio = (row[11])
        telefono = (row[13])
        id_eventos = (row[0])

        array.append({'estado': (estado),
                      'id_eventos': id_eventos,
                      'email': email,
                      'nombre': nombre,
                      'terraza': terraza,
                      'domicilio': domicilio,
                      'telefono' : telefono,
                      'dia': dia})

    if int(result.rowcount) > 0:
        return render_template('gestioneventoshistorico.html', eventos=array, name=name, picture=picture)
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('gestioneventoshistorico.html', eventos=array, name=name, picture=picture,msg=msg)
    cur.close()


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


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)






#unique


@app.route('/unique', methods=['GET', 'POST'])
def unique():
    if request.method == 'POST':
        user = request.form['fingerprint']
        print(user)
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
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = \"%s\"" % session['username'])

    articles = cur.fetchall()

    array = []
    for row in articles:
        id = (row[0])
        title = (row[1])
        body = (row[2])
        author = (row[3])

        array.append({'id' : int(id),
                      'title' : title,
                      'body' : body,
                      'author' : author})

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
        cur.execute("INSERT INTO articles(title, body, author) VALUES(\"%s\", \"%s\", \"%s\")" % (title, body, session['username']))

        # Commit to DB
        mysql.commit()

        #Close connection
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

        art.append({'id' : int(id),
                      'title' : title,
                      'body' : body,
                      'author' : author})

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
        cur.execute ("UPDATE articles SET title=\"%s\", body=\"%s\" WHERE article_id=\"%s\"" % (title, body, id))
        # Commit to DB
        mysql.commit()

        #Close connection
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

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

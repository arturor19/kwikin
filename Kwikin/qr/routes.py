from flask import render_template, flash, redirect, url_for, session, request, Blueprint, send_file, Flask
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from datetime import timedelta, datetime
from config import db
from bson import ObjectId
from flask_qrcode import QRcode
import json, secrets
import pytz



application = app = Flask(__name__, template_folder='templates')
qrcode = QRcode(app)
qr = Blueprint('qr', __name__, template_folder='templates', static_folder='Kwikin/static')


@qr.route('/scannerqr')
@is_user
@is_logged_in
@usuario_notificaciones
def scannerqr(**kws):
    return render_template('qr/scannerqr.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@qr.route('/scannerqrs')
@is_user
@is_logged_in
@usuario_notificaciones
def scannerqrs(**kws):
    return render_template('qr/scannerqrs.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])




@qr.route('/crearqr', methods=['GET', 'POST'])

@is_logged_in
@usuario_notificaciones
def peticionqr(**kws):
    resp = json.loads(session['profile'])
    print(resp)
    correo = (resp['correo'])
    coto = (resp['coto'])
    id_usuario = (resp['_id'])
    qr_colec = db.qr
    max_tpo_qr = db.cotos.find_one({"coto_nombre":coto},{"_id":0,"max_tpo_qr_unico":1})['max_tpo_qr_unico']
    print(max_tpo_qr)
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    now = ct
    array_qr = []
    qr = qr_colec.find({"$and":[{"creador": ObjectId(id_usuario)},{"estado":"Activo"},{"fin":{"$gte":now}}]})
    for row in qr:
        Nombre = (row['visitante'])
        Entrada = (row['inicio'])
        Salida = (row['fin'])
        email_qr = (row['correo_visitante'])
        placas = (row['placas'])
        entrada_real = (row['inicio_real'])
        fin_real = (row['fin_real'])
        estado = (row['estado'])
        id_qr = (row['_id'])
        estado_acceso = (row['estado_acceso'])
        codigo_qr = (row['codigo_qr'])
        coto_reg = (row['coto'])

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
                         'coto_reg' : coto_reg,
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
        elif datesal - dateent > timedelta(days=max_tpo_qr):
            flash(f'Recuerda que los accesos se otorgan sólo por {max_tpo_qr} días', 'danger')
        elif request.form['nombreqr'] == "":
            flash('Por favor agrega nombre', 'danger')
        fecha_entrada = dateent
        fecha_salida = datesal
        nombre = request.form['nombreqr']
        placas = request.form['placasqr']
        emailqr = request.form['emailqr']
        tipoqr = request.form['tipoqr']
        coto = coto
        timestamp = now
        codigo_qr = secrets.token_urlsafe(10)
        print(codigo_qr)
        qr = qrcode(codigo_qr, mode="raw", start_date=fecha_entrada, end_date=fecha_salida)
        try:
            qr_colec.insert_one({"codigo_qr": codigo_qr, "visitante": nombre, "inicio": fecha_entrada,
                                 "fin": fecha_salida, "correo_visitante": emailqr, "placas": placas,
                                 "inicio_real":"", "fin_real":"", "estado": "Activo", "timestamp":now,
                                 "tipo":tipoqr, "estado_acceso":"", "autobloqueo":"", "coto":coto, "creador":ObjectId(id_usuario)})

        except:
            flash(f'Codigo no creado correctamente', 'danger')
            return redirect(url_for('qr.peticionqr', qr_array=array_qr))
        qr_data = send_file(qr, mimetype="image/png")
        return redirect(url_for('qr.codigoqr', qr_data=codigo_qr, start_date=fecha_entrada, end_date=fecha_salida, qr_array=array_qr))

    return render_template('qr/crearpeticionqr.html', qr_array=array_qr, now=now,  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@qr.route('/codigoqr', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def codigoqr(**kws):
    if request.method == 'GET':
        qr_data = request.args.get('qr_data')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        return render_template('qr/codigoqr.html', qr_data=qr_data, mode="raw", start_date=start_date,
                               end_date=end_date,  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@qr.route('/actestadoqr', methods=['POST'])
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
            return redirect(url_for('qr.peticionqr'))
        elif str(result) == "Inactivo":
            db_execute("UPDATE qr SET estado = 'Activo' WHERE id_qr = '%s';" % ids)
            return redirect(url_for('qr.peticionqr'))
    return redirect(url_for('qr.peticionqr'))

@qr.route('/actestadoaccesoqr', methods=['POST'])
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
            return redirect(url_for('qr.peticionqr'))
    return redirect(url_for('qr.peticionqr'))

@qr.route('/gestionqrhistorico', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestionqrhistorico(**kws):
    resp = json.loads(session['profile'])
    id_usuario = (resp['_id'])
    qr_colec = db.qr
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    now = ct
    array_qrh = []
    qrh = qr_colec.find({"$and": [{"creador": ObjectId(id_usuario)}, {"estado": "Activo"}, {"fin": {"$lt": now}}]})
    for row in qrh:
        Nombre = (row['visitante'])
        Entrada = (row['inicio'])
        Salida = (row['fin'])
        email_qr = (row['correo_visitante'])
        placas = (row['placas'])
        entrada_real = (row['inicio_real'])
        fin_real = (row['fin_real'])
        estado = (row['estado'])
        id_qr = (row['_id'])
        estado_acceso = (row['estado_acceso'])
        codigo_qr = (row['codigo_qr'])

        array_qrh.append({'Nombre': Nombre,
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
    return render_template('qr/crearpeticionqrhistorico.html', qrh=array_qrh, now=now, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@qr.route('/actqr', methods=['POST','GET'])
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
                return redirect(url_for('qr.peticionqr', qr=array_qrh))
            except:
                flash(f'No se pudo actualizar el registro', 'danger')
                return redirect(url_for('qr.peticionqr', qr=array_qrh))
        elif request.form['actqr'] == 'ver':
            if request.method == 'POST':
                codigo_qr = request.form['qrhidden']
                fecha_entrada = request.form['starthidden']
                fecha_salida = request.form['endhidden']
                return redirect(
                    url_for('qr.codigoqr', qr_data=codigo_qr, start_date=fecha_entrada, end_date=fecha_salida))
    return redirect(url_for('qr.peticionqr', qr=array_qrh))


@qr.route('/validarqr', methods=['GET', 'POST'])
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
            return render_template("qr/noaprobado.html", cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
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
                    return render_template("qr/aprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
                else:
                    flash(f'el código ha sido cancelado', 'danger')
                    return render_template("qr/noaprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
            else:
                flash(f'Las fechas no son validas', 'danger')
                return render_template("qr/noaprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("qr/noaprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@qr.route('/validarqrs', methods=['GET', 'POST'])
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
            return render_template("noaprobado.html", cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
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
            return render_template("qr/aprobado.html", cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("qr/noaprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    return render_template("main/dashboard.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


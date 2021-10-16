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
    cotos = db.cotos
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    id_usuario = (resp['_id'])
    qr_colec = db.qr
    try:
        max_tpo_qr = db.cotos.find_one({"coto_nombre":coto},{"_id":0,"max_tpo_qr_unico":1})['max_tpo_qr_unico']
    except:
        max_tpo_qr = 0
        flash(f'Favor de configurar los parámetros de maximo tiempo QR en configuracion', 'danger')
    print(max_tpo_qr)
    check_tz = cotos.find_one({"coto_nombre":coto},{"_id":0,"zona_horaria":1})['zona_horaria']
    tz = pytz.timezone(check_tz)
    ct = datetime.now(tz=tz)
    now = ct
    array_qr = []
    qr_obj = qr_colec.find({"$and":[{"creador": ObjectId(id_usuario)},{"estado":"Activo"},{"fin":{"$gte":now}}]})
    for row in qr_obj:
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
        print(fecha_entrada)
        fecha_salida = datesal
        nombre = request.form['nombreqr']
        placas = request.form['placasqr']
        emailqr = request.form['emailqr']
        tipoqr = request.form['tipoqr']
        coto = coto
        codigo_qr = secrets.token_urlsafe(10)
        try:
            qr_colec.insert_one({"codigo_qr": codigo_qr, "visitante": nombre, "inicio": fecha_entrada,
                                 "fin": fecha_salida, "correo_visitante": emailqr, "placas": placas,
                                 "inicio_real":"", "fin_real":"", "estado": "Activo", "timestamp":now,
                                 "tipo":tipoqr, "estado_acceso":"", "autobloqueo":"", "coto":coto, "creador":ObjectId(id_usuario)})

        except:
            flash(f'Codigo no creado correctamente', 'danger')
            return redirect(url_for('qr.peticionqr', qr_array=array_qr))
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

@is_logged_in
def actestadoqr():
    ids = None
    qr_colec = db.qr
    if request.method == "POST":
        ids = request.form['data']
        result = qr_colec.find_one({"_id":ObjectId(ids)},{"_id":0,"estado":1})['estado']
        print(result)
        if result == "Activo":
            qr_colec.find_one_and_update({"_id":ObjectId(ids)},{"$set":{"estado":"Inactivo"}})
            return redirect(url_for('qr.peticionqr'))
        elif result == "Inactivo":
            qr_colec.find_one_and_update({"_id":ObjectId(ids)},{"$set":{"estado":"Activo"}})
            return redirect(url_for('qr.peticionqr'))
    return redirect(url_for('qr.peticionqr'))

@qr.route('/actestadoaccesoqr', methods=['POST'])
@is_user
@is_logged_in
def actestadoaccesoqr():
    ids = None
    qr_colec = db.qr
    if request.method == "POST":
        ids = request.form['data']
        result = qr_colec.find_one({"_id":ObjectId(ids)},{"_id":0,"estado_acceso":1})['estado_acceso']
        print(result)
        if result == "Entro":
            qr_colec.find_one_and_update({"_id":ObjectId(ids)},{"$set":{"estado_acceso":"Salio"}})
            return redirect(url_for('peticionqr'))
        elif result == "Salio":
            qr_colec.find_one_and_update({"_id":ObjectId(ids)},{"$set":{"estado_acceso":"Entro"}})
            return redirect(url_for('qr.peticionqr'))
    return redirect(url_for('qr.peticionqr'))

@qr.route('/gestionqrhistorico', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestionqrhistorico(**kws):
    cotos = db.cotos
    resp = json.loads(session['profile'])
    id_usuario = (resp['_id'])
    qr_colec = db.qr
    coto = (resp['coto'])
    check_tz = cotos.find_one({"coto_nombre": coto}, {"_id": 0, "zona_horaria": 1})['zona_horaria']
    tz = pytz.timezone(check_tz)
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
    qr_colec = db.qr
    cotos = db.cotos
    resp = json.loads(session['profile'])
    id_usuario = (resp['_id'])
    coto = (resp['coto'])
    check_tz = cotos.find_one({"coto_nombre": coto}, {"_id": 0, "zona_horaria": 1})['zona_horaria']
    tz = pytz.timezone(check_tz)
    ct = datetime.now(tz=tz)
    now = ct
    array_qrh = []
    qrh = qr_colec.find({"$and": [{"creador": ObjectId(id_usuario)}, {"estado": "Activo"}, {"fin": {"$gte": now}}]})
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
    if request.method == "POST":
        if request.form['actqr'] == 'act':
            qrid = request.form['idqrhidden']
            visitante = request.form['codigovisitante']
            correo_visitante = request.form['codigoemailvisitante']
            placas_visitante = request.form['codigoplacas']
            entrada_visitante = request.form['codigoEntrada']
            salida_visitante = request.form['codigoSalida']
            entrada_visitante = datetime.strptime(entrada_visitante, "%Y-%m-%d %H:%M:%S")
            salida_visitante = datetime.strptime(salida_visitante, "%Y-%m-%d %H:%M:%S")

            try:
                qr_colec.find_one_and_update({"_id": ObjectId(qrid)}, {"$set":
                                            {"visitante":visitante, "correo_visitante":correo_visitante,
                                             "placas":placas_visitante, "inicio":entrada_visitante,
                                             "fin":salida_visitante}})
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

@is_logged_in
@usuario_notificaciones
def validarqr(**kws):
    qr_colec = db.qr
    resp = json.loads(session['profile'])
    cotos = db.cotos
    coto = (resp['coto'])
    check_tz = cotos.find_one({"coto_nombre": coto}, {"_id": 0, "zona_horaria": 1})['zona_horaria']
    tz = pytz.timezone(check_tz)
    ct = datetime.now(tz=tz)
    now = ct
    if request.method == 'GET':
        qrval = request.args.get('qr')
        result = qr_colec.find_one({"codigo_qr":qrval})
        fecha_inicio = result['inicio']
        fecha_fin = result['fin']
        nombre = result['visitante']
        estado = result['estado']
        estado_acceso = result['estado_acceso']
        tipo = result['tipo']
        autobloqueo = result['autobloqueo']
        if result:
            if fecha_inicio.replace(tzinfo=tz) < now and fecha_fin.replace(tzinfo=tz) > now:
                if estado == "Activo" or autobloqueo != "Si":
                    if (tipo == "Único" and estado_acceso == "") or (tipo == "Temporal" and estado_acceso == ""):
                        flash(f'Adelante {nombre}', 'success')
                        qr_colec.find_one_and_update({"codigo_qr": qrval},{"$set":{"inicio_real":now,"estado_acceso":"Entro"}})
                        return render_template("qr/aprobado.html",  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
                    else:
                        flash(f'el código ya ha sido utilizado', 'danger')
                        return render_template("qr/noaprobado.html", cont=kws['cont'], foto=kws['foto'],
                                               nombre=kws['nombre'], com=kws['com'])
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
    qr_colec = db.qr
    cotos = db.cotos
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    check_tz = cotos.find_one({"coto_nombre": coto}, {"_id": 0, "zona_horaria": 1})['zona_horaria']
    tz = pytz.timezone(check_tz)
    ct = datetime.now(tz=tz)
    now = ct
    if request.method == 'GET':
        qrval = request.args.get('qrs')
        result = qr_colec.find_one({"codigo_qr": qrval})
        fecha_inicio = result['inicio']
        fecha_fin = result['fin']
        nombre = result['visitante']
        estado = result['estado']
        estado_acceso = result['estado_acceso']
        tipo = result['tipo']
        autobloqueo = result['autobloqueo']
        if result:
                if estado == "Activo" or autobloqueo != "Si":
                        flash(f'Gracias por tu visita {nombre}', 'success')
                        qr_colec.find_one_and_update({"codigo_qr": qrval},
                                                     {"$set": {"fin_real": now, "estado_acceso": ""}})
                        return render_template("qr/aprobado.html", cont=kws['cont'], foto=kws['foto'],
                                               nombre=kws['nombre'], com=kws['com'])

                else:
                    flash(f'el código ha sido cancelado', 'danger')
                    return render_template("qr/noaprobado.html", cont=kws['cont'], foto=kws['foto'],
                                           nombre=kws['nombre'], com=kws['com'])
        else:
            flash(f'el código no es valido', 'danger')
            return render_template("qr/noaprobado.html", cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'],
                                   com=kws['com'])

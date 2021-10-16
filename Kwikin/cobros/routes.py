from flask import render_template, flash, redirect, url_for, session, request, Blueprint, make_response, jsonify
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
from datetime import timedelta, datetime
import json, pytz, secrets
from enviar_email import enviar_correo
from bson import ObjectId, Binary, BSON

cobros = Blueprint('cobros', __name__, template_folder='templates', static_folder='Kwikin/static')



@cobros.route('/gestioncobros', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioncobros(**kws):
    tz = pytz.timezone('America/Mexico_City')
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    domicilios = casas.find({"$and": [{"coto": coto}, {"$or": [{"status": "Activo"}, {"status": "Inactivo"}]}]})
    array = []
    for row in domicilios:
        cargo_sum = 0
        array_ind = []
        status = (row['status'])
        direccion = (row['direccion'])
        for x in (row['cobro']):
            c = x['cargo']
            if c > 0:
                concepto = x['concepto']
                Fecha_limite = x['Fecha_limite']
                cargo = x['cargo']
                estado = x['estado']
                id = x['id']
                array.append({'concepto': concepto,
                                  'id':id,
                                  'Fecha_limite': Fecha_limite,
                                  'estado': estado,'status': (status),
                      'direccion': direccion,
                      'array_ind': array_ind,
                                  'cargo': cargo})

    print(array)
    if len(array) > 0:
        return render_template('cobros/gestioncobros.html', now=now, coto_it=coto, domicilios=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('cobros/gestioncobros.html', coto_it=coto, domicilios=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@cobros.route('/actdomicilio', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actdomicilio(**kws):
    usuario = db.usuarios
    casas = db.casas
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    coto = (resp['coto'])
    if request.method == "POST":
        idusuario = request.form['idusuariohidden']
        direccion = request.form['direccioncasa']
        check = casas.find_one({"coto":coto,"direccion":direccion},{"_id":1})
        if check:
            flash(f'Domicilio ya está registrado en el coto, '
                  f'por favor verifica que no este asignado', 'danger')
            return redirect(url_for('domicilios.gestiondomicilios'))
        else:
            try:
                lista = casas.find_one({"_id":ObjectId(idusuario)},{"_id":0,"residentes":1})['residentes']
                casas.find_one_and_update({"_id": ObjectId(idusuario)}, {"$set": { "direccion":direccion}})
                c = "direccion." + coto
                for x in lista:
                    usuario.find_one_and_update({"correo":x},{"$set":{c:direccion}})
                return redirect(url_for('domicilios.gestiondomicilios'))
            except:
                flash(f'No se pudo actualizar el registro', 'danger')
                return redirect(url_for('domicilios.gestiondomicilios'))
    return redirect(url_for('domicilios.gestiondomicilios'))


@cobros.route('/crearcargo', methods=['GET', 'POST'])
@is_user
@is_logged_in
def crearcargo():
    tz = pytz.timezone('America/Mexico_City')
    comunicados = db.comunicados
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    nowt = datetime.now(tz=tz).strftime("%Y-%m-%dT%H:%M")
    if request.method == 'POST':
        direccion = request.form['domdirigido']
        concepto = request.form['conceptoInd']
        fecha = request.form['fechalimite']
        cargo = int(request.form['cargoInd'])
        extra = "cobro.concepto"
        mensaje = "Un nuevo cargo se ha agregado por concepto de " + concepto
        sec = secrets.token_urlsafe(10)
        id_pago = secrets.token_urlsafe(15)
        if direccion == "Todos":
            array_alldir= []
            alldir = casas.find({"coto":coto},{"direccion":1,"_id":0})
            for row in alldir:
                direccion = (row['direccion'])
                array_alldir.append({"direccion": direccion})
            print(23, array_alldir)
            for entry in array_alldir:
                direccion = entry['direccion']
                check = casas.find_one({'direccion': direccion ,"coto":coto, extra:concepto},{"_id":1})
                email_res = casas.find_one({'direccion': entry['direccion'],"coto":coto}, {"_id": 0, "residentes": 1})['residentes'][
                    0]
                if check:
                    flash(f'El concepto {concepto} ya existe, por favor usa uno nuevo', 'danger')
                    return redirect(url_for('cobros.gestioncobros'))
                else:
                    casas.find_one_and_update(
                            {"direccion": direccion, "coto": coto}, {"$addToSet":{"cobro":{"concepto":concepto, "cargo":cargo, "estado":"Por Pagar", "Fecha_limite":fecha, "comprobante":"", "id":id_pago}}})
                    comunicados.insert_one({"fecha": nowt, "titulo": concepto, "mensaje": mensaje,
                                            "idmultiple_mensaje": sec, "email_usuario_receptor": email_res,
                                            "id_usuario_emisor": correo, "leido": 0, "opcion_a": "", "opcion_c": "",
                                            "opcion_b": "", "opcion_d": "", "resultado": "", "tipo": "Comunicado",
                                            "coto": coto})
                    flash(f'Nuevo cargo agregado a {direccion}, un mensaje se ha enviado ', 'success')
            return redirect(url_for('cobros.gestioncobros'))
        else:
            check = casas.find_one({'direccion': direccion, "coto": coto, extra:concepto},
                                   {"_id": 1})
            email_res = \
            casas.find_one({'direccion': direccion, "coto": coto}, {"_id": 0, "residentes": 1})['residentes'][
                0]
            if check:
                flash(f'El concepto {concepto} ya existe, por favor usa uno nuevo', 'danger')
                return redirect(url_for('cobros.gestioncobros'))
            else:
                casas.find_one_and_update(
                    {"direccion": direccion, "coto": coto}, {"$addToSet":{"cobro":{"concepto":concepto, "cargo":cargo, "estado":"Por Pagar", "Fecha_limite":fecha, "comprobante":"", "id":id_pago}}})
                comunicados.insert_one({"fecha": nowt, "titulo": concepto, "mensaje": mensaje,
                                        "idmultiple_mensaje": sec, "email_usuario_receptor": email_res,
                                        "id_usuario_emisor": correo, "leido": 0, "opcion_a": "", "opcion_c": "",
                                        "opcion_b": "", "opcion_d": "", "resultado": "", "tipo": "Comunicado",
                                        "coto": coto})
                flash(f'Nuevo cargo agregado a {direccion}, un mensaje se ha enviado ', 'success')
                return redirect(url_for('cobros.gestioncobros'))
    return redirect(url_for('cobros.gestioncobros'))

@cobros.route('/pagos', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def pagos(**kws):
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    try:
        cobro = casas.find_one({"$and": [{"coto": coto}, {"residentes":correo}]},{"_id":0,"cobro":1})['cobro']
    except:
        cobro = ""
    array = []
    x = len(cobro)
    print(cobro)
    for lista in cobro[0:x]:
        if lista['estado'] != "Pagado":
            array.append(lista)
    print(array)
    if len(cobro) > 0:
        return render_template('cobros/pagos.html', coto_it=coto, cobros=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('cobros/pagos.html', coto_it=coto, cobros=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@cobros.route('/pagoshistoricos', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def pagoshistoricos(**kws):
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    try:
        cobro = casas.find_one({"$and": [{"coto": coto}, {"residentes":correo}]},{"_id":0,"cobro":1})['cobro']
    except:
        cobro = ""
    array = []
    x = len(cobro)
    for lista in cobro[0:x]:
        if lista['estado'] == "Pagado":
            array.append(lista)
    if len(cobro) > 0:
        return render_template('cobros/pagoshistoricos.html', coto_it=coto, cobros=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('cobros/pagoshistoricos.html', coto_it=coto, cobros=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])



@cobros.route('/cargarpago', methods=['GET', 'POST'])
def cargarpago():
    casas = db.casas
    cotos = db.cotos
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    correo_admin = cotos.find_one({"coto_nombre":coto},{"correo_cobros":1,"_id":0})['correo_cobros']
    casa = casas.find_one({"$and":[{"coto": coto}, {"residentes": correo}]}, {"_id":0, "direccion":1})['direccion']
    if request.method == 'POST':
        concepto = request.form['nombreconcepto']
        idpago = request.form['idpago']
        cargo = request.form['tarifacobro']
        cargo = int(cargo)
        f = request.files['comprobante']
        encoded = Binary(f.read())
        subject = "Comprobante de Pago "+ concepto + " de casa " + casa
        casas.find_one_and_update({"direccion":casa,"cobro.concepto":concepto},{"$set":
                                    {"cobro.$.comprobante": encoded, "cobro.$.estado":"Pendiente"}})
        body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                               <body><p>El usuario {correo},</p><p> ha hecho un pago de <b>{cargo}<b> </p>
                                               <p>Valida que sea correcto en esta <a href="https://www.kwikin.mx/confirmarpago/{idpago}.html">direccion</a>
                                                h </p><p>Gracias.</p>
                                               </body></html>"""
        body_res = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                                       <body><p>Tu comprobante de pago de  {concepto},</p><p> se ha enviado</p>
                                                       <p>
                                                        h </p><p>Gracias.</p>
                                                       </body></html>"""
        enviar_correo('root@kwikin.mx', correo_admin, body, encoded, subject) #envia correo a admin
        enviar_correo('root@kwikin.mx', correo, body_res, encoded, subject) #envia comprobante a residente

        return redirect(url_for('cobros.pagos'))

    return redirect(url_for('cobros.pagos'))

@cobros.route('/confirmarpago/<id>', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def confirmarpago(id, **kws):
    casas = db.casas
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    x = "grupos."+coto
    check = usuario.find_one({x:"admin","correo":correo})
    aprob = []
    if check:
        aprobado = casas.find_one({"$and": [{"coto": coto}, {"cobro.id":id}]})
        f = aprobado['cobro']
        direccion = aprobado['direccion']
        residentes = aprobado['residentes']
        status = aprobado['status']
        for row in f:
            if row['id'] == id:
                concepto = row['concepto']
                cargo = row['cargo']
                estado = row['estado']
                Fecha_limite = row['Fecha_limite']
                id = row['id']
        aprob.append({"direccion":direccion,"residentes":residentes,"status":status,
                      "concepto": concepto, "cargo": cargo,
                      "estado": estado, "Fecha_limite": Fecha_limite, "id": id
                      })
    else:
        flash("No tienes acceso como administrador en este coto", "danger")
        return render_template('main/dashboard.html', coto_it=coto, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    return render_template('cobros/confirmarpago.html', coto_it=coto, cobros=aprob, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@cobros.route('/validarpago', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def validarpago(**kws):
    usuario = db.usuarios
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    correo = (resp['correo'])
    x = "grupos."+coto
    check = usuario.find_one({x:"admin", "correo":correo})
    if request.method == 'POST' and check:
        idpago = request.form['idpago']
        casa = request.form['direccion']
        cargo = request.form['tarifacobro']
        cargo_viejo = request.form['tarifacobroold']
        cargo_actual = int(cargo_viejo) - int(cargo)
        residentes = request.form['residentes']
        residentes = residentes.replace("[", "")
        residentes = residentes.replace("]", "")
        residentes = residentes.replace("'", "")
        concepto = request.form['concepto']
        if cargo_actual > 0:
            estado_pago = "Por Pagar" #concepto Por pagar es cuando no se ha hecho un pago. Pendiente es cuando se envio para aprobacion del admin y Pagado es Pagado
        else:
            estado_pago = "Pagado"
        subject = "Comprobante de Pago "+ concepto + " de casa " + casa
        casas.find_one_and_update({"cobro.id":idpago},{"$set":{"cobro.$.estado": estado_pago, "cobro.$.cargo": cargo_actual }})
        body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                               <body><p>Tu pago  <b>{cargo}<b> </p>
                                               <p>fue validado por el administrador, si tu pago fue parcial, valida que esté efectuado correctamente</a>
                                                h </p><p>Gracias.</p>
                                               </body></html>"""
        #enviar_correo('root@kwikin.mx', residentes, body, encoded, subject)

        return redirect(url_for('cobros.gestioncobros'))
    return redirect(url_for('cobros.gestioncobros'))
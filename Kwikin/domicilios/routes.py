from flask import render_template, flash, redirect, url_for, session, request, Blueprint
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from datetime import timedelta, datetime
import json, pytz
from config import db
import bcrypt, secrets
from bson import ObjectId
import pandas as pd

domicilios = Blueprint('domicilios', __name__, template_folder='templates', static_folder='Kwikin/static')


@domicilios.route('/actdom', methods=['POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def actdom(**kws):
    casas = db.casas
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    ids = None
    if request.method == "POST":
        ids = request.form['data']
        stat = "status." + coto
        act_status = casas.find_one({"_id": ObjectId(ids)}, {"_id": 0, "status": 1})["status"]
        lista = casas.find_one({"_id": ObjectId(ids)}, {"_id": 0, "residentes": 1})['residentes']
        if act_status == "Activo":
            casas.find_one_and_update({"_id": ObjectId(ids)},{"$set":{"status":"Inactivo"}})
            for x in lista:
                usuario.find_one_and_update({"correo": x}, {"$set": {stat: "Inactivo"}})
        else:
            if len(lista) > 0:
                casas.find_one_and_update({"_id": ObjectId(ids)}, {"$set": {"status": "Activo"}})
                for x in lista:
                    usuario.find_one_and_update({"correo": x}, {"$set": {stat: "Activo"}})
    return redirect(url_for('usuarios.gestionusuarios'))

@domicilios.route('/creardomInd', methods=['GET', 'POST'])
@is_user
@is_logged_in
def creardomInd():
    usuario = db.usuarios
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == 'POST':
        direccion = request.form['direccion']
        check = casas.find_one({'direccion': direccion,"coto":coto},{"_id":1})
        if check:
            flash(f'El domicilio {direccion} ya está registrado en el coto, por favor verifica que no esté asignado', 'danger')
            return redirect(url_for('domicilios.gestiondomicilios'))
        else:
            casas.insert_one(
                    {"direccion": direccion, "residentes": [], "coto": coto, "cobro": [], "status":"Inactivo"})
            flash(f'Nuevo domicilio agregado, recuerda que permanecerá Inactivo hasta agregar correos desde Gestión de Usuarios. Importante que la dirección coincida ', 'success')
            return redirect(url_for('domicilios.gestiondomicilios'))
    return redirect(url_for('domicilios.gestiondomicilios'))


@domicilios.route('/crearBulk', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def upload():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    casas =  db.casas
    if request.method == 'POST':
        try:
            df = pd.read_csv(request.files.get('file'))
            for index, row in df.iterrows():
                direccion = row['direccion']
                check = casas.find_one({"coto": coto, "direccion": direccion})
                if check:
                    flash(f'El domicilio {direccion} ya está registrado en el coto, por favor verifica que no esté asignado',
                          'danger')
                    return redirect(url_for('domicilios.gestiondomicilios'))
                else:
                    casas.insert_one(
                        {"direccion": direccion, "residentes": [], "coto": coto, "cobro": [],
                         "status": "Inactivo"})
                    flash(
                        f'Nuevo domicilio agregado, recuerda que permanecerá Inactivo hasta agregar correos desde Gestión de Usuarios. Importante que la dirección coincida ',
                        'success')
                    return redirect(url_for('domicilios.gestiondomicilios'))
                return redirect(url_for('domicilios.gestiondomicilios'))
            return redirect(url_for('domicilios.gestiondomicilios'))
        except:
            flash('No se agrego correctamente el domicilio', 'danger')
            return redirect(url_for('domicilios.gestiondomicilios'))

@domicilios.route('/gestiondomicilios', methods=['GET', 'POST', 'UPDATE'])

@is_logged_in
@usuario_notificaciones
def gestiondomicilios(**kws):
    tz = pytz.timezone('America/Mexico_City')
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    domicilios = casas.find({"$and":[{"coto":coto},{"$or":[{"status":"Activo"},{"status":"Inactivo"}]}]})
    array = []
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    for row in domicilios:
        cargo_sum = 0
        array_ind = []
        id_dom = (row['_id'])
        status = (row['status'])
        direccion = (row['direccion'])
        print(row['cobro'])
        if (row['cobro']) != '':
            for x in (row['cobro']):
                c = x['cargo']
                if c > 0:
                    cargo_sum = cargo_sum + c
                    concepto = x['concepto']
                    Fecha_limite = x['Fecha_limite']
                    cargo =  x['cargo']
                    estado = x['estado']
                    array_ind.append({'concepto':concepto,
                              'Fecha_limite': Fecha_limite,
                                      'estado':estado,
                                'cargo': cargo})
        else:
            array_ind = ""
        array.append({'status': (status),
                          'id_dom': id_dom,
                          'direccion': direccion,
                          "array_ind": array_ind,
                          'cargo_sum': cargo_sum,})
    print(array)
    if len(array) > 0:
        return render_template('domicilios/gestiondomicilios.html', coto_it=coto, domicilios=array, now=now, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('domicilios/gestiondomicilios.html', coto_it=coto, domicilios=array, now=now, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@domicilios.route('/actdomicilio', methods=['GET', 'POST'])
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

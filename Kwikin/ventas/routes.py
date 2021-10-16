from flask import render_template, flash, redirect, url_for, session, request, Blueprint, make_response, jsonify
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
from datetime import timedelta, datetime
import json, pytz, secrets
from enviar_email import enviar_correo
from werkzeug.utils import secure_filename
import os
from PIL import Image
from bson import ObjectId, Binary, BSON

ventas = Blueprint('ventas', __name__, template_folder='templates', static_folder='Kwikin/static')

@ventas.route('/crearcoto', methods=['GET', 'POST', 'UPDATE'])

@is_logged_in
@usuario_notificaciones
def crearcoto(**kws):
    cotos = db.cotos
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    check_tz = cotos.find_one({"coto_nombre": coto}, {"_id": 0, "zona_horaria": 1})['zona_horaria']
    tz = pytz.timezone(check_tz)
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    correo = (resp['correo'])
    grupo = (resp['grupo'])
    usuario = db.usuarios
    casas = db.casas
    arraycotos = []
    if coto == "Kwikin" and grupo == "ventas":
        allcotos = cotos.find({"vendedor":correo})
        print(allcotos)
        for row in allcotos:
            coto_nombre = (row['coto_nombre'])
            direccion = (row['direccion'])
            vendedor = (row['vendedor'])
            fecha_coto = (row['fecha_coto'])
            numero_casas = casas.find({"coto":coto_nombre}).count()
            arraycotos.append({"coto_nombre":coto_nombre,"direccion":direccion,
                               "vendedor":vendedor,"fecha_coto":fecha_coto,
                               "numero_casas":numero_casas})
        print(arraycotos)
        if request.method == 'POST':
            nombre = request.form['nombre']
            correo_admin = request.form['correo']
            apellido = request.form['apellido']
            telefono = request.form['telefono']
            if request.form['direccion'] is None:
                direccion = ""
            else:
                direccion = request.form['direccion']
            coto = request.form['coto_nombre']
            direccion_coto = request.form['coto_direccion']
            cp_coto = request.form['cp_coto']
            zona_horaria = request.form['zona_horaria']
            check_coto = cotos.find_one({"coto_nombre":coto},{"_id":1})
            if check_coto:
                flash("Nombre de coto ya existe, por favor usa otro", "danger")
            else:
                cotos.insert_one({"coto_nombre":coto,"direccion":direccion_coto, "fecha_coto":now,
                                  "cp_coto":cp_coto,"mensualidad":"","dia_de_corte":0, "vendedor":correo,
                                  "dias_de_gracia":0,"max_tpo_qr_unico":0,"zona_horaria":zona_horaria,
                                  "num_estacionamientos":"","activa_terraza":False,"activa_cobros":False,
                                  "activa_estacionamientos":False,"terrazas":{},"correo_cobros":correo_admin})
                flash("Coto agregado correctamente", "success")
                grupos = "admin"
                usuario.find_one({'correo': correo_admin})
                usuario_existe = usuario.find_one({'correo': correo_admin}, {'_id': 0, 'correo': 1})
                if usuario_existe is None:
                    passwordt = secrets.token_urlsafe(10)
                    usuario.insert_one({"correo": correo_admin, "passwordt": passwordt, "password": "",
                                        "password_temporal": True,
                                        "terminos_condiciones": False, "nombre": nombre, "apellido": apellido, "telefono": telefono, "direccion": {coto : direccion}, "status":{coto : "Activo"},
                                        "intentos": 0, "picture": "https://lh3.googleusercontent.com/a/AATXAJxS2dbSR20yfIpHsxolhr4i0VYKDV9NXPruhuxR=s96-c", "grupos": {coto :[grupos] }})
                    check = casas.find_one({"coto":coto,"direccion":direccion})
                    if check:
                        casas.find_one_and_update({"coto": coto, "direccion": direccion}, {"$addToSet": {"residentes": correo_admin}})
                        casas.find_one_and_update({"coto": coto, "direccion": direccion}, {"$set": {"status": "Activo"}})
                    elif direccion == "": #Creado para los admininstradores externos que no tienen casa en el coto
                        pass
                    else:
                        casas.insert_one({"direccion": direccion, "residentes":[correo_admin], "coto":coto, "cobro":[], "status":"Activo"})
                    body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                            <body><p>Estimado usuario,</p><p>Por favor usa <b>{passwordt}<b> como password temporal</p>
                                            <p>Una vez en la plataforma, necesitarás actualizarlo</p><p>Gracias.</p>
                                            </body></html>"""
                    #enviar_correo('root@kwikin.mx', correo, body)
                    flash(f'Usuario agregado correctamente. Contraseña fue enviada a {correo_admin}', 'success')
                    return redirect(url_for('usuarios.gestionusuarios'))
                else:
                    coto1 = "grupos." + coto
                    dir1 = "direccion." + coto
                    status1 = "status." + coto
                    usuario.find_one_and_update({"correo": correo_admin}, {"$set": {coto1: ["usuario"], dir1 : direccion, status1: "Activo"}})
                    check = casas.find_one({"coto": coto, "direccion": direccion})
                    if check:
                        casas.find_one_and_update({"coto": coto, "direccion": direccion}, {"$addToSet": {"residentes": correo_admin}})
                    else:
                        casas.insert_one(
                            {"direccion": direccion, "residentes": [correo_admin], "coto": coto, "mensualidad": {}, "extra": {}, "status":"Activo"})
                    flash(f'Nuevo coto agregado correctamente debido a que {correo_admin} ya esta registrado en nuestra base', 'success')
                    return redirect(url_for('ventas.crearcoto'))
        return render_template('ventas/crearcoto.html', cont=kws['cont'], arraycotos=arraycotos,
                           foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        return redirect(url_for('main.dashboard'))
from flask import render_template, flash, redirect, url_for, session, request, Blueprint, jsonify
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
from datetime import timedelta, datetime
import json, pytz, secrets
from bson import ObjectId

cobros = Blueprint('cobros', __name__, template_folder='templates', static_folder='Kwikin/static')



@cobros.route('/gestioncobros', methods=['GET', 'POST', 'UPDATE'])

@is_logged_in
@usuario_notificaciones
def gestioncobros(**kws):
    casas = db.casas
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    domicilios = casas.find({"$and": [{"coto": coto}, {"$or": [{"status": "Activo"}, {"status": "Inactivo"}]}]})
    array = []
    for row in domicilios:
        id_dom = (row['_id'])
        status = (row['status'])
        direccion = (row['direccion'])
        mensualidad = (row['mensualidad'])
        extra = (row['extra'])
        array.append({'status': (status),
                      'id_dom': id_dom,
                      'direccion': direccion,
                      'mensualidad': mensualidad,
                      'extra': extra})
    if len(array) > 0:
        return render_template('cobros/gestioncobros.html', coto_it=coto, domicilios=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('cobros/gestioncobros.html', coto_it=coto, domicilios=array, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


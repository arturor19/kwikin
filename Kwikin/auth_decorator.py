from flask import session, render_template, redirect, url_for, flash
from functools import wraps
from config import db
import sqlite3
import json
import os







def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('profile', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        return render_template('login/login.html')
    return decorated_function

def is_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            resp = json.loads(session['profile'])
            correo = (resp['correo'])
            usuario = db.usuarios
            usuario_bd = usuario.find_one({'correo': correo})
            usuario_login = json.dumps(usuario_bd, default=str)
            info_bd = json.loads(usuario_login)
            password_temporal = (info_bd['password_temporal'])
            terminos_condiciones = (info_bd['terminos_condiciones'])
            if password_temporal:
                return redirect(url_for('usuarios.act_usuario'))
            elif terminos_condiciones == False:
                return redirect(url_for('main.terminosycondiciones'))
            else:
                return f(*args, **kwargs)
        except:
            print(43675609457)
            return render_template('main/404.html')
    return decorated_function

def usuario_notificaciones(f):
    @wraps(f)
    def decorated_function(**kws):
        resp = json.loads(session['profile'])
        correo = (resp['correo'])
        coto = (resp['coto'])
        usuario = db.usuarios
        comunic = db.comunicados
        usuario_bd = usuario.find_one({'correo': correo})
        usuario_login = json.dumps(usuario_bd, default=str)
        info_bd = json.loads(usuario_login)
        foto = (info_bd['picture'])
        nombre = (info_bd['nombre'])
        cont = comunic.find({"$and": [{"leido": 0}, {"email_usuario_receptor": correo}, {"coto": coto}]}).count()
        com = comunic.find({"$and": [{"leido": {"$ne": 2}}, {"email_usuario_receptor": correo}, {"coto": coto}]},
                           {"_id": 1, "fecha": 1, "titulo": 1, "mensaje": 1, "leido": 1})
        array_com = []
        for row in com:
            id_notificaciones = (row['_id'])
            fecha = (row['fecha'])
            titulo = (row['titulo'])
            mensaje = (row['mensaje'])
            leido = (row['leido'])

            array_com.append({'id_notificaciones': (id_notificaciones),
                              'fecha': fecha,
                              'titulo': titulo,
                              'mensaje': mensaje,
                              'leido': leido})
        kws['cont'] = cont
        kws['com'] = array_com
        kws['foto'] = foto
        kws['nombre'] = nombre
        return f(**kws)
    return decorated_function
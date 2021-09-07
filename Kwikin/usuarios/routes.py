from flask import render_template, flash, redirect, url_for, session, request, Blueprint
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
import json
from config import db
import bcrypt, secrets

usuarios = Blueprint('usuarios', __name__, template_folder='templates', static_folder='Kwikin/static')

@usuarios.route('/act_usuario', methods=['GET', 'POST'])
@is_logged_in #No agregue el grupo de @is_user por que geenra unloop al mandarlo a la pagina de conf usuario
def act_usuario():
    if request.method == 'POST':
        usuario = db.usuarios
        resp = json.loads(session['profile'])
        correo = (resp['correo'])
        nombre = request.form['act_nombre']
        apellido = request.form['act_apellido']
        hashpass = request.form['act_password']
        hashpass2 = request.form['act_password2']
        letters = set(hashpass)
        mixed = any(letter.islower() for letter in letters) and any(letter.isupper() for letter in letters) and any(letter.isdigit() for letter in letters)
        if len(hashpass) < 8 or not mixed:
            flash('Password debe de ser mayor a 8 caracteres, debe contener un número, contener mayúsculas y minúsculas', 'danger')
            return redirect(url_for('usuarios.configuracion_usuario'))
        elif hashpass == hashpass2:
            hashpass = bcrypt.hashpw(request.form['act_password'].encode('utf-8'), bcrypt.gensalt())
            usuario.update_one({'correo': correo}, {'$set': {'password': hashpass, 'password_temporal': False, 'nombre': nombre, 'apellido': apellido}})
            flash('Password actualizado correctamente', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Password no coincide', 'danger')
            return redirect(url_for('usuarios.configuracion_usuario'))
    return redirect(url_for('usuarios.configuracion_usuario'))

@usuarios.route('/configuracion_usuario')
@is_logged_in
@usuario_notificaciones
def configuracion_usuario(**kws):
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    nombre = (resp['nombre'])
    apellido = (resp['apellido'])
    usuario_info_array = []
    usuario_info_array.append({'nombre': nombre, 'apellido':apellido})
    return render_template('usuarios/configuracion_usuario.html', usuarios=usuario_info_array, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@usuarios.route('/ayudabulk', methods=["GET", "POST"])#Necesita revisarse, agregar un excel de template
@is_user
@is_logged_in
@usuario_notificaciones
def ayudabulk(**kws):
    return render_template('usuarios/ayudabulk.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@usuarios.route('/crearInd', methods=['GET', 'POST'])
@is_user
@is_logged_in
def crearInd():
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        apellido = request.form['apellido']
        telefono = request.form['telefono']
        direccion = request.form['direccion']
        checkadmin = request.form.get('checkadmin')
        checkguardia = request.form.get('checkguardia')
        if checkguardia == 'on' and checkadmin == None:
            grupos = "guardia"
        elif checkadmin == 'on' and checkguardia == None:
            grupos = "admin"
        elif checkadmin == 'on' and checkguardia == 'on':
            flash(f'{correo} no fue dado de alta. Solo puedes seleccionar un tipo de usuario', 'danger')
            return redirect(url_for('usuarios.gestionusuarios'))
        else:
            grupos = "usuario"
        usuario.find_one({'correo': correo})
        usuario_existe = usuario.find_one({'correo': correo}, {'_id': 0, 'correo': 1})
        if usuario_existe is None:
            passwordt = secrets.token_urlsafe(10)
            usuario.insert_one({"correo": correo, "passwordt": passwordt, "password": "",
                                "password_temporal": True,
                                "terminos_condiciones": False, "nombre": nombre, "apellido": apellido, "telefono": telefono, "direccion": {coto : direccion}, "status":{coto : "Activo"},
                                "intentos": 0, "picture": "https://lh3.googleusercontent.com/a/AATXAJxS2dbSR20yfIpHsxolhr4i0VYKDV9NXPruhuxR=s96-c", "grupos": {coto :[grupos] }})
            body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                    <body><p>Estimado usuario,</p><p>Por favor usa <b>{passwordt}<b> como password temporal</p>
                                    <p>Una vez en la plataforma, necesitarás actualizarlo</p><p>Gracias.</p>
                                    </body></html>"""
            #enviar_correo('root@kwikin.mx', correo, body)
            flash(f'Usuario agregado correctamente. Contraseña fue enviada a {correo}', 'success')
            return redirect(url_for('login.bienvenida'))
        else:
            coto1 = "grupos." + coto
            usuario.find_one_and_update({"correo": correo}, {"$addToSet": {coto1: "usuario", "direccion": {coto : direccion}, "status":{coto : "Activo"}}})
            flash(f'Nuevo coto agregado correctamente debido a que {correo} ya esta registrado en nuestra base', 'success')
            print("yes")
            return redirect(url_for('login.bienvenida'))
    return redirect(url_for('usuarios.gestionusuarios'))


@usuarios.route('/crearBulk', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def upload():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == 'POST':
        usuario = db.usuarios
        try:
            df = pd.read_csv(request.files.get('file'))
            for index, row in df.iterrows():
                correo = row['correo']
                nombre = row['nombre']
                apellido = row['apellido']
                telefono = row['telefono']
                usuario.find_one({'correo': correo})
                usuario_existe = usuario.find_one({'correo': correo}, {'_id': 0, 'correo': 1})
                if usuario_existe is None and '@' in correo:
                    try:
                        passwordt = secrets.token_urlsafe(10)
                        usuario.insert_one({"correo": correo, "passwordt": passwordt, "password": "",
                                            "password_temporal": True,
                                            "terminos_condiciones": False, "nombre": nombre, "apellido": apellido, "telefono": telefono, "status":{coto : "Activo"},
                                            "intentos": 0, "picture": "https://lh3.googleusercontent.com/a/AATXAJxS2dbSR20yfIpHsxolhr4i0VYKDV9NXPruhuxR=s96-c", "grupos": {coto :["usuario"] }})
                        body = f"""<html><head><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
                                                            <body><p>Estimado usuario,</p><p>Por favor usa <b>{passwordt}<b> como password temporal</p>
                                                            <p>Una vez en la plataforma, necesitarás actualizarlo</p><p>Gracias.</p>
                                                            </body></html>"""
                        enviar_correo('root@kwikin.mx', correo, body)
                        flash(f'{correo} agregado correctamente', 'success')
                    except:
                        flash(f'El correo {correo} no se agrego correctamente', 'danger')
                elif usuario_existe:
                    coto1 = "grupos." + coto
                    usuario.find_one_and_update({"correo": correo}, {"$addToSet": {coto1: "usuario"}})
                    flash(
                        f'Nuevo coto agregado correctamente debido a que {correo} ya esta registrado en nuestra base',
                        'success')
                else:
                    flash(f'El correo {correo} es incorrecto, por favor valida el formato @', 'danger')
        except:
            flash(f"El formato no es valido o el archivo no existe", "danger")
        return render_template('usuarios/crearbulk.html')
    return render_template('usuarios/crearbulk.html')

@usuarios.route('/gestionusuarios', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestionusuarios(**kws):
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    coto_es = "status."+ coto
    usuarios = usuario.find({"$or":[{coto_es:"Activo"},{coto_es:"Inact"}]})
    array = []
    for row in usuarios:
        id_usuario = (row['_id'])
        status = (row['status'])
        correo = (row['correo'])
        grupo = (row['grupos'])
        nombre = (row['nombre'])+" "+(row['apellido'])
        domicilio = (row['direccion'])
        telefono = (row['telefono'])


        array.append({'status': (status),
                      'id_usuario': id_usuario,
                      'email': correo,
                      'nombre': nombre,
                      'telefono': telefono,
                      'grupo' : grupo,
                      'domicilio': domicilio})
    if len(array) > 0:
        return render_template('usuarios/gestionusuarios.html', coto_it=coto, usuarios=array, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios asociados al coto', 'danger')
        return render_template('usuarios/gestionusuarios.html', coto_it=coto, usuarios=array, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@usuarios.route('/actgrupousuario', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actgrupousuario():
    usuario = db.usuarios
    idsg = None
    if request.method == "POST":
        idsg = request.form['data']
        resp = json.loads(session['profile'])
        correo = (resp['correo'])
        coto = (resp['coto'])
        coto1 = "grupos." + coto
        act_grup = usuario.find_one({"$and": [{"_id": ObjectId(idsg)}, {coto1: "admin"}]})
        if act_grup:
            usuario.find_one_and_update({"_id": ObjectId(idsg)}, {"$pull": {coto1: "admin"}})
        else:
            usuario.find_one_and_update({"_id": ObjectId(idsg)}, {"$addToSet": {coto1: "admin"}})
    return redirect(url_for('usuarios.gestionusuarios'))


@usuarios.route('/actusuarinfo', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actusuarinfo(**kws):
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    coto = (resp['coto'])
    coto1 = "grupos." + coto
    cotodir = "direccion." + coto
    if request.method == "POST":
        if request.form['actusuarioinfo'] == 'actu':
            idusuario = request.form['idusuariohidden']
            domicilio_usuario = request.form['domiciliousuario']
            telefono_usuario = request.form['telefonousuario']
            try:
                usuario.find_one_and_update({"_id": ObjectId(idusuario)}, {"$set": {cotodir: domicilio_usuario, "telefono":telefono_usuario}})
                return redirect(url_for('usuarios.gestionusuarios'))
            except:
                flash(f'No se pudo actualizar el registro', 'danger')
                return redirect(url_for('usuarios.gestionusuarios'))
        elif request.form['actusuarioinfo'] == 'elim':
            if request.method == 'POST':
                idusuario = request.form['idusuariohidden']
                multipl = usuario.find_one({"_id":ObjectId(idusuario)},{"_id":0,"status":1})
                multiple = len(multipl['status'])
                try:
                    if multiple > 1:
                        coto_direc = usuario.find_one({"_id": ObjectId(idusuario)}, {"_id": 0, "direccion": 1})
                        coto_direc = (coto_direc['direccion'][coto])
                        #coto_status = usuario.find_one({"_id": ObjectId(idusuario)}, {"_id": 0, "status": 1})
                        #coto_status = (coto_status['status'][coto])
                        #coto_grup = usuario.find_one({"_id": ObjectId(idusuario)}, {"_id": 0, "grupos": 1})
                        #coto_grup = (coto_grup['grupos'][coto])
                        x = usuario.find({"_id": ObjectId(idusuario)}, {"$pull":{"direccion":({coto:coto_direc})}})
                        for y in x:
                            usuario.find_one_and_update({"_id": ObjectId(idusuario)}, {"$pull": {"direccion": ({coto: y[coto]})}})

                        #usuario.find_one_and_update({"_id": ObjectId(idusuario)},{"$pull": {"direccion":({coto:coto_direc}) }})
                            #, "status":{coto:coto_status} ,"grupos":{coto:coto_grup}}})
                        return redirect(url_for('usuarios.gestionusuarios'))
                    else:
                        #usuario.delete_one({"_id":ObjectId(idusuario)})
                        flash(f'Usuario eleminado del sistema', 'danger')
                        return redirect(url_for('usuarios.gestionusuarios'))
                except:
                    flash(f'No se pudo eliminar el registro', 'danger')
                    return redirect(url_for('usuarios.gestionusuarios'))
    return redirect(url_for('usuarios.gestionusuarios'))


@usuarios.route('/actusuario', methods=['POST'])
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
            return render_template('usuarios/gestionusuarios.html',  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('usuarios/gestionusuarios.html',  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    cur.close()
    return render_template('usuarios/gestionusuarios.html',  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@usuarios.route('/actdom', methods=['POST'])
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
            return render_template('usuarios/gestiondimicilios.html',  cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('usuarios/gestiondimicilios.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    cur.close()
    return render_template('usuarios/gestiondimicilios.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

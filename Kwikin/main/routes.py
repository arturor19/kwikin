from flask import render_template, flash, redirect, url_for, session, request, Blueprint
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
import json

main = Blueprint('main', __name__, template_folder='templates', static_folder='Kwikin/static')

@main.route('/avisodeprivacidad', methods=['GET', 'POST', 'UPDATE'])
def avisodeprivacidad():
    return render_template('main/avisodeprivacidad.html')

@main.route('/terminosycondiciones', methods=['GET', 'POST', 'UPDATE'])
@is_logged_in
def terminosycondiciones():
    resp = json.loads(session['profile'])
    correo = (resp['correo'])
    usuario = db.usuarios
    termyconjson = usuario.find_one({"correo":correo},{"_id":0,"terminos_condiciones":1})
    termyconjson = json.dumps(termyconjson, default=str)
    infotermycon = json.loads(termyconjson)
    termycon = (infotermycon['terminos_condiciones'])
    print(termycon)
    if request.method == 'POST':
        usuario.update_one({'correo': correo}, {'$set': {'terminos_condiciones': True}})
        return redirect(url_for('main.dashboard'))
    return render_template('main/terminosycondiciones.html', termycon=termycon)

# Index
@main.route('/')
def index():
    try:
        resp = json.loads(session['profile'])
        if resp:
          return redirect(url_for('main.dashboard'))
    except:
        return render_template('login/login.html')
    return render_template('login/login.html')



@main.route('/dashboard')
@is_user
@is_logged_in
@usuario_notificaciones
def dashboard(**kws):
    resp = json.loads(session['profile'])
    print(resp)
    return render_template('main/dashboard.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@main.route('/configuracion', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def configuracion(**kws):
    resp = json.loads(session['profile'])
    print(resp)
    correo = (resp['correo'])
    coto = (resp['coto'])
    grupo = (resp['grupo'])
    configuracion = db.cotos.find({"coto_nombre":coto})
    print(configuracion)
    mensualidad = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"mensualidad":1})['mensualidad'])
    dia_de_corte = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"dia_de_corte":1})['dia_de_corte'])
    dias_de_gracia = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"dias_de_gracia":1})['dias_de_gracia'])
    max_tpo_qr_unico = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"max_tpo_qr_unico":1})['max_tpo_qr_unico'])
    num_estacionamiento = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"num_estacionamiento":1})['num_estacionamiento'])
    terrazas = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"terrazas":1})['terrazas'])
    activa_cobros = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"activa_cobros":1})['activa_cobros'])
    activa_terraza = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"activa_terraza":1})['activa_terraza'])
    activa_estacionamientos = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,"activa_estacionamientos":1})['activa_estacionamientos'])
    print(terrazas)
    array_conf = terrazas
    if configuracion and grupo == 'admin':
        return render_template('main/configuracion.html', terrazas=terrazas,
                               num_estacionamiento=num_estacionamiento,
                               max_tpo_qr_unico=max_tpo_qr_unico,
                               dias_de_gracia=dias_de_gracia, activa_cobros=activa_cobros,
                               configuracion=array_conf, activa_terraza=activa_terraza,
                               activa_estacionamientos=activa_estacionamientos,
                               dia_de_corte=dia_de_corte, mensualidad=mensualidad,
                               cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        flash('No hay usuarios configuraciones', 'danger')
        return render_template('configuracion.html', configuracion=array_conf,
                               cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    return render_template('main/configuracion.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@main.route('/cobros', methods=['GET', 'POST', 'UPDATE'])
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
        return render_template('main/cobros.html', cobros=array_cobros, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados'
        return render_template('main/cobros.html', cobros=array_cobros, msg=msg, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])

@main.route('/actconfterraza', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfterraza():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        try:
            idterraza = request.form['actterrazas']
            q = "terrazas." +idterraza
            db.cotos.update_one({"coto_nombre":coto},{"$unset":{q:1}})

            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('main.configuracion'))
        except:
            flash(f'Cambio No efectuado correctamente', 'Danger')
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

@main.route('/actconfterraza2', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfterraza2():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        agregarterraza = request.form['agregarterraza']
        colorterraza = request.form['colorselector']
        q = "terrazas."+agregarterraza
        terraza_disponible = db.cotos.find_one({q:{"$exists" : 1 } })
        if terraza_disponible:
            flash(f'El nombre ha sido usado anteriormente', 'danger')
            return redirect(url_for('main.configuracion'))
        else:
            db.cotos.update_one({"coto_nombre":coto},{"$set":{q:colorterraza}})
            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

@main.route('/actconfest', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfest():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        try:
            num_estacionamiento = request.form['num_estacionamiento']
            db.cotos.update_one({"coto_nombre": coto}, {"$set":{"num_estacionamiento": num_estacionamiento}})
            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('main.configuracion'))
        except:
            flash(f'Cambio No efectuado correctamente', 'Danger')
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

@main.route('/actconfduraccionqr', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfduraccionqr():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        try:
            max_tpo_qr_unico = request.form['max_tpo_qr_unico']
            db.cotos.update_one({"coto_nombre": coto}, {"$set": {"max_tpo_qr_unico": max_tpo_qr_unico}})
            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('main.configuracion'))
        except:
            flash(f'Cambio No efectuado correctamente', 'Danger')
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

@main.route('/actconfmens', methods=['GET', 'POST'])
@is_user
@is_logged_in
def actconfmens():
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        try:
            mensualidad = request.form['mensualidad']
            dias_de_gracia = request.form['dias_de_gracia']
            db.cotos.update_one({"coto_nombre": coto}, {"$set": {"mensualidad": mensualidad,"dias_de_gracia":dias_de_gracia}})
            flash(f'Cambio efectuado correctamente', 'success')
            return redirect(url_for('main.configuracion'))
        except Exception as e:
            print(e)
            flash(f'Cambio No efectuado correctamente', 'Danger')
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

@main.route('/actconfcheckbox', methods=['POST'])

@is_logged_in
@usuario_notificaciones
def actconfcheckbox(**kws):
    resp = json.loads(session['profile'])
    coto = (resp['coto'])
    if request.method == "POST":
        nombrecolumna = request.form['data']
        print(nombrecolumna)
        resultconf = (db.cotos.find_one({"coto_nombre":coto},{"_id":0,nombrecolumna:1})[nombrecolumna])
        print(resultconf)
        #resultconf = (db_execute(f"SELECT {nombrecolumna} FROM configuracion")[0][nombrecolumna])
        if resultconf:
            db.cotos.update_one({"coto_nombre": coto}, {"$set": {nombrecolumna: False}})
            return redirect(url_for('main.configuracion'))
        else:
            db.cotos.update_one({"coto_nombre": coto}, {"$set": {nombrecolumna: True}})
            return redirect(url_for('main.configuracion'))
    return redirect(url_for('main.configuracion'))

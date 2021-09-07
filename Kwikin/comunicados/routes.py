from datetime import datetime
import pytz
from flask import render_template, flash, redirect, url_for, session, request, Blueprint
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
import json, secrets
from bson import ObjectId


comunicados = Blueprint('comunicados', __name__, template_folder='templates', static_folder='kwikin/static')




@comunicados.route('/comunicados', methods=['GET', 'POST'])

def comunicado(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    creador = (resp['correo'])
    id_mensaje = ""
    array_comunica = []
    comunica = db_execute("SELECT DISTINCT idmultiple_mensaje, fecha, titulo, mensaje, id_usuario_emisor, tipo from comunicados")
    for row in comunica:
        id_mensaje = (row['idmultiple_mensaje'])
        fecha = (row['fecha'])
        titulo = (row['titulo'])
        mensaje = (row['mensaje'])
        creador = (row['id_usuario_emisor'])
        tipo = (row['tipo'])
        id_mensaje = (row['idmultiple_mensaje'])
        array_comunica.append({'idmultiple_mensaje' : id_mensaje,
                             'fecha': fecha,
                             'titulo': titulo,
                             'mensaje': mensaje,
                             'id_mensaje': id_mensaje,
                             'tipo': tipo,
                             'creador': creador})
        print(array_comunica)
    array_allemails = []
    allemails = db_execute("SELECT * FROM usuarios ")
    for row in allemails:
        email = (row['email'])
        array_allemails.append({'email': email})
    print(array_allemails)

    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = hex(int(time.time()))
        titulo = request.form['titulocom']
        mensaje = request.form['commensaje']
        email_usuario_receptor = request.form['comdirigido']
        if email_usuario_receptor == "Todos":
            for entry in array_allemails:
                db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
                timestamp, titulo, mensaje, idmultmensaje, entry['email'], creador, 0, "Comunicado"))
            return redirect(url_for('comunicados.comunicado'))
        else:
            db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            timestamp, titulo, mensaje, idmultmensaje, email_usuario_receptor, creador, 0, "Comunicado"))
            return redirect(url_for('comunicados.comunicado'))
        return render_template('comunicados/comunicados.html', comuni=array_comunica, cont=kws['cont'], com=kws['com'],
                               allemails=array_allemails, id_mensaje=id_mensaje)
    return render_template('comunicados/comunicados.html',  cont=kws['cont'], com=kws['com'], comuni=array_comunica,
                           allemails=array_allemails, id_mensaje=id_mensaje)


@comunicados.route('/entregadoact/<id_mensaje>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoact(id_mensaje, **kws):
    usuario = dict(session)['profile']['email']
    id_usuario = db_execute(f"SELECT id_usuario FROM usuarios WHERE email = '{usuario}'")[0]['id_usuario']
    valida = db_execute(f"SELECT id_grupo FROM asoc_usuario_grupo WHERE id_usuario = '{id_usuario}'")[0]['id_grupo']
    if valida == 1 or valida == 2 or valida == 3:
        if request.method == 'GET':
            titulo = db_execute(f"SELECT titulo FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['titulo']
            mensaje = db_execute(f"SELECT mensaje FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['mensaje']
            tipo = db_execute(f"SELECT tipo FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['tipo']
            resp_a = db_execute(f"SELECT opcion_a FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_a']
            resp_b = db_execute(f"SELECT opcion_b FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_b']
            resp_c = db_execute(f"SELECT opcion_c FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_c']
            resp_d = db_execute(f"SELECT opcion_d FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}'")[0]['opcion_d']
            array_leido = []
            leido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido != 0 and idmultiple_mensaje = '{id_mensaje}'")
            contleidopor = len(leido)
            array_noleido = []
            noleido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido = 0 and idmultiple_mensaje = '{id_mensaje}'")
            contnoleidopor = len(noleido)
            try:
                opcion_a = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'A'")
                contopa = len(opcion_a)
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'B'")
                contopb = len(opcion_b)
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'C'")
                contopc = len(opcion_c)
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE idmultiple_mensaje = '{id_mensaje}' AND resultado = 'D'")
                contopd = len(opcion_d)
            except:
                opcion_d = ""
                contopd = 0
            if tipo == "Comunicado":
                labels = ["Leido","No leido"]
                values = [contleidopor, contnoleidopor]
                colors = ["#1cc88a", "#e74a3b"]
            else:
                labels = ["Opcion A", "Opcion B", "Opcion C", "Opcion D"]
                values = [contopa, contopb, contopc, contopd]
                colors = ["#4e73df", "#858796", "#1cc88a", "#36b9cc"]
            array_opa = []
            array_opb = []
            array_opc = []
            array_opd = []
            for row in noleido:
                noleidopor =  (row['email_usuario_receptor'])
                array_noleido.append({'noleidopor':noleidopor})
            for rows in leido:
                leidopor =  (rows['email_usuario_receptor'])
                array_leido.append({'leidopor':leidopor})
            for row in opcion_a:
                opa = (row['email_usuario_receptor'])
                array_opa.append({'opa':opa})
            for row in opcion_b:
                opb = (row['email_usuario_receptor'])
                array_opb.append({'opb':opb})
            for row in opcion_c:
                opc = (row['email_usuario_receptor'])
                array_opc.append({'opc':opc})
            for row in opcion_d:
                opd = (row['email_usuario_receptor'])
                array_opd.append({'opd':opd})
        return render_template('comunicados/detallescomunicado.html', contopa=contopa, contopb=contopb, contopc=contopc,
                               contopd=contopd, opa=array_opa, opb=array_opb, opc=array_opc, opd=array_opd,
                               leidopor=array_leido, tipo=tipo, titulo=titulo, mensaje=mensaje, noleidopor=array_noleido,
                               contleidopor=contleidopor, contnoleidopor=contnoleidopor, resp_a=resp_a, resp_b=resp_b,
                               resp_c=resp_c, resp_d=resp_d, set=zip(values, labels, colors),
                               cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        return redirect(url_for('main.dashboard'))

@comunicados.route('/entregadoactres/eliminarres', methods=['GET','POST'])
@is_user
@is_logged_in
def eliminarres():
    if request.method == 'POST':
        id_mensajes =  request.form['elim']
        db_execute("UPDATE comunicados SET leido =\"%s\"  WHERE id_notificaciones =\"%s\";" % (2, id_mensajes))
        return redirect(url_for('comunicados.comunicadosres'))
    return redirect(url_for('main.dashboard'))

@comunicados.route('/entregadoactres/contestarenc', methods=['GET','POST'])
@is_user
@is_logged_in
def contestarenc():
    if request.method == 'POST':
        id_mensajes = request.form['residhidden']
        resultado =  request.form['contestarenc']
        db_execute("UPDATE comunicados SET resultado =\"%s\"  WHERE id_notificaciones =\"%s\";" % (resultado, id_mensajes))
        return redirect(url_for('comunicados.comunicadosres'))
    return redirect(url_for('main.dashboard'))

@comunicados.route('/entregadoactres/<id_mensajes>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoactres(id_mensajes, **kws):
    id_mensajes = id_mensajes
    usuario = dict(session)['profile']['email']
    resultado_var = db_execute(f"SELECT resultado FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0][
        'resultado']  # para validar cual es la variable de leido
    valida = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['email_usuario_receptor']
    try:
        if request.method == 'GET' and usuario == valida:
            db_execute("UPDATE comunicados SET leido =\"%s\"  WHERE id_notificaciones =\"%s\";" % (1, id_mensajes))
            titulo = db_execute(f"SELECT titulo FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['titulo']
            mensaje = db_execute(f"SELECT mensaje FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['mensaje']
            tipo = db_execute(f"SELECT tipo FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['tipo']
            resp_a = db_execute(f"SELECT opcion_a FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_a']
            resp_b = db_execute(f"SELECT opcion_b FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_b']
            resp_c = db_execute(f"SELECT opcion_c FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_c']
            resp_d = db_execute(f"SELECT opcion_d FROM comunicados WHERE id_notificaciones = '{id_mensajes}'")[0]['opcion_d']
            array_leido = []
            leido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido != 0 and id_notificaciones = '{id_mensajes}'")
            contleidopor = len(leido)
            array_noleido = []
            noleido = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE leido = 0 and id_notificaciones = '{id_mensajes}'")
            contnoleidopor = len(noleido)
            try:
                opcion_a = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'A'")
                contopa = len(opcion_a)
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'B'")
                contopb = len(opcion_b)
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'C'")
                contopc = len(opcion_c)
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = db_execute(f"SELECT email_usuario_receptor FROM comunicados WHERE id_notificaciones = '{id_mensajes}' AND resultado = 'D'")
                contopd = len(opcion_d)
            except:
                opcion_d = ""
                contopd = 0
            if tipo == "Comunicado":
                labels = ["Leido","No leido"]
                values = [contleidopor, contnoleidopor]
                colors = ["#1cc88a", "#e74a3b"]
            else:
                labels = ["Opcion A", "Opcion B", "Opcion C", "Opcion D"]
                values = [contopa, contopb, contopc, contopd]
                colors = ["#4e73df", "#858796", "#1cc88a", "#36b9cc"]
            array_opa = []
            array_opb = []
            array_opc = []
            array_opd = []
            for row in noleido:
                noleidopor =  (row['email_usuario_receptor'])
                array_noleido.append({'noleidopor':noleidopor})
            for rows in leido:
                leidopor =  (rows['email_usuario_receptor'])
                array_leido.append({'leidopor':leidopor})
            for row in opcion_a:
                opa = (row['email_usuario_receptor'])
                array_opa.append({'opa':opa})
            for row in opcion_b:
                opb = (row['email_usuario_receptor'])
                array_opb.append({'opb':opb})
            for row in opcion_c:
                opc = (row['email_usuario_receptor'])
                array_opc.append({'opc':opc})
            for row in opcion_d:
                opd = (row['email_usuario_receptor'])
                array_opd.append({'opd':opd})
        return render_template('comunicados/detallescomunicadores.html', contopa=contopa, contopb=contopb, contopc=contopc,
                               contopd=contopd, opa=array_opa, opb=array_opb, opc=array_opc, opd=array_opd, resultado_var=resultado_var,
                               leidopor=array_leido, tipo=tipo, titulo=titulo, mensaje=mensaje, noleidopor=array_noleido,
                               contleidopor=contleidopor, contnoleidopor=contnoleidopor, resp_a=resp_a, resp_b=resp_b,
                               resp_c=resp_c, resp_d=resp_d, set=zip(values, labels, colors),
                               cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'], id_mensajes=id_mensajes)
    except:
        return redirect(url_for('comunicados.comunicadosres'))


@comunicados.route('/encuesta', methods=['GET', 'POST'])
@is_user
@is_logged_in
def encuesta():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    creador = dict(session)['profile']['email']
    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = hex(int(time.time()))
        titulo = request.form['enctitulo']
        mensaje = request.form['encmensaje']
        email_usuario_receptor = request.form['encdirigido']
        opcion_a =  request.form['enca']
        opcion_b = request.form['encb']
        opcion_c = request.form['encc']
        opcion_d = request.form['encd']
        array_allemails = []
        allemails = db_execute("SELECT * FROM usuarios ")
        for row in allemails:
            email = (row['email'])
            array_allemails.append({'email': email})
        if email_usuario_receptor == "Todos":
            for entry in array_allemails:
                db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo, opcion_a, opcion_b, opcion_c, opcion_d) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
                timestamp, titulo, mensaje, idmultmensaje, entry['email'], creador, 0, "Encuesta", opcion_a, opcion_b, opcion_c, opcion_d))
            return redirect(url_for('comunicados.comunicado'))
        else:
            db_execute("INSERT INTO comunicados (fecha, titulo, mensaje, idmultiple_mensaje, email_usuario_receptor, id_usuario_emisor, leido, tipo, opcion_a, opcion_b, opcion_c, opcion_d) VALUES(\"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\", \"%s\")" % (
            timestamp, titulo, mensaje, idmultmensaje, email_usuario_receptor, creador, 0, "Encuesta", opcion_a, opcion_b, opcion_c, opcion_d))
            return redirect(url_for('comunicados.comunicado'))


        return redirect(url_for('comunicados.comunicado'))
    return redirect(url_for('comunicados.comunicado'))


@comunicados.route('/comunicadosres', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def comunicadosres(**kws):
    email = dict(session)['profile']['email']
    conta = db_execute(f"SELECT * FROM comunicados WHERE leido = 0 AND email_usuario_receptor = '{email}'")
    conti = len(conta)
    comuni = db_execute(f"SELECT * FROM comunicados WHERE email_usuario_receptor = '{email}' AND (leido != 2) ")
    array_comuni = []
    for row in comuni:
        id_notificaciones = (row['id_notificaciones'])
        fecha = (row['fecha'])
        titulo = (row['titulo'])
        tipo = (row['tipo'])
        mensaje = (row['mensaje'])
        leido = (row['leido'])
        array_comuni.append({'id_notificaciones': (id_notificaciones),
                          'fecha': fecha,
                          'tipo': tipo,
                          'titulo': titulo,
                          'mensaje': mensaje,
                          'leido': leido})
    return render_template('comunicados/comunicadosres.html', cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'], comuni=array_comuni)

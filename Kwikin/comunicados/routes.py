from datetime import datetime
import pytz
from flask import render_template, flash, redirect, url_for, session, request, Blueprint
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
import json, secrets
from bson import ObjectId


comunicados = Blueprint('comunicados', __name__, template_folder='templates', static_folder='kwikin/static')




@comunicados.route('/comunicados', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def comunicado(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    comunic = db.comunicados
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    print(resp)
    creador = (resp['correo'])
    coto = (resp['coto'])
    array_comunica = []
    comunica = comunic.find({"coto":coto}, {"idmultiple_mensaje": 1, "coto":1, "grupo": 1, "fecha": 1, "titulo": 1, "mensaje": 1,
                                 "id_usuario_emisor": 1, "tipo": 1}).distinct("idmultiple_mensaje")
    for ro in comunica:
        row = comunic.find_one({"idmultiple_mensaje": ro},
                               {"idmultiple_mensaje": 1, "grupo": 1, "fecha": 1, "titulo": 1, "mensaje": 1,
                                "id_usuario_emisor": 1, "tipo": 1, "coto":1})
        id_mensaje = (row['idmultiple_mensaje'])
        fecha = (row['fecha'])
        titulo = (row['titulo'])
        mensaje = (row['mensaje'])
        creador = (row['id_usuario_emisor'])
        tipo = (row['tipo'])
        coto_m = (row['coto'])


        array_comunica.append({'idmultiple_mensaje': id_mensaje,
                               'fecha': fecha,
                               'titulo': titulo,
                               'mensaje': mensaje,
                               'id_mensaje': id_mensaje,
                               'tipo': tipo,
                                'coto': coto_m,
                               'creador': creador})
    array_allemails = []
    x = "grupos." + coto
    allemails = usuario.find({x: {"$exists": True}}, {"_id": 0, "correo": 1})
    for row in allemails:
        email = (row['correo'])
        array_allemails.append({'email': email})
    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = secrets.token_urlsafe(10)
        titulo = request.form['titulocom']
        mensaje = request.form['commensaje']
        email_usuario_receptor = request.form['comdirigido']
        tipo = "Comunicado"
        if email_usuario_receptor == "Todos":
            array_allemails = []
            print(coto)
            allemails = usuario.find({x:{"$exists": True}}, {"_id": 0, "correo": 1})
            print(allemails, 1)
            for row in allemails:
                email = (row['correo'])
                print(email)
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0,
                     "opcion_a": "", "opcion_b": "", "opcion_c": "", "opcion_d": "", "resultado": "", "tipo": tipo, "coto":coto})
            return redirect(url_for('comunicados.comunicado'))
        elif email_usuario_receptor == "Administradores":
            array_allemails = []
            allemails = usuario.find({x: "admin"}, {"_id": 0, "correo": 1})
            for row in allemails:
                email = (row['correo'])
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0,
                     "opcion_a": "", "opcion_b": "", "opcion_c": "", "opcion_d": "", "resultado": "",
                     "tipo": "Comunicado", "coto":coto})
            return redirect(url_for('comunicados.comunicado'))
        elif email_usuario_receptor == "Morosos":
            array_allemails = []
            allemails = usuario.find({x: "morosos"}, {"_id": 0,
                                                            "correo": 1})  # revisar como insertamos el dato de cliente o ventas con empresa
            for row in allemails:
                email = (row['correo'])
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0,
                     "opcion_a": "", "opcion_b": "", "opcion_c": "", "opcion_d": "", "resultado": "", "tipo": tipo, "coto":coto})
            return redirect(url_for('comunicados.comunicado'))
        else:
            comunic.insert_one(
                {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                 "email_usuario_receptor": email_usuario_receptor, "id_usuario_emisor": creador, "leido": 0,
                 "tipo": tipo, "coto":coto})

            return redirect(url_for('comunicados.comunicado'))
        return render_template('comunicados/comunicados.html', comuni=array_comunica, foto=kws['foto'], coto=coto,
                               nombre=kws['nombre'], cont=kws['cont'], com=kws['com'], allemails=array_allemails,
                               id_mensaje=id_mensaje)
    return render_template('comunicados/comunicados.html', cont=kws['cont'], com=kws['com'], foto=kws['foto'],
                           nombre=kws['nombre'], comuni=array_comunica, allemails=array_allemails, coto=coto)


@comunicados.route('/entregadoact/<id_mensaje>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoact(id_mensaje, **kws):
    comunic = db.comunicados
    resp = json.loads(session['profile'])
    grupo = (resp['grupo'])
    if grupo == "admin":
        if request.method == 'GET':
            detallescom = comunic.find_one({"idmultiple_mensaje": id_mensaje})
            titulo = (detallescom['titulo'])
            mensaje = (detallescom['mensaje'])
            tipo = (detallescom['tipo'])
            resp_a = (detallescom['opcion_a'])
            resp_b = (detallescom['opcion_b'])
            resp_c = (detallescom['opcion_c'])
            resp_d = (detallescom['opcion_d'])
            array_leido = []
            leido = comunic.find({"$and": [{"leido": {"$ne": 0}}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
            contleidopor = comunic.find({"$and": [{"leido": {"$ne": 0}}, {"idmultiple_mensaje": id_mensaje}]}).count()
            array_noleido = []
            noleido = comunic.find({"$and": [{"leido": 0}, {"idmultiple_mensaje": id_mensaje}]},
                                   {"_id": 0, "email_usuario_receptor": 1})
            contnoleidopor = comunic.find({"$and": [{"leido": 0}, {"idmultiple_mensaje": id_mensaje}]}).count()
            try:
                opcion_a = comunic.find({"$and": [{"resultado": "A"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
                contopa = comunic.find({"$and": [{"resultado": "A"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = comunic.find({"$and": [{"resultado": "B"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
                contopb = comunic.find({"$and": [{"resultado": "B"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = comunic.find({"$and": [{"resultado": "C"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
                contopc = comunic.find({"$and": [{"resultado": "C"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = comunic.find({"$and": [{"resultado": "D"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
                contopd = comunic.find({"$and": [{"resultado": "D"}, {"idmultiple_mensaje": id_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1}).count()
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
    comunic = db.comunicados
    if request.method == 'POST':
        id_mensajes =  request.form['elim']
        comunic.find_one_and_update({"_id": ObjectId(id_mensajes)}, {"$set": {"leido": 2}})
        return redirect(url_for('comunicados.comunicadosres'))
    return redirect(url_for('comunicados.comunicadosres'))

@comunicados.route('/entregadoactres/contestarenc', methods=['GET','POST'])
@is_user
@is_logged_in
def contestarenc():
    comunic = db.comunicados
    if request.method == 'POST':
        id_mensajes = request.form['residhidden']
        resultado =  request.form['contestarenc']
        comunic.find_one_and_update({"_id": ObjectId(id_mensajes)},{"$set":{"resultado":resultado}})
        return redirect(url_for('comunicados.comunicadosres'))
    return redirect(url_for('comunicados.comunicadosres'))

@comunicados.route('/entregadoactres/<id_mensajes>', methods=['GET'])
@is_user
@is_logged_in
@usuario_notificaciones
def entregadoactres(id_mensajes, **kws):
    id_mensajes = id_mensajes
    comunic = db.comunicados
    resp = json.loads(session['profile'])
    usuario = (resp['correo'])
    resultado_var = comunic.find_one({"_id":ObjectId(id_mensajes)},{"_id":0,"resultado":1})['resultado']
    if resultado_var != "":
        resultado_var = resultado_var
    else:
        resultado_var = "None"
    print(resultado_var)
    valida = comunic.find_one({"_id":ObjectId(id_mensajes)},{"_id":0,"email_usuario_receptor":1})['email_usuario_receptor']
    print(valida)
    try:
        if request.method == 'GET' and usuario == valida:
            comunic.find_one_and_update({"_id":ObjectId(id_mensajes)},{"$set":{"leido":1}})
            detallescom = comunic.find_one({"_id": ObjectId(id_mensajes)})
            titulo = (detallescom['titulo'])
            mensaje = (detallescom['mensaje'])
            tipo = (detallescom['tipo'])
            resp_a = (detallescom['opcion_a'])
            resp_b = (detallescom['opcion_b'])
            resp_c = (detallescom['opcion_c'])
            resp_d = (detallescom['opcion_d'])
            id_Multiple_mensaje = (detallescom['idmultiple_mensaje'])
            array_leido = []
            leido = comunic.find({"$and": [{"leido": {"$ne": 0}}, {"idmultiple_mensaje": id_Multiple_mensaje}]},
                                 {"_id": 0, "email_usuario_receptor": 1})
            contleidopor = comunic.find({"$and": [{"leido": {"$ne": 0}}, {"idmultiple_mensaje": id_Multiple_mensaje}]}).count()
            array_noleido = []
            noleido = comunic.find({"$and": [{"leido": 0}, {"idmultiple_mensaje": id_Multiple_mensaje}]},
                                   {"_id": 0, "email_usuario_receptor": 1})
            contnoleidopor = comunic.find({"$and": [{"leido": 0}, {"idmultiple_mensaje": id_Multiple_mensaje}]}).count()
            try:
                opcion_a = comunic.find({"$and": [{"resultado": "A"}, {"_id": ObjectId(id_mensajes)}]},
                                        {"_id": 0, "email_usuario_receptor": 1})
                contopa = comunic.find({"$and": [{"resultado": "A"}, {"_id": ObjectId(id_mensajes)}]},
                                       {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_a = ""
                contopa = 0
            try:
                opcion_b = comunic.find({"$and": [{"resultado": "B"}, {"_id": ObjectId(id_mensajes)}]},
                                        {"_id": 0, "email_usuario_receptor": 1})
                contopb = comunic.find({"$and": [{"resultado": "B"}, {"_id": ObjectId(id_mensajes)}]},
                                       {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_b = ""
                contopb = 0
            try:
                opcion_c = comunic.find({"$and": [{"resultado": "C"}, {"_id": ObjectId(id_mensajes)}]},
                                        {"_id": 0, "email_usuario_receptor": 1})
                contopc = comunic.find({"$and": [{"resultado": "C"}, {"_id": ObjectId(id_mensajes)}]},
                                       {"_id": 0, "email_usuario_receptor": 1}).count()
            except:
                opcion_c = ""
                contopc = 0
            try:
                opcion_d = comunic.find({"$and": [{"resultado": "D"}, {"_id": ObjectId(id_mensajes)}]},
                                        {"_id": 0, "email_usuario_receptor": 1})
                contopd = comunic.find({"$and": [{"resultado": "D"}, {"_id": ObjectId(id_mensajes)}]},
                                       {"_id": 0, "email_usuario_receptor": 1}).count()
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
    comunic = db.comunicados
    usuario = db.usuarios
    resp = json.loads(session['profile'])
    creador = (resp['correo'])
    coto = (resp['coto'])
    array_allemails = []
    array_comunica = []
    x = "grupos." + coto
    allemails = usuario.find({x: {"$exists": True}}, {"_id": 0, "correo": 1})
    for row in allemails:
        email = (row['correo'])
        array_allemails.append({'email': email})
    if request.method == 'POST':
        timestamp = ct.strftime("%Y-%m-%d %H:%M")
        idmultmensaje = secrets.token_urlsafe(10)
        titulo = request.form['enctitulo']
        mensaje = request.form['encmensaje']
        email_usuario_receptor = request.form['encdirigido']
        opcion_a =  request.form['enca']
        opcion_b = request.form['encb']
        opcion_c = request.form['encc']
        opcion_d = request.form['encd']
        tipo = "Encuesta"
        if email_usuario_receptor == "Todos":
            array_allemails = []
            allemails = usuario.find({x:{"$exists": True}}, {"_id": 0, "correo": 1})
            for row in allemails:
                email = (row['correo'])
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0, "coto":coto,
                     "opcion_a": opcion_a, "opcion_b": opcion_b, "opcion_c": opcion_c, "opcion_d": opcion_d, "resultado": "", "tipo": tipo})
            return redirect(url_for('comunicados.comunicado'))
        elif email_usuario_receptor == "Administradores":
            array_allemails = []
            allemails = usuario.find({x: "admin"}, {"_id": 0, "correo": 1})
            for row in allemails:
                email = (row['correo'])
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0, "coto":coto,
                     "opcion_a": opcion_a, "opcion_b": opcion_b, "opcion_c": opcion_c, "opcion_d": opcion_d,
                     "resultado": "", "tipo": tipo})
            return redirect(url_for('comunicados.comunicado'))
        elif email_usuario_receptor == "Morosos":
            array_allemails = []
            allemails = usuario.find({x: "morosos"}, {"_id": 0,
                                                             "correo": 1})  # revisar como insertamos el dato de cliente o ventas con empresa
            for row in allemails:
                email = (row['correo'])
                # Aqui puedo agregar opcion de enviar correo automaticamente con comunicado
                array_allemails.append({'email': email})
            for entry in array_allemails:
                comunic.insert_one(
                    {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                     "email_usuario_receptor": entry['email'], "id_usuario_emisor": creador, "leido": 0, "coto":coto,
                     "opcion_a": opcion_a, "opcion_b": opcion_b, "opcion_c": opcion_c, "opcion_d": opcion_d,
                     "resultado": "", "tipo": tipo})
            return redirect(url_for('comunicados.comunicado'))
        else:
            comunic.insert_one(
                {"fecha": timestamp, "titulo": titulo, "mensaje": mensaje, "idmultiple_mensaje": idmultmensaje,
                 "email_usuario_receptor": email_usuario_receptor, "id_usuario_emisor": creador, "leido": 0,
                 "opcion_a": opcion_a, "opcion_b": opcion_b, "opcion_c": opcion_c, "opcion_d": opcion_d, "coto":coto,
                 "resultado": "", "tipo": tipo})

            return redirect(url_for('comunicados.comunicado'))
        return render_template('comunicados/comunicados.html', comuni=array_comunica, foto=kws['foto'],
                               nombre=kws['nombre'], cont=kws['cont'], com=kws['com'], allemails=array_allemails,
                               id_mensaje=id_mensaje)
    return render_template('comunicados/comunicados.html', cont=kws['cont'], com=kws['com'], foto=kws['foto'],
                           nombre=kws['nombre'], comuni=array_comunica, allemails=array_allemails)

@comunicados.route('/comunicadosres', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def comunicadosres(**kws):
    comunic = db.comunicados
    resp = json.loads(session['profile'])
    email = (resp['correo'])
    coto = (resp['coto'])
    comuni = comunic.find({"$and": [{"leido": {"$ne": 2}}, {"email_usuario_receptor": email}, {"coto":coto}]},
                                 {"_id": 1, "email_usuario_receptor": 1, "fecha":1,
                                  "titulo":1, "tipo":1, "mensaje":1, "leido":1})
    array_comuni = []
    for row in comuni:
        id_notificaciones = (row['_id'])
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

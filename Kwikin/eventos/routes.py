from flask import render_template, flash, redirect, url_for, session, request, Blueprint, jsonify
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
from datetime import timedelta, datetime
import json, pytz, secrets
from bson import ObjectId

eventos = Blueprint('eventos', __name__, template_folder='templates', static_folder='Kwikin/static')



@eventos.route('/calendario')

@is_logged_in
@usuario_notificaciones
def calendario(**kws):
    res = json.loads(session['profile'])
    coto = (res['coto'])
    cotos = db.cotos
    arr_terraza = []
    arr_terr = cotos.find_one({"coto_nombre": coto}, {"_id":0,"terrazas":1})['terrazas']
    for k, v in arr_terr.items():
        terraza = k
        color = v
        arr_terraza.append({"terraza":terraza,"color":color})
    return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], terrazas=arr_terraza, foto=kws['foto'], nombre=kws['nombre'])

@eventos.route('/calendario_ini/remote')

@is_logged_in
def calendario_ini():
    test_cal = ''
    if request.method == 'GET':
        callback = request.args.get('callback')
        print(callback)
    if callback in "in mbsc_jsonp_comp_demo-responsive-month-view":
        test_cal = '''try { window['mbsc_jsonp_comp_demo-responsive-month-view']('{"calendar":{},"datetime":{"wheels":[[{"cssClass":"mbsc-dt-whl-d","label":"Día","data":[{"value":1,"display":"1"},{"value":2,"display":"2"},{"value":3,"display":"3"},{"value":4,"display":"4"},{"value":5,"display":"5"},{"value":6,"display":"6"},{"value":7,"display":"7"},{"value":8,"display":"8"},{"value":9,"display":"9"},{"value":10,"display":"10"},{"value":11,"display":"11"},{"value":12,"display":"12"},{"value":13,"display":"13"},{"value":14,"display":"14"},{"value":15,"display":"15"},{"value":16,"display":"16"},{"value":17,"display":"17"},{"value":18,"display":"18"},{"value":19,"display":"19"},{"value":20,"display":"20"},{"value":21,"display":"21"},{"value":22,"display":"22"},{"value":23,"display":"23"},{"value":24,"display":"24"},{"value":25,"display":"25"},{"value":26,"display":"26"},{"value":27,"display":"27"},{"value":28,"display":"28"},{"value":29,"display":"29"},{"value":30,"display":"30"},{"value":31,"display":"31"}]},{"cssClass":"mbsc-dt-whl-m","label":"Mes","data":[{"value":0,"display":"<span class=\\\\"mbsc-dt-month\\\\">Enero</span>"},{"value":1,"display":"<span class=\\\\"mbsc-dt-month\\\\">Febrero</span>"},{"value":2,"display":"<span class=\\\\"mbsc-dt-month\\\\">Marzo</span>"},{"value":3,"display":"<span class=\\\\"mbsc-dt-month\\\\">Abril</span>"},{"value":4,"display":"<span class=\\\\"mbsc-dt-month\\\\">Mayo</span>"},{"value":5,"display":"<span class=\\\\"mbsc-dt-month\\\\">Junio</span>"},{"value":6,"display":"<span class=\\\\"mbsc-dt-month\\\\">Julio</span>"},{"value":7,"display":"<span class=\\\\"mbsc-dt-month\\\\">Agosto</span>"},{"value":8,"display":"<span class=\\\\"mbsc-dt-month\\\\">Septiembre</span>"},{"value":9,"display":"<span class=\\\\"mbsc-dt-month\\\\">Octubre</span>"},{"value":10,"display":"<span class=\\\\"mbsc-dt-month\\\\">Noviembre</span>"},{"value":11,"display":"<span class=\\\\"mbsc-dt-month\\\\">Diciembre</span>"}]},{"cssClass":"mbsc-dt-whl-y","label":"A&ntilde;o","data":"function getYearValue(i, inst) {\\\\r\\\\n    var s = inst.settings;\\\\r\\\\n    return {\\\\r\\\\n      value: i,\\\\r\\\\n      display: (/yy/i.test(s.dateDisplay) ? i : (i + \\'\\').substr(2, 2)) + (s.yearSuffix || \\'\\')\\\\r\\\\n    };\\\\r\\\\n  }","getIndex":"function getYearIndex(v) {\\\\r\\\\n    return v;\\\\r\\\\n  }"}]],"wheelOrder":{"d":0,"m":1,"y":2},"isoParts":{"y":1,"m":1,"d":1}},"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div>"}'); } catch (ex) {}'''
    elif "mbsc_jsonp_comp_" in callback:
        id_num_cal = str(callback).replace("mbsc_jsonp_comp_", '')
        head_cal = ("try { window['mbsc_jsonp_comp_" + id_num_cal + "']")
        tail_cal = '''('{"html1":"<div lang=\\\\"es\\\\" class=\\\\"mbsc-fr mbsc-no-touch mbsc-ios","html2":" mbsc-fr-nobtn\\\\"><div class=\\\\"mbsc-fr-persp\\\\"><div role=\\\\"dialog\\\\" class=\\\\"mbsc-fr-scroll\\\\"><div class=\\\\"mbsc-fr-popup mbsc-ltr","html3":"<div class=\\\\"mbsc-fr-focus\\\\" tabindex=\\\\"-1\\\\"></div><div class=\\\\"mbsc-fr-w\\\\"><div aria-live=\\\\"assertive\\\\" class=\\\\"mbsc-fr-aria mbsc-fr-hdn\\\\"></div>","html4":"</div></div></div></div></div></div></div>"}'); } catch (ex) {}'''
        test_cal = head_cal + tail_cal
    return test_cal

@eventos.route('/calendario_data')

@is_logged_in
def test_calendario():
    cotos = db.cotos
    eventos = db.eventos
    res = json.loads(session['profile'])
    coto = (res['coto'])
    col = (cotos.find({"coto_nombre": coto},{"_id":0,"terrazas":1}))
    colores = {}
    for x in col:
        for k,v in x.items():
            colores.update({k: v})
    colores = colores['terrazas']
    print(colores)
    arr_evetos_aprobados = eventos.find({"coto":coto,"estado":"Aprobado"},{"_id":0,"terraza":1,"dia":1})
    arr_cal = []
    for event in arr_evetos_aprobados:
        start = event['dia']
        text = event['terraza']
        color = colores[text]
        print(color, text, start)
        arr_cal.append({"start": start, "text": text, "color": color})
    events_json = json.dumps(arr_cal, indent=4)
    info_calendario = 'try {mbscjsonp1(' + events_json + ');' + '} catch (ex) {}'
    return info_calendario




@eventos.route('/crearevento', methods=['GET', 'POST'])

@is_logged_in
@usuario_notificaciones
def peticionevento(**kws):
    tz = pytz.timezone('America/Mexico_City')
    casas = db.casas
    eventos = db.eventos
    res = json.loads(session['profile'])
    coto = (res['coto'])
    correo = (res['correo'])
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    casareq = casas.find_one({"coto": coto, "residentes": correo},{"_id":1})["_id"]
    print(casareq)
    if request.method == 'POST':

            fechaevento = request.form['fechaevento']
            terraza = request.form['terraza']

            if fechaevento < now:
                flash('Por favor valida que las fechas sean correctas', 'danger')
            elif terraza == 'Selecciona terraza':
                flash('Por favor selecciona una terraza del listado', 'danger')
            else:
                try:
                    existe_evento = eventos.find_one({"coto":coto, "terraza":terraza, "dia":fechaevento})
                    if existe_evento:
                        pass
                    else:
                        eventos.insert_one({"coto":coto, "terraza":terraza, "dia":fechaevento, "casa_req":ObjectId(casareq), "estado":"Pendiente"})
                    flash(f'Evento guardado correctamente, recibiras un correo cuando el administrador lo apruebe',
                          'success')
                    return redirect(url_for('eventos.calendario'))
                except:
                    flash(f'Evento no creado correctamente', 'danger')
                    return redirect(url_for('eventos.calendario'))
            return redirect(url_for('eventos.calendario'))

    return redirect(url_for('eventos.calendario'))


@eventos.route('/gestioneventos', methods=['GET', 'POST', 'UPDATE'])

@is_logged_in
@usuario_notificaciones
def gestioneventos(**kws):
    tz = pytz.timezone('America/Mexico_City')
    casas = db.casas
    eventos = db.eventos
    res = json.loads(session['profile'])
    coto = (res['coto'])
    correo = (res['correo'])
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    eventos = eventos.find({"coto":coto,"dia":{"$gte":now}})
    print(eventos)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        casa_req = (row['casa_req'])
        direccion = casas.find_one({"_id":ObjectId(row['casa_req'])},{"_id":0,"direccion":1})['direccion']
        status_casa = casas.find_one({"_id":ObjectId(row['casa_req'])},{"_id":0,"status":1})['status']
        try:
            email_1 = casas.find_one({"_id": ObjectId(row['casa_req'])},{"_id":0,"residentes":1})['residentes'][0]
            telefono_1 = db.usuarios.find_one({"correo":email_1},{"_id":0,"telefono":1})["telefono"]
            nombre_1 = db.usuarios.find_one({"correo":email_1},{"_id":0,"nombre":1})["nombre"] + " " + db.usuarios.find_one({"correo":email_1},{"_id":0,"apellido":1})["apellido"]
        except:
            email_1 = "No registrado"
            telefono_1 = "No registrado"
            nombre_1 = "No registrado"
        id_eventos = (row['_id'])
        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'telefono_1': telefono_1,
                              'status_casa':status_casa,
                              'email_1':email_1,
                              'casa_req':casa_req,
                              'nombre_1':nombre_1,
                              'direccion': direccion,
                              'terraza': terraza,
                              'dia': dia})

    if eventos:
        return render_template('eventos/gestioneventos.html', eventos=array_eventos, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('eventos/gestioneventos.html', eventos=array_eventos, msg=msg, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@eventos.route('/acteventos', methods=['POST'])

@is_logged_in
def acteventos():
    tz = pytz.timezone('America/Mexico_City')
    casas = db.casas
    eventos = db.eventos
    comunicados = db.comunicados
    res = json.loads(session['profile'])
    coto = (res['coto'])
    correo = (res['correo'])
    nowt = datetime.now(tz=tz).strftime("%Y-%m-%dT%H:%M")
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    sec = secrets.token_urlsafe(10)
    if request.method == 'POST':
        eventsvalue = request.form['mycheckboxE']
        eventsid = request.form['idhidden']
        terraza = request.form['terrazahidden']
        tarifa = request.form['tarifaeventos']
        if tarifa:
            pass
        else:
            tarifa = 0
        id_casa = request.form['casa_req']
        email_res = request.form['emailhidden']
        dia = request.form['diaevento']
        titulo = terraza + " " + eventsvalue
        mensaje = terraza + " fue " + eventsvalue + " para el dia " + dia + " con una tarifa de $" + str(tarifa)
        mensajen = terraza + "No fue aprobada para el dia " + dia
        validador = eventos.find_one({"coto": coto, "terraza": terraza, "dia": dia, "estado": "Aprobado"}, {"_id": 1})
        print(eventsvalue)
        if validador:
            flash(f'La terraza {terraza} ya esta apartada el dia {dia}, revisa fecha', 'danger')
            return redirect(url_for('eventos.gestioneventos'))
        else:
            if eventsvalue == "Aprobado":
                eventos.find_one_and_update({"_id":ObjectId(eventsid)},{"$set":{"estado":eventsvalue,"tarifa":tarifa}})
                comunicados.insert_one({"fecha":nowt,"titulo":titulo,"mensaje":mensaje,
                                        "idmultiple_mensaje":sec,"email_usuario_receptor":email_res,
                                        "id_usuario_emisor":correo,"leido":0,"opcion_a":"", "opcion_c":"",
                                        "opcion_b":"","opcion_d":"","resultado":"","tipo":"Comunicado","coto":coto})
                #enviar correo aqui
                return redirect(url_for('eventos.gestioneventos'))
            elif eventsvalue == "Pre-aprobado":
                eventos.find_one_and_update({"_id": ObjectId(eventsid)}, {"$set": {"estado": eventsvalue, "tarifa": tarifa}})
                comunicados.insert_one({"fecha": nowt, "titulo": titulo, "mensaje": mensaje,
                                        "idmultiple_mensaje": sec, "email_usuario_receptor": email_res,
                                        "id_usuario_emisor": correo, "leido": 0, "opcion_a": "", "opcion_c": "",
                                        "opcion_b": "", "opcion_d": "", "resultado": "", "tipo": "Comunicado",
                                        "coto": coto})
                #enviar correo aqui
                ex = "extra."+ terraza + "_" + dia
                casas.find_one_and_update({"_id":ObjectId(id_casa)},{"$set":{ex:tarifa}})
                return redirect(url_for('eventos.gestioneventos'))
            elif eventsvalue == "No Aprobado":
                eventos.find_one_and_update({"_id": ObjectId(eventsid)}, {"$set": {"estado": eventsvalue, "tarifa": tarifa}})
                comunicados.insert_one({"fecha": nowt, "titulo": titulo, "mensaje": mensajen,
                                        "idmultiple_mensaje": sec, "email_usuario_receptor": email_res,
                                        "id_usuario_emisor": correo, "leido": 0, "opcion_a": "", "opcion_c": "",
                                        "opcion_b": "", "opcion_d": "", "resultado": "", "tipo": "Comunicado",
                                        "coto": coto})
                return redirect(url_for('eventos.gestioneventos'))
            else:
                return redirect(url_for('eventos.gestioneventos'))
        return redirect(url_for('eventos.gestioneventos'))
    return redirect(url_for('eventos.gestioneventos'))


@eventos.route('/gestioneventoshistorico', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioneventoshistorico(**kws):
    tz = pytz.timezone('America/Mexico_City')
    casas = db.casas
    eventos = db.eventos
    res = json.loads(session['profile'])
    coto = (res['coto'])
    correo = (res['correo'])
    now = datetime.now(tz=tz).strftime("%Y-%m-%d")
    eventos = eventos.find({"coto": coto, "dia": {"$lt": now}})
    print(eventos)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        casa_req = (row['casa_req'])
        direccion = casas.find_one({"_id": ObjectId(row['casa_req'])}, {"_id": 0, "direccion": 1})['direccion']
        status_casa = casas.find_one({"_id": ObjectId(row['casa_req'])}, {"_id": 0, "status": 1})['status']
        try:
            email_1 = casas.find_one({"_id": ObjectId(row['casa_req'])}, {"_id": 0, "residentes": 1})['residentes'][0]
            telefono_1 = db.usuarios.find_one({"correo": email_1}, {"_id": 0, "telefono": 1})["telefono"]
            nombre_1 = db.usuarios.find_one({"correo": email_1}, {"_id": 0, "nombre": 1})["nombre"] + " " + \
                       db.usuarios.find_one({"correo": email_1}, {"_id": 0, "apellido": 1})["apellido"]
        except:
            email_1 = "No registrado"
            telefono_1 = "No registrado"
            nombre_1 = "No registrado"
        id_eventos = (row['_id'])
        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'telefono_1': telefono_1,
                              'status_casa': status_casa,
                              'email_1': email_1,
                              'casa_req': casa_req,
                              'nombre_1': nombre_1,
                              'direccion': direccion,
                              'terraza': terraza,
                              'dia': dia})

    if eventos:
        return render_template('eventos/gestioneventoshistorico.html', eventos=array_eventos, cont=kws['cont'], foto=kws['foto'],
                               nombre=kws['nombre'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('eventos/gestioneventoshistorico.html', eventos=array_eventos, msg=msg, cont=kws['cont'],
                               foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


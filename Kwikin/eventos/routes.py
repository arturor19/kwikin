from flask import render_template, flash, redirect, url_for, session, request, Blueprint, jsonify
from auth_decorator import is_logged_in, is_user, usuario_notificaciones
from config import db
import json

eventos = Blueprint('eventos', __name__, template_folder='templates', static_folder='Kwikin/static')



@eventos.route('/calendar-events')

@is_logged_in
@usuario_notificaciones
def calendar_events(**kws):
    res = json.loads(session['profile'])
    coto = (res['coto'])
    cotos = db.cotos
    arr_terr = cotos.find_one({"coto_nombre": coto}, {"_id":0,"terrazas":1})['terrazas']
    try:
        rows = db_execute("SELECT id, titulo, casa, UNIX_TIMESTAMP(start_date)*1000 as start, UNIX_TIMESTAMP("
                          "end_date)*1000 as end FROM event FROM eventos")
        resp = jsonify({'success': 1, 'result': rows})
        print(rows)
        resp.status_code = 200
        return resp
    except Exception as e:
        print(e)
    return render_template('eventos/calendar_events.html', rows=rows, terrazas=arr_terr, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@eventos.route('/calendario')

@is_logged_in
@usuario_notificaciones
def calendario(**kws):
    res = json.loads(session['profile'])
    coto = (res['coto'])
    cotos = db.cotos
    arr_terr = cotos.find_one({"coto_nombre": coto}, {"_id":0,"terrazas":1})['terrazas']
    print(arr_terr)
    return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], terrazas=arr_terr, foto=kws['foto'], nombre=kws['nombre'])

@eventos.route('/calendario_ini/remote')
@is_user
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
@is_user
@is_logged_in
def test_calendario():
    colores = {}
    for v in (db_execute("select id_terrazas, colores_terraza from terrazas;")):
        colores.update({v["id_terrazas"]: v["colores_terraza"]})
    arr_evetos_aprobados = db_execute("select t2.id_terrazas, t2.terraza, e.dia from eventos e, terrazas t2 where "
                                      "e.estado = 'Aprobado' and t2.terraza = e.terraza")
    arr_cal = []
    for event in arr_evetos_aprobados:
        start = event['dia']
        text = event['terraza']
        color = colores[event['id_terrazas']]
        arr_cal.append({"start": start, "text": text, "color": color})
    events_json = json.dumps(arr_cal, indent=4)
    info_calendario = 'try {mbscjsonp1(' + events_json + ');' + '} catch (ex) {}'
    return info_calendario




@eventos.route('/crearevento', methods=['GET', 'POST'])
@is_user
@is_logged_in
@usuario_notificaciones
def peticionevento(**kws):
    arr_terr = db_execute('select * from terrazas')
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = session['profile']['email']
    name = session['profile']['name']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = str(now)

    if request.method == 'POST':
        try:
            fechaevento = request.form['fechaevento']
            terraza = request.form['terraza']

            if fechaevento < now:
                flash('Por favor valida que las fechas sean correctas', 'danger')
            elif terraza == 'Selecciona terraza':
                flash('Por favor selecciona una terraza del listado', 'danger')
            else:
                try:
                    existe_evento = db_execute(f"select * from eventos where terraza='{terraza}' and nombre_eventos='{name}' and correo='{email}' and dia='{fechaevento}'")
                    valor_evento = (len(existe_evento))
                    if valor_evento == 1:
                        pass
                    else:
                        db_execute(
                        "INSERT INTO eventos(terraza, nombre_eventos, correo, dia) VALUES(\"%s\", \"%s\", \"%s\", \"%s\")" % (
                            terraza, name, email, fechaevento))

                    flash(f'Evento guardado correctamente, recibiras un correo cuando el administrador lo apruebe',
                          'success')
                    # insert_asoc_qr_usuario = f"""INSERT INTO asoc_qr_usuario(id_usuario, id_qr, id_coto) VALUES
                    #  (
                    #  (SELECT id_usuario FROM usuarios where email = '{email}'),
                    # (SELECT id_qr FROM qr where codigo_qr = '{codigo_qr}'),
                    #  (SELECT id_coto FROM asoc_usuario_coto where id_usuario = (SELECT id_usuario FROM usuarios where email = '{email}'))
                    #  );"""
                    #                cur.execute(insert_asoc_qr_usuario)
                    #                mysql.commit()
                    cur.close()
                except:
                    flash(f'Evento no creado correctamente', 'danger')
                    return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now,
                                           terrazas=arr_terr)
                return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)
        except:
            flash(f'Revisa todos los campos', 'danger')
            return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)

    return render_template('eventos/calendar_events.html',  cont=kws['cont'], com=kws['com'], now=now, terrazas=arr_terr)


@eventos.route('/gestioneventos', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioneventos(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    email = session['profile']['email']
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia >= '%s';" % now)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        email = (row['correo'])
        nombre = (row['nombre_eventos'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])
        id_eventos = (row['id_eventos'])

        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'email': email,
                              'nombre': nombre,
                              'terraza': terraza,
                              'domicilio': domicilio,
                              'telefono': telefono,
                              'dia': dia})

    if len(eventos) > 0:
        return render_template('eventos/gestioneventos.html', eventos=array_eventos, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('eventos/gestioneventos.html', eventos=array_eventos, msg=msg, cont=kws['cont'], foto=kws['foto'], nombre=kws['nombre'], com=kws['com'])


@eventos.route('/acteventos', methods=['POST'])
@is_user
@is_logged_in
def acteventos():
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    now = ct
    now = datetime.strftime((now), "%Y-%m-%d")
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia >= '%s';" % now)
    array_eventos = []
    if request.method == 'POST':
        eventsvalue = request.form['mycheckboxE']
        eventsid = request.form['idhidden']
        terraza = request.form['terrazahidden']
        print(eventsvalue, eventsid, terraza)
        dia = db_execute("SELECT dia FROM eventos WHERE id_eventos = '%s';" % eventsid)[0]['dia']
        print(eventsvalue)
        print(eventsid)
        print(terraza)
        print(dia)
        print(f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia}' AND estado = 'Aprobado'")
        validador = db_execute(
            f"SELECT correo FROM eventos WHERE terraza = {terraza} AND dia = '{dia}' AND estado = 'Aprobado'")
        print(validador)
        if len(validador) > 0 and eventsvalue == 'Aprobado':
            flash(f'La terraza {terraza} ya esta apartada el dia {dia}, revisa fecha', 'danger')
            return redirect(url_for('eventos.gestioneventos'))
        else:
            db_execute("UPDATE eventos SET estado =\"%s\"  WHERE id_eventos =\"%s\";" % (eventsvalue, eventsid))
            db_execute(
                "SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email AND eventos.dia >= '%s';" % now)
            flash(f'La terraza {terraza} fue  cambiada a {eventsvalue} el dia {dia} con éxito', 'success')
            return redirect(url_for('eventos.gestioneventos'))

        return redirect(url_for('eventos.gestioneventos'))

    return redirect(url_for('eventos.gestioneventos'))


@eventos.route('/gestioneventoshistorico', methods=['GET', 'POST', 'UPDATE'])
@is_user
@is_logged_in
@usuario_notificaciones
def gestioneventoshistorico(**kws):
    tz = pytz.timezone('America/Mexico_City')
    ct = datetime.now(tz=tz)
    tzone = ct
    now = ct
    now = str(now)
    eventos = db_execute("SELECT eventos.*, usuarios.* FROM eventos, usuarios WHERE eventos.correo = usuarios.email "
                         "AND eventos.dia < '%s';" % now)
    array_eventos = []
    for row in eventos:
        estado = (row['estado'])
        email = (row['correo'])
        nombre = (row['nombre_eventos'])
        terraza = (row['terraza'])
        dia = (row['dia'])
        domicilio = (row['domicilio'])
        telefono = (row['telefono'])
        id_eventos = (row['id_eventos'])

        array_eventos.append({'estado': (estado),
                              'id_eventos': id_eventos,
                              'email': email,
                              'nombre': nombre,
                              'terraza': terraza,
                              'domicilio': domicilio,
                              'telefono': telefono,
                              'dia': dia})
    if len(eventos) > 0:
        return render_template('gestioneventoshistorico.html',  cont=kws['cont'], com=kws['com'], eventos=array_eventos)
    else:
        msg = 'No hay eventos asociados al coto'
        return render_template('eventos/gestioneventoshistorico.html',  cont=kws['cont'], com=kws['com'],
                               eventos=array_eventos, msg=msg)
    cur.close()


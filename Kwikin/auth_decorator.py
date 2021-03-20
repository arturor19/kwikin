from flask import session, render_template
from functools import wraps
import sqlite3

db_sqlite = 'kw.db'

list_create_db = ['''CREATE TABLE "usuarios" (
	"id_usuario"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"nombre"	TEXT,
	"imagen"	TEXT,
	"email"	TEXT UNIQUE,
	"status"	TEXT DEFAULT "Activo",
	"domicilio"	TEXT,
	"id_google"	TEXT,
	"telefono"	TEXT
);''',

'''CREATE TABLE "terrazas" (
	"id_terrazas"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	"terraza"	TEXT NOT NULL,
	"descripcion" TEXT NULL
);''',

'''CREATE TABLE "qr" (
	"id_qr"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"codigo_qr"	TEXT,
	"inicio"	TEXT,
	"fin"	TEXT,
	"visitante"	TEXT,
	"correo_visitante"	TEXT,
	"placas"	TEXT,
	"inicio_real"	TEXT,
	"fin_real"	TEXT,
	"estado"	TEXT DEFAULT "Activo"
, "timestamp" TEXT, tipo TEXT, estado_acceso TEXT, autobloqueo INTEGER DEFAULT 0);''',

'''CREATE TABLE "productos" (
	"id_producto"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"nombre_producto"	TEXT UNIQUE,
	"descripcion"	TEXT
);''',

'''CREATE TABLE "grupos" (
	"id_grupo"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"nombre_grupo"	TEXT,
	"descripcion"	TEXT
);''',

'''CREATE TABLE "eventos" (
	"id_eventos"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	"terraza"	TEXT NOT NULL,
	"nombre_eventos"	TEXT NOT NULL,
	"correo"	TEXT NOT NULL,
	"dia"	NUMERIC NOT NULL,
	"estado"	TEXT DEFAULT "Pendiente"
);''',

'''CREATE TABLE "domicilios" (
	"id_dom"	INTEGER PRIMARY KEY AUTOINCREMENT,
	"direccion"	TEXT,
	"adeudo"	NUMERIC,
	"coto"	TEXT
);''',

'''CREATE TABLE "comunicados" (
	"id_notificaciones"	INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT UNIQUE,
	"fecha"	TEXT,
	"titulo"	TEXT,
	"mensaje"	TEXT,
	"idmultiple_mensaje"	TEXT,
	"email_usuario_receptor"	TEXT,
	"tipo"  TEXT,
	"opcion_a" TEXT,
	"opcion_b" TEXT,
	"opcion_c" TEXT,
	"opcion_d" TEXT,
	"resultado"  TEXT,
	"leido"	INTEGER,
	"id_usuario_emisor"	INTEGER,
	FOREIGN KEY("id_usuario_emisor") REFERENCES "usuarios"("id_usuario")
);''',

'''CREATE TABLE "asoc_usuario_grupo" (
	"id_grupo"	INTEGER,
	"id_usuario"	INTEGER,
	FOREIGN KEY("id_usuario") REFERENCES "usuarios"("id_usuario"),
	FOREIGN KEY("id_grupo") REFERENCES "grupos"("id_grupo")
);''',

'''CREATE TABLE "asoc_qr_usuario" (
	"id_usuario"	INTEGER,
	"id_qr"	INTEGER,
	FOREIGN KEY("id_qr") REFERENCES "qr"("id_qr"),
	FOREIGN KEY("id_usuario") REFERENCES "usuarios"("id_usuario")
);''',
'''INSERT INTO "main"."grupos" ("id_grupo", "nombre_grupo", "descripcion") VALUES ('1', 'superadmin', 'Super administrador');''',
'''INSERT INTO "main"."grupos" ("id_grupo", "nombre_grupo", "descripcion") VALUES ('2', 'vendedor', 'Vendedor');''',
'''INSERT INTO "main"."grupos" ("id_grupo", "nombre_grupo", "descripcion") VALUES ('3', 'admin', 'Administrador');''',
'''INSERT INTO "main"."grupos" ("id_grupo", "nombre_grupo", "descripcion") VALUES ('4', 'residente', 'Residente');''',
'''INSERT INTO "main"."grupos" ("id_grupo", "nombre_grupo", "descripcion") VALUES ('5', 'guardia', 'Guardia');''']


def db_create(db_name):
    vsm_db = sqlite3.connect("./" + db_name + ".db") # db conn
    dbh = vsm_db.cursor()  # db cursor
    # excecute sql statement
    for query in list_create_db:
        dbh.execute(query)
        desc = dbh.description
    vsm_db.commit()
    data = vsm_db.total_changes
    dbh.close()
    vsm_db.close()
    return data



def db_execute(query):
    query_lc = query.lower()
    vsm_db = sqlite3.connect(db_sqlite) # db conn
    dbh = vsm_db.cursor()  # db cursor
    # excecute sql statement
    dbh.execute(query)
    desc = dbh.description
    if "select" in query_lc:
        column_names = [col[0] for col in desc]
        data = [dict(zip(column_names, row)) for row in dbh.fetchall()]  # store query in dictionary
    else:
        vsm_db.commit()
        data = vsm_db.total_changes
    dbh.close()
    vsm_db.close()
    return data

def db_describe(query):
    vsm_db = sqlite3.connect(db_sqlite) # db conn
    dbh = vsm_db.cursor()  # db cursor
    # excecute sql statement
    dbh.execute(query)
    desc = dbh.description
    return desc

def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = dict(session).get('profile', None)
        # You would add a check here and usethe user id or something to fetch
        # the other data for that user/check if they exist
        if user:
            return f(*args, **kwargs)
        return render_template('login.html')
    return decorated_function

def is_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            grupo = (db_execute(
                "select id_grupo from asoc_usuario_grupo where id_usuario = (select id_usuario from usuarios "
                "where email = '{}')".format(session['profile']['email']))[0]['id_grupo'])
            email = session['profile']['email']
            termycon = db_execute(f"SELECT termycon FROM usuarios WHERE email = '{email}'")[0]['termycon']
        except:
            grupo = None
        if grupo is not None and termycon == "Acepto":
            email = session['profile']['email']
            name = session['profile']['name']
            id_google = (session['profile']['id'])
            picture = session['profile']['picture']
            db_execute(f'update usuarios set nombre = "{name}", id_google = {id_google}, imagen = "{picture}" where '
                       f'email = "{email}"')
            return f(*args, **kwargs)
        else:
            return render_template('404.html')
    return decorated_function


def usuario_notificaciones(f):
    @wraps(f)
    def decorated_function(**kws):
        email = dict(session)['profile']['email']
        conta = db_execute(f"SELECT * FROM comunicados WHERE leido = 0 AND email_usuario_receptor = '{email}'")
        cont = len(conta)
        com = db_execute(f"SELECT * FROM comunicados WHERE email_usuario_receptor = '{email}' AND (leido != 2) ")

        array_com = []
        for row in com:
            id_notificaciones = (row['id_notificaciones'])
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
        return f(**kws)
        #return render_template('layout.html', cont=cont, com=array_com)
    return decorated_function



#print(db_describe('select * from asoc_usuario_grupo'))
#print(db_execute('select * from usuarios'))
#print(db_execute("insert into asoc_usuario_grupo (id_grupo, id_usuario) values (1, 2);"))

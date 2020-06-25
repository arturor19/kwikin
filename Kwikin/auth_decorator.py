from flask import session, render_template
from functools import wraps
import sqlite3

db_sqlite = 'kw.db'

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
        return render_template('404.html')
    return decorated_function

def is_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            grupo = (db_execute(
                "select id_grupo from asoc_usuario_grupo where id_usuario = (select id_usuario from usuarios "
                "where email = '{}')".format(session['profile']['email']))[0]['id_grupo'])
        except:
            grupo = None
        if grupo is not None:
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



#print(db_describe('select * from asoc_usuario_grupo'))
#print(db_execute('select * from usuarios'))
#print(db_execute("insert into asoc_usuario_grupo (id_grupo, id_usuario) values (1, 2);"))

from flask import session, render_template
from functools import wraps
import sqlite3

con = sqlite3.connect('kw.db')

def db_execute(query):
    query_lc = query.lower()
    vsm_db = con # db conn
    dbh = vsm_db.cursor()  # db cursor
    # excecute sql statement
    dbh.execute(query)
    desc = dbh.description
    if "select" in query_lc:
        column_names = [col[0] for col in desc]
        data = [dict(zip(column_names, row)) for row in dbh.fetchall()]  # store query in dictionary
        dbh.close()
    else:
        vsm_db.commit()
        data = vsm_db.total_changes
        dbh.close()
    vsm_db.close()
    return data

def db_describe(query):
    vsm_db = con # db conn
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
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, send_file, send_from_directory
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, RadioField, SelectField, IntegerField, HiddenField
from authlib.integrations.flask_client import OAuth
from auth_decorator import is_logged_in, is_user
import os
import pandas as pd
from wtforms.fields.html5 import EmailField
from wtforms.validators import InputRequired, Email, DataRequired
from functools import wraps
import sqlite3
from Crypto.Cipher import AES
import base64
from datetime import timedelta, datetime
import time
from flask_qrcode import QRcode
import io


#../templates', static_folder='../static'
app = Flask(__name__, template_folder='templates', static_folder='static')
qrcode = QRcode(app)

# Config MySQL
#obj = AES.new('This is a key123'.encode("utf8"), AES.MODE_CBC, 'This is an IV456'.encode("utf8"))

# init MYSQL
# Session config
app.secret_key = os.getenv("APP_SECRET_KEY")
app.config['SESSION_COOKIE_NAME'] = 'google-login-session'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(minutes=15)
cipher = AES.new("1234567890123456".encode("utf8"), AES.MODE_ECB)

# oAuth Setup
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/userinfo/v2/me',  # This is only needed if using openId to fetch user info
    client_kwargs={'scope': 'openid email profile'},
)

@app.route('/login')
def login():
    google = oauth.create_client('google')  # create the google oauth client
    redirect_uri = url_for('authorize', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/authorize')
def authorize():
    google = oauth.create_client('google')  # create the google oauth client
    token = google.authorize_access_token()  # Access token from google (needed to get user info)
    resp = google.get('userinfo')  # userinfo contains stuff u specificed in the scrope
    user_info = resp.json()
    user = oauth.google.userinfo()  # uses openid endpoint to fetch user info
    # Here you use the profile/user data that you got and query your database find/register the user
    # and set ur own data in the session not the profile from google
    session['profile'] = user_info
    session.permanent = True  # make the session permanant so it keeps existing after broweser gets closed
    return redirect(url_for('dashboard'))
# Index
@app.route('/')
def index():
    return render_template('login.html')

@app.route('/dashboard')
@is_user
@is_logged_in
def dashboard():
    name = dict(session)['profile']['name']
    email = dict(session)['profile']['email']
    family_name = dict(session)['profile']['family_name']
    given_name = dict(session)['profile']['given_name']
    picture = dict(session)['profile']['picture']
    return render_template('dashboard.html', name=name, picture=picture)

@app.route('/logout')
def logout():
    for key in list(session.keys()):
        session.pop(key)
    return render_template('login.html')

@app.route('/crearqr', methods=['GET', 'POST'])
@is_logged_in
def peticionqr():
    if request.method == 'POST':
        print(request.form)
        if request.form['dateE'] > request.form['dateS'] or request.form['dateE'] < str(datetime.now()):
            flash('Por favor valida que las fechas sean correctas')
        else:
            fecha_entrada = request.form['dateE']
            fecha_salida = request.form['dateS']
            nombre = request.form['name']
            qr = qrcode("quedsfsiii", mode="raw", start_date=fecha_entrada, end_date=fecha_salida)
            return send_file(qr, mimetype="image/png")
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    return render_template('crearpeticionQR.html',  name=name, picture=picture)


@app.route("/qrcode", methods=['GET', 'POST'])
def get_qrcode():
    if request.method == 'POST':
        fecha_entrada = request.form['dateE']
        fecha_salida = request.form['dateS']
        nombre = request.form['name']
        qr = qrcode("quedsfsiii", mode="raw", start_date=fecha_entrada, end_date=fecha_salida)
    print(qr)
    return send_file(qr, mimetype="image/png")

@app.route('/crearInd', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def crearInd():
    if request.method == 'POST':
        domicilio = request.form['direccion']
        email = request.form['correo']
        checkguardia = request.form.get('checkguardia')
        if checkguardia == 'on':
            grupo = 4
        else:
            grupo = 3
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        try:
            cur.execute("INSERT INTO usuarios(domicilio, email) VALUES(\"%s\", \"%s\")" % (
            domicilio, email))
            flash('Usuario agregado correctamente')
            mysql.commit()
        except:
            flash('Correo ya existe')
        try:
            cur.execute(f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
            mysql.commit()
        except:
            flash(f'El correo {email} no pudo asociar un grupo, contacta un administrador')
        cur.close()
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    return render_template('crearIndividual.html', name=name, picture=picture)

@app.route('/crearBulk', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def upload():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    if request.method == 'POST':
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        df = pd.read_csv(request.files.get('file'))
        for index, row in df.iterrows():
            email = row['Email']
            domicilio = row['Direccion']
            if '@gmail.com' in email:
                try:
                    cur.execute(f"INSERT INTO usuarios(domicilio, email) VALUES('{domicilio}','{email}')")
                except:
                    flash(f'El correo {email} ya existe')
                mysql.commit()
                cur.execute(
                    f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values (3, (SELECT id_usuario FROM "
                    f"usuarios WHERE email = '{email}'))")
                mysql.commit()
            else:
                flash(f'El correo {email} es incorrecto, por favor valida que sea Gmail')
        cur.close()
        return render_template('crearBulk.html', name=name, picture=picture)
    return render_template('crearBulk.html', name=name, picture=picture)

@app.route('/gestionusuarios', methods=['GET', 'POST', 'UPDATE'] )
@is_user
@is_logged_in
def gestionusuarios():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    result = cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()
    array = []
    for row in usuarios:
        status = (row[4])
        email = (row[3])
        nombre = (row[1])
        domicilio = (row[5])

        array.append({'status': (status),
                      'email': email,
                      'nombre': nombre,
                      'domicilio': domicilio})
    if int(result.rowcount) > 0:
        return render_template('gestionusuarios.html', usuarios=array, name=name, picture=picture)
    else:
        msg = 'No hay usuarios asociados al coto'
        return render_template('gestionusuarios.html', usuarios=array, name=name, picture=picture,msg=msg)
    cur.close()

@app.route('/actusuario', methods=['POST'])
@is_user
@is_logged_in
def actusuario():
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    mysql = sqlite3.connect('kw.db')
    cur = mysql.cursor()
    ids = None
    if request.method == "POST":
        ids=request.form['data']
        result = cur.execute("SELECT status FROM usuarios WHERE email = '%s';" % ids)
        result = cur.fetchone()
        if str(result) == "('Activo',)":
            cur.execute("UPDATE usuarios SET status = 'Inactivo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html',  name=name, picture=picture)
        elif str(result) == "('Inactivo',)":
            cur.execute("UPDATE usuarios SET status = 'Activo' WHERE email = '%s';" % ids)
            mysql.commit()
            return render_template('gestionusuarios.html', name=name, picture=picture)
    cur.close()
    return render_template('gestionusuarios.html', name=name, picture=picture)

@app.route('/ventas', methods=['GET', 'POST'] )
@is_user
@is_logged_in
def ventas():
    if request.method == 'POST':
        domicilio = request.form['direccion']
        email = request.form['correo']
        checkguardia = request.form.get('checkguardia')
        if checkguardia == 'on':
            grupo = 4
        else:
            grupo = 3
        mysql = sqlite3.connect('kw.db')
        cur = mysql.cursor()
        try:
            cur.execute("INSERT INTO usuarios(domicilio, email) VALUES(\"%s\", \"%s\")" % (
            domicilio, email))
            flash('Usuario agregado correctamente')
            mysql.commit()

        except:
            flash('Correo ya existe')
        try:
            cur.execute(f"insert into asoc_usuario_grupo (id_grupo, id_usuario) values ({grupo}, (SELECT id_usuario FROM usuarios WHERE email = '{email}'))")
            mysql.commit()
        except:
            flash(f'El correo {email} no pudo asociar un grupo, contacta un administrador')
        cur.close()
    name = dict(session)['profile']['name']
    picture = dict(session)['profile']['picture']
    return render_template('ventas.html', name=name, picture=picture)

# De aqui para abajo creo que es basura, pero nos puede servir para ver como insertar en la BD
@app.route('/articles')
def articles():
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get articles
    result = cur.execute("SELECT * FROM articles")

    articles = cur.fetchall()

    if int(result.rowcount) > 0:
        return render_template('articles.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('articles.html', msg=msg)
    # Close connection
    cur.close()


#Single Article
@app.route('/article/<string:id>/')
def article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get article
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()

    return render_template('article.html', article=article)






#unique


@app.route('/unique', methods=['GET', 'POST'])
def unique():
    if request.method == 'POST':
        user = request.form['fingerprint']
        print(user)
    return render_template('unique.html')






# Dashboard
@app.route('/dashboardpaborrar')
@is_logged_in
@is_user
def dashboardpaboorar():

    mysql = sqlite3.connect('qr.db')
    # Create cursor
    cur = mysql.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = \"%s\"" % session['username'])

    articles = cur.fetchall()

    array = []
    for row in articles:
        id = (row[0])
        title = (row[1])
        body = (row[2])
        author = (row[3])

        array.append({'id' : int(id),
                      'title' : title,
                      'body' : body,
                      'author' : author})

    print(array)

    print(result.rowcount)
    if int(len(array)) > 0:
        return render_template('dashboardpaborrar.html', articles=array)
    else:
        msg = 'No Articles Found'
        return render_template('dashboardpaborrar.html', msg=msg)
    # Close connection
    cur.close()






# Article Form Class
class ArticleForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=200)])
    body = TextAreaField('Body', [validators.Length(min=30)])

# Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
    form = ArticleForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        body = form.body.data

        # Create Cursor
        mysql = sqlite3.connect('qr.db')
        cur = mysql.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(\"%s\", \"%s\", \"%s\")" % (title, body, session['username']))

        # Commit to DB
        mysql.commit()

        #Close connection
        cur.close()

        flash('Article Created', 'success')

        return redirect(url_for('dashboard'))

    return render_template('add_article.html', form=form)


# Edit Article
@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Get article by id


    article = cur.execute("SELECT * FROM articles WHERE article_id = \"%s\"" % id).fetchall()

    # Get form
    form = ArticleForm(request.form)

    art = []

    print(article)

    for row in article:
        id = (row[0])
        title = (row[1])
        body = (row[2])
        author = (row[3])

        art.append({'id' : int(id),
                      'title' : title,
                      'body' : body,
                      'author' : author})

    cur.close()
    # Populate article form fields
    form.title.data = art[0]['title']
    form.body.data = art[0]['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=\"%s\", body=\"%s\" WHERE article_id=\"%s\"" % (title, body, id))
        # Commit to DB
        mysql.commit()

        #Close connection
        cur.close()

        flash('Article Updated', 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', form=form)

# Delete Article
@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
    # Create cursor
    mysql = sqlite3.connect('qr.db')
    cur = mysql.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE article_id = \"%s\"" % id)

    # Commit to DB
    mysql.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))


if __name__ == '__main__':
    app.run(debug=True)

import os
from flask_sqlalchemy import SQLAlchemy
import pydicom
from pydicom.data import get_testdata_file
import tempfile
import pydicom
from pydicom.data import get_testdata_file
from flask import Flask, render_template, flash, redirect, url_for, session, request, logging, current_app
#from data import Articles
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators, FileField
from flask_wtf.file import FileRequired
from passlib.hash import sha256_crypt
from functools import wraps

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "mysql://momo:passer@127.0.0.1/telediagnostic"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
UPLOAD_FOLDER = '/home/momo/Desktop/telediagnostic/dicomfiles'
DOWNLOAD_FOLDER = '/home/momo/Downloads'
RAPPORT_FOLDER = '/home/momo/Desktop/telediagnostic/rapports'
app.config['DOWNLOAD_FOLDER'] = DOWNLOAD_FOLDER
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RAPPORT_FOLDER'] = RAPPORT_FOLDER

# Config MySQL
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = '123456'
# app.config['MYSQL_DB'] = 'myflaskapp'
# app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
# init MYSQL
#mysql = MySQL(app)


@app.route('/')
def index():
    return render_template('login.html')

@app.route("/login",methods=["POST", "GET"])
def login():
    email = request.form.get("username")
    password = request.form.get("password")
    user = Medecin.query.filter_by(email=email).first()

    if not user :
        return "Login ou mot de passe incorrect "
    
    elif user.password != password:
        return "Login ou mot de passe incorrect "

    else:
        return render_template('home.html')


# Index
#@app.route('/home')
#def home():
#   return render_template('home.html')


# About
@app.route('/about')
def about():
    return render_template('about.html')

# Register Form Class
class RegisterForm(Form):
    #dicomfile = FileField('DICOM')
    codeCC = StringField('Code CCAM')
    modalite = StringField('Modalité')
    examef = StringField('Examen effectué')
    numeroO = StringField('Numéro ordre')
    obsvCl = StringField('Observation clinique')
    quesCl = StringField('Question clinicien')
    obsvTech = StringField('Observation technicien')
    medecin = StringField('Medecin')
    image = StringField('UrlImage')

class Medecin(db.Model):
    __tablename__ ='medecin'

    idmedecin = db.Column(db.Integer, primary_key=True, autoincrement=True)
    prenom = db.Column(db.String(100))
    nom = db.Column(db.String(100))
    email = db.Column(db.String(100))
    password = db.Column(db.String(100))

    def __init__(self, prenom, nom, email, password):
        self.prenom = prenom
        self.nom = nom
        self.email = email
        self.password = password


class Rapport(db.Model):
    __tablename__ = 'rapport'

    idrapport = db.Column(db.Integer, primary_key = True, autoincrement=True)
    rapport = db.Column(db.String(100))
    medecin = db.Column(db.Integer, db.ForeignKey('medecin.idmedecin'))

    def __init__(self, rapport):
        self.rapport = rapport



class Patient(db.Model):
    __tablename__ = 'patient'

    idpatient = db.Column(db.Integer, primary_key = True, autoincrement=True)
    prenom = db.Column(db.String(100))
    nom = db.Column(db.String(50))
    sexe = db.Column(db.Enum("M", "F"))
    datenaissance = db.Column(db.DATE)

    def __init__(self, prenom, nom, sexe, datenaissance):
        self.prenom = prenom
        self.nom = nom
        self.sexe = sexe
        self.datenaissance = datenaissance

class Demande(db.Model):
    __tablename__ = 'demande' 

    iddemande = db.Column(db.Integer, primary_key = True, autoincrement=True)
    codeccam = db.Column(db.String(100))
    modalité = db.Column(db.String(200))
    exameffectue = db.Column(db.String(200))
    numorde = db.Column(db.Integer())
    observationclinique = db.Column(db.String(200))   
    questionclinicien = db.Column(db.String(200))
    observationtech = db.Column(db.String(200))
    image = db.Column(db.String(100))
    medecin = db.Column(db.String(100))

    def __init__(self, codeccam, modalité, exameffectue, numorde, observationclinique, questionclinicien, observationtech, image, medecin):
        self.codeccam = codeccam
        self.modalité = modalité
        self.exameffectue = exameffectue
        self.numorde = numorde
        self.observationclinique = observationclinique
        self.questionclinicien = questionclinicien
        self.observationtech = observationtech
        self.image = image
        self.medecin = medecin

class concerner(db.Model):
    __tablename__ = 'concerner'

    medecin = db.Column(db.Integer, db.ForeignKey('medecin.idmedecin'), primary_key=True)
    patient = db.Column(db.Integer, db.ForeignKey('patient.idpatient'), primary_key=True)
    rapport = db.Column(db.Integer, db.ForeignKey('rapport.idrapport'), primary_key=True)
    demande = db.Column(db.Integer, db.ForeignKey('demande.iddemande'), primary_key=True)

def make_tree(path):
    tree = dict(name=os.path.basename(path), children=[])
    try: lst = os.listdir(path)
    except OSError:
        pass #ignore errors
    else:
        for name in lst:
            fn = os.path.join(path, name)
            if os.path.isdir(fn):
                tree['children'].append(make_tree(fn))
            else:
                tree['children'].append(dict(name=name))
    return tree




@app.route('/demande', methods=['GET', 'POST'])
def demande():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        fichier = request.files['mon_fichier']
        codeCC = form.codeCC.data
        modalite = form.modalite.data
        examef = form.examef.data
        numeroO = form.numeroO.data
        obsvCl = form.obsvCl.data
        quesCl = form.quesCl.data
        obsvTech = form.obsvTech.data
        image = form.image.data
        medecin = form.medecin.data

        nom_fichier = fichier.filename
        if (nom_fichier[-4:] == '.dcm' or nom_fichier[-4:] == '.DCM'):
            dataset = pydicom.dcmread(nom_fichier)

            data_elements = ['PatientID',
                        'PatientBirthDate']
            elements = list()
            for de in data_elements:
                elements.append(dataset.data_element(de))

            ###############################################################################
            # We can define a callback function to find all tags corresponding to a person
            # names inside the dataset. We can also define a callback function to remove
            # curves tags.


            def person_names_callback(dataset, data_element):
                if data_element.VR == "PN":
                    data_element.value = "anonymous"


            def curves_callback(dataset, data_element):
                if data_element.tag.group & 0xFF00 == 0x5000:
                    del dataset[data_element.tag]


            ###############################################################################
            # We can use the different callback function to iterate through the dataset but
            # also some other tags such that patient ID, etc.

            dataset.PatientID = "id"
            dataset.walk(person_names_callback)
            dataset.walk(curves_callback)

            ###############################################################################
            # pydicom allows to remove private tags using ``remove_private_tags`` method

            dataset.remove_private_tags()

            ###############################################################################
            # Data elements of type 3 (optional) can be easily deleted using ``del`` or
            # ``delattr``.

            if 'OtherPatientIDs' in dataset:
                delattr(dataset, 'OtherPatientIDs')

            if 'OtherPatientIDsSequence' in dataset:
                del dataset.OtherPatientIDsSequence

            ###############################################################################
            # For data elements of type 2, this is possible to blank it by assigning a
            # blank string.

            tag = 'PatientBirthDate'
            if tag in dataset:
                dataset.data_element(tag).value = '19000101'

            ##############################################################################
            # Finally, this is possible to store the image

            data_elements = ['PatientID',
                            'PatientBirthDate']
            #for de in data_elements:
            #   print(dataset.data_element(de))

            output_filename = tempfile.NamedTemporaryFile().name
            dataset.save_as(output_filename)
            # elif nom_fichier[-4:] != '.dcm' and nom_fichier[-4:] != '.DCM':
            #     return 'Choisir un fichier dicom'

            demandePatient = Demande(codeCC, modalite, examef, numeroO, obsvCl, quesCl, obsvTech, image, medecin)
            db.session.add(demandePatient)
            db.session.commit()

            # # Create cursor
            # cur = mysql.connection.cursor()

            # # Execute query
            # cur.execute("INSERT INTO users(name, email, username, password) VALUES(%s, %s, %s, %s)", (name, email, username, password))

            # # Commit to DB
            # mysql.connection.commit()

            # # Close connection
            # cur.close()

            # flash('You are now registered and can log in', 'success')
            fichier.save(os.path.join(app.config['UPLOAD_FOLDER'], nom_fichier))
            path = '/home/momo/Desktop/telediagnostic/rapports'
            return render_template('dicom.html', data_elements = data_elements, dataset = dataset, elements = elements, tree=make_tree(path))
        elif nom_fichier[-4:] != '.dcm' and nom_fichier[-4:] != '.DCM':
            return 'Choisir un fichier dicom'
    return render_template('register.html', form=form)



@app.route('/radiologue', methods=['GET', 'POST'])
def radiologue():
    form = RegisterForm(request.form)
    if request.method == 'POST':
        fichier = request.files['rapport']
        nom_fichier = fichier.filename
        fichier.save(os.path.join(app.config['RAPPORT_FOLDER'], nom_fichier))
    demande = Demande.query.all()
    path = '/home/momo/Desktop/telediagnostic/dicomfiles'
    return render_template('radiologue.html', demande = demande, tree=make_tree(path))
    

# Check if user logged in
@app.route('/dwnload', methods=['GET', 'POST'])
def download():
    #uploads = os.path.join(app.config['DOWNLOAD_FOLDER'])
    #radiologue()
    #return 'YES'
    #return render_template('login.html', demande = demande, tree=make_tree(path))
    uploads = os.path.join(app.config['RAPPORT_FOLDER'])
    return send_from_directory(directory=uploads)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap

# Logout
@app.route('/logout')
@is_logged_in
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
    # Create cursor
    cur = mysql.connection.cursor()

    # Get articles
    #result = cur.execute("SELECT * FROM articles")
    # Show articles only from the user logged in 
    result = cur.execute("SELECT * FROM articles WHERE author = %s", [session['username']])

    articles = cur.fetchall()

    if result > 0:
        return render_template('dashboard.html', articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html', msg=msg)
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
        cur = mysql.connection.cursor()

        # Execute
        cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title, body, session['username']))

        # Commit to DB
        mysql.connection.commit()

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
    cur = mysql.connection.cursor()

    # Get article by id
    result = cur.execute("SELECT * FROM articles WHERE id = %s", [id])

    article = cur.fetchone()
    cur.close()
    # Get form
    form = ArticleForm(request.form)

    # Populate article form fields
    form.title.data = article['title']
    form.body.data = article['body']

    if request.method == 'POST' and form.validate():
        title = request.form['title']
        body = request.form['body']

        # Create Cursor
        cur = mysql.connection.cursor()
        app.logger.info(title)
        # Execute
        cur.execute ("UPDATE articles SET title=%s, body=%s WHERE id=%s",(title, body, id))
        # Commit to DB
        mysql.connection.commit()

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
    cur = mysql.connection.cursor()

    # Execute
    cur.execute("DELETE FROM articles WHERE id = %s", [id])

    # Commit to DB
    mysql.connection.commit()

    #Close connection
    cur.close()

    flash('Article Deleted', 'success')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.secret_key='secret123'
    app.run(debug=True, port=3000)

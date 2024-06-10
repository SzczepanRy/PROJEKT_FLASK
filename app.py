from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, FileField
from wtforms.fields.choices import SelectField
from wtforms.validators import DataRequired, Length
from flask_wtf.file import FileAllowed
from werkzeug.utils import secure_filename
from flask_bcrypt import Bcrypt
from flask_bs4 import Bootstrap
import os
from datetime import datetime

# app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
bootstrap = Bootstrap(app)
bcrypt = Bcrypt(app)
app.config['UPLOAD_PATH'] = 'uploads'
app.config['UPLOAD_FOLDER'] = ''
app.config['UPLOAD_EXTENSIONS'] = ['.txt', '.jpg', '.jpeg', '.png', '.gif', '.php']
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# database
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'+os.path.join(basedir,'data/users.sqlite')
db = SQLAlchemy(app)

# db table
class Users(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    firstName = db.Column(db.String(50))
    lastName = db.Column(db.String(50))
    userMail = db.Column(db.String(50), unique=True)
    userPass = db.Column(db.String(100))
    userRole = db.Column(db.String(50))

    def is_authenticated(self):
        return True


class Folders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    folderName = db.Column(db.String(50), unique=True)
    type = db.Column(db.String(50))
    icon = db.Column(db.String(50))
    time = db.Column(db.String(50))


class Files(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fileName = db.Column(db.String(50), unique=True)
    type = db.Column(db.String(50))
    icon = db.Column(db.String(50))
    time = db.Column(db.String(50))
    size = db.Column(db.String(50))


# flask login
loginManager = LoginManager()
loginManager.init_app(app)
loginManager.login_view = 'login'
loginManager.login_message = 'Nie jesteś zalogowany'
loginManager.login_message_category = 'warning'

@loginManager.user_loader
def loadUser(id):
    return Users.query.filter_by(id=id).first()

# froms
class Login(FlaskForm):
    userMail = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Zaloguj się')


class Register(FlaskForm):
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Zarejestruj się')

class Add(FlaskForm):
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'User'), ('staff', 'Staff'), ('moderator', 'Moderator'), ('admin', 'Admin')])
    submit = SubmitField('Zarejestruj się')

class Edit(FlaskForm):
    firstName = StringField('Imię', validators=[DataRequired()], render_kw={"placeholder": "Imię"})
    lastName = StringField('Nazwisko', validators=[DataRequired()], render_kw={"placeholder": "Nazwisko"})
    userMail = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email"})
    userRole = SelectField('Uprawnienia', validators=[DataRequired()], choices=[('user', 'User'), ('staff', 'Staff'), ('moderator', 'Moderator'), ('admin', 'Admin')])
    submit = SubmitField('Zarejestruj się')

class ChangePass(FlaskForm):
    userPass = PasswordField('Hasło', validators=[DataRequired()], render_kw={"placeholder": "Hasło"})
    submit = SubmitField('Zmień hasło')

class ChangePassLoggedIn(FlaskForm):
    userMail = EmailField('Email', validators=[DataRequired()], render_kw={"placeholder": "Email", "readonly": True})
    userPassOld = PasswordField('Bieżące hasło', validators=[DataRequired()], render_kw={"placeholder": "Bieżące hasło"})
    userPassNew = PasswordField('Nowe hasło', validators=[DataRequired()], render_kw={"placeholder": "Nowe hasło"})
    submit = SubmitField('Zmień hasło')

class Search(FlaskForm):
    search = StringField('Szukaj', validators=[DataRequired()])
    submit = SubmitField('Szukaj')

class CreateFile(FlaskForm):
    fileName = StringField('Nazwa pliku', validators=[DataRequired()], render_kw={"placeholder": "Nazwa pliku"})
    submit = SubmitField('Utwórz')

# class CreateFolder(FlaskForm):
#     folderName = StringField('Nazwa folderu', validators=[DataRequired()], render_kw={"placeholder": "Nazwa folderu"})
#     submit = SubmitField('Utwórz')

class NameForm(FlaskForm):
    name = StringField('Nazwa folderu', validators=[DataRequired()], render_kw={"placeholder": "Nazwa folderu"})
    submit = SubmitField('Utwórz')

class UploadFile(FlaskForm):
    fileName = FileField('Plik', validators=[DataRequired(), FileAllowed(app.config['UPLOAD_EXTENSIONS'], 'Tylko pliki: .txt, .jpg, .jpeg, .png, .gif')])#, render_kw={"placeholder": ".txt, .jpg, .jpeg, .png, .gif"})
    submit = SubmitField('Prześlij')



# main app


def getFolders():

    if app.config['UPLOAD_FOLDER'] != '':
        folders = Folders.query.filter(Folders.folderName.contains(app.config['UPLOAD_FOLDER'])).all()
        for folder in folders:
            folder.folderName = folder.folderName.replace(app.config['UPLOAD_FOLDER'], '')

        return folders
    else:
        return Folders.query.filter(~Folders.folderName.contains('/')).all()

    # return folders

def getFiles():
    if app.config['UPLOAD_FOLDER'] != '':
        files = Files.query.filter(Files.fileName.contains(app.config['UPLOAD_FOLDER'])).all()
        for file in files:
            file.fileName = file.fileName.replace(app.config['UPLOAD_FOLDER'], '')

        return files
    else:
        return Files.query.filter(~Files.fileName.contains('/')).all()

def folderBar():
    bar = app.config['UPLOAD_FOLDER'].split('/')
    bar.pop()
    folders = Folders.query.all()
    bars = []
    for folder in folders:
        tbar = "/".join(bar)
        if folder.folderName in tbar:
            bars.append(folder)
            bar.pop()
    return bars




@app.route('/')
def index():
    return render_template('index.html', title='Dashboard', headline='Zarządzanie użytkownikami')

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = Users.query.all()
    if not user:
        return redirect(url_for('register'))
    else:
        loginForm = Login()
        if loginForm.validate_on_submit():
            user = Users.query.filter_by(userMail=loginForm.userMail.data).first()
            if user and bcrypt.check_password_hash(user.userPass, loginForm.userPass.data):
                login_user(user)
                return redirect(url_for('dashboard'))
    return render_template('login.html', title='Login', headline='Logowanie', loginForm=loginForm)

@app.route('/register', methods=['GET', 'POST'])
def register():
    registerForm = Register()

    user = Users.query.all()
    role = 'user'
    if not user:
        role = 'admin'

    if registerForm.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(registerForm.userPass.data)
            newUser = Users(userMail=registerForm.userMail.data, userPass=hashPass, firstName=registerForm.firstName.data, lastName=registerForm.lastName.data,
                            userRole=role)
            db.session.add(newUser)
            db.session.commit()
            flash('Konto zostało utworzone', 'success')
            return redirect(url_for('login'))
        except Exception:
            flash('Email jest już zajęty', 'danger')
            return redirect(url_for('register'))
    return render_template('register.html', title='Register', headline='Rejestracja', registerForm=registerForm)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    users = Users.query.all()
    addUser = Add()
    editUser = Edit()
    editUserPass = ChangePass()
    search = Search()
    createFile = CreateFile()
    # createFolder = CreateFolder()
    nameForm = NameForm()
    uploadFile = UploadFile()
    folders = getFolders()      # Folders.query.all()
    files = getFiles()          # Files.query.all()
    foldersBar = folderBar()
    # files = os.listdir(app.config['UPLOAD_PATH'])
    return render_template('dashboard.html', title='Dashboard', headline='Zarządzanie użytkownikami',
                           users=users, addUser=addUser, editUser=editUser, editUserPass=editUserPass, search=search,
                           createFile=createFile, nameForm=nameForm, uploadFile=uploadFile,
                           files=files, folders=folders, foldersBar=foldersBar)

@app.route('/addUser', methods=['GET', 'POST'])
@login_required
def addUser():
    addUser = Add()
    if addUser.validate_on_submit():
        try:
            hashPass = bcrypt.generate_password_hash(addUser.userPass.data)
            newUser = Users(userMail=addUser.userMail.data, userPass=hashPass, firstName=addUser.firstName.data, lastName=addUser.lastName.data,
                            userRole=addUser.userRole.data)
            db.session.add(newUser)
            db.session.commit()
            flash('Konto zostało dodane', 'success')
            return redirect(url_for('dashboard'))
        except Exception:
            flash('Email jest już zajęty', 'danger')
            return redirect(url_for('dashboard'))

@app.route('/edit-user<int:id>', methods=['GET', 'POST'])
@login_required
def editUser(id):
    editUser = Edit()
    user = Users.query.get_or_404(id)
    if editUser.validate_on_submit():
        try:
            user.firstName = editUser.firstName.data
            user.lastName = editUser.lastName.data
            user.userMail = editUser.userMail.data
            user.userRole = editUser.userRole.data
            db.session.commit()
            flash('Konto zostało zaktualizowane', 'success')
            return redirect(url_for('dashboard'))
        except Exception:
            flash('Email jest już zajęty', 'danger')
            return redirect(url_for('dashboard'))

@app.route('/edit-user-pass<int:id>', methods=['GET', 'POST'])
@login_required
def editUserPass(id):
    editUserPass = ChangePass()
    user = Users.query.get_or_404(id)
    if editUserPass.validate_on_submit():
        user.userPass = bcrypt.generate_password_hash(editUserPass.userPass.data)
        db.session.commit()
        flash('Hasło zostało zaktualizowane', 'success')
        return redirect(url_for('dashboard'))

@app.route('/changePass', methods=['GET', 'POST'])
@login_required
def changePass():
    changePass = ChangePassLoggedIn()
    if changePass.validate_on_submit():
        user = Users.query.filter_by(userMail=changePass.userMail.data).first()
        if user and bcrypt.check_password_hash(user.userPass, changePass.userPassOld.data):
            user.userPass = bcrypt.generate_password_hash(changePass.userPassNew.data)
            db.session.commit()
            flash('Hasło zostało zaktualizowane', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Bieżące hasło jest nieprawidłowe', 'danger')
            return redirect(url_for('changePass'))
    return render_template('change-pass.html', title='Zmiana hasła', headline='Zmiana hasła', changePass=changePass)


@app.route('/delete-user', methods=['GET', 'POST'])
@login_required
def deleteUser():
    if request.method == 'GET':
        id = request.args.get('id')
        user = Users.query.filter_by(id=id).one()
        db.session.delete(user)
        db.session.commit()
        flash('Użytkownik został usunięty', 'success')
        return redirect(url_for('dashboard'))


@app.route('/upload-file', methods=['GET', 'POST'])
@login_required
def uploadFile():
    uploadedFile = request.files['fileName']
    filename = secure_filename(uploadedFile.filename)
    if filename != '':

        fileExt = os.path.splitext(filename)[1]
        if fileExt not in app.config['UPLOAD_EXTENSIONS']:
            flash('Niedozwolony format pliku', 'danger')
            return redirect(url_for('dashboard'))


        match fileExt:
            case '.txt':
                type = 'txt'
                icon = 'bi bi-filetype-txt'
            case '.jpg':
                type = 'jpg'
                icon = 'bi bi-filetype-jpg'
            case '.jpeg':
                type = 'jpeg'
                icon = 'bi bi-filetype-jpg'
            case '.png':
                type = 'png'
                icon = 'bi bi-filetype-png'
            case _:
                type = 'file'
                icon = 'bi bi-file-earmark'

        filename = app.config['UPLOAD_FOLDER'] + filename
        uploadedFile.save(os.path.join(app.config['UPLOAD_PATH'], filename))
        size = round(os.stat(os.path.join(app.config['UPLOAD_PATH'], filename)).st_size / (1024 * 1024), 4)
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        newFile = Files(fileName=filename, type=type, icon=icon, time=time, size=size)
        db.session.add(newFile)
        db.session.commit()
        flash('Plik został przesłany', 'success')
        return redirect(url_for('dashboard'))


@app.route('/create-file', methods=['GET', 'POST'])
@login_required
def createFile():
    fileName = request.form['fileName']
    if fileName != '':
        fileName = app.config['UPLOAD_FOLDER'] + fileName
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        size = ''
        os.mknod(os.path.join(app.config['UPLOAD_PATH'], fileName))
        newFile = Files(fileName=fileName, type='file', icon='bi bi-file-earmark', time=time, size=size)
        db.session.add(newFile)
        db.session.commit()
        flash('Plik został utworzony', 'success')
        return redirect(url_for('dashboard'))


@app.route('/rename-file', methods=['GET', 'POST'])
@login_required
def renameFile():
    id = request.args.get('fileID')
    file = Files.query.filter_by(id=id).one()
    # extenstion = file.fileName.split('.')[-1]
    extenstion = file.type
    fileName = app.config['UPLOAD_FOLDER'] + request.form['name'] + '.' + extenstion
    os.rename(os.path.join(app.config['UPLOAD_PATH'], file.fileName), os.path.join(app.config['UPLOAD_PATH'], fileName))
    file.fileName = fileName
    db.session.commit()
    flash('Plik został zaktualizowany', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete-file', methods=['GET', 'POST'])
@login_required
def deleteFile():
    id = request.args.get('fileID')
    file = Files.query.filter_by(id=id).one()
    os.remove(os.path.join(app.config['UPLOAD_PATH'], file.fileName))
    db.session.delete(file)
    db.session.commit()
    flash('Plik został usunięty', 'success')
    return redirect(url_for('dashboard'))


@app.route('/create-folder', methods=['GET', 'POST'])
@login_required
def createFolder():
    folderName = request.form['name']
    if folderName != '':
        folderName = app.config['UPLOAD_FOLDER'] + folderName
        time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        os.mkdir(os.path.join(app.config['UPLOAD_PATH'], folderName))
        newFolder = Folders(folderName=folderName, type='folder', icon='bi bi-folder', time=time)
        db.session.add(newFolder)
        db.session.commit()
        flash('Folder został utworzony', 'success')
        return redirect(url_for('dashboard'))


@app.route('/rename-folder', methods=['GET', 'POST'])
@login_required
def renameFolder():
    id = request.args.get('folderID')
    folder = Folders.query.filter_by(id=id).one()
    folderName = app.config['UPLOAD_FOLDER'] + request.form['name']
    os.rename(os.path.join(app.config['UPLOAD_PATH'], folder.folderName), os.path.join(app.config['UPLOAD_PATH'], folderName))
    folder.folderName = folderName
    db.session.commit()
    flash('Folder został zaktualizowany', 'success')
    return redirect(url_for('dashboard'))




@app.route('/delete-folder', methods=['GET', 'POST'])
@login_required
def deleteFolder():
    id = request.args.get('folderID')
    folder = Folders.query.filter_by(id=id).one()
    os.rmdir(os.path.join(app.config['UPLOAD_PATH'], folder.folderName))
    db.session.delete(folder)
    db.session.commit()
    flash('Folder został usunięty', 'success')
    return redirect(url_for('dashboard'))


@app.route('/enter-folder', methods=['GET', 'POST'])
@login_required
def enterFolder():
    folderID = request.args.get('folderID')
    folderName = Folders.query.filter_by(id=folderID).one().folderName
    app.config['UPLOAD_FOLDER'] = folderName + '/'
    return redirect(url_for('dashboard'))

@app.route('/home-folder', methods=['GET', 'POST'])
@login_required
def homeFolder():
    app.config['UPLOAD_FOLDER'] = ''
    return redirect(url_for('dashboard'))





if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
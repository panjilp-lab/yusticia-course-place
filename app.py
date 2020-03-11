import os
import json
import psycopg2
from datetime import datetime
from models import Question
from flask import Flask, render_template, redirect, url_for, send_file, flash, request, session
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_script import Manager, Shell
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, FileField, PasswordField, BooleanField, SelectMultipleField, ValidationError
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from flask_migrate import Migrate, MigrateCommand
from flask_heroku import Heroku

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://jlgfvpgjttfcfb:e4b12b906ca1c24206518a932ba3fc7ce5200b3088eb33bda5c6b182daa7f017@ec2-34-206-252-187.compute-1.amazonaws.com:5432/d30kapn9hkf6lb'
app.config['SECRET_KEY'] = 'whoa there'

manager = Manager(app)
heroku = Heroku(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db) # For database use/updating
manager.add_command('db', MigrateCommand)

# Login configurations setup
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'login'
login_manager.init_app(app) # set up login manager

def make_shell_context():
    return dict(app=app, db=db, User=User)

# Add function use to manager
manager.add_command("shell", Shell(make_context=make_shell_context))

"""class Sekolah(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(20), unique=True)
    userss = db.relationship('User', backref='sekolah')

    def __repr__(self):
        return self.id
"""

class BlogPost(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(30), nullable=False, default='N/A')
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return 'Blog post' + str(self.id)

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    alamat = db.Column(db.String(60))
    password_hash = db.Column(db.String(128))

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

## DB load function
## Necessary for behind the scenes login manager that comes with flask_login capabilities! Won't run without this.
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) # returns User object or None


##### Set up Forms #####

class RegistrationForm(FlaskForm):
    email = StringField('Email:', validators=[Required(),Length(1,64),Email()])
    username = StringField('Username:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'email')])
    alamat = StringField('Alamat:',validators=[Required(),Length(1,64),Regexp('^[A-Za-z][A-Za-z0-9_.]*$',0,'Usernames must have only letters, numbers, dots or underscores')])
    password = PasswordField('Password:',validators=[Required(),EqualTo('password2',message="Passwords must match")])
    password2 = PasswordField("Confirm Password:",validators=[Required()])
    submit = SubmitField('Register User')

    #Additional checking methods for the form
    def validate_email(self,field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self,field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already taken')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[Required(), Length(1,64), Email()])
    password = PasswordField('Password', validators=[Required()])
    remember_me = BooleanField('Keep me logged in')
    submit = SubmitField('Log In')

## Error handling routes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')

@app.route('/visimisi')
def visimisi():
    return render_template('visimisi.html')

@app.route('/daftar')
def daftar():
    return render_template('daftar1.html')

@app.route('/soal')
def soal():
    with open('data/question_bank.json', 'rb') as choose_quiz:
        quiz_bank = json.load(choose_quiz)
#rendering page for file selection.
    return render_template("soal.html", quiz_bank=quiz_bank)

@app.route("/takequiz/<quiz_name>/")
def takeQuiz(quiz_name):
    filename = 'data/' + quiz_name + '.json'
    question = Question(filename)
    return render_template("take_quiz.html",quiz = question.quiz, quiz_name=quiz_name)

@app.route("/answer/<quiz_name>/", methods =['POST'])
def answer(quiz_name):
    filename = 'data/' + quiz_name + '.json'
    question = Question(filename)
    check = [] # list of tuples - original questions and user given answers.
    score = 0
    for option in request.form:
        q_num = int(option.split('-')[-1])
        ans_given = request.form.get(option)
        result = question.check(q_num, ans_given)# calling class method to check answers.
        if result:
            score += 1
    return render_template("result.html" ,score = score) #user can see score in result.html

@app.route('/download')
def download():
    return render_template('download.html')

@app.route('/downloadfile')
def downloadfile():
	#path = "html2pdf.pdf"
	#path = "info.xlsx"
	#path = "simple.docx"
	path = "sample.txt"
	return send_file(path, as_attachment=True)

@app.route('/login',methods=["GET","POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('index'))
        flash('Invalid username or password.')
    return render_template('login.html',form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out')
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return "Only authenticated users can do this! Try to log in or contact the site admin."

@app.route('/register',methods=["GET","POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,username=form.username.data,
                    alamat=form.alamat.data, password=form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('You can now log in!')
        return redirect(url_for('login'))
    return render_template('register.html',form=form)

@app.route('/pagetestimoni', methods=['GET', 'POST'])
def pagetestimoni():
    if request.method == 'POST':
        post_nama = request.form['nama']
        post_content = request.form['content']
        post_author = request.form['author']
        new_post = BlogPost(nama=post_nama, content=post_content, author=post_author)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/hasiltesti')
    else:
        all_posts = BlogPost.query.order_by(BlogPost.date_posted).all()
        return render_template('testimoni.html', posts=all_posts)

@app.route('/hasiltesti', methods=['GET', 'POST'])
def hasiltesti():
    nama = request.form.get('nama')
    content = request.form.get('content')
    all_posts = BlogPost.query.order_by(BlogPost.date_posted).all()
    return render_template('hasiltesti.html', posts=all_posts)

@app.route('/struktur')
def struktur():
    return render_template('struktur.html')

@app.route('/instruktur')
def instruktur():
    return render_template('instruktur.html')

@app.route('/foto')
def foto():
    return render_template('foto.html')

if __name__=='__main__':
    db.create_all()
    app.run(debug=True)

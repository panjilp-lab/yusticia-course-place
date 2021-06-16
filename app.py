import os
import json
import psycopg2
import sys
from datetime import datetime
from models import Question
from flask import Flask, render_template, redirect, url_for, send_file, flash, request, session, abort
from flask import Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager
from flask_login import LoginManager, login_required, logout_user, login_user, UserMixin, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from flask_heroku import Heroku
from forms import *

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///guruku.sqlite'
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
##### Set up Forms #####

## Error handling routes
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

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
        flash('Pastikan Huruf Besar dan Kecil sama')
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

@app.route('/jurusan')
def jurusan():
    return render_template('jurusan.html')

if __name__=='__main__':
    from config import db
    db.create_all()
    app.run(debug=True)

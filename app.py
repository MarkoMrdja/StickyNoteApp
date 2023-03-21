from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import InputRequired, Length, ValidationError, DataRequired
from flask_bcrypt import Bcrypt
import os
from dotenv import load_dotenv


load_dotenv()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(300), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

    def __rep__(self):
        return '<Task %r>' % self.id


class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), nullable=False, unique=True)
    password = db.Column(db.String(200), nullable=False)
    notes = db.relationship('Note', backref='user')


class RegisterForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Register")

    def validate_username(self, username):
        existing_username = User.query.filter_by(username=username.data).first()
        if existing_username:
            raise ValidationError("That username already exists. Please choose a different one.")


class LoginForm(FlaskForm):
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Username"})
    password = PasswordField(validators=[InputRequired(), Length(min=4, max=20)], render_kw={"placeholder": "Password"})
    submit = SubmitField("Login")


class SearchForm(FlaskForm):
    searched = StringField("Searched", validators=[DataRequired()])
    submit = SubmitField("Submit")


with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        pass
    else:
        if current_user.is_authenticated:
            tasks = Note.query.filter_by(user_id=current_user.id).all()
            return render_template("index.html", tasks=tasks)
        else:
            tasks = []
            return render_template("index.html", tasks=tasks)


@app.route('/create-note', methods=['POST', 'GET'])
@login_required
def create_note():
    if request.method == 'POST':
        note_title = request.form['note_title']
        note_content = request.form['note_content']
        new_task = Note(title=note_title, content=note_content, user_id=current_user.id)
        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/')
        except:
            return 'Doslo je do greske prilikom dodavanja beleske'
    else:
        note_title = ""
        note_content = ""
    return render_template('create-note.html', note_title=note_title, note_content=note_content)


@app.route('/note/<int:id>', methods=['POST', 'GET'])
@login_required
def note(id):
    task = Note.query.get_or_404(id)
    if current_user.id != task.user_id:
        return 'Nemate pristup ovog belesci'
    if request.method == 'POST':
        task.content = request.form['note_content']
        task.title = request.form['note_title']
        try:
            db.session.commit()
            return redirect(url_for('note', id=task.id))
        except:
            return 'Doslo je do greske prilikom promene beleske'

    else:
        return render_template("note.html", note_id=task.id, note_title=task.title, note_content=task.content)



@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Note.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return "Doslo je do greske prilikom brisanja beleske"


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if bcrypt.check_password_hash(user.password, form.password.data):
                login_user(user)
                return redirect(url_for('home'))
    return render_template('login.html', form=form)


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html', form=form)


@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/search', methods=['POST'])
def search():
    form = SearchForm()
    notes = Note.query
    if form.validate_on_submit():
        note.searched = form.searched.data
        notes = notes.filter(Note.title.like('%' + note.searched + '%'))
        notes = notes.order_by(Note.title).all()
        return render_template("search.html", form=form, searched=note.searched, notes=notes)


@app.context_processor
def base():
    form = SearchForm()
    return dict(form=form)


if __name__ == '__main__':
    app.run(debug=True)


from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///task.db'
db = SQLAlchemy(app)


class ToDoNote(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(20), nullable=False)
    content = db.Column(db.String(300), nullable=False)

    def __rep__(self):
        return '<Task %r>' % self.id


with app.app_context():
    db.create_all()


@app.route('/', methods=['POST', 'GET'])
def home():
    if request.method == 'POST':
        pass
    else:
        tasks = ToDoNote.query.all()
        return render_template("index.html", tasks=tasks)


@app.route('/create-note', methods=['POST', 'GET'])
def create_note():
    if request.method == 'POST':
        note_title = request.form['note_title']
        note_content = request.form['note_content']
        new_task = ToDoNote(title=note_title, content=note_content)
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
def note(id):
    task = ToDoNote.query.get_or_404(id)
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
    task_to_delete = ToDoNote.query.get_or_404(id)
    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/')
    except:
        return "Doslo je do greske prilikom brisanja beleske"


if __name__ == '__main__':
    app.run(debug=True)


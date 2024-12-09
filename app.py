from flask import Flask, render_template, request, redirect, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

project_dir = os.path.dirname(os.path.abspath(__file__))
database_file = "sqlite:///{}".format(os.path.join(project_dir, "bookdatabase.db"))

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = database_file
app.secret_key = os.urandom(24)
db = SQLAlchemy(app)


# Modelos

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

    def __repr__(self):
        return f"<User {self.username}>"


class Book(db.Model):
    title = db.Column(db.String(80), unique=True, nullable=False, primary_key=True)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Float, nullable=True)

    def __repr__(self):
        return f"<Book {self.title}>"


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_title = db.Column(db.String(80), db.ForeignKey('book.title'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='comments')
    book = db.relationship('Book', backref='comments')

    def __repr__(self):
        return f"<Comment {self.content[:20]}...>"

with app.app_context():
    db.create_all()


# Rotas

@app.route("/", methods=["GET", "POST"])
def home():
    if "user_id" not in session:
        return redirect("/register")

    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        rating = request.form.get("rating")

        try:
            book = Book(title=title, description=description, rating=float(rating))
            db.session.add(book)
            db.session.commit()
            flash("Livro adicionado com sucesso!", "success")
        except Exception as e:
            flash("Falha ao adicionar livro", "danger")
            print("Falha ao adicionar livro:", e)

    books = Book.query.all()
    return render_template("index.html", books=books)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash("Nome de usuário já existe. Escolha outro.", "danger")
            return redirect("/register")

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            flash("E-mail já cadastrado. Use outro.", "danger")
            return redirect("/register")

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash("Usuário cadastrado com sucesso!", "success")
        return redirect("/login")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = user.username
            flash("Login realizado com sucesso!", "success")
            return redirect("/")
        else:
            flash("Credenciais inválidas. Tente novamente.", "danger")

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Você saiu com sucesso!", "success")
    return redirect("/login")


@app.route("/update", methods=["POST"])
def update():
    try:
        newtitle = request.form.get("newtitle")
        newdescription = request.form.get("newdescription")
        newrating = request.form.get("newrating")
        oldtitle = request.form.get("oldtitle")
        book = Book.query.filter_by(title=oldtitle).first()
        if book:
            book.title = newtitle
            book.description = newdescription
            book.rating = float(newrating)
            db.session.commit()
            flash("Livro atualizado com sucesso!", "success")
        else:
            flash("Livro não encontrado.", "danger")
    except Exception as e:
        flash("Falha ao atualizar livro", "danger")
        print("Falha ao atualizar livro:", e)
    return redirect("/")


@app.route("/delete", methods=["POST"])
def delete():
    title = request.form.get("title")
    book = Book.query.filter_by(title=title).first()
    if book:
        db.session.delete(book)
        db.session.commit()
        flash("Livro excluído com sucesso!", "success")
    else:
        flash("Livro não encontrado.", "danger")
    return redirect("/")


@app.route("/jogo/<title>", methods=["GET", "POST"])
def jogo(title):
    book = Book.query.filter_by(title=title).first()
    if not book:
        return "Livro não encontrado", 404

    if request.method == "POST":
        content = request.form.get("content")
        if "user_id" not in session:
            flash("Você precisa estar logado para comentar.", "danger")
            return redirect("/login")

        comment = Comment(content=content, user_id=session["user_id"], book_title=book.title)
        db.session.add(comment)
        db.session.commit()
        flash("Comentário adicionado com sucesso!", "success")

    comments = Comment.query.filter_by(book_title=title).all()
    return render_template("jogo.html", book=book, comments=comments)


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)

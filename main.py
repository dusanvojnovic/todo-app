from flask import Flask, render_template, redirect, url_for, flash, request
import flask
from flask_bootstrap import Bootstrap
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
from flask_sqlalchemy import SQLAlchemy
from forms import LoginForm, RegisterForm



app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo_list_users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    todo_items = relationship("Item", back_populates="owner")
    
db.create_all()

class Item(db.Model):
    __tablename__ = 'items'
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    owner = relationship("User", back_populates="todo_items")
    text = db.Column(db.Text, nullable=False)

db.create_all()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/", methods = ["GET", "POST"])
def home():
    todo_list = []
    if current_user.is_authenticated:
        todo_list = Item.query.filter_by(owner = current_user).all()
        
    return render_template('index.html', todo=todo_list)


@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash("That email doesn't exist")
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash("Password incorrect, please try again")
            return redirect(url_for('login'))  
        else:
            login_user(user)
            return redirect(url_for('todo'))
    
    return render_template('login.html',form=form, current_user=current_user)

@app.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        # checking if user with entered email already exist
        if User.query.filter_by(email=form.email.data).first():
            flash("You've already signed up with that email, log in instead or try with different email")
            return redirect(url_for("register"))
        if User.query.filter_by(username=form.username.data).first():
            flash("You're already registered with this username.")
            return redirect(url_for("register"))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method = "pbkdf2:sha256",
            salt_length = 5
        )

        new_user = User(
            email = form.email.data,
            username = form.username.data,
            password = hash_and_salted_password
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    
    return render_template('register.html', form=form, current_user=current_user)


    
@app.route("/todo", methods=["GET", "POST"])
def todo():
    if request.method == "POST":
        if current_user.is_authenticated:
            new_item = Item(
                owner=current_user,
                text = request.form['item']
            )
            db.session.add(new_item)
            db.session.commit()
    return redirect(url_for('home'))

@app.route("/delete/<int:id>", methods=["GET", "POST"])
def delete(id):
    item_to_delete = Item.query.get(id)
    db.session.delete(item_to_delete)
    db.session.commit()
    return redirect(url_for("home"))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


if __name__ == "__main__":
    app.run(debug=True)
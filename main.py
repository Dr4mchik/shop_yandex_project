from flask import Flask, render_template, redirect
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename
import datetime
import os

from data import db_session

# импортируем модели
from data.user import User
from data.product import Product

# импортируем формы
from form.user_registration import RegistrationForm
from form.user_login import LoginForm
from form.product import ProductForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'upload'

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Обработчик регистрации нового пользователя"""
    # создадим форму пользователя
    form = RegistrationForm()
    # проверим форму на заполненность
    if form.validate_on_submit():
        # проверим, ввёл ли пользователь два одинаковых пароля
        if form.password.data != form.repeat_password.data:
            # укажем пользователю, что он ошибся в паролях
            return render_template('register.html', form=form, message='Ошибка, пароли не совпадают!')

        # если пользователь ввёл всё правильно подключимся к бд
        db_sess = db_session.create_session()
        # проверим, что пользователь новый
        if db_sess.query(User).filter(User.email == form.email.data).first():
            message = 'Такой пользователь уже есть!'
            return render_template('register.html', form=form, message=message)

        # создание нового пользователя через модель
        user = User(
            email=form.email.data,
            surname=form.surname.data,
            name=form.name.data,
            modified_date=datetime.datetime.now(),
        )
        user.set_password(form.password.data)

        db_sess.add(user)
        db_sess.commit()

        # перенаправляем пользователя на главную страницу
        return redirect('/')
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            return redirect("/")
        message = "Неправильный логин или пароль"
        return render_template('login.html', message=message, form=form)

    return render_template('login.html', title='Login', form=form)


@app.route('/user/products')
@login_required
def user_products():
    products = current_user.products
    return render_template('user_products.html', products=products)


@app.route('/user/products/add', methods=['POST', "GET"])
@login_required
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        image_file = form.image.data  # Получаем файл из формы
        filename = None

        if image_file:  # Если файл был загружен
            filename = secure_filename(image_file.filename)  # Безопасное имя файла
            upload_folder = app.config['UPLOAD_FOLDER']  # Путь из конфига
            image_file.save(os.path.join(upload_folder, filename))  # Сохраняем файл

        product = Product(
            name=form.name.data,
            price=form.price.data,
            description=form.description.data,
            image=filename,
            user_id=current_user.id,
        )

        current_user.products.append(product)
        db_sess.merge(current_user)
        db_sess.commit()

        return redirect('/user/products')

    return render_template('product.html', form=form)


if __name__ == '__main__':
    db_session.global_init('db/online_store.db')
    app.run()

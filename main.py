from flask import Flask, render_template, redirect, request, abort, flash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy import and_
from werkzeug.utils import secure_filename
import datetime
import os

from data import db_session

# импортируем модели
from data.user import User
from data.product import Product
from data.order import Order, OrderItem

# импортируем формы
from form.user_registration import RegistrationForm
from form.user_login import LoginForm
from form.product import ProductForm
from form.profileform import ProfileForm
from form.balanceform import BalanceForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/upload'

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
    db_sess = db_session.create_session()
    # возьмём из аргументов в url параметр поиска, появится если пользователь что-то искал
    search = request.args.get('search', '')
    # выбираем товары которые октрыты
    query = db_sess.query(Product).filter(Product.open == True)
    if search:
        # если пользователь что-то ищёт, будем искать совпадение в названии товара
        products = query.filter(Product.name.ilike(f'%{search}%')).all()
    else:
        products = query.all()
    return render_template('all_products.html', products=products)


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
            balance=0.0  # Устанавливаем начальный баланс
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
            open=form.open.data,
            amount_available=form.amount_available.data
        )

        current_user.products.append(product)
        db_sess.merge(current_user)
        db_sess.commit()

        return redirect('/user/products')

    return render_template('add_product.html', form=form)


@app.route('/user/products/edit/<int:product_id>', methods=['GET', "POST"])
@login_required
def edit_product(product_id):
    form = ProductForm()
    db_sess = db_session.create_session()
    product = db_sess.query(Product).filter(and_(Product.id == product_id, Product.user_id == current_user.id)).first()

    if not product:
        abort(404)

    if request.method == 'GET':

        form.name.data = product.name
        form.price.data = product.price
        form.description.data = product.description
        form.amount_available.data = product.amount_available
        form.open.data = product.open
        form.submit.label.text = 'Изменить товар'

        return render_template('add_product.html', form=form)

    else:
        if form.validate_on_submit():

            image_file = form.image.data  # Получаем файл из формы
            filename = product.filename.data

            if image_file:  # Если файл был загружен
                os.remove(filename)  # удаляем старый файл
                filename = secure_filename(image_file.filename)  # Безопасное имя файла
                upload_folder = app.config['UPLOAD_FOLDER']  # Путь из конфига
                image_file.save(os.path.join(upload_folder, filename))  # Сохраняем файл

            product.name = form.name.data
            product.price = form.price.data
            product.description = form.description.data
            product.amount_available = form.amount_available.data
            product.open = form.open.data

            db_sess.commit()
            return redirect('/user/products')


# Новые маршруты для профиля пользователя

@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()

    if request.method == 'GET':
        # Заполняем форму данными пользователя
        form.email.data = current_user.email
        form.name.data = current_user.name
        form.surname.data = current_user.surname

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)

        # Проверяем, не занят ли email другим пользователем
        if user.email != form.email.data:
            existing_user = db_sess.query(User).filter(User.email == form.email.data).first()
            if existing_user and existing_user.id != current_user.id:
                return render_template('profile.html', form=form,
                                       message='Этот email уже используется другим пользователем',
                                       message_category='danger')

        # Обновляем данные пользователя
        user.email = form.email.data
        user.name = form.name.data
        user.surname = form.surname.data

        # Если введен новый пароль, обновляем его
        if form.new_password.data:
            user.set_password(form.new_password.data)

        db_sess.commit()
        return render_template('profile.html', form=form,
                               message='Профиль успешно обновлен',
                               message_category='success')

    return render_template('profile.html', form=form, title='Профиль')


@app.route('/user/balance', methods=['GET', 'POST'])
@login_required
def balance():
    form = BalanceForm()

    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).get(current_user.id)

        # Имитация пополнения баланса (в реальном приложении здесь была бы интеграция с платежной системой)
        amount = form.amount.data
        user.balance += amount
        db_sess.commit()

        flash(f'Баланс успешно пополнен на {amount}₽', 'success')
        return redirect('/user/profile')

    return render_template('balance.html', form=form, title='Пополнение баланса')


@app.route('/user/orders')
@login_required
def user_orders():
    db_sess = db_session.create_session()
    # Получаем все заказы пользователя, отсортированные по дате (новые сначала)
    orders = db_sess.query(Order).filter(Order.user_id == current_user.id).order_by(Order.created_date.desc()).all()
    return render_template('orders.html', orders=orders, title='Мои заказы')


# Пример маршрута для создания заказа (для тестирования)
@app.route('/test/create_order')
@login_required
def test_create_order():
    db_sess = db_session.create_session()

    # Найдем какой-нибудь доступный товар (не принадлежащий текущему пользователю)
    product = db_sess.query(Product).filter(
        Product.user_id != current_user.id,
        Product.open == True,
        Product.amount_available > 0
    ).first()

    if not product:
        flash('Нет доступных товаров для тестового заказа', 'warning')
        return redirect('/')

    # Проверяем, достаточно ли средств
    if current_user.balance < product.price:
        flash('Недостаточно средств для оформления заказа', 'danger')
        return redirect('/')

    # Создаем новый заказ
    order = Order(
        user_id=current_user.id,
        total_price=product.price,
        status='new'
    )

    # Добавляем товар в заказ
    order_item = OrderItem(
        product_id=product.id,
        quantity=1,
        price=product.price
    )

    # Связываем заказ и товар
    order.products.append(order_item)

    # Уменьшаем количество доступных товаров
    product.amount_available -= 1

    # Списываем средства с баланса пользователя
    user = db_sess.query(User).get(current_user.id)
    user.balance -= product.price

    # Сохраняем изменения
    db_sess.add(order)
    db_sess.commit()

    flash('Тестовый заказ успешно создан!', 'success')
    return redirect('/user/orders')


if __name__ == '__main__':
    db_session.global_init('db/online_store.db')
    app.run()
from flask import Flask, render_template, redirect, request, abort, flash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy import and_
from werkzeug.utils import secure_filename
import datetime
import os
from form.checkout_form import CheckoutForm
from data.order import Order

from data import db_session

# импортируем модели
from data.user import User
from data.product import Product
from data.order import OrderItem

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



@app.route('/user/add_cart/<int:product_id>')
@login_required
def add_cart(product_id):
    db_sess = db_session.create_session()
    order_item = OrderItem()
    order_item.user_id = current_user.id
    order_item.product_id = product_id
    db_sess.add(order_item)
    db_sess.commit()
    return redirect('/')


@app.route('/user/cart')
@login_required
def cart():
    db_sess = db_session.create_session()
    order_item = db_sess.query(OrderItem).filter(current_user.id == OrderItem.user_id).all()
    product_amount_sum = sum([i.amount for i in order_item])
    product_price_sum = sum([i.amount * i.product.price for i in order_item])
    return render_template('cart.html', products=order_item,
                           product_amount_sum=product_amount_sum, product_price_sum=product_price_sum)


@app.route('/user/cart/update/<int:product_id>', methods=['POST'])
@login_required
def cart_update(product_id):
    db_sess = db_session.create_session()
    new_amount = request.form.get('amount', type=int)
    if new_amount is None:
        return redirect('/user/cart')

    order_item = db_sess.query(OrderItem).filter(OrderItem.product_id == product_id).first()
    if not order_item:
        abort(404)

    if new_amount < 0 or order_item.product.amount_available < new_amount:
        abort(400)

    order_item.amount = new_amount
    db_sess.commit()

    return redirect('/user/cart')


@app.route('/user/cart/delete/<int:product_id>')
@login_required
def cart_delete(product_id):
    db_sess = db_session.create_session()
    order_item = db_sess.query(OrderItem).filter(OrderItem.id == product_id).first()
    if not order_item:
        abort(404)

    db_sess.delete(order_item)
    db_sess.commit()
    return redirect('/user/cart')


@app.route('/user/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Обработчик страницы оформления заказа"""
    form = CheckoutForm()

    db_sess = db_session.create_session()

    # Получаем все товары из корзины
    cart_items = db_sess.query(OrderItem).filter(
        OrderItem.user_id == current_user.id,
        OrderItem.is_in_order == False
    ).all()

    # Если корзина пуста, перенаправляем на страницу корзины
    if not cart_items:
        flash('Ваша корзина пуста', 'warning')
        return redirect('/user/cart')

    # Вычисляем сумму товаров и их количество
    product_amount_sum = sum([item.amount for item in cart_items])
    product_price_sum = sum([item.amount * item.product.price for item in cart_items])

    # Предзаполняем форму данными пользователя
    if request.method == 'GET':
        form.name.data = current_user.name
        form.surname.data = current_user.surname
        form.email.data = current_user.email

    if form.validate_on_submit():
        # Определяем стоимость доставки
        delivery_cost = 0
        if request.method == 'POST' and form.delivery_type.data == 'pickup_point':
            delivery_cost = 150  # Базовая стоимость доставки в ПВЗ

        # Общая сумма заказа с учетом доставки
        order_total = product_price_sum + delivery_cost

        # Проверяем достаточно ли средств на балансе при оплате с баланса
        if form.payment_method.data == 'balance' and current_user.balance < order_total:
            flash('Недостаточно средств на балансе', 'danger')
            return render_template('checkout.html',
                                   form=form,
                                   products=cart_items,
                                   product_amount_sum=product_amount_sum,
                                   product_price_sum=product_price_sum,
                                   order_total=order_total)

        try:
            # Создаем заказ
            order = Order(
                user_id=current_user.id,
                created_date=datetime.datetime.now(),
                status='new',
                total_price=order_total,

                # Контактная информация
                name=form.name.data,
                surname=form.surname.data,
                email=form.email.data,
                phone=form.phone.data,

                # Доставка
                delivery_type=form.delivery_type.data,
                delivery_service=form.delivery_service.data if form.delivery_type.data == 'pickup_point' else None,
                pvz_info=form.selected_pvz.data if form.delivery_type.data == 'pickup_point' else None,
                delivery_cost=delivery_cost,

                # Оплата
                payment_method=form.payment_method.data,
                is_paid=form.payment_method.data == 'balance',  # Оплачено сразу, если с баланса
                payment_date=datetime.datetime.now() if form.payment_method.data == 'balance' else None,

                # Комментарий
                comment=form.comment.data
            )

            db_sess.add(order)
            db_sess.flush()  # Получаем ID заказа

            # Добавляем товары из корзины в заказ
            for item in cart_items:
                item.is_in_order = True
                item.order_id = order.id

                # Уменьшаем количество доступных товаров
                item.product.amount_available -= item.amount

            # Если оплата с баланса, списываем средства
            if form.payment_method.data == 'balance':
                user = db_sess.query(User).get(current_user.id)
                user.balance -= order_total

            db_sess.commit()
            flash('Заказ успешно оформлен!', 'success')

            # Перенаправляем на страницу заказов или страницу с деталями заказа
            return redirect(f'/user/order/{order.id}')

        except Exception as e:
            db_sess.rollback()
            flash(f'Произошла ошибка: {str(e)}', 'danger')

    return render_template('checkout.html', form=form,
                           products=cart_items,
                           product_amount_sum=product_amount_sum,
                           product_price_sum=product_price_sum,
                           order_total=product_price_sum)


@app.route('/user/order/<int:order_id>')
@login_required
def user_order_details(order_id):
    """Страница с деталями заказа"""
    db_sess = db_session.create_session()
    order = db_sess.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id
    ).first()

    if not order:
        flash('Заказ не найден', 'danger')
        return redirect('/user/orders')

    return render_template('order_details.html', order=order)


@app.route('/user/orders')
@login_required
def user_orders():
    """Страница со списком заказов пользователя"""
    db_sess = db_session.create_session()
    # Получаем все заказы пользователя, отсортированные по дате (новые сначала)
    orders = db_sess.query(Order).filter(
        Order.user_id == current_user.id
    ).order_by(Order.created_date.desc()).all()

    return render_template('orders.html', orders=orders)


if __name__ == '__main__':
    db_session.global_init('db/online_store.db')
    app.run()

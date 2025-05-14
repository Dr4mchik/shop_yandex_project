from flask import Flask, render_template, redirect, request, abort, flash
from flask_login import LoginManager, login_user, login_required, current_user, logout_user
from sqlalchemy import and_, or_
from werkzeug.utils import secure_filename
import datetime
import os
from PIL import Image

from data import db_session

# импортируем модели
from data.user import User
from data.product import Product
from data.order import OrderItem, OrderStatus, OrderStatusHistory
from data.order import Order
from data.massage import Message

# импортируем формы
from form.massage_form import MessageForm
from form.user_registration import RegistrationForm
from form.user_login import LoginForm
from form.product import ProductForm
from form.profileform import ProfileForm
from form.balanceform import BalanceForm
from form.checkout_form import CheckoutForm

# api
from api import products_api, users_api, orders_api

app = Flask(__name__)
app.config['SECRET_KEY'] = 'yandexlyceum_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/upload'

login_manager = LoginManager()
login_manager.init_app(app)


def set_filename_image(image_file):
    filename = secure_filename(image_file.filename)  # Безопасное имя файла

    if filename in os.listdir('static/upload'):  # проверяем уникальность названия файла
        # если название файла не уникальное, нумеруем его
        name, ext = os.path.splitext(filename)
        number_to_add_filename = 0
        while name + f'({number_to_add_filename}){ext}' in os.listdir():
            number_to_add_filename += 1
        filename = name + f'({number_to_add_filename})' + ext

    return filename


@login_manager.user_loader
def load_user(user_id):
    db_sess = db_session.create_session()
    return db_sess.query(User).get(user_id)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/")


@app.errorhandler(404)
def error404(error):
    return render_template('page404.html', title='Страница не найдена'), 404


@app.route('/')
def home():
    db_sess = db_session.create_session()
    try:
        # возьмём из аргументов в url параметр поиска, появится если пользователь что-то искал
        search = request.args.get('search', '')
        # выбираем товары которые октрыты
        query = db_sess.query(Product).filter(Product.open == True)
        if search:
            # если пользователь что-то ищёт, будем искать совпадение в названии товара
            products = query.filter(Product.name.ilike(f'%{search}%')).all()
        else:
            products = query.all()
        return render_template('show_products.html', products=products, button_name='В корзину', link_button='add_cart')
    finally:
        db_sess.close()


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
        try:
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
            flash('Пользователь успешно создан! Можете авторизоваться.', 'success')

            return redirect('/')
        finally:
            db_sess.close()
    return render_template('register.html', title='Регистрация', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        try:
            user = db_sess.query(User).filter(User.email == form.email.data).first()
            if user and user.check_password(form.password.data):
                login_user(user, remember=form.remember_me.data)
                return redirect("/")
            message = "Неправильный логин или пароль"
            return render_template('login.html', message=message, form=form)
        finally:
            db_sess.close()
    return render_template('login.html', title='Login', form=form)


@app.route('/user/products')
@login_required
def user_products():
    db_sess = db_session.create_session()
    try:
        search = request.args.get('search', '')
        # выбираем товары которые октрыты
        query = db_sess.query(Product).filter(Product.user_id == current_user.id)
        if search:
            # если пользователь что-то ищёт, будем искать совпадение в названии товара
            products = query.filter(Product.name.ilike(f'%{search}%')).all()
        else:
            products = query.all()
        return render_template('show_products.html', products=products, button_name='Редактировать',
                               link_button='edit_product', edit=1)
    finally:
        db_sess.close()


@app.route('/user/products/add', methods=['POST', "GET"])
@login_required
def add_product():
    form = ProductForm()
    db_sess = db_session.create_session()
    try:
        if request.method == 'POST':

            if form.validate_on_submit():

                user = db_sess.query(User).filter(User.id == current_user.id).first()
                image_file = form.image.data  # Получаем файл из формы
                filename = None

                if image_file:  # Если файл был загружен

                    image = Image.open(image_file)
                    image = image.resize((520, 520))

                    filename = set_filename_image(image_file)  # Безопасное имя файла

                    upload_folder = app.config['UPLOAD_FOLDER']  # Путь из конфига
                    image.save(os.path.join(upload_folder, filename))  # Сохраняем файл

                # создаём объект продукта
                product = Product(
                    name=form.name.data,
                    price=form.price.data,
                    description=form.description.data,
                    image=filename,
                    user_id=current_user.id,
                    open=form.open.data,
                    amount_available=form.amount_available.data
                )

                # сохраняем его пользователю, который авторизован
                user.products.append(product)
                db_sess.merge(user)
                db_sess.commit()

                flash('Товар успешно добавлен!', 'success')

                return redirect('/user/products')

            else:
                flash('Ошибки при заполнении', 'danger')

        return render_template('add_product.html', form=form, title_text='Добавить новый товар', product_id=0)
    finally:
        db_sess.close()


@app.route('/user/products/edit/<int:product_id>', methods=['GET', "POST"])
@login_required
def edit_product(product_id):
    form = ProductForm()
    db_sess = db_session.create_session()
    try:
        product = db_sess.query(Product).filter(
            and_(Product.id == product_id, Product.user_id == current_user.id)).first()

        if not product:
            abort(404)

        if request.method == 'GET':

            form.name.data = product.name
            form.price.data = product.price
            form.description.data = product.description
            form.amount_available.data = product.amount_available
            form.open.data = product.open
            form.submit.label.text = 'Изменить товар'

        else:
            if form.validate_on_submit():

                image_file = form.image.data  # Получаем файл из формы
                filename = product.image

                if image_file:  # Если файл был загружен
                    if filename and filename in os.listdir(
                            'static/upload/'):  # если на продукте есть изображение удаляем его
                        os.remove(f'static/upload/{filename}')  # удаляем старый файл
                    filename = set_filename_image(image_file)
                    upload_folder = app.config['UPLOAD_FOLDER']  # Путь из конфига
                    image_file.save(os.path.join(upload_folder, filename))  # Сохраняем файл

                product.name = form.name.data
                product.price = form.price.data
                product.description = form.description.data
                product.amount_available = form.amount_available.data
                product.open = form.open.data
                product.image = filename

                db_sess.commit()
                flash('Товар успешно изменен!', 'success')
                return redirect('/user/products')
            else:
                flash('Ошибка при заполнении', 'danger')

        return render_template('add_product.html', form=form, title_text='Редактирование товара', product_id=product_id)
    finally:
        db_sess.close()


@app.route('/user/product/delete/<int:product_id>')
@login_required
def delete_product(product_id):
    # если продукт ид == 0, то значит это ещё не созданный продукт и мы просто перенаправим пользователя
    if product_id == 0:
        flash('Отмена создания товара', 'warning')
        return redirect('/user/products')
    else:
        db_sess = db_session.create_session()
        try:
            product = db_sess.query(Product).filter(and_(
                product_id == Product.id,
                Product.user_id == current_user.id
            )).first()
            db_sess.delete(product)
            db_sess.commit()
            flash('Товар успешно удалён!', 'warning')
            return redirect('/user/products')
        finally:
            db_sess.close()


@app.route('/products/<int:product_id>')
def show_product(product_id):
    db_sess = db_session.create_session()
    try:
        product = db_sess.query(Product).filter(Product.id == product_id).first()
        return render_template('product.html', product=product)
    finally:
        db_sess.close()


# Новые маршруты для профиля пользователя

@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    db_sess = db_session.create_session()
    try:

        if request.method == 'GET':
            # Заполняем форму данными пользователя
            form.email.data = current_user.email
            form.name.data = current_user.name
            form.surname.data = current_user.surname

        if form.validate_on_submit():
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
    finally:
        db_sess.close()


@app.route('/user/balance', methods=['GET', 'POST'])
@login_required
def balance():
    form = BalanceForm()
    db_sess = db_session.create_session()
    try:

        if form.validate_on_submit():
            user = db_sess.query(User).get(current_user.id)

            # Имитация пополнения баланса (в реальном приложении здесь была бы интеграция с платежной системой)
            amount = form.amount.data
            user.balance += amount
            db_sess.commit()

            flash(f'Баланс успешно пополнен на {amount}₽', 'success')
            return redirect('/user/profile')

        return render_template('balance.html', form=form, title='Пополнение баланса')
    finally:
        db_sess.close()


@app.route('/user/add_cart/<int:product_id>')
@login_required
def add_cart(product_id):
    """Функция добавление товара в корзину товаров"""
    db_sess = db_session.create_session()
    try:
        # проверим на наличие такого же товара в корзине
        # проверяем совпадение по пользователю (его корзина) и по продукту
        order_item = db_sess.query(OrderItem).filter(
            and_(OrderItem.product_id == product_id, OrderItem.user_id == current_user.id,
                 OrderItem.is_in_order == False)
        ).first()
        if order_item:
            # если такой товар есть в корзине
            if order_item.product.amount_available >= order_item.amount + 1:
                order_item.amount += 1
            else:
                db_sess.close()
                flash('Нету такого кол-во товара!', 'warning')
                return redirect('/')
        else:
            # если такого товара нет в корзине
            order_item = OrderItem()
            order_item.user_id = current_user.id
            order_item.product_id = product_id
            db_sess.add(order_item)
        db_sess.commit()
        flash('Товар добавлен в корзину!', 'info')
        return redirect('/')
    finally:
        db_sess.close()


@app.route('/user/cart')
@login_required
def cart():
    db_sess = db_session.create_session()
    try:
        order_item = db_sess.query(OrderItem).filter(
            and_(current_user.id == OrderItem.user_id, OrderItem.is_in_order == False)
        ).all()
        print(f'{order_item[0].amount=}')
        product_amount_sum = sum([i.amount for i in order_item])
        product_price_sum = sum([i.amount * i.product.price for i in order_item])
        return render_template('cart.html', products=order_item,
                               product_amount_sum=product_amount_sum, product_price_sum=product_price_sum)
    finally:
        db_sess.close()


@app.route('/user/cart/update/<int:product_id>', methods=['POST'])
@login_required
def cart_update(product_id):
    db_sess = db_session.create_session()
    try:
        print('вход в функцию обновления')
        new_amount = request.form.get('amount', type=int)
        print(f'{new_amount=}')
        if new_amount is None:
            return redirect('/user/cart')

        order_item = db_sess.query(OrderItem).filter(and_(
            OrderItem.product_id == product_id,
            current_user.id == OrderItem.user_id,
            OrderItem.is_in_order == False
        )).first()
        if not order_item:
            abort(404)

        if new_amount < 0 or order_item.product.amount_available < new_amount:
            abort(400)

        order_item.amount = new_amount
        print(f'{order_item.amount=}')
        db_sess.commit()
        print(f'{order_item.amount=}')

        return redirect('/user/cart')
    finally:
        db_sess.close()


@app.route('/user/cart/delete/<int:product_id>')
@login_required
def cart_delete(product_id):
    """Удаляет из корзины пользователя продукт"""
    db_sess = db_session.create_session()
    try:
        order_item = db_sess.query(OrderItem).filter(OrderItem.id == product_id).first()
        if not order_item:
            abort(404)

        db_sess.delete(order_item)
        db_sess.commit()
        return redirect('/user/cart')
    finally:
        db_sess.close()


@app.route('/user/products/orders')
@login_required
def show_user_products_order():
    """Показывает, что у пользователя заказали"""
    db_sess = db_session.create_session()
    try:
        all_order_items = db_sess.query(OrderItem).filter(OrderItem.is_in_order == True).all()

        order_items = [order_item for order_item in all_order_items if order_item.product.user_id == current_user.id]

        return render_template('user_products_orders.html', order_items=order_items, title='Заказы ваших товаров')
    finally:
        db_sess.close()


@app.route('/user/order/<int:order_id>')
@login_required
def user_order_details(order_id):
    """Страница с деталями заказа"""
    db_sess = db_session.create_session()
    try:
        order = db_sess.query(Order).filter(
            Order.id == order_id,
            Order.user_id == current_user.id
        ).first()

        if not order:
            flash('Заказ не найден', 'danger')
            return redirect('/user/orders')

        return render_template('order_details.html', order=order)
    finally:
        db_sess.close()


@app.route('/user/orders')
@login_required
def user_orders():
    """Страница со списком заказов пользователя"""
    db_sess = db_session.create_session()
    try:
        # Получаем все заказы пользователя, отсортированные по дате (новые сначала)
        orders = db_sess.query(Order).filter(
            Order.user_id == current_user.id
        ).order_by(Order.created_date.desc()).all()

        return render_template('orders.html', orders=orders)
    finally:
        db_sess.close()


def register_payment_routes(app):
    @app.route('/user/order/pay/<int:order_id>', methods=['GET', 'POST'])
    @login_required
    def pay_order(order_id):
        db_sess = db_session.create_session()
        try:
            order = db_sess.query(Order).filter(
                Order.id == order_id,
                Order.user_id == current_user.id,
                Order.is_paid == False
            ).first()

            if not order:
                flash('Заказ не найден или уже оплачен', 'danger')
                return redirect('/user/orders')

            if request.method == 'POST':
                # Получаем данные карты из формы
                card_number = request.form.get('card_number')
                card_expiry = request.form.get('card_expiry')
                card_cvv = request.form.get('card_cvv')

                if not (card_number and card_expiry and card_cvv):
                    flash('Пожалуйста, заполните все поля', 'danger')
                    return render_template('pay_order.html', order=order)

                try:
                    order.is_paid = True
                    order.status = 'paid'
                    order.payment_date = datetime.datetime.now()

                    db_sess.commit()
                    flash('Заказ успешно оплачен!', 'success')
                    return redirect('/user/orders')

                except Exception as e:
                    db_sess.rollback()
                    flash(f'Ошибка при оплате: {str(e)}', 'danger')

            return render_template('pay_order.html', order=order)
        finally:
            db_sess.close()

    return pay_order


@app.route('/user/contact_seller/<int:product_id>', methods=['GET', 'POST'])
@login_required
def contact_seller(product_id):
    """Страница для начала общения с продавцом товара"""
    db_sess = db_session.create_session()
    try:
        product = db_sess.query(Product).filter(Product.id == product_id).first()

        if not product:
            flash('Товар не найден', 'danger')
            return redirect('/')

        # Проверяем, что пользователь не пытается написать сам себе
        if product.user_id == current_user.id:
            flash('Вы не можете отправить сообщение самому себе', 'warning')
            return redirect(f'/products/{product_id}')

        form = MessageForm()

        if form.validate_on_submit():
            # Проверяем, есть ли уже существующий заказ с этим товаром для чата
            existing_order = db_sess.query(Order).filter(
                Order.user_id == current_user.id,
                Order.status == 'chat_only',
                Order.items.any(OrderItem.product_id == product_id)
            ).first()

            if not existing_order:
                # Создаем специальный заказ для чата, если его еще нет
                chat_order = Order(
                    user_id=current_user.id,
                    created_date=datetime.datetime.now(),
                    status='chat_only',  # Специальный статус для чатов, не являющихся реальными заказами
                    total_price=0,  # Нулевая цена, так как это только чат
                    name=current_user.name,
                    surname=current_user.surname,
                    email=current_user.email
                )

                db_sess.add(chat_order)
                db_sess.flush()  # Чтобы получить ID заказа

                # Добавляем товар в этот заказ
                order_item = OrderItem(
                    product_id=product_id,
                    user_id=current_user.id,
                    order_id=chat_order.id,
                    amount=0,  # Нулевое количество, так как товар не покупается
                    is_in_order=True  # Помечаем как часть заказа
                )

                db_sess.add(order_item)
                order_id = chat_order.id
            else:
                order_id = existing_order.id

            # Создаем сообщение
            message = Message(
                sender_id=current_user.id,
                recipient_id=product.user_id,
                order_id=order_id
            )

            # Обрабатываем текст и изображение
            if form.text.data:
                message.text = form.text.data

            image_file = form.image.data
            if image_file:
                filename = set_filename_image(image_file)
                upload_folder = app.config['UPLOAD_FOLDER']
                image_file.save(os.path.join(upload_folder, filename))
                message.image = filename

            db_sess.add(message)
            db_sess.commit()

            flash('Сообщение отправлено продавцу!', 'success')
            return redirect(f'/user/chat/{order_id}')

        return render_template('contact_seller.html', product=product, form=form)
    finally:
        db_sess.close()


# Обновить маршрут оформления заказа для исправления проблемы списания средств
@app.route('/user/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Обработчик страницы оформления заказа"""
    form = CheckoutForm()

    db_sess = db_session.create_session()
    try:
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
            if form.delivery_type.data == 'pickup_point':
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

                # Добавляем товары из корзины в заказ и уменьшаем доступное количество
                for item in cart_items:
                    item.is_in_order = True
                    item.order_id = order.id

                    # Уменьшаем количество доступных товаров
                    product = db_sess.query(Product).get(item.product_id)
                    if product.amount_available < item.amount:
                        db_sess.rollback()
                        flash(f'Недостаточное количество товара {product.name}', 'danger')
                        return redirect('/user/cart')

                    product.amount_available -= item.amount

                # Если оплата с баланса, списываем средства
                if form.payment_method.data == 'balance':
                    user = db_sess.query(User).get(current_user.id)
                    if user.balance < order_total:
                        db_sess.rollback()
                        flash('Недостаточно средств на балансе', 'danger')
                        return redirect('/user/cart')

                    user.balance -= order_total
                    order.status = 'paid'  # Сразу помечаем как оплаченный

                db_sess.commit()
                flash('Заказ успешно оформлен!', 'success')

                # Перенаправляем на страницу с деталями заказа
                return redirect(f'/user/order/{order.id}')

            except Exception as e:
                db_sess.rollback()
                flash(f'Произошла ошибка: {str(e)}', 'danger')

        return render_template('checkout.html', form=form,
                               products=cart_items,
                               product_amount_sum=product_amount_sum,
                               product_price_sum=product_price_sum,
                               order_total=product_price_sum + (150 if request.method == 'POST' and
                                                                       form.delivery_type.data == 'pickup_point' else 0))
    finally:
        db_sess.close()


def register_seller_routes(app):
    @app.route('/seller/orders')
    @login_required
    def seller_orders():
        """Страница со списком заказов для продавца"""
        db_sess = db_session.create_session()
        try:

            # Находим все заказы, содержащие товары данного продавца
            # Используем distinct() чтобы избежать дублирования заказов
            seller_orders = db_sess.query(Order).join(OrderItem).join(Product).filter(
                Product.user_id == current_user.id,
                Order.status != OrderStatus.CHAT_ONLY  # Исключаем "только чат" записи
            ).distinct().order_by(Order.created_date.desc()).all()

            return render_template('seller_order.html', orders=seller_orders)
        finally:
            db_sess.close()

    @app.route('/seller/order/<int:order_id>')
    @login_required
    def seller_order_details(order_id):
        """Страница с подробной информацией о заказе для продавца"""
        db_sess = db_session.create_session()
        try:

            # Проверяем, содержит ли заказ товары данного продавца
            order = db_sess.query(Order).filter(
                Order.id == order_id,
                Order.items.any(OrderItem.product.has(Product.user_id == current_user.id))
            ).first()

            if not order:
                flash('Заказ не найден или у вас нет доступа к этому заказу', 'danger')
                return redirect('/seller/orders')

            # Находим только те товары в заказе, которые принадлежат данному продавцу
            seller_items = [item for item in order.items if item.product.user_id == current_user.id]

            # Рассчитываем сумму только для товаров этого продавца
            seller_total = sum(item.product.price * item.amount for item in seller_items)

            return render_template('seller_order_details.html',
                                   order=order,
                                   seller_items=seller_items,
                                   seller_total=seller_total)
        finally:
            db_sess.close()

    @app.route('/update_order_status', methods=['POST'])
    @login_required
    def update_order_status():
        """Обработчик изменения статуса заказа продавцом"""
        if request.method != 'POST':
            return redirect('/seller/orders')

        order_id = request.form.get('order_id', type=int)
        new_status = request.form.get('status')
        comment = request.form.get('comment', '')

        if not order_id or not new_status:
            flash('Неверные параметры', 'danger')
            return redirect('/seller/orders')

        db_sess = db_session.create_session()
        try:

            # Проверяем, содержит ли заказ товары данного продавца
            order = db_sess.query(Order).filter(
                Order.id == order_id,
                Order.items.any(OrderItem.product.has(Product.user_id == current_user.id))
            ).first()

            if not order:
                flash('Заказ не найден или у вас нет доступа к этому заказу', 'danger')
                return redirect('/seller/orders')

            # Проверяем, доступен ли данный переход статуса для этого заказа
            available_statuses = order.get_available_status_changes(current_user)
            if new_status not in available_statuses:
                flash('Недопустимое изменение статуса', 'danger')
                return redirect(f'/seller/order/{order_id}')

            # Обновляем статус заказа
            old_status = order.status
            order.status = new_status

            # Если заказ был отправлен, сохраняем информацию о доставке
            if new_status == OrderStatus.SHIPPED:
                tracking_number = request.form.get('tracking_number', '')
                shipping_service = request.form.get('shipping_service', '')

                # Сохраняем информацию о доставке в комментарии к изменению статуса
                if tracking_number:
                    comment += f"\nТрек-номер: {tracking_number}"
                if shipping_service:
                    comment += f"\nСлужба доставки: {shipping_service}"

            # Создаем запись в истории статусов
            status_history = OrderStatusHistory(
                order_id=order.id,
                status=new_status,
                comment=comment,
                user_id=current_user.id,
                timestamp=datetime.datetime.now()
            )

            db_sess.add(status_history)

            # Особая логика для разных статусов
            if new_status == OrderStatus.COMPLETED:
                # Если статус "Завершен", переводим средства продавцу
                if not order.balance_transferred and order.is_paid:
                    # Находим продавца и переводим ему деньги
                    # Вычисляем сумму только для товаров данного продавца
                    seller_items = [item for item in order.items if item.product.user_id == current_user.id]
                    seller_total = sum(item.product.price * item.amount for item in seller_items)

                    # Распределяем доставку пропорционально стоимости товаров продавца
                    order_total_without_delivery = order.total_price - order.delivery_cost
                    if order_total_without_delivery > 0:
                        seller_share = seller_total / order_total_without_delivery
                        delivery_share = order.delivery_cost * seller_share
                    else:
                        delivery_share = 0

                    # Финальная сумма к переводу
                    transfer_amount = seller_total - delivery_share

                    # Переводим деньги продавцу
                    user = db_sess.query(User).get(current_user.id)
                    user.balance += transfer_amount

                    # Отмечаем, что средства переведены
                    # В реальном приложении здесь должна быть более сложная логика для разных продавцов
                    if all(item.product.user_id == current_user.id for item in order.items):
                        order.balance_transferred = True

                    comment += f"\nСредства в размере {transfer_amount:.2f}₽ переведены продавцу."

            elif new_status == OrderStatus.CANCELLED or new_status == OrderStatus.RETURNED:
                # Если заказ отменен или возвращен, возвращаем товары на склад
                for item in order.items:
                    if item.product.user_id == current_user.id:
                        product = db_sess.query(Product).get(item.product_id)
                        product.amount_available += item.amount

            db_sess.commit()

            flash(
                f'Статус заказа изменен с "{OrderStatus.get_buyer_viewable_statuses().get(old_status)}" на "{OrderStatus.get_buyer_viewable_statuses().get(new_status)}"',
                'success')
            return redirect(f'/seller/order/{order_id}')
        finally:
            db_sess.close()
    return seller_orders, seller_order_details, update_order_status


@app.route('/user/chats')
@login_required
def user_chats():
    """Список чатов пользователя"""
    db_sess = db_session.create_session()
    try:

        # Находим все активные чаты с учетом роли пользователя (продавец/покупатель)
        chats = db_sess.query(Order).filter(
            or_(
                Order.user_id == current_user.id,  # Чаты, где пользователь покупатель
                Order.items.any(Product.user_id == current_user.id)  # Чаты, где пользователь продавец
            )
        ).order_by(Order.created_date.desc()).all()

        return render_template('chats.html', chats=chats)
    finally:
        db_sess.close()


@app.route('/user/chat/<int:order_id>', methods=['GET', 'POST'])
@login_required
def user_chat(order_id):
    """Страница чата по определенному заказу"""
    db_sess = db_session.create_session()
    try:

        # Проверяем права доступа к чату
        order = db_sess.query(Order).filter(
            Order.id == order_id,
            or_(
                Order.user_id == current_user.id,  # Пользователь - покупатель
                Order.items.any(Product.user_id == current_user.id)  # Пользователь - продавец
            )
        ).first()

        if not order:
            flash('У вас нет доступа к этому чату', 'danger')
            return redirect('/user/chats')

        # Определяем собеседника
        if order.user_id == current_user.id:
            # Если текущий пользователь - покупатель
            chat_partner = order.items[0].product.user
        else:
            # Если текущий пользователь - продавец
            chat_partner = order.user

        # Получаем все сообщения для этого заказа
        messages = db_sess.query(Message).filter(
            Message.order_id == order_id
        ).order_by(Message.timestamp).all()

        # Форма для отправки сообщений
        form = MessageForm()

        if form.validate_on_submit():
            # Обработка отправки сообщения
            message = Message(
                sender_id=current_user.id,
                recipient_id=chat_partner.id,
                order_id=order_id
            )

            # Сохраняем текст сообщения, если есть
            if form.text.data:
                message.text = form.text.data

            # Обработка загрузки изображения
            image_file = form.image.data
            if image_file:
                # Генерируем уникальное имя файла
                filename = set_filename_image(image_file)

                # Сохраняем файл
                upload_folder = app.config['UPLOAD_FOLDER']
                image_file.save(os.path.join(upload_folder, filename))

                # Сохраняем путь к файлу в сообщении
                message.image = filename

            # Если нет текста и нет изображения - игнорируем
            if message.text or message.image:
                db_sess.add(message)
                db_sess.commit()

                flash('Сообщение отправлено', 'success')
                return redirect(f'/user/chat/{order_id}')

        return render_template('chat.html',
                               order=order,
                               messages=messages,
                               form=form,
                               chat_partner=chat_partner)
    finally:
        db_sess.close()

@app.route('/user/transfer_balance/<int:order_id>')
@login_required
def transfer_balance(order_id):
    """Перевод средств продавцу после успешного заказа"""
    db_sess = db_session.create_session()
    try:

        # Находим заказ
        order = db_sess.query(Order).filter(
            Order.id == order_id,
            or_(
                Order.user_id == current_user.id,  # Пользователь - покупатель
                Order.items.any(Product.user_id == current_user.id)  # Пользователь - продавец
            )
        ).first()

        if not order:
            flash('Доступ запрещен', 'danger')
            return redirect('/user/orders')

        # Проверяем, что заказ оплачен и еще не была произведена передача средств
        if order.status == 'paid' and not order.balance_transferred:
            try:
                # Находим продавца
                seller = order.items[0].product.user

                # Переводим деньги продавцу
                seller.balance += order.total_price - order.delivery_cost
                order.balance_transferred = True
                order.status = 'completed'

                db_sess.commit()

                flash(f'Средства в размере {order.total_price - order.delivery_cost}₽ переведены продавцу', 'success')
            except Exception as e:
                db_sess.rollback()
                flash(f'Ошибка при переводе средств: {str(e)}', 'danger')

        return redirect(f'/user/order/{order_id}')
    finally:
        db_sess.close()


if __name__ == '__main__':
    db_session.global_init('db/online_store.db')
    register_payment_routes(app)
    register_seller_routes(app)
    app.register_blueprint(products_api.blueprint)
    app.register_blueprint(users_api.blueprint)
    app.register_blueprint(orders_api.blueprint)
    app.run(debug=True)

# from flask import render_template, redirect, flash, url_for, request
# from flask_login import login_required, current_user
# import json
# import datetime
#
# from data import db_session
# from data.order import Order, OrderItem
# from data.user import User
# from form.checkout_form import CheckoutForm
#
#
# @app.route('/user/checkout', methods=['GET', 'POST'])
# @login_required
# def checkout():
#     """Обработчик страницы оформления заказа"""
#     form = CheckoutForm()
#
#     db_sess = db_session.create_session()
#
#     # Получаем все товары из корзины
#     cart_items = db_sess.query(OrderItem).filter(
#         OrderItem.user_id == current_user.id,
#         OrderItem.is_in_order == False
#     ).all()
#
#     # Если корзина пуста, перенаправляем на страницу корзины
#     if not cart_items:
#         flash('Ваша корзина пуста', 'warning')
#         return redirect('/user/cart')
#
#     # Вычисляем сумму товаров и их количество
#     product_amount_sum = sum([item.amount for item in cart_items])
#     product_price_sum = sum([item.amount * item.product.price for item in cart_items])
#
#     # Предзаполняем форму данными пользователя
#     if request.method == 'GET':
#         form.name.data = current_user.name
#         form.surname.data = current_user.surname
#         form.email.data = current_user.email
#
#     if form.validate_on_submit():
#         # Определяем стоимость доставки
#         delivery_cost = 0
#         if form.delivery_type.data == 'pickup_point':
#             delivery_cost = 150  # Базовая стоимость доставки в ПВЗ
#
#         # Общая сумма заказа с учетом доставки
#         total_price = product_price_sum + delivery_cost
#
#         # Проверяем достаточно ли средств на балансе при оплате с баланса
#         if form.payment_method.data == 'balance' and current_user.balance < total_price:
#             flash('Недостаточно средств на балансе', 'danger')
#             return render_template('checkout.html', form=form,
#                                    products=cart_items,
#                                    product_amount_sum=product_amount_sum,
#                                    product_price_sum=product_price_sum,
#                                    order_total=total_price)
#
#         try:
#             # Создаем заказ
#             order = Order(
#                 user_id=current_user.id,
#                 created_date=datetime.datetime.now(),
#                 status='new',
#                 total_price=total_price,
#
#                 # Контактная информация
#                 name=form.name.data,
#                 surname=form.surname.data,
#                 email=form.email.data,
#                 phone=form.phone.data,
#
#                 # Доставка
#                 delivery_type=form.delivery_type.data,
#                 delivery_service=form.delivery_service.data if form.delivery_type.data == 'pickup_point' else None,
#                 pvz_info=form.selected_pvz.data if form.delivery_type.data == 'pickup_point' else None,
#                 delivery_cost=delivery_cost,
#
#                 # Оплата
#                 payment_method=form.payment_method.data,
#                 is_paid=form.payment_method.data == 'balance',  # Оплачено сразу, если с баланса
#                 payment_date=datetime.datetime.now() if form.payment_method.data == 'balance' else None,
#
#                 # Комментарий
#                 comment=form.comment.data
#             )
#
#             db_sess.add(order)
#             db_sess.flush()  # Получаем ID заказа
#
#             # Добавляем товары из корзины в заказ
#             for item in cart_items:
#                 item.is_in_order = True
#                 item.order_id = order.id
#
#                 # Уменьшаем количество доступных товаров
#                 item.product.amount_available -= item.amount
#
#             # Если оплата с баланса, списываем средства
#             if form.payment_method.data == 'balance':
#                 user = db_sess.query(User).get(current_user.id)
#                 user.balance -= total_price
#
#             db_sess.commit()
#             flash('Заказ успешно оформлен!', 'success')
#
#             # Перенаправляем на страницу заказов или страницу с деталями заказа
#             return redirect(url_for('user_order_details', order_id=order.id))
#
#         except Exception as e:
#             db_sess.rollback()
#             flash(f'Произошла ошибка: {str(e)}', 'danger')
#
#     return render_template('checkout.html', form=form,
#                            products=cart_items,
#                            product_amount_sum=product_amount_sum,
#                            product_price_sum=product_price_sum,
#                            order_total=product_price_sum)
#
#
# @app.route('/user/order/<int:order_id>')
# @login_required
# def user_order_details(order_id):
#     """Страница с деталями заказа"""
#     db_sess = db_session.create_session()
#     order = db_sess.query(Order).filter(
#         Order.id == order_id,
#         Order.user_id == current_user.id
#     ).first()
#
#     if not order:
#         flash('Заказ не найден', 'danger')
#         return redirect('/user/orders')
#
#     return render_template('order_details.html', order=order)

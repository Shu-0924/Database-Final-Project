from flask_sqlalchemy import SQLAlchemy
from flask import Flask, session, render_template, url_for, redirect, flash, request
from flask_uploads import UploadSet, IMAGES, configure_uploads
from flask_wtf.csrf import CSRFProtect
from datetime import datetime
from geopy import distance
from hashlib import md5
import os

app = Flask(__name__)
path = os.path.abspath(os.path.dirname(__file__))
app.jinja_env.add_extension('jinja2.ext.loopcontrols')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(path, 'platform.db')
app.config['UPLOADED_DEF_DEST'] = path + r'\static\img'
app.config['UPLOADED_DEF_URL'] = 'img/'

upload = UploadSet(name='def', extensions=IMAGES)
configure_uploads(app, upload)
csrf = CSRFProtect(app)
db = SQLAlchemy(app)

import tables
import forms


@app.route('/', methods=['GET'])
def root():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('account') is not None:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is not None and session['password'] == U.password:
            return redirect(url_for('home'))
        else:
            session.clear()
            return redirect(url_for('login'))

    login_form = forms.Login()
    if request.method == 'GET':
        return render_template('login.html', login_form=login_form)
    if login_form.validate_on_submit():
        secret = md5(login_form.password.data.encode('utf-8')).hexdigest()
        user = db.session.query(tables.User).filter_by(account=login_form.account.data).first()
        if user is not None and secret == user.password:
            session['account'] = user.account
            session['password'] = user.password
            return redirect(url_for('home'))
    flash('Login failed!', category='danger')
    return redirect(url_for('login'))


@app.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
    session.clear()
    form = forms.SignUp()
    if form.validate_on_submit():
        secret = md5(form.password.data.encode('utf-8')).hexdigest()
        user = tables.User(form.name.data, form.phone_number.data, form.account.data,
                           secret, form.latitude.data, form.longitude.data)
        db.session.add(user)
        db.session.commit()
        flash('Sign-up success!', category='success')
        return redirect(url_for('login'))
    return render_template('sign-up.html', sign_up_form=form)


@app.route('/home', methods=['GET', 'POST'])
def home():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    edit_location_form = forms.EditLocation()
    user = db.session.query(tables.User).filter_by(account=account).first()
    distance_require = None

    if request.method == 'POST' and request.form['submit'] == 'Search':
        show_result = True
        search = ['%', '%', '%']
        shop_name = str(request.form['shop_name']).strip()
        shop_category = str(request.form['shop_category']).strip()
        meal_name = str(request.form['meal_name']).strip()
        min_price = str(request.form['min_price']).strip()
        max_price = str(request.form['max_price']).strip()
        if shop_name != "":
            search[0] = '%' + shop_name + '%'
        if shop_category != "":
            search[1] = '%' + shop_category + '%'
        if request.form['distance'] != "":
            distance_require = str(request.form['distance'])
        if meal_name != "":
            search[2] = '%' + meal_name + '%'
            meal_list = db.session.query(tables.Product)\
                .filter(tables.Product.meal_name.ilike(search[2])).all()
            SID_list_1 = list(set([meal.SID for meal in meal_list]))
        else:
            SID_list_1 = [S.SID for S in db.session.query(tables.Shop).all()]
        if min_price != "":
            meal_list = db.session.query(tables.Product) \
                .filter(tables.Product.price >= min_price).all()
            SID_list_2 = list(set([meal.SID for meal in meal_list]))
        else:
            SID_list_2 = [S.SID for S in db.session.query(tables.Shop).all()]
        if max_price != "":
            meal_list = db.session.query(tables.Product) \
                .filter(tables.Product.price <= max_price).all()
            SID_list_3 = list(set([meal.SID for meal in meal_list]))
        else:
            SID_list_3 = [S.SID for S in db.session.query(tables.Shop).all()]
        shop_list = db.session.query(tables.Shop)\
            .filter(tables.Shop.shop_name.ilike(search[0])) \
            .filter(tables.Shop.shop_category.ilike(search[1]))\
            .filter(tables.Shop.SID.in_(SID_list_1)) \
            .filter(tables.Shop.SID.in_(SID_list_2)) \
            .filter(tables.Shop.SID.in_(SID_list_3))
    else:
        show_result = False
        shop_list = db.session.query(tables.Shop).all()

    dist_list = [int(distance.distance((user.latitude, user.longitude), (S.latitude, S.longitude)).km)
                 for S in shop_list]
    distances = dict(zip(range(1, len(dist_list) + 1), dist_list))
    menu_list = [db.session.query(tables.Product).filter_by(SID=S.SID).all() for S in shop_list]
    shop_menu = dict(zip(range(1, len(menu_list) + 1), menu_list))
    all_category = list(set([S.shop_category for S in db.session.query(tables.Shop).all()]))

    if edit_location_form.validate_on_submit():
        user.latitude = edit_location_form.latitude.data
        user.longitude = edit_location_form.longitude.data
        db.session.merge(user)
        db.session.commit()
        return redirect(url_for('home'))

    return render_template('home.html', user=user,
                           show_result=show_result,
                           all_category=all_category,
                           shop_list=shop_list,
                           shop_menu=shop_menu,
                           distances=distances,
                           distance_require=distance_require,
                           edit_location_form=edit_location_form)


@app.route('/home/A', methods=['POST'])
def add_value():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    value = str(request.form['value']).strip()
    if value != "":
        try:
            user.wallet_balance += int(value)
            now = datetime.now()
            T = tables.Record(user.UID, 'Recharge', now.strftime('%Y-%m-%d %H:%M:%S'), user.name, '+'+str(value))
            db.session.add(user)
            db.session.add(T)
            db.session.commit()
            flash(f"You have charged {value} dollar!", category='success')
        except ValueError:
            db.session.rollback()
            flash("Fail to charge!", category='danger')
    return redirect(url_for('home'))


@app.route('/home/V/<SID>', methods=['POST'])
def view_order(SID):
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    order_shop = db.session.query(tables.Shop).filter_by(SID=SID).first()
    shop_product = db.session.query(tables.Product).filter_by(SID=SID).all()
    order_list = []
    for P in shop_product:
        try:
            str(request.form[f'PID{P.PID}'])
        except KeyError:
            continue
        if str(request.form[f'PID{P.PID}']).strip() == "":
            order_list.append((P.PID, P.price, 0))
        else:
            order_list.append((P.PID, P.price, int(request.form[f'PID{P.PID}'])))
    order_type = str(request.form['type']).strip()
    subtotal = sum([order[1]*order[2] for order in order_list])
    if subtotal == 0:
        flash('You need to order at least one product!', category='danger')
        return redirect(url_for('home'))
    dist = distance.distance((user.latitude, user.longitude), (order_shop.latitude, order_shop.longitude)).km
    delivery_fee = max(10, int(dist*10+0.5)) if order_type == 'Delivery' else 0
    total = subtotal+delivery_fee
    if total > user.wallet_balance:
        flash(f'Wallet balance is not enough! (Include {delivery_fee} dollar deliver fee)', category='danger')
        return redirect(url_for('home'))
    order_item = [db.session.query(tables.Product).filter_by(PID=P[0]).first() for P in order_list if P[2] != 0]
    order_quantity = dict([(P[0], P[2]) for P in order_list if P[2] != 0])
    return render_template('order.html', shop=order_shop, order_item=order_item, order_quantity=order_quantity,
                           subtotal=subtotal, delivery_fee=delivery_fee, total=total)


@app.route('/home/C/<SID>', methods=['POST'])
def confirm_order(SID):
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    order_shop = db.session.query(tables.Shop).filter_by(SID=SID).first()
    shop_product = db.session.query(tables.Product).filter_by(SID=SID).all()

    order_list = []
    for P in shop_product:
        try:
            price = int(request.form[f'PID{P.PID}price'])
            quantity = int(request.form[f'PID{P.PID}quantity'])
            if P.exist == 'false' or price != P.price:
                flash('The shop has updated its product, please order again.', category='warning')
                return redirect(url_for('home'))
            order_list.append((P.PID, P.price, quantity))
        except KeyError:
            pass

    flag = [False]
    not_enough = 'There are no enough products for you, please be faster next time.\n'
    for product in order_list:
        P = db.session.query(tables.Product).filter_by(PID=product[0]).first()
        if product[2] > P.quantity:
            flag[0] = True
            not_enough += f'  > {P.meal_name}\n'
    if flag[0] is True:
        flash(not_enough, category='warning')
        return redirect(url_for('home'))

    now = datetime.now()
    total = int(request.form['total'])
    latest_order = db.session.query(tables.Order).order_by(tables.Order.OID.desc()).first()
    OID = 1 if latest_order is None else latest_order.OID + 1
    order = tables.Order(OID, user.UID, order_shop.SID, 'Not Finish', now.strftime('%Y-%m-%d %H:%M:%S'), None, total)
    db.session.add(order)
    for product in order_list:
        p = db.session.query(tables.Product).filter_by(PID=product[0]).first()
        p.quantity -= product[2]
        db.session.add(p)
        order_meal = tables.OrderProduct(OID, product[0], product[1], product[2])
        db.session.add(order_meal)
    shop_manager = db.session.query(tables.User).filter_by(UID=order_shop.UID).first()
    user.wallet_balance -= total
    shop_manager.wallet_balance += total
    T1 = tables.Record(user.UID, 'Payment', now.strftime('%Y-%m-%d %H:%M:%S'), order_shop.shop_name, '-'+str(total))
    T2 = tables.Record(shop_manager.UID, 'Receive', now.strftime('%Y-%m-%d %H:%M:%S'), user.name, '+'+str(total))
    db.session.add(user)
    db.session.add(shop_manager)
    db.session.add(T1)
    db.session.add(T2)
    db.session.commit()
    flash('Order success!', category='success')
    return redirect(url_for('home'))


@app.route('/shop', methods=['GET', 'POST'])
def shop():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    register_form = forms.Register()
    add_meal_form = forms.AddMeal()
    user = db.session.query(tables.User).filter_by(account=account).first()
    user_shop = db.session.query(tables.Shop).filter_by(UID=user.UID).first()
    if user_shop is not None:
        shop_menu = db.session.query(tables.Product).filter_by(SID=user_shop.SID).all()
    else:
        shop_menu = None

    if user_shop is None:
        if register_form.validate_on_submit():
            user_shop = tables.Shop(user.UID,
                                    str(register_form.shop_name.data).strip(),
                                    str(register_form.shop_category.data).strip(),
                                    register_form.latitude.data,
                                    register_form.longitude.data)
            db.session.add(user_shop)
            db.session.commit()
            flash('Registration success!', category='success')
            return redirect(url_for('shop'))
    else:
        if add_meal_form.validate_on_submit():
            if not all(ord(c) < 128 for c in add_meal_form.picture.data.filename):
                flash('Sorry, we can not accept this filename.', category='warning')
                return redirect(url_for('shop'))
            file_name = upload.save(add_meal_form.picture.data)
            file_url = upload.url(file_name)
            meal = tables.Product(user_shop.SID,
                                  file_url,
                                  str(add_meal_form.meal_name.data).strip(),
                                  add_meal_form.price.data,
                                  add_meal_form.quantity.data)
            db.session.add(meal)
            db.session.commit()
            return redirect(url_for('shop'))
    return render_template('shop.html', user=user, shop=user_shop, shop_menu=shop_menu,
                           register_form=register_form,
                           add_meal_form=add_meal_form)


@app.route('/shop/<PID>/EP', methods=['POST'])
def edit_product(PID):
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    new_price = str(request.form[f'{PID}price']).strip()
    new_quantity = str(request.form[f'{PID}quantity']).strip()
    if new_price == "" or new_quantity == "":
        flash('Both field is required!', category='danger')
        return redirect(url_for('shop'))
    try:
        if int(new_price) < 0:
            raise ValueError
        if int(new_quantity) < 0:
            raise ValueError
        meal = db.session.query(tables.Product).filter_by(PID=PID).first()
        meal.price = new_price
        meal.quantity = new_quantity
        db.session.add(meal)
        db.session.commit()
        flash('Update success', category='success')
    except ValueError:
        flash('Invalid input!', category='danger')
    return redirect(url_for('shop'))


@app.route('/shop/<PID>/DP', methods=['POST'])
def delete_product(PID):
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    meal = db.session.query(tables.Product).filter_by(PID=PID).first()
    meal.exist = 'false'
    db.session.add(meal)
    db.session.commit()
    return redirect(url_for('shop'))


@app.route('/MyOrder', methods=['GET', 'POST'])
def my_order():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    orders = db.session.query(tables.Order).filter_by(UID=user.UID)\
        .order_by(tables.Order.start.desc()).all()
    order_shops = [db.session.query(tables.Shop).filter_by(SID=order.SID).first() for order in orders]
    shop_list = dict(zip(range(1, len(order_shops) + 1), order_shops))
    order_d = [db.session.query(tables.OrderProduct).filter_by(OID=order.OID).all() for order in orders]
    order_details = dict(zip(range(1, len(order_d) + 1), order_d))
    all_products_L = []
    for order_products in order_d:
        L = [db.session.query(tables.Product).filter_by(PID=OP.PID).first() for OP in order_products]
        D = dict(zip(range(1, len(L) + 1), L))
        all_products_L.append(D)
    all_products = dict(zip(range(1, len(all_products_L) + 1), all_products_L))
    subtotals_L = [sum([OP.product_price*OP.product_quantity for OP in order_products]) for order_products in order_d]
    subtotals = dict(zip(range(1, len(subtotals_L) + 1), subtotals_L))
    if request.method == 'POST':
        status_show = request.form['status']
    else:
        status_show = 'All'
    return render_template('my_order.html', user=user, orders=orders,
                           shop_list=shop_list, status_show=status_show,
                           order_details=order_details, subtotals=subtotals,
                           all_products=all_products)


@app.route('/ShopOrder', methods=['GET', 'POST'])
def shop_order():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    user_shop = db.session.query(tables.Shop).filter_by(UID=user.UID).first()
    if user_shop is None:
        flash('Please register the shop first.', category='warning')
        return redirect(url_for('shop'))
    orders = db.session.query(tables.Order).filter_by(SID=user_shop.SID) \
        .order_by(tables.Order.start.desc()).all()
    order_shops = [db.session.query(tables.Shop).filter_by(SID=order.SID).first() for order in orders]
    shop_list = dict(zip(range(1, len(order_shops) + 1), order_shops))
    order_d = [db.session.query(tables.OrderProduct).filter_by(OID=order.OID).all() for order in orders]
    order_details = dict(zip(range(1, len(order_d) + 1), order_d))
    all_products_L = []
    for order_products in order_d:
        L = [db.session.query(tables.Product).filter_by(PID=OP.PID).first() for OP in order_products]
        D = dict(zip(range(1, len(L) + 1), L))
        all_products_L.append(D)
    all_products = dict(zip(range(1, len(all_products_L) + 1), all_products_L))
    subtotals_L = [sum([OP.product_price * OP.product_quantity for OP in order_products]) for order_products in order_d]
    subtotals = dict(zip(range(1, len(subtotals_L) + 1), subtotals_L))
    if request.method == 'POST':
        status_show = request.form['status']
    else:
        status_show = 'All'
    return render_template('shop_order.html', user=user, orders=orders,
                           shop_list=shop_list, status_show=status_show,
                           order_details=order_details, subtotals=subtotals,
                           all_products=all_products)


@app.route('/cancel-order/<ret>', methods=['POST'])
def cancel_order(ret):
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    OID = int(request.form['OID'])
    order = db.session.query(tables.Order).filter_by(OID=OID).first()

    user = db.session.query(tables.User).filter_by(account=account).first()
    order_shop = db.session.query(tables.Shop).filter_by(SID=order.SID).first()
    manager = db.session.query(tables.User).filter_by(UID=order_shop.UID).first()
    if ret == 'shop_order' and order.total > user.wallet_balance:
        db.session.rollback()
        flash('You do not have enough money to cancel this order!', category='danger')
        return redirect(url_for('shop_order'))
    user.wallet_balance += order.total
    manager.wallet_balance -= order.total
    db.session.add(user)
    db.session.add(manager)

    OPs = db.session.query(tables.OrderProduct).filter_by(OID=OID).all()
    product_change = [(db.session.query(tables.Product).filter_by(PID=OP.PID).first(), OP.product_quantity) for OP in OPs]
    for P in product_change:
        if P[0].exist == 'false':
            continue
        P[0].quantity += P[1]
        db.session.add(P[0])

    now = datetime.now()
    if order.status != 'Not Finish':
        flash('Fail to finish the order! Someone canceled or finished the order.', category='danger')
        db.session.rollback()
        if ret == 'shop_order':
            return redirect(url_for('shop_order'))
        else:
            return redirect(url_for('my_order'))
    order.status = 'Cancel'
    order.end = now.strftime('%Y-%m-%d %H:%M:%S')
    T1 = tables.Record(user.UID, 'Receive', now.strftime('%Y-%m-%d %H:%M:%S'), order_shop.shop_name, '+' + str(order.total))
    T2 = tables.Record(manager.UID, 'Payment', now.strftime('%Y-%m-%d %H:%M:%S'), user.name, '-' + str(order.total))
    db.session.add(T1)
    db.session.add(T2)
    db.session.add(order)
    db.session.commit()

    if ret == 'my_order':
        return redirect(url_for('my_order'))
    elif ret == 'shop_order':
        return redirect(url_for('shop_order'))
    return redirect(url_for('home'))


@app.route('/finish-order', methods=['POST'])
def finish_order():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    OID = int(request.form['OID'])
    order = db.session.query(tables.Order).filter_by(OID=OID).first()
    now = datetime.now()
    if order.status != 'Not Finish':
        flash('Fail to finish the order! Someone canceled the order.', category='danger')
        db.session.rollback()
        return redirect(url_for('shop_order'))
    order.status = 'Finished'
    order.end = now.strftime('%Y-%m-%d %H:%M:%S')
    db.session.add(order)
    db.session.commit()
    return redirect(url_for('shop_order'))


@app.route('/record', methods=['GET', 'POST'])
def record():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    account = session['account']
    user = db.session.query(tables.User).filter_by(account=account).first()
    transaction_records = db.session.query(tables.Record).\
        filter_by(UID=user.UID).order_by(tables.Record.time.desc()).all()
    if request.method == 'POST':
        action_show = request.form['action']
    else:
        action_show = 'All'
    return render_template('record.html', user=user, action_show=action_show,
                           transaction_records=transaction_records)


@app.route('/logout', methods=['GET'])
def logout():
    if session.get('account') is None:
        session.clear()
        return redirect(url_for('login'))
    else:
        U = db.session.query(tables.User).filter_by(account=session['account']).first()
        if U is None or session['password'] != U.password:
            session.clear()
            return redirect(url_for('login'))

    session.clear()
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.debug = True
    app.secret_key = "NMSL"
    app.run()

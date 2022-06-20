import main
import os

db = main.db


class User(db.Model):
    __tablename__ = 'Users'
    UID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    phone_number = db.Column(db.String, nullable=False)
    account = db.Column(db.String, unique=True, nullable=False)
    password = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    wallet_balance = db.Column(db.Integer, default=0, nullable=False)

    def __init__(self, name, phone_number, account, password, latitude, longitude):
        self.name = name
        self.phone_number = phone_number
        self.account = account
        self.password = password
        self.latitude = latitude
        self.longitude = longitude
        self.wallet_balance = 0

    def __repr__(self):
        return '<User %r>' % self.UID


class Shop(db.Model):
    __tablename__ = 'Shops'
    SID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UID = db.Column(db.Integer, db.ForeignKey('Users.UID', ondelete='CASCADE'), nullable=False)
    shop_name = db.Column(db.String, unique=True, nullable=False)
    shop_category = db.Column(db.String, nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    def __init__(self, UID, shop_name, shop_category, latitude, longitude):
        self.UID = UID
        self.shop_name = shop_name
        self.shop_category = shop_category
        self.latitude = latitude
        self.longitude = longitude

    def __repr__(self):
        return '<Shop %r>' % self.SID


class Product(db.Model):
    __tablename__ = 'Products'
    PID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Shops.SID', ondelete='CASCADE'), nullable=False)
    picture = db.Column(db.String, nullable=False)
    meal_name = db.Column(db.String, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    exist = db.Column(db.String, default='true', nullable=False)

    def __init__(self, SID, picture, meal_name, price, quantity):
        self.SID = SID
        self.picture = picture
        self.meal_name = meal_name
        self.price = price
        self.quantity = quantity
        self.exist = 'true'

    def __repr__(self):
        return '<Product %r>' % self.PID


class Order(db.Model):
    __tablename__ = 'Orders'
    OID = db.Column(db.Integer, primary_key=True)
    UID = db.Column(db.Integer, db.ForeignKey('Users.UID', ondelete='CASCADE'), nullable=False)
    SID = db.Column(db.Integer, db.ForeignKey('Shops.SID', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.String, nullable=False)
    start = db.Column(db.String, nullable=False)
    end = db.Column(db.String, nullable=True)
    total = db.Column(db.Integer, nullable=False)

    def __init__(self, OID, UID, SID, status, start, end, total):
        self.OID = OID
        self.UID = UID
        self.SID = SID
        self.status = status
        self.start = start
        self.end = end
        self.total = total

    def __repr__(self):
        return '<Order %r>' % self.OID


class OrderProduct(db.Model):
    __tablename__ = 'OrderProducts'
    OID = db.Column(db.Integer, db.ForeignKey('Orders.OID', ondelete='CASCADE'), primary_key=True)
    PID = db.Column(db.Integer, db.ForeignKey('Products.PID', ondelete='CASCADE'), primary_key=True)
    product_price = db.Column(db.Integer, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)

    def __init__(self, OID, PID, product_price, product_quantity):
        self.OID = OID
        self.PID = PID
        self.product_price = product_price
        self.product_quantity = product_quantity

    def __repr__(self):
        return '<OrderProduct OID={}, PID={}>'.format(self.OID, self.PID)


class Record(db.Model):
    __tablename__ = 'Records'
    TID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    UID = db.Column(db.Integer, db.ForeignKey('Users.UID', ondelete='CASCADE'), nullable=False)
    action = db.Column(db.String, nullable=False)
    time = db.Column(db.String, nullable=False)
    trader = db.Column(db.String, nullable=False)
    amount_change = db.Column(db.String, nullable=False)

    def __init__(self, UID, action, time, trader, amount_change):
        self.UID = UID
        self.action = action
        self.time = time
        self.trader = trader
        self.amount_change = amount_change

    def __repr__(self):
        return '<Record %r>' % self.TID


if not os.path.exists('platform.db'):
    db.create_all()

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.Text, nullable=False)
    role = db.Column(db.String(20), nullable=False)

    # Address fields
    street = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    province = db.Column(db.String(100), nullable=False)
    postal_code = db.Column(db.String(20), nullable=False)

    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)

    # Establish unique backref names for each relationship
    consumer = db.relationship('Consumer', backref=db.backref('consumer_user', uselist=False), uselist=False, overlaps="consumer_user")
    retailer = db.relationship('Retailer', backref=db.backref('retailer_user', uselist=False), uselist=False, overlaps="retailer_user")
    organization = db.relationship('Organization', backref=db.backref('organization_user', uselist=False), uselist=False, overlaps="organization_user")


class Consumer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Define the relationship with User
    user = db.relationship('User', backref=db.backref('consumer_user', uselist=False), uselist=False)


class Organization(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    org_type = db.Column(db.String(20), nullable=False)  # shelter or food bank

    # Establish relationship with User
    user = db.relationship('User', backref=db.backref('organization_user', uselist=False), uselist=False)


class Retailer(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Define the relationship with User
    user = db.relationship('User', backref=db.backref('retailer_user', uselist=False), uselist=False)

    # Food items related to the retailer
    food_items = db.relationship('FoodItem', backref='retailer', lazy=True)


class FoodItem(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    retailer_id = db.Column(db.Integer, db.ForeignKey('retailer.id'), nullable=False)


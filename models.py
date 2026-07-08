from database import db
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash



# USERS TABLE


class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(50),
        default="Inventory Officer"
    )


    def set_password(self, password):

        self.password = generate_password_hash(password)


    def check_password(self, password):

        return check_password_hash(
            self.password,
            password
        )


# PRODUCT TABLE

class Product(db.Model):

    id=db.Column(
        db.Integer,
        primary_key=True
    )

    name=db.Column(
        db.String(100)
    )


    category=db.Column(
        db.String(100)
    )


    quantity=db.Column(
        db.Integer,
        default=0
    )


    unit=db.Column(
        db.String(50)
    )




# STOCK TRANSACTION TABLE

class StockTransaction(db.Model):

    __tablename__ = "stock_transaction"

    id = db.Column(db.Integer, primary_key=True)

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("product.id")
    )

    transaction_type = db.Column(db.String(10))

    quantity = db.Column(db.Integer)

    balance_after = db.Column(db.Integer)

    reference = db.Column(db.String(100))

    remarks = db.Column(db.Text)

    created_by = db.Column(db.Integer)

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    product = db.relationship("Product")
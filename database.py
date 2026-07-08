from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialize SQLAlchemy
db = SQLAlchemy()


# ============= USERS TABLE =============
class User(db.Model):
    __tablename__ = 'users'

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

    # Timestamps for tracking
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    transactions = db.relationship(
        'StockTransaction',
        backref='user',
        foreign_keys='StockTransaction.created_by',
        lazy=True
    )

    def set_password(self, password):
        """Hash and set the user's password"""
        self.password = generate_password_hash(password)

    def check_password(self, password):
        """Check if the provided password matches the stored hash"""
        return check_password_hash(
            self.password,
            password
        )

    def __repr__(self):
        return f'<User {self.username}>'


# ============= PRODUCT TABLE =============
class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    category = db.Column(
        db.String(100)
    )

    quantity = db.Column(
        db.Integer,
        default=0
    )

    unit = db.Column(
        db.String(50)
    )

    # Timestamps for tracking
    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    # Relationships
    transactions = db.relationship(
        'StockTransaction',
        backref='product',
        foreign_keys='StockTransaction.product_id',
        lazy=True
    )

    def __repr__(self):
        return f'<Product {self.name} (Qty: {self.quantity})>'

    def get_low_stock(self):
        """Check if product is low stock (less than 10 units)"""
        return self.quantity <= 10

    def get_stock_status(self):
        """Return stock status as string"""
        if self.quantity <= 0:
            return "Out of Stock"
        elif self.quantity <= 10:
            return "Low Stock"
        elif self.quantity <= 50:
            return "Normal"
        else:
            return "High Stock"


# ============= STOCK TRANSACTION TABLE =============
class StockTransaction(db.Model):
    __tablename__ = "stock_transactions"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    transaction_type = db.Column(
        db.String(10),
        nullable=False
    )  # 'IN' or 'OUT'

    quantity = db.Column(
        db.Integer,
        nullable=False
    )

    balance_after = db.Column(
        db.Integer,
        nullable=False
    )

    reference = db.Column(
        db.String(100)
    )

    remarks = db.Column(
        db.Text
    )

    created_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f'<StockTransaction {self.transaction_type} {self.quantity} of Product {self.product_id}>'

    def get_transaction_type_badge(self):
        """Return badge class for transaction type"""
        return "success" if self.transaction_type == "IN" else "danger"


# ============= CUSTOMER TABLE (Optional) =============
class Customer(db.Model):
    __tablename__ = 'customers'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    phone = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f'<Customer {self.name}>'


# ============= SUPPLIER TABLE (Optional) =============
class Supplier(db.Model):
    __tablename__ = 'suppliers'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    contact_person = db.Column(
        db.String(100)
    )

    phone = db.Column(
        db.String(20)
    )

    email = db.Column(
        db.String(100)
    )

    address = db.Column(
        db.Text
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    def __repr__(self):
        return f'<Supplier {self.name}>'


# ============= INVENTORY LOG (Audit Trail) =============
class InventoryLog(db.Model):
    __tablename__ = 'inventory_logs'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    product_id = db.Column(
        db.Integer,
        db.ForeignKey("products.id"),
        nullable=False
    )

    action = db.Column(
        db.String(50),
        nullable=False
    )  # 'CREATED', 'UPDATED', 'DELETED'

    old_value = db.Column(
        db.Text
    )

    new_value = db.Column(
        db.Text
    )

    changed_by = db.Column(
        db.Integer,
        db.ForeignKey("users.id"),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Relationships
    product = db.relationship('Product', backref='logs')
    user = db.relationship('User', backref='logs')

    def __repr__(self):
        return f'<InventoryLog {self.action} Product {self.product_id} by User {self.changed_by}>'


# ============= HELPER FUNCTIONS =============
def init_db():
    """Initialize the database with default data"""
    db.create_all()

    # Create default admin user if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            role='Admin'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # Create some sample products
        sample_products = [
            Product(name='Cooking Gas 12kg', category='Cooking Gas', quantity=100, unit='kg'),
            Product(name='Cooking Gas 6kg', category='Cooking Gas', quantity=150, unit='kg'),
            Product(name='Cooking Gas 3kg', category='Cooking Gas', quantity=200, unit='kg'),
            Product(name='Industrial Gas 50kg', category='Industrial Gas', quantity=50, unit='kg'),
            Product(name='Argon Gas', category='Industrial Gas', quantity=30, unit='L'),
            Product(name='Oxygen Gas', category='Medical Gas', quantity=40, unit='L'),
            Product(name='Nitrogen Gas', category='Industrial Gas', quantity=25, unit='L'),
        ]

        for product in sample_products:
            db.session.add(product)

        db.session.commit()

        # Add initial stock transactions for sample products
        for product in Product.query.all():
            if product.quantity > 0:
                transaction = StockTransaction(
                    product_id=product.id,
                    transaction_type='IN',
                    quantity=product.quantity,
                    balance_after=product.quantity,
                    reference='Initial Stock',
                    remarks='System initialization',
                    created_by=admin.id
                )
                db.session.add(transaction)

        db.session.commit()
        print("Database initialized with default admin and sample data!")
    else:
        print("Database already initialized.")


def get_product_summary():
    """Get summary statistics for products"""
    total_products = Product.query.count()
    total_stock = db.session.query(db.func.sum(Product.quantity)).scalar() or 0
    low_stock = Product.query.filter(Product.quantity <= 10).count()
    out_of_stock = Product.query.filter(Product.quantity <= 0).count()

    return {
        'total_products': total_products,
        'total_stock': total_stock,
        'low_stock': low_stock,
        'out_of_stock': out_of_stock
    }


def get_daily_transactions(date=None):
    """Get transactions for a specific date"""
    if date is None:
        date = datetime.utcnow().date()

    start_date = datetime(date.year, date.month, date.day, 0, 0, 0)
    end_date = datetime(date.year, date.month, date.day, 23, 59, 59)

    transactions = StockTransaction.query.filter(
        StockTransaction.created_at >= start_date,
        StockTransaction.created_at <= end_date
    ).all()

    total_in = sum(t.quantity for t in transactions if t.transaction_type == 'IN')
    total_out = sum(t.quantity for t in transactions if t.transaction_type == 'OUT')

    return {
        'transactions': transactions,
        'total_in': total_in,
        'total_out': total_out,
        'net_change': total_in - total_out
    }


def log_inventory_change(product_id, action, old_value, new_value, user_id):
    """Log inventory changes for audit trail"""
    log = InventoryLog(
        product_id=product_id,
        action=action,
        old_value=str(old_value),
        new_value=str(new_value),
        changed_by=user_id
    )
    db.session.add(log)
    db.session.commit()
    return log
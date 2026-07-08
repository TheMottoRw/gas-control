import os

from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from database import db, User, Product, StockTransaction
from werkzeug.security import generate_password_hash, check_password_hash
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] =  "sqlite:///" + os.path.join(BASE_DIR, "database", "gas_control.db")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# Create tables
with app.app_context():
    db.create_all()
    # Create default admin user if not exists
    if not User.query.filter_by(username='asua@yopmail.com').first():
        admin = User(username='asua@yopmail.com', role='Admin')
        admin.set_password('12345')
        db.session.add(admin)
        db.session.commit()


# ============= ROUTES =============

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password!', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully!', 'info')
    return redirect(url_for('login'))


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    # Get statistics
    total_products = Product.query.count()
    total_stock = db.session.query(db.func.sum(Product.quantity)).scalar() or 0
    recent_transactions = StockTransaction.query.order_by(
        StockTransaction.created_at.desc()
    ).limit(10).all()

    return render_template('dashboard.html',
                           total_products=total_products,
                           total_stock=total_stock,
                           recent_transactions=recent_transactions)


# ============= PRODUCT MANAGEMENT =============

@app.route('/products')
def products():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    all_products = Product.query.all()
    return render_template('products.html', products=all_products)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form.get('name')
        category = request.form.get('category')
        quantity = int(request.form.get('quantity', 0))
        unit = request.form.get('unit')

        if Product.query.filter_by(name=name).first():
            flash('Product already exists!', 'warning')
            return redirect(url_for('add_product'))

        product = Product(
            name=name,
            category=category,
            quantity=quantity,
            unit=unit
        )

        db.session.add(product)
        db.session.commit()

        # Log initial stock
        if quantity > 0:
            transaction = StockTransaction(
                product_id=product.id,
                transaction_type='IN',
                quantity=quantity,
                balance_after=quantity,
                reference='Initial Stock',
                remarks='Initial product creation',
                created_by=session['user_id']
            )
            db.session.add(transaction)
            db.session.commit()

        flash('Product added successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('add_product.html')


@app.route('/edit_product/<int:id>', methods=['GET', 'POST'])
def edit_product(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name')
        product.category = request.form.get('category')
        product.unit = request.form.get('unit')

        db.session.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('products'))

    return render_template('edit_product.html', product=product)


@app.route('/delete_product/<int:id>')
def delete_product(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    product = Product.query.get_or_404(id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('products'))


# ============= STOCK MANAGEMENT =============

@app.route('/stock_adjustment', methods=['GET', 'POST'])
def stock_adjustment():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        product_id = request.form.get('product_id')
        transaction_type = request.form.get('transaction_type')
        quantity = int(request.form.get('quantity'))
        reference = request.form.get('reference')
        remarks = request.form.get('remarks')

        product = Product.query.get_or_404(product_id)

        # Calculate new balance
        if transaction_type == 'IN':
            new_balance = product.quantity + quantity
        else:  # OUT
            if product.quantity < quantity:
                flash('Insufficient stock!', 'danger')
                return redirect(url_for('stock_adjustment'))
            new_balance = product.quantity - quantity

        # Update product quantity
        product.quantity = new_balance

        # Create transaction record
        transaction = StockTransaction(
            product_id=product.id,
            transaction_type=transaction_type,
            quantity=quantity,
            balance_after=new_balance,
            reference=reference,
            remarks=remarks,
            created_by=session['user_id']
        )

        db.session.add(transaction)
        db.session.commit()

        flash(f'Stock {transaction_type} successful!', 'success')
        return redirect(url_for('stock_transactions'))

    products = Product.query.all()
    return render_template('stock_adjustment.html', products=products)


# ============= TRANSACTION HISTORY =============

@app.route('/transactions')
def stock_transactions():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    transactions = StockTransaction.query.order_by(
        StockTransaction.created_at.desc()
    ).all()

    return render_template('transactions.html', transactions=transactions)


# ============= USER MANAGEMENT =============

@app.route('/users')
def users():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    all_users = User.query.all()
    return render_template('users.html', users=all_users)


@app.route('/add_user', methods=['GET', 'POST'])
def add_user():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role')

        if User.query.filter_by(username=username).first():
            flash('Username already exists!', 'warning')
            return redirect(url_for('add_user'))

        user = User(username=username, role=role)
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        flash('User added successfully!', 'success')
        return redirect(url_for('users'))

    return render_template('add_user.html')


@app.route('/delete_user/<int:id>')
def delete_user(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'Admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('dashboard'))

    user = User.query.get_or_404(id)
    if user.id == session['user_id']:
        flash('Cannot delete yourself!', 'danger')
        return redirect(url_for('users'))

    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!', 'success')
    return redirect(url_for('users'))


if __name__ == '__main__':
    app.run(debug=True)
import pyotp
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash, g
from Forms import CreateCartForm, CreateUserForm, CreateCustomerForm, CreateFeedbackForm, ProductForm
import shelve, Product, Price, User, Customer, Feedback, app
from models import Product
import database
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import MySQLdb.cursors
import cryptography
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, timezone
import os
import re
from password_strength import PasswordPolicy
from password_strength import PasswordStats
import random
from pyotp import TOTP
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your secret key'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'mysql'
app.config['MYSQL_DB'] = 'pythonbiro'
app.config['MYSQL_PORT'] = 3306
app.config['SECRET_KEY'] = 'Thisisasecret!'
app.config['RECAPTCHA_PUBLIC_KEY'] = '6LerHiUqAAAAANG4DuDc6u1UN8aYFOSI_fg-D2Z2'
app.config['RECAPTCHA_PRIVATE_KEY'] = '6LerHiUqAAAAAEsAskWHpNu30hURrRdiBwEquwMs'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = 'birocompany921@gmail.com' #Password: birocompany12 or fxmm zqrv kzgj mnfc
app.config['MAIL_PASSWORD'] = 'fxmm zqrv kzgj mnfc'
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
mail = Mail(app)

policy = PasswordPolicy.from_names(
    length=8, # min length: 8
    uppercase=1, # need min. 2 uppercase letters
    numbers=1, # need min. 2 digits
    strength=0.66 # need a password that scores at least 0.5 with its entropy bits
)

mysql = MySQL(app)
bcrypt = Bcrypt()

app.session_cleared = False

app.permanent_session_lifetime = timedelta(minutes=10)


SECURITY_QUESTIONS = [
    "What is your favorite color?",
    "What is your favorite animal?",
    "Who is your favorite idol?",
    "What high school did you attend?",
    "What is your favorite food?",
    "What is your favorite game?"
]


@app.before_request
def check_and_update_session():
    # Clear session

    if not app.session_cleared:
        session.clear()  # Clear session on the first request after the app starts
        app.session_cleared = True

    # Session Timeout

    if 'loggedin' in session:  # Check if user (customer or staff) is logged in
        session.permanent = True  # Make session permanent
        now = datetime.now(timezone.utc)  # Make 'now' timezone-aware

        if 'last_activity' in session:
            last_activity = session['last_activity']

            if (now - last_activity).total_seconds() > 600:  # Check if 10 minutes have passed
                session.clear()  # Clear the session data
                return redirect(url_for('home', msg='Session timed out. Please log in again.'))

        session['last_activity'] = now  # Update last activity time

@app.route('/')
def home():
    return render_template('home.html')


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('home'))  # Redirect to home page


#Magnus Done changing db
@app.route('/createUser', methods=['GET', 'POST'])
def create_user():
    create_user_form = CreateUserForm(request.form)
    if request.method == 'POST' and create_user_form.validate():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        password = create_user_form.password.data
        stats = PasswordStats(password)
        checkpolicy = policy.test(password)

        if stats.strength() < 0.66:
            flash("Password not strong enough. Avoid consecutive characters and easily guessed words.")
            return render_template('createUser.html', form=create_user_form)

        # Check if the username already exists
        cursor.execute('SELECT * FROM staff WHERE staff_username = %s', ( create_user_form.username.data,))
        staff = cursor.fetchone()

        if staff:
            # Username already exists
            msg = 'Username already exists, please choose a different one!'
            flash(msg, 'danger')  # Use Flask's flash to show messages
        else:
            # Username does not exist, proceed with registration

            # Hash password securely before storing
            hashpwd = bcrypt.generate_password_hash(create_user_form.password.data)
            #
            # session['staff_username'] = create_user_form.username.data
            # session['staff_password'] = hashpwd

            cursor.execute(
                'INSERT INTO staff (staff_username, staff_password,staff_position) VALUES (%s, %s, %s)',
                (create_user_form.username.data, hashpwd, create_user_form.role.data)
            )
            mysql.connection.commit()
            msg = 'You have successfully registered!'
            flash(msg, 'success')


        return redirect(url_for('staff_login'))
    return render_template('createUser.html', form=create_user_form)

def send_email_otp(email, otp_secret):
    authenticator = pyotp.TOTP(otp_secret, interval=60)  # 60-second time window
    email_otp = authenticator.now()
    print("Email OTP:", email_otp)
    msg = Message('OTP for Registration', sender='birocompany921@gmail.com', recipients=[email])
    msg.body = f'Your OTP is: {email_otp}'
    mail.send(msg)
@app.route('/createCustomer', methods=['GET', 'POST'])
def create_customer():
    create_customer_form = CreateCustomerForm(request.form)
    msg = ''
    otp_sent = False
    otp_verified = session.get('otp_verified', False)

    if request.method == 'POST':
        if 'verify_email' in request.form:
            # Only validate the email field
            if create_customer_form.email.validate(create_customer_form):
                # Send OTP to user's email
                otp_secret = pyotp.random_base32()
                session['otp_secret'] = otp_secret
                send_email_otp(create_customer_form.email.data, otp_secret)
                otp_sent = True
                msg = 'OTP sent to your email. Please enter the OTP below.'
            else:
                msg = 'Invalid email address'

        elif 'verify_otp' in request.form:
            otp_input = request.form['otp']
            otp_secret = session.get('otp_secret')
            if otp_secret:
                authenticator = pyotp.TOTP(otp_secret, interval=60)
                if authenticator.verify(otp_input):
                    session['otp_verified'] = True
                    otp_verified = True
                    # OTP is valid, update the form
                    create_customer_form.email_verified.data = True
                    msg = 'Email Verified!'
                else:
                    msg = 'Invalid OTP entered'
            else:
                msg = 'OTP secret not found in session'

        elif create_customer_form.validate() and otp_verified:
            # Only allow form submission if OTP is verified
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            password = create_customer_form.password.data
            stats = PasswordStats(password)
            checkpolicy = policy.test(password)

            if stats.strength() < 0.66:
                flash("Password not strong enough. Avoid consecutive characters and easily guessed words.")
                return render_template('createCustomer.html', form=create_customer_form)

            # Check if the username already exists
            cursor.execute('SELECT * FROM customer WHERE username = %s', (create_customer_form.username.data,))
            account = cursor.fetchone()

            if account:
                # Username already exists
                msg = 'Username already exists, please choose a different one!'
            else:
                # Username does not exist, proceed with registration
                key = Fernet.generate_key()
                f = Fernet(key)

                email = create_customer_form.email.data.encode()
                encrypted_email = f.encrypt(email)

                # Hash password securely before storing
                hashpwd = bcrypt.generate_password_hash(create_customer_form.password.data)

                session['username'] = create_customer_form.username.data
                session['password'] = hashpwd
                session['email'] = encrypted_email.decode('utf-8')
                session['encryption_key'] = key.decode('utf-8')

                cursor.execute(
                    'INSERT INTO customer (username, password, email, gender, creditcardType, mailingAddress, encryptionKey, failedAttempts, lastFailedAttempts, totalFailedAttempts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                    (create_customer_form.username.data, hashpwd, encrypted_email, create_customer_form.gender.data,
                     create_customer_form.payment.data, create_customer_form.address.data, key.decode(), 0, None, 0)
                )
                mysql.connection.commit()
                msg = 'You have successfully registered!'
                session.pop('otp_verified', None)  # Remove otp_verified from session
                return redirect(url_for('security_questions'))

        else:
            msg = 'Please fill out the form correctly!'

    return render_template('createCustomer.html', form=create_customer_form, msg=msg, otp_sent=otp_sent, otp_verified=otp_verified)

@app.route('/retrieveUsers')
def retrieve_users():
    if session.get('staff_loggedin'):  # Check if staff is logged in
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff')
        staff_list = cursor.fetchall()
        cursor.close()

        print("1")
        print(staff_list)
        print("2")

        return render_template('retrieveUsers.html', count=len(staff_list), staff_list=staff_list)
    else:
        return redirect(url_for('staff_login'))  # Redirect if not logged in


#DONE
@app.route('/retrieveCustomers')
def retrieve_customers():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('select * from editcustomer')
    customers_list = cursor.fetchall()
    cursor.close()


    print("1")
    print(customers_list)
    print("2")

    return render_template('retrieveCustomers.html', count=len(customers_list), customers_list=customers_list)


@app.route('/updateUser/<username>/', methods=['GET', 'POST'])
def update_user(username):
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

    # Fetch the current user data from the database
    cursor.execute('SELECT * FROM STAFF WHERE staff_username = %s', (username,))
    user = cursor.fetchone()
    if not user:
        return "User not found", 404

    update_user_form = CreateUserForm(request.form, obj=user)

    if request.method == 'POST' and update_user_form.validate():
        new_username = update_user_form.username.data

        # Check if the new username is already taken by another user
        cursor.execute('SELECT * FROM STAFF WHERE staff_username = %s AND staff_username != %s', (new_username, username))
        duplicate_user = cursor.fetchone()

        if duplicate_user:
            msg = "Username is already taken. Please choose a different one."
            return render_template('updateUser.html', form=update_user_form, username=username, msg=msg)

        password = update_user_form.password.data
        stats = PasswordStats(password)
        checkpolicy = policy.test(password)

        if stats.strength() < 0.66:
            msg = "Password not strong enough. Avoid consecutive characters and easily guessed words."
            return render_template('updateUser.html', form=update_user_form, username=username, msg=msg)

        hashpwd = bcrypt.generate_password_hash(update_user_form.password.data)

        cursor.execute(
            'UPDATE STAFF SET staff_username = %s, staff_password = %s, staff_position = %s WHERE staff_username = %s',
            (new_username, hashpwd, update_user_form.role.data, username)
        )
        mysql.connection.commit()
        msg = 'User updated successfully!'
        return redirect(url_for('retrieve_users'))

    return render_template('updateUser.html', form=update_user_form, username=username, msg=msg)

@app.route('/updateCustomer/<username>/', methods=['GET', 'POST'])
def update_customer(username):
    msg = ''
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM customer WHERE username = %s', (username,))
    customer = cursor.fetchone()
    if not customer:
        return "Customer not found", 404

    update_customer_form = CreateCustomerForm(request.form, obj=customer)
    if request.method == 'POST' and update_customer_form.validate():
        new_username = update_customer_form.username.data

        # Check if the new username is already taken by another customer
        cursor.execute('SELECT * FROM customer WHERE username = %s AND username != %s', (new_username, username))
        duplicate_customer = cursor.fetchone()

        if duplicate_customer:
            msg = "Username is already taken. Please choose a different one."
            return render_template('updateCustomer.html', form=update_customer_form, username=username, msg=msg)

        password = update_customer_form.password.data
        stats = PasswordStats(password)
        checkpolicy = policy.test(password)

        if stats.strength() < 0.66:
            msg = "Password not strong enough. Avoid consecutive characters and easily guessed words."
            return render_template('updateCustomer.html', form=update_customer_form, username=username, msg=msg)

        # Encrypt the email before updating
        key = customer['encryptionKey'].encode()  # Retrieve the existing encryption key
        f = Fernet(key)
        encrypted_email = f.encrypt(update_customer_form.email.data.encode())
        customer_hashpwd = bcrypt.generate_password_hash(update_customer_form.password.data)

        cursor.execute(
            'UPDATE customer SET username = %s, password=%s, email=%s, gender = %s, creditcardType = %s, mailingAddress = %s WHERE username = %s',
            (new_username, customer_hashpwd, encrypted_email.decode('utf-8'),
             update_customer_form.gender.data, update_customer_form.payment.data, update_customer_form.address.data,
             username)
        )
        mysql.connection.commit()
        msg = 'Customer updated successfully!'
        return redirect(url_for('retrieve_customers'))

    return render_template('updateCustomer.html', form=update_customer_form, username=username, msg=msg)


@app.route('/deleteUser/<username>', methods=['POST'])
def delete_user(username):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM STAFF WHERE staff_username = %s', (username,))
    mysql.connection.commit()
    flash('Product deleted successfully!', 'success')

    return redirect(url_for('retrieve_users'))





@app.route('/deleteCustomer/<username>', methods=['POST'])
def delete_customer(username):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM customer WHERE username = %s', (username,))
    mysql.connection.commit()
    flash('Product deleted successfully!', 'success')

    return redirect(url_for('retrieve_customers'))


#Magnus Finished (changing db)
@app.route('/CustomerLogin', methods=['GET', 'POST'])
def customer_login():
    msg = ''
    if request.method == 'POST':
        session.pop('customer_id', None)
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer WHERE username = %s', (username,))
        customer = cursor.fetchone()

        if customer:
            # Check if account is locked based on total failed attempts
            total_failed_attempts = customer['totalFailedAttempts']

            lock_period = timedelta(0)  # Default to no lock period

            if total_failed_attempts >= 25:
                msg = 'Account is permanently locked.'
                return render_template('CustomerLogin.html', msg=msg)
            elif total_failed_attempts >= 20:
                lock_period = timedelta(hours=1)
            elif total_failed_attempts >= 15:
                lock_period = timedelta(minutes=30)
            elif total_failed_attempts >= 10:
                lock_period = timedelta(minutes=20)
            elif total_failed_attempts >= 5:
                lock_period = timedelta(minutes=10)

            if lock_period.total_seconds() > 0:
                last_failed_attempt_time = customer['lastFailedAttempts']
                unlock_time = last_failed_attempt_time + lock_period

                if datetime.now() < unlock_time:
                    msg = f'Account is locked until {unlock_time} . Please try again later.'
                    return render_template('CustomerLogin.html', msg=msg)

            # Check password
            user_hashpwd = customer['password']
            if bcrypt.check_password_hash(user_hashpwd, password):
                # Reset failed attempts after successful login
                cursor.execute('UPDATE customer SET failedAttempts = 0, totalFailedAttempts = %s, lastFailedAttempts = NULL WHERE customerID = %s',
                               (total_failed_attempts, customer['customerID']))
                mysql.connection.commit()

                session['loggedin'] = True
                session['id'] = customer['customerID']
                session['username'] = customer['username']
                session['customer_loggedin'] = True
                session['last_activity'] = datetime.now()

                # Log successful login activity
                log_activity(customer['customerID'], 'Logged in')

                # Data decryption
                cursor.execute('SELECT email, encryptionKey FROM customer WHERE username = %s', (username,))
                account = cursor.fetchone()

                if customer:
                    encrypted_email = customer['email'].encode()
                    key = customer['encryptionKey'].encode()

                    f = Fernet(key)
                    decrypted_email = f.decrypt(encrypted_email).decode()

                    print(f"Decrypted email: {decrypted_email}")

                else:
                    print("Account not found.")

                return redirect(url_for('home'))
            else:
                # Increment for failed attempts
                new_failed_attempts = customer['failedAttempts'] + 1
                new_total_failed_attempts = total_failed_attempts + 1
                cursor.execute('UPDATE customer SET failedAttempts = %s, totalFailedAttempts = %s, lastFailedAttempts = %s WHERE customerID = %s',
                               (new_failed_attempts, new_total_failed_attempts, datetime.now(), customer['customerID']))
                mysql.connection.commit()

                if new_total_failed_attempts >= 25:
                    msg = 'Account is permanently locked.'
                    # Log account lock due to too many failed attempts
                    log_activity(customer['customerID'], 'Account permanently locked due to too many failed attempts')
                elif new_failed_attempts >= 5:
                    msg = 'Account is locked. Please try again later.'
                    # Log account lock due to temporary lockout
                    log_activity(customer['customerID'], 'Account temporarily locked due to too many failed attempts')
                else:
                    msg = 'Incorrect username/password!'

        else:
            msg = 'Incorrect username/password!'
    return render_template('CustomerLogin.html', msg=msg)


#Magnus done changing db
@app.route('/StaffLogin', methods=['GET', 'POST'])
def staff_login():
    msg = ''
    if request.method == 'POST':
        staff_username = request.form['username']
        staff_password = request.form['password']

        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM staff WHERE staff_username = %s', (staff_username,))
        # Fetch one record and return result
        staff = cursor.fetchone()

        if staff:
            # Retrieve the stored password hash
            staff_hashpwd = staff['staff_password']

            # Check if the entered password matches the stored password hash
            if bcrypt.check_password_hash(staff_hashpwd, staff_password):
                # Create session data, we can access this data in other routes
                session['loggedin'] = True
                session['id'] = staff['staffID']
                session['username'] = staff['staff_username']
                session['staff_loggedin'] = True
                session['last_activity'] = datetime.now()


                # print(session)
                # Redirect to home page
                # return redirect(url_for('manage_products'))
                return render_template('manage_products.html', session=session)
            else:
                # Password is incorrect
                msg = 'Incorrect username/password!'
        else:
            # Username doesn't exist
            msg = 'Incorrect username/password!'

    return render_template('StaffLogin.html', msg=msg)



# Magnus create Product CRUD
@app.route('/createCart', methods=['GET','POST'])
def create_cart():
    create_cart_form = CreateCartForm(request.form)
    if request.method == 'POST' and create_cart_form.validate():
        carts_dict = {}
        db = shelve.open('cart.db', 'c')
        try:
            carts_dict = db['Products']
        except:
            print("Error in retrieving Products from cart.db.")

        product = Product.Product(create_cart_form.product.data, create_cart_form.price.data, create_cart_form.quantity.data,create_cart_form.remarks.data)
        carts_dict[product.get_user_id()] = product
        db['Products'] = carts_dict
        # # Test codes
        # carts_dict = db['Products']
        # product = carts_dict[product.get_user_id()]
        # print(product.get_product(),"was stored in cart.db successfully")

        db.close()

        return redirect(url_for('retrieve_cart'))

    return render_template('createCart.html', form=create_cart_form)


@app.route('/retrieveCart')
def retrieve_cart():
    carts_dict = {}
    db = shelve.open('cart.db', 'r')
    carts_dict = db['Products']
    db.close()

    carts_list = []
    for key in carts_dict:
        cart = carts_dict.get(key)
        carts_list.append(cart)

    return render_template('retrieveCart.html', count=len(carts_list), carts_list=carts_list)


@app.route('/updateCart/<int:id>/', methods=['GET', 'POST'])
def update_cart(id):

    update_cart_form = CreateCartForm(request.form)
    if request.method == 'POST' and update_cart_form.validate():
        carts_dict = {}
        db = shelve.open('cart.db', 'w')
        carts_dict = db['Products']

        cart = carts_dict.get(id)
        cart.set_product(update_cart_form.product.data)
        cart.set_price(update_cart_form.price.data)
        cart.set_quantity(update_cart_form.quantity.data)
        cart.set_remarks(update_cart_form.remarks.data)

        db['Products'] = carts_dict
        db.close()

        return redirect(url_for('retrieve_cart'))
    else:
        carts_dict = {}
        db = shelve.open('cart.db', 'r')
        carts_dict = db['Products']
        db.close()

        cart = carts_dict.get(id)
        update_cart_form.product.data = cart.get_product()
        update_cart_form.price.data = cart.get_price()
        update_cart_form.quantity.data = cart.get_quantity()
        update_cart_form.remarks.data = cart.get_remarks()

        return render_template('updateCart.html', form=update_cart_form)


# Magnus Shopping Cart

@app.route('/Shopping')
def Shopping():
    products = database.all_products()
    return render_template('Shopping.html', products=products)

@app.route('/cart')
def shopping_cart():
    if 'customer_id' not in session:
        return redirect('/CustomerLogin')
    else:
        cart_list = []
        db = shelve.open('cart')
        cart_list = db.get((session['customer_id']), None)
        if cart_list is None:
            cart_list = []
            number_item = 0
            Grandtotal = 0
        else:
            number_item = range(len(cart_list))
            Grandtotal = 0
            for item in number_item:
                quantity = cart_list[item]["quantity"]
                total = quantity * cart_list[item]["price"]
                print(total)
                Grandtotal += total

        return render_template("cart.html", cart_list=cart_list, number_item=number_item, Grandtotal=Grandtotal)

@app.route('/add_cart/<product>/<price>', methods = ["GET", "POST"])
def AddCart(product, price):
    user = session["customer_id"]
    # print(f"Product ID = {product} price = {price} user={user}")
    user_cart = shelve.open("cart")
    cart_list = user_cart.get(session['customer_id'], [])
    if len(cart_list) == 0:
        new_id = 1
    else:
        new_id = int(cart_list[-1]['id']) +1

    cart_item = {"id": new_id, "product": product, "quantity": 1, "price": int(price)}
    cart_list.append(cart_item)
    user_cart[session['customer_id']] = cart_list

    return redirect('/cart')


@app.route('/update_item/<index>', methods=["POST"])
def update_item(index):
    quantity = int(request.form.get('quantity'))
    user = session["customer_id"]
    user_cart = shelve.open("cart")
    number_item = user_cart[user]
    for item in range(len(number_item)):
        id = number_item[item]["id"]
        if id == int(index):
            number_item[item]["quantity"] = quantity
            break

    user_cart[user] = number_item
    user_cart.sync()
    user_cart.close()
    return redirect('/cart')

@app.route('/delete_item/<index>', methods=["GET", "POST"])
def delete_item(index):
    user = session["customer_id"]
    user_cart = shelve.open("cart")
    number_item = user_cart[user]
    for item in range(len(number_item)):
        id = number_item[item]["id"]
        if id == int(index):
            del number_item[item]
            break

    user_cart[user] = number_item
    user_cart.sync()
    user_cart.close()
    return redirect('/cart')

# Joseph


@app.route('/checkout', methods=["GET", "POST"])
def checkout():
    cart_list = []
    db = shelve.open('cart')
    cart_list = db[session['customer_id']]
    number_item = range(len(cart_list))
    Grandtotal = 0
    for item in number_item:
        quantity = cart_list[item]["quantity"]
        total = quantity * cart_list[item]["price"]
        print(total)
        Grandtotal += total

    customers_dict = {}
    db = shelve.open('customer.db', 'r')
    customers_dict = db['Customers']
    db.close()

    customers_list = []
    for key in customers_dict:
        customer = customers_dict.get(key)
        customers_list.append(customer)

    return render_template("checkout.html", Grandtotal=Grandtotal, cart_list=cart_list, number_item=number_item,
                           count=len(customers_list), customers_list=customers_list)


@app.route('/receipt')
def receipt():
    return render_template('receipt.html')


@app.route('/createFeedback', methods=['GET', 'POST'])
def create_feedback():
    create_feedback_form = CreateFeedbackForm(request.form)
    if request.method == 'POST' and create_feedback_form.validate():
        feedbacks_dict = {}
        db = shelve.open('feedback.db', 'c')

        try:
            feedbacks_dict = db['Feedbacks']
        except:
            print("Error in retrieving Feedbacks from feedback.db.")

        feedback = Feedback.Feedback(create_feedback_form.first_name.data, create_feedback_form.last_name.data,
                                     create_feedback_form.email.data, create_feedback_form.topic.data, create_feedback_form.date_joined.data,
                                     create_feedback_form.rating.data, create_feedback_form.message.data)

        Feedback.count_id = len('feedback.db')
        feedbacks_dict[feedback.get_feedback_id()] = feedback
        db['Feedbacks'] = feedbacks_dict

        db.close()

        return redirect(url_for('retrieve_feedbacks'))
    return render_template('createFeedback.html', form=create_feedback_form)

@app.route('/retrieveFeedbacks')
def retrieve_feedbacks():
    feedbacks_dict = {}
    db = shelve.open('feedback.db', 'r')
    feedbacks_dict = db['Feedbacks']
    db.close()

    feedbacks_list = []
    for key in feedbacks_dict:
        feedback = feedbacks_dict.get(key)
        feedbacks_list.append(feedback)

    return render_template('retrieveFeedbacks.html', count=len(feedbacks_list), feedbacks_list=feedbacks_list)


@app.route('/updateFeedback/<int:id>/', methods=['GET', 'POST'])
def update_feedback(id):
    update_feedback_form = CreateFeedbackForm(request.form)
    if request.method == 'POST':
        feedbacks_dict = {}
        db = shelve.open('feedback.db', 'w')
        feedbacks_dict = db['Feedbacks']

        feedback = feedbacks_dict.get(id)
        feedback.set_first_name(update_feedback_form.first_name.data)
        feedback.set_last_name(update_feedback_form.last_name.data)
        feedback.set_email(update_feedback_form.email.data)
        feedback.set_topic(update_feedback_form.topic.data)
        feedback.set_date_joined(update_feedback_form.date_joined.data)
        feedback.set_rating(update_feedback_form.rating.data)
        feedback.set_message(update_feedback_form.message.data)

        db['Feedbacks'] = feedbacks_dict
        db.close()

        return redirect(url_for('retrieve_feedbacks'))
    else:
        feedbacks_dict = {}
        db = shelve.open('feedback.db', 'r')
        feedbacks_dict = db['Feedbacks']
        db.close()

        feedback = feedbacks_dict.get(id)
        update_feedback_form.first_name.data = feedback.get_first_name()
        update_feedback_form.last_name.data = feedback.get_last_name()
        update_feedback_form.email.data = feedback.get_email()
        update_feedback_form.topic.data = feedback.get_topic()
        update_feedback_form.date_joined.data = feedback.get_date_joined()
        update_feedback_form.rating.data = feedback.get_rating()
        update_feedback_form.message.data = feedback.get_message()

        return render_template('updateFeedback.html', form=update_feedback_form)

@app.route('/deleteFeedback/<int:id>', methods=['POST'])
def delete_feedback(id):
    feedbacks_dict = {}
    db = shelve.open('feedback.db', 'w')
    feedbacks_dict = db['Feedbacks']
    feedbacks_dict.pop(id)

    db['Feedbacks'] = feedbacks_dict
    db.close()

    return redirect(url_for('retrieve_feedbacks'))


# Xavier done changing db

@app.route('/add-product', methods=['GET', 'POST'])
def add_product():
    form = ProductForm()
    if form.validate_on_submit():
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'INSERT INTO products (productID, productName, productCategory, productUnitPrice, productStock, imageURL) VALUES (%s, %s, %s, %s, %s, %s)',
            (form.product_id.data, form.name.data, form.category.data, form.price.data, form.stock.data, form.image_url.data)
        )
        mysql.connection.commit()
        flash('Product added successfully!', 'success')
        return redirect(url_for('manage_products'))
    return render_template('add_product.html', form=form)


@app.route('/update-product/<int:product_id>', methods=['GET', 'POST'])
def update_product(product_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products WHERE productID = %s', (product_id,))
    product = cursor.fetchone()
    if not product:
        return "Product not found", 404

    form = ProductForm(request.form, obj=product)
    if request.method == 'POST' and form.validate():
        cursor.execute(
            'UPDATE products SET productName = %s, productCategory = %s, productUnitPrice = %s, productStock = %s, imageURL = %s WHERE productID = %s',
            (form.name.data, form.category.data, form.price.data, form.stock.data, form.image_url.data, product_id)
        )
        mysql.connection.commit()
        flash('Product updated successfully!', 'success')
        return redirect(url_for('manage_products'))
    return render_template('update_product.html', form=form, product_id=product_id)


@app.route('/delete-product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('DELETE FROM products WHERE productID = %s', (product_id,))
    mysql.connection.commit()
    flash('Product deleted successfully!', 'success')
    return redirect(url_for('manage_products'))


@app.route('/manage-products')
def manage_products():
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('SELECT * FROM products')
    products = cursor.fetchall()
    return render_template('manage_products.html', products=products)


@app.route('/security_questions', methods=['GET', 'POST'])
def security_questions():
    questions = random.sample(SECURITY_QUESTIONS, 3)
    return render_template('security_questions.html', questions=questions)


@app.route('/save_security_questions', methods=['POST'])
def save_security_questions():
    if 'username' in session and 'password' in session and 'email' in session and 'encryption_key' in session:
        username = session['username']
        password = session['password']
        email = session['email']
        encryption_key = session['encryption_key']

        # Initialize the Fernet instance with the encryption key
        f = Fernet(encryption_key.encode('utf-8'))

        security_question1 = request.form['question1']
        security_answer1 = f.encrypt(request.form['answer1'].encode()).decode('utf-8')
        security_question2 = request.form['question2']
        security_answer2 = f.encrypt(request.form['answer2'].encode()).decode('utf-8')
        security_question3 = request.form['question3']
        security_answer3 = f.encrypt(request.form['answer3'].encode()).decode('utf-8')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)

        # Check if the username already exists
        cursor.execute('SELECT * FROM customer WHERE username = %s', (username,))
        existing_user = cursor.fetchone()

        if existing_user:
            # Update existing user
            cursor.execute(
                'UPDATE customer SET password = %s, email = %s, encryptionKey = %s, security_question1 = %s, security_answer1 = %s, security_question2 = %s, security_answer2 = %s, security_question3 = %s, security_answer3 = %s WHERE username = %s',
                (password, email, encryption_key, security_question1, security_answer1, security_question2, security_answer2, security_question3, security_answer3, username)
            )
        else:
            # Insert new user
            cursor.execute(
                'INSERT INTO customer (username, password, email, encryptionKey, security_question1, security_answer1, security_question2, security_answer2, security_question3, security_answer3, mailingAddress, creditcardType, failedAttempts, lastFailedAttempts, totalFailedAttempts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)',
                (username, password, email, encryption_key, security_question1, security_answer1, security_question2,
                 security_answer2, security_question3, security_answer3, 'Not Provided', 'None', 0, None, 0)
            )

        mysql.connection.commit()

        session.pop('username', None)
        session.pop('password', None)
        session.pop('email', None)
        session.pop('encryption_key', None)

        return redirect(url_for('customer_login'))
    return redirect(url_for('create_customer'))


@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    msg = ''
    if request.method == 'POST' and 'username' in request.form:
        username = request.form['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            session['username'] = username
            questions = [
                account['security_question1'],
                account['security_question2'],
                account['security_question3']
            ]
            return render_template('security_questions_reset.html', questions=questions)
        else:
            msg = 'Account not found!'
    return render_template('forgot_password.html', msg=msg)


@app.route('/reset_password', methods=['POST'])
def reset_password():
    if 'username' in session:
        username = session['username']
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM customer WHERE username = %s', (username,))
        account = cursor.fetchone()
        if account:
            f = Fernet(account['encryptionKey'].encode('utf-8'))
            answers = [
                f.decrypt(account['security_answer1'].encode()).decode('utf-8'),
                f.decrypt(account['security_answer2'].encode()).decode('utf-8'),
                f.decrypt(account['security_answer3'].encode()).decode('utf-8')
            ]
            if (request.form['answer1'] == answers[0] and
                request.form['answer2'] == answers[1] and
                request.form['answer3'] == answers[2]):
                log_activity(account['customerID'], 'Reset password')
                return render_template('reset_password.html')
            else:
                msg = 'Security answers do not match!'
                return render_template('security_questions_reset.html', questions=[
                    account['security_question1'],
                    account['security_question2'],
                    account['security_question3']
                ], msg=msg)
    return redirect(url_for('forgot_password'))


@app.route('/save_new_password', methods=['POST'])
def save_new_password():
    if 'username' in session:
        username = session['username']
        new_password = request.form['new_password']
        hashpwd = bcrypt.generate_password_hash(new_password).decode('utf-8')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('UPDATE customer SET password = %s WHERE username = %s', (hashpwd, username,))
        mysql.connection.commit()
        session.pop('username', None)
        return redirect(url_for('customer_login'))
    return redirect(url_for('forgot_password'))


@app.route('/settings', defaults={'option': None})
@app.route('/settings/<option>')
def settings(option):
    if 'loggedin' in session:
        logs = []
        if option == 'account_activity':
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute(
                'SELECT * FROM account_activity_log WHERE user_id = %s',
                (session['id'],)
            )
            logs = cursor.fetchall()
        return render_template('settings.html', option=option, logs=logs)
    return redirect(url_for('customer_login'))


def log_activity(user_id, activity):
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('INSERT INTO account_activity_log (user_id, activity) VALUES (%s, %s)', (user_id, activity))
    mysql.connection.commit()


@app.route('/activity')
def activity():
    if 'loggedin' in session:
        # Fetch activity logs from the database
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM account_activity_log WHERE user_id = %s ORDER BY timestamp DESC', (session['id'],))
        logs = cursor.fetchall()

        # Render the activity template with the logs
        return render_template('activity.html', logs=logs)
    return redirect(url_for('customer_login'))


if __name__ == '__main__':
    app.run(debug=True)

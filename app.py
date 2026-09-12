from flask import Flask, render_template, request, redirect, session, flash

from flask_mysqldb import MySQL

import MySQLdb.cursors

import hashlib


app = Flask(__name__)

app.secret_key = 'your_secret_key'


# ------------------ MYSQL CONFIGURATION ------------------

app.config['MYSQL_HOST'] = 'sql12.freesqldatabase.com'
app.config['MYSQL_USER'] = 'sql12836988'
app.config['MYSQL_PASSWORD'] = 'PNMiPh95a7'
app.config['MYSQL_DB'] = 'sql12836988'

mysql = MySQL(app)


# ------------------ REGISTER ------------------

@app.route('/register', methods=['GET', 'POST'])
def register():

    if request.method == 'POST':

        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        hashed_password = hashlib.sha256(
            password.encode()
        ).hexdigest()

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        cursor.execute(
            "SELECT * FROM users WHERE email=%s",
            (email,)
        )

        account = cursor.fetchone()

        if account:

            flash("Email already exists!")

        else:

            cursor.execute(
                """
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
                """,
                (username, email, hashed_password)
            )

            mysql.connection.commit()

            flash("Registration successful! Please login.")

            return redirect('/login')

    return render_template('register.html')


# ------------------ LOGIN ------------------

@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form['email']
        password = request.form['password']

        hashed_password = hashlib.sha256(
            password.encode()
        ).hexdigest()

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        cursor.execute(
            """
            SELECT * FROM users
            WHERE email=%s AND password=%s
            """,
            (email, hashed_password)
        )

        account = cursor.fetchone()

        if account:

            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']

            return redirect('/dashboard')

        else:

            flash("Invalid email or password!")

    return render_template('login.html')


# ------------------ DASHBOARD ------------------

@app.route('/dashboard')
def dashboard():

    if 'loggedin' in session:

        return render_template(
            'dashboard.html',
            username=session['username']
        )

    return redirect('/login')


# ------------------ LOGOUT ------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect('/login')


# ------------------ STOCKS ------------------

@app.route('/stocks')
def stocks():

    if 'loggedin' in session:

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        cursor.execute(
            "SELECT * FROM stocks ORDER BY id DESC"
        )

        stocks = cursor.fetchall()

        return render_template(
            'stocks.html',
            stocks=stocks
        )

    return redirect('/login')

@app.route('/calculator')
def calculator():
    username = session.get('username')
    return render_template('computation.html', username=username)


# ------------------ HISTORY ------------------

@app.route('/history')
def history():
    if 'loggedin' in session:

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        cursor.execute(
            """
            SELECT
                transactions.id,
                transactions.customer_name,
                transactions.service,

                stocks.item_name AS item_name,
                stocks2.item_name AS item_name_2,
                stocks3.item_name AS item_name_3,
                stocks4.item_name AS item_name_4,
                stocks5.item_name AS item_name_5,

                transactions.quantity_used,
                transactions.total_amount,
                transactions.created_at,
                transactions.quantity_used_2,
                transactions.quantity_used_3,
                transactions.quantity_used_4,
                transactions.quantity_used_5

            FROM transactions

            INNER JOIN stocks
                ON transactions.stock_id = stocks.id

            LEFT JOIN stocks AS stocks2
                ON transactions.stock_id_2 = stocks.id

            LEFT JOIN stocks AS stocks3
                ON transactions.stock_id_3 = stocks.id

            LEFT JOIN stocks AS stocks4
                ON transactions.stock_id_4 = stocks.id

            LEFT JOIN stocks AS stocks5
                ON transactions.stock_id_5 = stocks.id

            ORDER BY transactions.created_at DESC
            """
        )

        transactions = cursor.fetchall()

        return render_template(
            'history.html',
            transactions=transactions
        )

    return redirect('/login')


# ------------------ ADD CUSTOMER ------------------

@app.route('/add_customer', methods=['GET', 'POST'])
def add_customer():

    # ------------------ SHOW FORM ------------------

    if request.method == 'GET':

        if 'loggedin' in session:

            cursor = mysql.connection.cursor(
                MySQLdb.cursors.DictCursor
            )

            cursor.execute(
                """
                SELECT
                    id,
                    item_name,
                    remaining_quantity,
                    selling_price
                FROM stocks
                ORDER BY item_name
                """
            )

            stocks = cursor.fetchall()

            return render_template(
                'add_customer.html',
                stocks=stocks
            )

        return redirect('/login')


    # ------------------ CHECK LOGIN ------------------

    if 'loggedin' not in session:
        return redirect('/login')


    # ------------------ GET CUSTOMER DATA ------------------

    customer_name = request.form.get('customer_name', '').strip()
    service = request.form.get('service', '').strip()

    try:
        total_amount = float(request.form.get('total_amount', 0))
    except ValueError:
        flash("Invalid total amount.")
        return redirect('/add_customer')


    if not customer_name:
        flash("Customer name is required.")
        return redirect('/add_customer')


    if not service:
        flash("Please select a service.")
        return redirect('/add_customer')


    # ==========================================================
    # GET MATERIALS 1-5
    # ==========================================================

    materials = []

    for i in range(1, 6):

        stock_id = request.form.get(f'stock_id_{i}')
        quantity = request.form.get(f'quantity_used_{i}')


        # Material is empty
        if not stock_id:

            # If quantity was entered without selecting stock
            if quantity:
                flash(
                    f"Please select a material for Material #{i}."
                )
                return redirect('/add_customer')

            # Empty rows #2-#5 are allowed
            continue


        # Stock selected but quantity is empty
        if not quantity:

            flash(
                f"Please enter the quantity for Material #{i}."
            )
            return redirect('/add_customer')


        try:
            stock_id = int(stock_id)
            quantity = int(quantity)

        except ValueError:

            flash(
                f"Invalid material or quantity for Material #{i}."
            )
            return redirect('/add_customer')


        if quantity <= 0:

            flash(
                f"Quantity for Material #{i} "
                f"must be greater than 0."
            )
            return redirect('/add_customer')


        materials.append({
            'stock_id': stock_id,
            'quantity': quantity
        })


    # ==========================================================
    # MATERIAL #1 IS REQUIRED
    # ==========================================================

    if not request.form.get('stock_id_1'):

        flash("Material #1 is required.")

        return redirect('/add_customer')


    # ==========================================================
    # OPEN DATABASE CURSOR
    # ==========================================================

    cursor = mysql.connection.cursor(
        MySQLdb.cursors.DictCursor
    )


    # ==========================================================
    # CHECK ALL STOCK FIRST
    # ==========================================================

    for material in materials:

        cursor.execute(
            """
            SELECT
                id,
                item_name,
                remaining_quantity
            FROM stocks
            WHERE id=%s
            """,
            (material['stock_id'],)
        )

        stock = cursor.fetchone()


        # Stock doesn't exist
        if not stock:

            flash(
                "Selected stock item was not found."
            )

            return redirect('/add_customer')


        # Not enough stock
        if stock['remaining_quantity'] < material['quantity']:

            flash(
                f"Not enough {stock['item_name']}! "
                f"Available: {stock['remaining_quantity']}, "
                f"Requested: {material['quantity']}."
            )

            return redirect('/add_customer')


    # ==========================================================
    # DEDUCT THE EXACT STOCK SELECTED
    # ==========================================================

    for material in materials:

        cursor.execute(
            """
            UPDATE stocks
            SET remaining_quantity =
                remaining_quantity - %s
            WHERE id=%s
            """,
            (
                material['quantity'],
                material['stock_id']
            )
        )


    # ==========================================================
    # PREPARE MATERIAL DATA FOR TRANSACTION
    # ==========================================================

    stock_ids = [None, None, None, None, None]
    quantities = [None, None, None, None, None]


    for index, material in enumerate(materials):

        stock_ids[index] = material['stock_id']
        quantities[index] = material['quantity']


    # ==========================================================
    # SAVE TRANSACTION
    # ==========================================================

    cursor.execute(
        """
        INSERT INTO transactions
        (
            customer_name,
            service,

            stock_id,
            quantity_used,

            stock_id_2,
            quantity_used_2,

            stock_id_3,
            quantity_used_3,

            stock_id_4,
            quantity_used_4,

            stock_id_5,
            quantity_used_5,

            total_amount
        )

        VALUES
        (
            %s, %s,

            %s, %s,

            %s, %s,

            %s, %s,

            %s, %s,

            %s, %s,

            %s
        )
        """,

        (
            customer_name,
            service,

            stock_ids[0],
            quantities[0],

            stock_ids[1],
            quantities[1],

            stock_ids[2],
            quantities[2],

            stock_ids[3],
            quantities[3],

            stock_ids[4],
            quantities[4],

            total_amount
        )
    )


    # ==========================================================
    # SAVE EVERYTHING
    # ==========================================================

    mysql.connection.commit()


    flash(
        "Customer transaction recorded successfully!"
    )

    return redirect('/history')


# ------------------ ADD STOCK ------------------

@app.route('/stocks/add', methods=['POST'])
def add_stock():

    if 'loggedin' in session:

        item_name = request.form['item_name']

        bought_quantity = request.form[
            'bought_quantity'
        ]

        cost_price = request.form['cost_price']

        selling_price = request.form[
            'selling_price'
        ]


        cursor = mysql.connection.cursor()


        cursor.execute(
            """
            INSERT INTO stocks
            (
                item_name,
                bought_quantity,
                remaining_quantity,
                cost_price,
                selling_price
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (
                item_name,
                bought_quantity,
                bought_quantity,
                cost_price,
                selling_price
            )
        )


        mysql.connection.commit()


        return redirect('/stocks')

    return redirect('/login')


# ------------------ EDIT STOCK ------------------

@app.route('/stocks/edit/<int:id>', methods=['POST'])
def edit_stock(id):

    if 'loggedin' in session:

        item_name = request.form['item_name']

        bought_quantity = request.form[
            'bought_quantity'
        ]

        cost_price = request.form['cost_price']

        selling_price = request.form[
            'selling_price'
        ]


        cursor = mysql.connection.cursor()


        cursor.execute(
            """
            UPDATE stocks
            SET
                item_name=%s,
                bought_quantity=%s,
                cost_price=%s,
                selling_price=%s
            WHERE id=%s
            """,
            (
                item_name,
                bought_quantity,
                cost_price,
                selling_price,
                id
            )
        )


        mysql.connection.commit()


        return redirect('/stocks')

    return redirect('/login')


# ------------------ DELETE STOCK ------------------

# ------------------ DELETE STOCK ------------------

@app.route('/stocks/delete/<int:id>')
def delete_stock(id):

    if 'loggedin' in session:

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        # Check if this stock is used in transaction history
        cursor.execute(
            """
            SELECT COUNT(*) AS total
            FROM transactions
            WHERE stock_id=%s
            """,
            (id,)
        )

        result = cursor.fetchone()

        # If stock has transaction history, don't delete it
        if result['total'] > 0:

            flash(
                "This stock cannot be deleted because it has transaction history."
            )

            return redirect('/stocks')

        # Delete stock if it has no transaction history
        cursor.execute(
            """
            DELETE FROM stocks
            WHERE id=%s
            """,
            (id,)
        )

        mysql.connection.commit()

        flash("Stock deleted successfully!")

        return redirect('/stocks')

    return redirect('/login')

# ------------------ INCOME & EXPENSES ------------------
@app.route('/income-expenses', methods=['GET', 'POST'])
def income_expenses():
    if 'loggedin' in session:

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        # ADD EXPENSE
        if request.method == 'POST':

            expense_name = request.form['expense_name']
            amount = request.form['amount']
            date = request.form['date']

            cursor.execute(
                """
                INSERT INTO expenses
                (expense_name, amount, date)
                VALUES (%s, %s, %s)
                """,
                (expense_name, amount, date)
            )

            mysql.connection.commit()

            return redirect('/income-expenses')

        # GET EXPENSES
        cursor.execute(
            """
            SELECT
                id,
                expense_name,
                amount,
                date
            FROM expenses
            ORDER BY date DESC, id DESC
            """
        )

        expenses = cursor.fetchall()

        # TOTAL EXPENSES
        cursor.execute(
            """
            SELECT COALESCE(SUM(amount), 0) AS total
            FROM expenses
            """
        )

        total_expenses = cursor.fetchone()['total']

        # INCOME FROM TRANSACTIONS
        cursor.execute(
            """
            SELECT
                created_at AS date,
                CONCAT(customer_name, ' - ', service) AS description,
                total_amount AS amount
            FROM transactions
            ORDER BY created_at DESC
            """
        )

        incomes = cursor.fetchall()

        # TOTAL INCOME
        cursor.execute(
            """
            SELECT COALESCE(SUM(total_amount), 0) AS total
            FROM transactions
            """
        )

        total_income = cursor.fetchone()['total']

        # NET INCOME
        net_income = total_income - total_expenses

        return render_template(
            'income_expenses.html',
            username=session['username'],
            expenses=expenses,
            incomes=incomes,
            total_income=total_income,
            total_expenses=total_expenses,
            net_income=net_income
        )

    return redirect('/login')

@app.route('/expenses/edit/<int:id>', methods=['GET', 'POST'])
def edit_expense(id):
    if 'loggedin' in session:

        cursor = mysql.connection.cursor(
            MySQLdb.cursors.DictCursor
        )

        if request.method == 'POST':

            expense_name = request.form['expense_name']
            amount = request.form['amount']
            date = request.form['date']

            cursor.execute(
                """
                UPDATE expenses
                SET expense_name = %s,
                    amount = %s,
                    date = %s
                WHERE id = %s
                """,
                (expense_name, amount, date, id)
            )

            mysql.connection.commit()

            return redirect('/income-expenses')

        cursor.execute(
            """
            SELECT *
            FROM expenses
            WHERE id = %s
            """,
            (id,)
        )

        expense = cursor.fetchone()

        return render_template(
            'edit_expense.html',
            expense=expense,
            username=session['username']
        )

    return redirect('/login')

@app.route('/expenses/delete/<int:id>', methods=['POST'])
def delete_expense(id):
    if 'loggedin' in session:

        cursor = mysql.connection.cursor()

        cursor.execute(
            """
            DELETE FROM expenses
            WHERE id = %s
            """,
            (id,)
        )

        mysql.connection.commit()

        return redirect('/income-expenses')

    return redirect('/login')


# ------------------ RUN APPLICATION ------------------

if __name__ == '__main__':

    app.run(debug=True)
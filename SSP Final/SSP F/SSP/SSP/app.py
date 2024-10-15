from flask import Flask, render_template, request, redirect, url_for
import shelve

app = Flask(__name__)

# Set the secret key for session management
app.secret_key = 'your_secret_key'


def get_products():
    with shelve.open('products', writeback=True) as shelf:
        return dict(shelf)


def save_product(product):
    with shelve.open('products', writeback=True) as shelf:
        shelf[product['product_id']] = product


def get_product_list():
    with shelve.open('product_list', writeback=True) as shelf:
        return dict(shelf)


def save_product_list(updated_list):
    with shelve.open('product_list', writeback=True) as shelf:
        shelf.update(updated_list)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/productInformation', methods=['GET', 'POST'])
def product_information():
    error = None

    if request.method == 'POST':
        product_id = request.form['product_id']
        unit_price = request.form['unit_price']
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        image_url = request.form['image_url']

        # Validate that the product ID has exactly 5 digits
        if not (product_id.isdigit() and len(product_id) == 5):
            error = "Product ID must be a valid 5-digit number"
        # Validate that the unit price is a positive float
        elif not (unit_price.replace('.', '', 1).isdigit() and float(unit_price) >= 0):
            error = "Unit price must be a valid positive number"
        # Validate that category is one of the allowed options in capital letters
        elif category not in ['SHIRTS', 'T-SHIRTS', 'BOTTOMS']:
            error = "Invalid category"
        else:
            # Save product_id, unit_price, name, description, category, and image_url in capital letters
            product = {
                'product_id': product_id,
                'unit_price': float(unit_price),
                'name': name,
                'description': description,
                'category': category.upper(),
                'image_url': image_url
            }
            save_product(product)

            # Update product list with initial quantity of 0 for the newly created product
            product_list_data = get_product_list()
            product_list_data[product_id] = 0
            save_product_list(product_list_data)

            return redirect(url_for('product_information'))

    products = get_products()
    return render_template('product_information.html', products=products, error=error)


@app.route('/delete_product/<product_id>', methods=['POST'])
def delete_product(product_id):
    with shelve.open('products', writeback=True) as shelf_products, \
            shelve.open('product_list', writeback=True) as shelf_product_list:

        str_product_id = str(product_id)
        if str_product_id in shelf_products:
            # Delete the product from the products database
            del shelf_products[str_product_id]
            shelf_products.sync()

            # Delete the corresponding entry from the product_list
            if str_product_id in shelf_product_list:
                del shelf_product_list[str_product_id]
                shelf_product_list.sync()

    # Redirect to the product_information route after deletion
    return redirect(url_for('product_information'))




@app.route('/productList')
def product_list():
    updated_product_list_data = get_product_list()
    return render_template('product_list.html', product_list=updated_product_list_data)


@app.route('/update_quantity/<product_id>', methods=['POST'])
def update_quantity(product_id):
    if request.method == 'POST':
        new_quantity = int(request.form['quantity'])
        product_list = get_product_list()
        product_list[product_id] = new_quantity
        save_product_list(product_list)

        # Update the quantity in the database
        products = get_products()
        if product_id in products:
            products[product_id]['qty'] = new_quantity
            save_product(products[product_id])

    return redirect(url_for('product_list'))


if __name__ == '__main__':
    app.run(debug=True)

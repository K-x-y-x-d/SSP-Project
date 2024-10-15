import shelve


def with_shelve(func):
    """ Decorator to open and close the shelve database. """
    def wrapper(*args, **kwargs):
        with shelve.open('birodb') as db:
            return func(db, *args, **kwargs)
    return wrapper


@with_shelve
def get_product(db, product_id):
    return db.get(product_id)


@with_shelve
def save_product(db, product):
    existing_product = db.get(product.get_product_id(), None)
    if existing_product:
        existing_product.set_name(product.get_name())
        existing_product.set_category(product.get_category())
        existing_product.set_price(product.get_price())
        existing_product.set_stock(product.get_stock())
        existing_product.set_image_url(product.get_image_url())
        db[product.get_product_id()] = existing_product
    else:
        db[product.get_product_id()] = product


@with_shelve
def delete_product(db, product_id):
    if product_id in db:
        del db[product_id]


@with_shelve
def all_products(db):
    return list(db.values())

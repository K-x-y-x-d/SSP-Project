class Product:
    def __init__(self, product_id, name, category, price, stock, image_url=None):
        self._product_id = product_id
        self._name = name
        self._category = category
        self._price = price
        self._stock = stock
        self._image_url = image_url

    def get_product_id(self):
        return self._product_id

    def get_name(self):
        return self._name

    def get_category(self):
        return self._category

    def get_price(self):
        return self._price

    def get_stock(self):
        return self._stock

    def get_image_url(self):
        return self._image_url

    def set_product_id(self, product_id):
        self._product_id = product_id

    def set_name(self, name):
        self._name = name

    def set_category(self, category):
        self._category = category

    def set_price(self, price):
        if price < 0:
            raise ValueError("Price cannot be negative.")
        self._price = price

    def set_stock(self, stock):
        if stock < 0:
            raise ValueError("Stock cannot be negative.")
        self._stock = stock

    def set_image_url(self, image_url):
        self._image_url = image_url

class Cart:
    counts_id = 0

    def __init__(self, product, price, quantity):
        Cart.counts_id += 1
        self.__cart_id = Cart.counts_id
        self.__product = product
        self.__price = price
        self.__quantity = quantity

    def get_product(self):
        return self.__product

    def get_price(self):
        return self.__price

    def get_cart_id(self):
        return self.__cart_id

    def get_quantity(self):
        return self.__quantity

    def set_product(self, product):
        self.__product = product

    def set_price(self, price):
        self.__price = price

    def set_cart_id(self, cart_id):
        self.__cart_id = cart_id

    def set_quantity(self, quantity):
        self.__quantity = quantity

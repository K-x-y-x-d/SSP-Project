from Product import *

class Price(Product):


    def __init__(self,product, price, quantity, remarks, final_price):
        super().__init__(product, price, quantity, remarks)
        self.__final_price = final_price

    def set_final_price(self, final_price):
        self.__final_price = final_price

    def get_final_price(self):
        return Product.get_price() * Product.get_quantity()
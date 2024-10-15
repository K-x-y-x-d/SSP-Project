class Customer:
    count_id = 0

    def __init__(self, username, gender, email, address, payment, password):
        Customer.count_id += 1
        self.__customer_id = username
        self.__username = username
        self.__gender = gender
        self.__email = email
        self.__address = address
        self.__password = password
        self.__payment = payment

    # accessor methods
    def get_customer_id(self):
        return self.__customer_id

    def get_username(self):
        return self.__username

    def get_gender(self):
        return self.__gender

    def get_email(self):
        return self.__email

    def get_address(self):
        return self.__address

    def get_payment(self):
        return self.__payment

    def get_password(self):
        return self.__password

    # mutator methods
    def set_customer_id(self, customer_id):
        self.__customer_id = customer_id

    def set_username(self, username):
        self.__username = username

    def set_gender(self, gender):
        self.__gender = gender

    def set_email(self, email):
        self.__email = email

    def set_address(self, address):
        self.__address = address

    def set_payment(self, payment):
        self.__payment = payment

    def set_password(self, password):
        self.__password = password







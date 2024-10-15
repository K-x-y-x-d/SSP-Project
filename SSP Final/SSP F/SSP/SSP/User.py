# User class
class User:
    count_id = 0

    # initializer method
    def __init__(self, username, password,role):
        User.count_id += 1
        self.__user_id = username
        self.__username = username
        self.__password = password
        self.__role = role

    # accessor methods
    def get_user_id(self):
        return self.__user_id

    def get_username(self):
        return self.__username

    def get_password(self):
        return self.__password

    def get_role(self):
        return self.__role

    # mutator methods
    def set_user_id(self, user_id):
        self.__user_id = user_id

    def set_username(self, username):
        self.__username = username

    def set_password(self, password):
        self.__password = password

    def set_role(self, role):
        self.__role = role


def get(user_id):
    return None
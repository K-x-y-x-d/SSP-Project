class Feedback:
    count_id = 0

    def __init__(self, first_name, last_name, email, topic, date_joined, rating, message):
        Feedback.count_id += 1
        self.__feedback_id = Feedback.count_id
        self.__first_name = first_name
        self.__last_name = last_name
        self.__email = email
        self.__topic = topic
        self.__message = message
        self.__date_joined = date_joined
        self.__rating = rating
    def get_feedback_id(self):
        return self.__feedback_id

    def get_first_name(self):
        return self.__first_name

    def get_last_name(self):
        return self.__last_name

    def get_email(self):
        return self.__email

    def get_topic(self):
        return self.__topic

    def get_date_joined(self):
        return self.__date_joined

    def get_rating(self):
        return self.__rating

    def get_message(self):
        return self.__message

    def set_first_name(self, first_name):
        self.__first_name = first_name

    def set_last_name(self, last_name):
        self.__last_name = last_name

    def set_email(self, email):
        self.__email = email

    def set_topic(self, topic):
        self.__topic = topic

    def set_date_joined(self, date_joined):
        self.__date_joined = date_joined

    def set_rating(self, rating):
        self.__rating = rating

    def set_message(self, message):
        self.__message = message


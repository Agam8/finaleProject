__author__ = 'Agam'


class Token():
    def __init__(self, token, start_time):
        self.token = token
        self.start_time = start_time


    def __str__(self):
        return self.token+"~"+str(self.start_time)



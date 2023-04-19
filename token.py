<<<<<<< HEAD
__author__ = 'Agam'
=======
__author__ = 'Yossi'
>>>>>>> c696e1b5c6c515672ff90086675f60aa347617fc

class Token():
    def __init__(self, token, start_time):
        self.token = token
        self.start_time = start_time


    def __str__(self):
        return self.token+"~"+str(self.start_time)+"~"+str(self.client_ip)



__author__ = 'Yossi'

class Shared_file():
    def __init__(self, name, size, ip):
        self.name = name
        self.ip = ip
        self.size = size
        self.checksum = None
        self.token = {}
    def __str__(self):
        print(" at str ")
        print(self.name + "~" + self.ip + "~" + str(self.size))
        return self.name+"~"+self.ip+"~"+str(self.size)
    def set_token(self,token):
        self.token = token
    def delete_token(self):
        self.token = {}


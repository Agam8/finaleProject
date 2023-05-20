class User(object):
    def __init__(self, id, username, password, current_ip, is_logged):
        self.id = id
        self.username = username
        self.password = password
        self.current_ip = current_ip
        self.is_logged = is_logged

    def __str__(self):
        return f'{self.username}~***~{self.current_ip}~{self.is_logged}'

class Song(object):
    def __init__(self, md5, file_name, song_name, artist, genre, committed_user, ip='', size=''):
        self.md5 = md5
        self.file_name = file_name
        self.song_name = song_name
        self.artist = artist
        self.genre = genre
        self.ip = ip
        self.size = size
        self.committed_user = committed_user


    def __str__(self):
        return f'\n\tmd5: {self.md5}' \
               f'\n\tfile name: {self.file_name}' \
               f'\n\tsong name: {self.song_name}' \
               f'\n\tartist: {self.artist}' \
               f'\n\tgenre: {self.genre}' \
               f'\n\tcommitted user: {self.committed_user}' \
               f'\n\tip: {self.ip}' \
               f'\n\tsize: {self.size}'

class Token():
    def __init__(self, token, start_time):
        self.token = token
        self.start_time = start_time
        self.ack=False
    def is_ack(self):
        return self.ack
    def set_ack(self):
        self.ack=True

    def __str__(self):
        return self.token+"~"+str(self.start_time)
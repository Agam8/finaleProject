__author__ = 'Agam'

import sqlite3
import hashlib
import os

class User(object):
    def __init__(self, id, username, password, current_ip, is_logged):
        self.id = id
        self.username = username
        self.password = password
        self.current_ip = current_ip
        self.is_logged = is_logged

    def __str__(self):
        return f'{self.username}~***~{self.current_ip}~{self.is_logged}'

class UserORM():
    def __init__(self,db_file):
        self.db_file = db_file
        self.conn = None  # will store the DB connection
        self.cursor = None  # will store the DB connection cursor

    def open_DB(self):
        """
        will open DB file and put value in:
        self.conn (need DB file name)
        and self.cursor
        """
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def close_DB(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def get_user_by_id(self, user_id):
        self.open_DB()
        user = ''
        sql = f"SELECT * FROM users WHERE id={user_id};"
        res = self.cursor.execute(sql)
        user = res.fetchone()
        self.close_DB()
        return user

    def get_user_by_username(self, username):
        self.open_DB()
        user_data = None
        sql = f"SELECT * FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        row = res.fetchone()
        if row is not None:
            user_data = User(*row)
        self.close_DB()
        return user_data

    def add_user(self, user):
        self.open_DB()
        added = False
        sql = f"SELECT * FROM users WHERE username='{user.username}';"
        res = self.cursor.execute(sql)
        if res.fetchone() is None:
            sql = f"INSERT INTO users (username, password, current_ip, is_logged) VALUES ('{user.username}', '{user.password}', '{user.current_ip}', '{user.is_logged}');"
            self.cursor.execute(sql)
            added = True
        self.close_DB()
        return added

    def check_user_exists(self, username):
        self.open_DB()
        exists = False
        sql = f"SELECT * FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        if res.fetchone() is not None:
            exists = True
        self.close_DB()
        return exists

    def update_user(self, user):
        self.open_DB()
        sql = f"UPDATE users SET password='{user.password}', current_ip='{user.current_ip}', is_logged='{user.is_logged}' WHERE id={user.id};"
        self.cursor.execute(sql)
        self.close_DB()

    def create_user(self, username, password,ip):
        self.open_DB()
        new_user = User(username=username, password=password, current_ip="", is_logged=0)
        self.cursor.execute("INSERT INTO users (username, password, current_ip, is_logged) VALUES (?, ?, ?, ?)",
                            (new_user.username, new_user.password, new_user.current_ip, new_user.is_logged))
        self.commit()
        self.close_DB()

    def login(self, username, password, ip):
        user = self.get_user_by_username(username)
        print(user)
        if user is not None:
            secure_pass = hashlib.sha256(password.encode()).hexdigest()
            if user.password == secure_pass and user.is_logged == 0:
                self.open_DB()
                self.cursor.execute("UPDATE users SET current_ip=?, is_logged=? WHERE username=?",
                                    (ip, 1, username))
                self.cursor.execute("UPDATE songs SET ip=? WHERE committed_user=?",
                                    (ip, user.id))
                self.commit()
                self.close_DB()
                return True
        return False
    def signup(self,username,password,cli_ip):
        user = self.get_user_by_username(username)
        if user is None:
            secure_pass = hashlib.sha256(password.encode()).hexdigest()
            self.open_DB()
            self.cursor.execute("""
                            INSERT INTO Users (
                                username, password, current_ip, is_logged
                            ) VALUES (?, ?, ?, ?)
                        """, (username, secure_pass, cli_ip, 0))
            self.commit()
            self.close_DB()
            return True, 'sign'
        else:
            return False, 'exst'
    def logout(self, username):
        user = self.get_user_by_username(username)
        if user is not None and user.is_logged == 1:
            self.open_DB()
            self.cursor.execute("UPDATE users SET current_ip=?, is_logged=? WHERE username=?",
                                ("", 0, username))
            self.commit()
            self.close_DB()
            return True
        return False
    def logout_all(self):
        self.open_DB()
        self.cursor.execute("UPDATE Users SET current_ip=?, is_logged=?", ('',0))
        self.commit()
        self.close_DB()

    def is_user_logged_in(self, username):
        self.open_DB()
        sql = f"SELECT is_logged FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        is_logged = res.fetchone()
        self.close_DB()
        if is_logged is not None and is_logged[0] == 1:
            return True
        return False

    def change_status_and_ip(self, username, new_ip):
        user = self.get_user_by_username(username)
        self.open_DB()
        if user is not None and user.is_logged == 0:
            self.cursor.execute("UPDATE users SET current_ip=?, is_logged=? WHERE username=?",
                                (new_ip, 1, username))
            self.commit()
            self.close_DB()
            return True
        self.close_DB()
        return False

    def get_all_users(self):
        self.open_DB()
        self.cursor.execute("SELECT * FROM users")
        user_rows = self.cursor.fetchall()
        self.close_DB()
        return [User(*user_row) for user_row in user_rows]

    # connected function to Songs table
    def get_user_by_song(self, song):
        self.open_DB()
        user = None
        sql = f"SELECT * FROM users WHERE id={song.committed_user};"
        res = self.cursor.execute(sql)
        row = res.fetchone()
        if row is not None:
            user = User(*row)
        self.close_DB()
        return user






class Song(object):
    def __init__(self, file_name, song_name, artist, genre, committed_user, ip = '', size = ''):
        self.file_name = file_name
        self.song_name = song_name
        self.artist = artist
        self.genre = genre
        self.ip = ip
        self.size = size
        self.committed_user = committed_user


    def __str__(self):
        return f'\n\tfile name: {self.file_name}' \
               f'\n\tsong name: {self.song_name}' \
               f'\n\tartist: {self.artist}' \
               f'\n\tgenre: {self.genre}' \
               f'\n\tcommitted user: {self.committed_user}' \
               f'\n\tip: {self.ip}\n\tsize: {self.size}'


class SongsORM():
    def __init__(self, db_file):
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def open_DB(self):
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def close_DB(self):
        self.cursor.close()
        self.conn.close()

    def commit(self):
        self.conn.commit()

    def add_song(self, song):
        self.open_DB()
        try:
            self.cursor.execute("""
                INSERT INTO songs (
                    file_name, song_name, artist, genre, committed_user, ip, size
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (song.file_name, song.song_name, song.artist, song.genre, song.committed_user, song.ip, song.size))
            self.commit()
            self.close_DB()
            return True
        except Exception as e:
            print(e)
            self.close_DB()
            return False

    def get_all_songs(self):
        self.open_DB()
        self.cursor.execute("SELECT * FROM songs;")
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def get_songs_by_name(self, name):
        self.open_DB()
        self.cursor.execute("SELECT * FROM songs WHERE song_name LIKE ?;", ('%' + name + '%',))
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def get_song_by_file(self, file_name):
        self.open_DB()
        self.cursor.execute(f"SELECT * FROM songs WHERE file_name == '{file_name}';")
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def get_songs_by_artist(self, artist):
        self.open_DB()
        self.cursor.execute("SELECT * FROM songs WHERE artist LIKE '?';", ('%' + artist + '%',))
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def get_songs_by_genre(self, genre):
        self.open_DB()
        self.cursor.execute("SELECT * FROM songs WHERE genre LIKE '?';", ('%' + genre + '%',))
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def song_exists(self, file_name):
        self.open_DB()
        sql = "SELECT * " \
              "FROM Songs " \
              f"WHERE file_name == '{file_name}';"

        # print('executing:',sql)
        res = self.cursor.execute(sql)
        exists = bool(res.fetchone())
        self.close_DB()
        return exists

    def count_songs(self):
        self.open_DB()
        sql = "SELECT COUNT(*) FROM songs;"
        res = self.cursor.execute(sql)
        count = res.fetchone()[0]
        self.close_DB()
        return count

    def add_client_folder(self, fields, cli_ip):
        length = int(fields[0])
        print("Got %d files" % length)
        try:
            for i in range(length):
                #print("splitting by ~")
                info = fields[i + 1].split("~")  # info[0]: file name, info[1]: song name, info[2]: artist, info[3]: genre, info[4]: username, info[5]: size
                print('song ', i + 1, ':', info)

                exists = self.song_exists(info[0])
                print(info[0]," exsits: ",exists)
                if not exists:
                    new_song = Song(info[0], info[1], info[2], info[3], info[4], cli_ip, info[5])
                    self.add_song(new_song)
                    print("got new file" + str(new_song))
                else:
                    print("file already exist " + info[0])
        except Exception as e:
            print("adding client's folder through exception: ", e)
        print("Len of files " + str(self.count_songs()))

    def add_server_folder(self,srv_path):
        for f in os.listdir(srv_path):
            full_name = os.path.join(srv_path, f)
            print("f " + full_name + " " + str(os.path.isfile(full_name)))
            if os.path.isfile(full_name) and f.endswith(".mp3"):
                exists = self.song_exists(full_name)
                if not exists:
                    new_song = Song(full_name, 'unknown', 'unknown', 'unknown', '0.0.0.0', str(os.path.getsize(full_name)))
                    self.add_song(new_song)
                else:
                    print(f, 'already exists')

    def search_songs(self, keyword):
        self.open_DB()
        songs = []
        sql = f"SELECT * FROM songs WHERE " \
              f"file_name LIKE '%{keyword}%' OR " \
              f"song_name LIKE '%{keyword}%' OR " \
              f"artist LIKE '%{keyword}%' OR " \
              f"genre LIKE '%{keyword}%';"
        res = self.cursor.execute(sql)
        rows = res.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    # connected functions to Users table
    def get_songs_by_user(self, user_id):
        self.open_DB()
        songs = []
        sql = f"SELECT * FROM songs WHERE committed_user={user_id};"
        res = self.cursor.execute(sql)
        for row in res.fetchall():
            song = Song(*row)
            songs.append(song)
        self.close_DB()
        return songs

def main():
    # create an instance of the SongsORM class and create the songs table
    songs_orm = SongsORM(r'E:\finaleProject\server_database.db')
    # songs_orm.create_table()

    # create a song object and add it to the songs table
    # song = Song('song_file.mp3', 'Song Name', 'Artist Name',  'Pop', '192.168.0.1', '1024')
    # songs_orm.add_song(song)

    # get all the songs from the songs table
    # all_songs = songs_orm.get_all_songs()
    print(songs_orm.song_exists('Brakhage - No Coincidence.mp3'))
    print(songs_orm.get_song_by_file('Brakhage - No Coincidence.mp3'))

if __name__ == "__main__":
    main()

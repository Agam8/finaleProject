__author__ = 'Agam'

import sqlite3
import hashlib
from objects import User, Song


class UserORM():
    def __init__(self, db_file):
        """
        Initializes a UserORM object.

        :param db_file: The path to the database file.
        """
        self.db_file = db_file
        self.conn = None  # will store the DB connection
        self.cursor = None  # will store the DB connection cursor

    def open_DB(self):
        """
        Opens the database connection and initializes the cursor.
        """
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def close_DB(self):
        """
        Closes the database connection.
        """
        self.conn.close()

    def commit(self):
        """
        Commits the changes to the database.
        """
        self.conn.commit()

    def get_user_by_username(self, username: str):
        """
        Retrieves a user from the database based on the username.

        :param username: The username of the user.
        :return: The user object if found, else None.
        """
        self.open_DB()
        username = username.lower()
        user_data = None
        sql = f"SELECT * FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        row = res.fetchone()
        if row is not None:
            user_data = User(*row)
        self.close_DB()
        return user_data

    def add_user(self, user):
        """
        Adds a new user to the database.

        :param user: The user object to be added.
        :return: True if the user is added successfully, False otherwise.
        """
        self.open_DB()
        added = False
        sql = f"SELECT * FROM users WHERE username='{user.username}';"
        res = self.cursor.execute(sql)
        if res.fetchone() is None:
            sql = f"INSERT INTO users (username, password, current_ip, is_logged) VALUES ('{user.username}', " \
                  f"'{user.password}', '{user.current_ip}', '{user.is_logged}');"
            self.cursor.execute(sql)
            added = True
        self.close_DB()
        return added

    def check_user_exists(self, username: str):
        """
        Checks if a user with the given username exists in the database.

        :param username: The username to check.
        :return: True if the user exists, False otherwise.
        """
        self.open_DB()
        exists = False
        username.lower()
        sql = f"SELECT * FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        if res.fetchone() is not None:
            exists = True
        self.close_DB()
        return exists

    def update_user(self, user):
        """
        Updates a user's information in the database.

        :param user: The updated user object.
        :return: None
        """
        self.open_DB()
        sql = f"UPDATE users SET password='{user.password}', current_ip='{user.current_ip}', " \
              f"is_logged='{user.is_logged}' WHERE id={user.id};"
        self.cursor.execute(sql)
        self.close_DB()

    def login(self, username, password, ip):
        """
        Logs in a user with the provided username, password, and IP.

        :param username: The username of the user.
        :param password: The password of the user.
        :param ip: The IP address of the user.

        :return: True if login is successful, False otherwise.
        """
        username = username.lower()
        user = self.get_user_by_username(username)
        if user is not None:
            secure_pass = hashlib.sha256(password.encode()).hexdigest()
            if user.password == secure_pass and user.is_logged == 0:
                self.open_DB()
                self.cursor.execute("UPDATE users SET current_ip=?, is_logged=? WHERE username=?",
                                    (ip, 1, username))
                self.cursor.execute("UPDATE songs SET ip=? WHERE committed_user=?",
                                    (ip, username))
                self.commit()
                self.close_DB()
                return True
        return False

    def signup(self, username, password, cli_ip):
        """
        Signs up a new user with the provided username, password, and IP.

        :param username: The username of the new user.
        :param password: The password of the new user.
        :param cli_ip: The IP address of the new user.

        :return: Tuple (success, message) where success is True if signup is successful, False otherwise,
                 and message is a string indicating the result.
        """
        username.lower()
        user = self.get_user_by_username(username)
        if user is None:
            secure_pass = hashlib.sha256(password.encode()).hexdigest()
            self.open_DB()
            self.cursor.execute("""
                            INSERT INTO Users (
                                username, password, current_ip, is_logged
                            ) VALUES (?, ?, ?, ?)
                        """, (username, secure_pass, cli_ip, 1))
            self.commit()
            self.close_DB()
            return True, 'OK'
        else:
            return False, 'NO'

    def logout(self, username):
        """
        Logs out a user with the provided username.

        :param username: The username of the user to log out.
        :return: True if logout is successful, False otherwise.
        """
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
        """
        Logs out all users.

        :return: None
        """
        self.open_DB()
        self.cursor.execute("UPDATE Users SET current_ip=?, is_logged=?", ('', 0))
        self.commit()
        self.close_DB()

    def is_user_logged_in(self, username):
        """
        Checks if a user is currently logged in.

        :param username: The username of the user to check.
        :return: True if the user is logged in, False otherwise.
        """
        username.lower()
        self.open_DB()
        sql = f"SELECT is_logged FROM users WHERE username='{username}';"
        res = self.cursor.execute(sql)
        is_logged = res.fetchone()
        self.close_DB()
        if is_logged is not None and is_logged[0] == 1:
            return True
        return False

    # connected function to Songs table
    def get_user_by_song(self, song):
        """
        Retrieves the user who committed a specific song.

        :param song: The song object.
        :return: The user object who committed the song if found, else None.
        """
        self.open_DB()
        user = None
        sql = f"SELECT * FROM users WHERE username={song.committed_user};"
        res = self.cursor.execute(sql)
        row = res.fetchone()
        if row is not None:
            user = User(*row)
        self.close_DB()
        return user

    def is_available(self, md5, req_user):
        """
        Checks if a song with the given MD5 hash is available for a specific user.

        :param md5: The MD5 hash of the song.
        :param req_user: The username of the user requesting the availability.
        :return: True if the song is available for the user, False otherwise.
        """
        self.open_DB()
        user = None
        sql = f"SELECT committed_user FROM songs WHERE md5=='{md5}';"
        res = self.cursor.execute(sql)
        row = res.fetchone()
        if row is not None:
            username = row[0]
            if req_user == username:
                self.close_DB()
                return False
            sql = f"SELECT is_logged FROM Users WHERE username == '{username.lower()}';"
            res = self.cursor.execute(sql)
            row = res.fetchone()
            self.close_DB()
            if row is not None:
                return int(row[0]) == 1
            else:
                return False
        else:
            self.close_DB()
            return False


class SongsORM():
    def __init__(self, db_file):
        """
        Initializes the SongsORM object.

        :param db_file: The path to the SQLite database file.
        """
        self.db_file = db_file
        self.conn = None
        self.cursor = None

    def open_DB(self):
        """
        Opens a connection to the database.
        """
        self.conn = sqlite3.connect(self.db_file)
        self.cursor = self.conn.cursor()

    def close_DB(self):
        """
        Closes the connection to the database.
        """
        self.cursor.close()
        self.conn.close()

    def commit(self):
        """
        Commits the changes made to the database.
        """
        self.conn.commit()

    def add_song(self, song):
        """
        Adds a song to the database.

        :param song: The Song object to be added.
        :return: True if the song is successfully added, False otherwise.
        """
        self.open_DB()
        try:
            self.cursor.execute("""
                INSERT INTO songs (
                    md5, file_name, song_name, artist, genre, committed_user, ip, size
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                song.md5, song.file_name, song.song_name, song.artist, song.genre, song.committed_user, song.ip,
                song.size))
            self.commit()
            self.close_DB()
            return True
        except Exception as e:
            print(e)
            self.close_DB()
            return False

    def add_songs(self, songs_list):
        """
        Adds a song to the database.

        :param song: The Song object to be added.
        :return: True if the song is successfully added, False otherwise.
        """
        self.open_DB()
        try:
            for song in songs_list:
                self.cursor.execute("""
                    INSERT INTO songs (
                        md5, file_name, song_name, artist, genre, committed_user, ip, size
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    song.md5, song.file_name, song.song_name, song.artist, song.genre, song.committed_user, song.ip,
                    song.size))
            self.commit()
            self.close_DB()
            return True
        except Exception as e:
            print(e)
            self.close_DB()
            return False

    def get_all_songs(self):
        """
        Retrieves all songs from the database.

        :return: A list of Song objects representing all the songs in the database.
        """
        self.open_DB()
        self.cursor.execute("SELECT * FROM songs;")
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def get_song_by_md5(self, md5):
        """
        Retrieves a song from the database based on its MD5 hash.

        :param md5: The MD5 hash of the song.
        :return: A list of Song objects that match the given MD5 hash.
        """
        self.open_DB()
        self.cursor.execute(f"SELECT * FROM songs WHERE md5 == '{md5}';")
        rows = self.cursor.fetchall()
        self.close_DB()
        return [Song(*row) for row in rows]

    def song_exists(self, md5):
        """
        Checks if a song with the given MD5 hash exists in the database.

        :param md5: The MD5 hash of the song.
        :return: True if the song exists, False otherwise.
        """
        self.open_DB()
        sql = "SELECT * " \
              "FROM Songs " \
              f"WHERE md5 == '{md5}';"

        res = self.cursor.execute(sql)
        exists = bool(res.fetchone())
        self.close_DB()
        return exists

    def count_songs(self):
        """
        Counts the number of songs in the database.

        :return: The total number of songs in the database.
        """
        self.open_DB()
        sql = "SELECT COUNT(*) FROM songs;"
        res = self.cursor.execute(sql)
        count = res.fetchone()[0]
        self.close_DB()
        return count

    def add_client_folder(self, fields, cli_ip):
        """
        Adds songs from a client's folder to the database.

        :param fields: The information about the songs.
        :param cli_ip: The IP address of the client.
        :param username: The username of the client.
        :return: None
        """
        length = int(fields[0])
        username = fields[1]
        print("Got %d files" % length)
        try:
            existing_md5s = self.get_md5s_by_username(username)
            md5_available = []

            for i in range(1,length+1):
                info = fields[i + 1].split("~")
                md5 = info[0]
                exists = self.song_exists(md5)
                if not exists:
                    new_song = Song(md5, info[1], info[2], info[3], info[4], info[5], cli_ip, info[6])
                    self.add_song(new_song)
                    print("Got new file: " + str(new_song))
                else:
                    print("File already exists: " + info[1])
                md5_available.append(md5)

            # Delete MD5s that were not uploaded by the same username
            md5s_to_delete = [md5 for md5 in existing_md5s if md5 not in md5_available]
            self.delete_songs_by_md5s(md5s_to_delete)
        except Exception as e:
            print("Adding client's folder threw an exception:", e)

        print("Length of files:", self.count_songs())

    def get_md5s_by_username(self, username):
        """
        Retrieves the MD5 values associated with a given username.

        :param username: The username of the user.
        :return: A list of MD5 values.
        """
        self.open_DB()
        md5s = []
        try:
            sql = f"SELECT md5 FROM songs WHERE committed_user='{username}';"
            self.cursor.execute(sql)
            rows = self.cursor.fetchall()
            md5s = [row[0] for row in rows]
        except Exception as e:
            print("Error retrieving MD5s by username:", e)
        self.close_DB()
        return md5s

    def delete_songs_by_md5s(self, md5s):
        """
        Deletes songs from the database based on their MD5 values.

        :param md5s: A set of MD5 values.
        :return: None
        """
        try:
            self.open_DB()
            for md5 in md5s:
                sql = f"DELETE FROM songs WHERE md5='{md5}';"
                self.cursor.execute(sql)
            self.commit()
            self.close_DB()
            print("Deleted songs with MD5s:", md5s)
        except Exception as e:
            print("Error deleting songs:", e)

    def search_songs(self, keyword):
        """
        Searches for songs in the database based on a keyword.

        :param keyword: The keyword to search for.
        :return: A list of Song objects that match the given keyword.
        """
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
        if len(rows)!= 0:
            return [Song(*row) for row in rows]
        else:
            return []

    # connected functions to Users table
    def get_songs_by_user(self, user):
        """
        Retrieves songs from the database that were committed by a specific user.
        :param user: The committed user to search for.
        :return: A list of Song objects that were committed by the specified user.
        """
        self.open_DB()
        songs = []
        sql = f"SELECT * FROM songs WHERE committed_user=={user};"
        res = self.cursor.execute(sql)
        for row in res.fetchall():
            song = Song(*row)
            songs.append(song)
        self.close_DB()
        return songs

    def get_user_by_song(self, md5):
        """
        Retrieves the committed user for a song with the given MD5 hash.
        :param md5: The MD5 hash of the songs
        :return: The committed user for the song.
        """
        self.open_DB()
        user = ''
        sql = f"SELECT committed_user FROM songs WHERE md5 == '{md5}'"
        res = self.cursor.execute(sql)
        user = res.fetchone()[0].strip("'")
        self.close_DB()
        return user


def main():
    # create an instance of the SongsORM class and create the songs table
    songs_orm = SongsORM(r'server_database.db')
    users_orm = UserORM(r'server_database.db')
    #print(len(songs_orm.search_songs('x')))
    # songs_orm.create_table()
    fields=["jazz","agam8"]
    songs = songs_orm.search_songs(fields[0])
    answer='SRCHBK'
    if len(songs) == 0:
        answer += ''
    else:
        for song in songs:
            is_available = users_orm.is_available(song.md5, fields[1])
            answer += f"|{song.md5}~{song.file_name}~{song.song_name}~{song.artist}~{song.genre}~{song.size}~" \
                      f"{song.committed_user}~{is_available}"
    to_send = answer

    # create a song object and add it to the songs table
    # song = Song('song_file.mp3', 'Song Name', 'Artist Name',  'Pop', '192.168.0.1', '1024')
    # songs_orm.add_song(song)

    # get all the songs from the songs table
    # all_songs = songs_orm.get_all_songs()


if __name__ == "__main__":
    main()

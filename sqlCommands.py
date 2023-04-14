import sqlite3
import os

__author__ = 'agam'


class User(object):
    def __init__(self, id, username, email, password, is_logged,
                 saved_playlists, liked_songs, average_duration):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.is_logged = is_logged
        self.saved_playlists = saved_playlists
        self.liked_songs = liked_songs
        self.average_duration = average_duration

    def __str__(self):
        pass


class UsersORM():
    def __init__(self):
        self.conn = None  # will store the DB connection
        self.cursor = None  # will store the DB connection cursor

    def open_DB(self):
        """
        will open DB file and put value in:
        self.conn (need DB file name)
        and self.cursor
        """
        self.conn = sqlite3.connect('Users.db')
        self.current = self.conn.cursor()

    def close_DB(self):
        self.conn.close()

    def commit(self):
        self.conn.commit()

    # All read SQL

    def get_user(self, id):
        self.open_DB()
        user = None
        sql = f"SELECT * FROM users WHERE id == '{id}' ;"
        res = self.current.execute(sql)
        user = res.fetchall()
        self.close_DB()
        return user

    def get_all_users(self):
        self.open_DB()
        users = []
        sql = "SELECT *" \
              "FROM users;"
        res = self.current.execute(sql)
        users = res.fetchall()
        self.close_DB()
        return users

    def get_users_passwords(self, entered_value):
        self.open_DB()
        sql = "SELECT username, password" \
              f"FROM users WHERE username == {entered_value} OR email == {entered_value}"
        res = self.current.execute(sql)
        users = res.fetchall()
        self.close_DB()

    def login_user(self, entered_value):
        self.open_DB()
        sql = "SELECT username, password" \
              f"FROM users WHERE username == {entered_value} OR email == {entered_value}"
        res = self.current.execute(sql)
        users = res.fetchall()
        self.close_DB()

    def get_students_in_grade(self, grade):
        self.open_DB()

        sql = "SELECT personal_id, first_Name, last_Name, school FROM students WHERE students.grade == " + str(
            grade) + ";"
        res = self.current.execute(sql)
        students_in_grade = []
        students_in_grade = res.fetchall()
        self.close_DB()
        return students_in_grade

    def get_principle_and_students(self, school):
        self.open_DB()
        answer = f"{school}:\n"
        sql = f"SELECT principle FROM schools WHERE name == '{school}';"
        res = self.current.execute(sql)
        answer += f"principle:{res.fetchall()}\n"
        sql = f"SELECT first_Name,last_Name FROM students WHERE school == '{school}';"
        res = self.current.execute(sql)
        answer += f"{(res.fetchall())}"
        return answer

    def remove_student(self, personal_id, school):
        try:
            self.open_DB()

            sql = f"UPDATE schools SET student_count = student_count -1 WHERE name == '{school}';"
            res = self.current.execute(sql)
            sql = f"DELETE FROM students WHERE personal_id == '{personal_id}' ;"
            res = self.current.execute(sql)
            self.commit()
            self.close_DB()
            return True
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.close_DB()
            return False

    def update_phone(self, personal_id, new_phone):
        try:
            self.open_DB()
            sql = "UPDATE students SET phone = " + new_phone + " WHERE personal_id ==" + personal_id + ";"
            res = self.current.execute(sql)
            self.commit()
            self.close_DB()
            return True
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.close_DB()
            return False

    def insert_new_student(self, student):
        try:
            self.open_DB()
            sql = "SELECT * FROM students;"
            res = self.current.execute(sql)
            print("cur students:", res.fetchall())
            sql = f"INSERT INTO students VALUES ('{student.personal_id}', '{student.first_Name}','{student.last_Name}','{student.phone}',{student.grade},'{student.school}')"
            res = self.current.execute(sql)
            sql = f"UPDATE schools SET student_count=student_count+1 WHERE name == '{student.school}';"
            res = self.current.execute(sql)
            self.commit()
            self.close_DB()
            print(res)
            return True
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.close_DB()
            return False

    def update_grades(self):
        try:
            self.open_DB()
            sql = "DELETE FROM students WHERE grade == 12;"
            res = self.current.execute(sql)
            sql = "UPDATE students SET grade = grade + 1 ;"
            res = self.current.execute(sql)

            self.commit()
            self.close_DB()
            return True
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.close_DB()
            return False

    def transfer_schools(self, personal_id, new_school, old_school):
        try:
            self.open_DB()
            sql = f"UPDATE students set school = '{new_school}' WHERE personal_id == '{personal_id}';"
            res = self.current.execute(sql)
            sql = f"UPDATE schools SET student_count = student_count - 1 WHERE name == '{old_school}';"
            res = self.current.execute(sql)
            sql = f"UPDATE schools SET student_count = student_count + 1 WHERE name == '{new_school}';"
            res = self.current.execute(sql)

            self.commit()
            self.close_DB()
            return True
        except sqlite3.Error as error:
            print("Error while connecting to sqlite", error)
            self.close_DB()
            return False


class Song(object):
    def __init__(self, file_name, song_name, artist, genre, ip = '', size = ''):
        self.file_name = file_name
        self.song_name = song_name
        self.artist = artist
        self.genre = genre
        self.ip = ip
        self.size = size


    def __str__(self):
        return f'song: {self.file_name}\n' \
               f'name: {self.song_name}\n' \
               f'artist: {self.artist}\n' \
               f'size: {self.size}\n'


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

    def create_table(self):
        self.open_DB()
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS songs (
                file_name TEXT PRIMARY KEY,
                song_name TEXT,
                artist TEXT,
                genre TEXT,
                ip TEXT,
                size INTEGER,
                checksum TEXT
            )
        """)
        self.close_DB()

    def add_song(self, song):
        self.open_DB()
        try:
            self.cursor.execute("""
                INSERT INTO songs (
                    file_name, song_name, artist, genre, ip, size
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (song.file_name, song.song_name, song.artist, song.genre, song.ip, song.size))
            self.commit()
            return True
        except Exception as e:
            print(e)
            return False
        finally:
            self.close_DB()

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
                info = fields[i + 1].split("~")  # info[0]: file name, info[1]: song name, info[2]: artist, info[3]: genre, info[4]: size
                #print('song ', i + 1, ':', info)


                print('checking if ',info[0],' exsits')
                exists = self.song_exists(info[0])

                if not exists:
                    new_song = Song(info[0], info[1], info[2], info[3], cli_ip, info[4])
                    self.add_song(new_song)
                    print("got new file" + str(new_song))
                else:
                    print("file already exist " + info[0])
        except Exception as e:
            print("adding client's folder through exception: ", e)
        print("Len of files" + str(self.count_songs()))

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




"""    # search for songs by name
    name_search_results = songs_orm.get_songs_by_name('song')

    # search for songs by artist
    artist_search_results = songs_orm.get_songs_by_artist('artist')

    # search for songs by genre
    genre_search_results = songs_orm.get_songs_by_genre('pop')

    print(all_songs, name_search_results, artist_search_results,genre_search_results)
"""

if __name__ == "__main__":
    main()

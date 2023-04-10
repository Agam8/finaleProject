import sqlite3

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
        return f'User: {self.id}\n' \
            f'username: {self.username}\n' \
            f'email: {self.email}\n' \
            f'password: ***\n' \ 
            f'logged rn?: {self.is_logged}'




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
        user=None
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

        sql = "SELECT personal_id, first_Name, last_Name, school FROM students WHERE students.grade == " + str(grade) + ";"
        res = self.current.execute(sql)
        students_in_grade = []
        students_in_grade = res.fetchall()
        self.close_DB()
        return students_in_grade

    def get_principle_and_students(self,school):
        self.open_DB()
        answer=f"{school}:\n"
        sql=f"SELECT principle FROM schools WHERE name == '{school}';"
        res = self.current.execute(sql)
        answer+=f"principle:{res.fetchall()}\n"
        sql = f"SELECT first_Name,last_Name FROM students WHERE school == '{school}';"
        res = self.current.execute(sql)
        answer += f"{(res.fetchall())}"
        return answer


    def remove_student(self, personal_id,school):
        try:
            self.open_DB()

            sql=f"UPDATE schools SET student_count = student_count -1 WHERE name == '{school}';"
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

    def update_phone(self,personal_id,new_phone):
        try:
            self.open_DB()
            sql = "UPDATE students SET phone = "+new_phone+" WHERE personal_id =="+personal_id+";"
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
    def transfer_schools(self,personal_id,new_school,old_school):
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
    def __init__(self, id, name, artist, size, checksum):
        self.id = id
        self.name = name
        self.artist = artist
        self.size = size
        self.checksum = checksum


    def __str__(self):
        return f'song: {self.id}\n' \
           f'name: {self.name}\n' \
           f'artist: {self.artist}\n' \
           f'size: {self.size}\n' \
           f'checksum: {self.checksum}'

class SongsORM():
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

    def get_all_songs(self):
        self.open_DB()
        songs = []
        sql = "SELECT *" \
              "FROM songs;"
        res = self.current.execute(sql)
        songs = res.fetchall()
        self.close_DB()
        return songs
    def get_song_by_name(self, name):
        self.open_DB()
        song = ''
        sql = "SELECT *" \ 
              "FROM songs" \ 
              f"WHEN name == {name};"
        res = self.current.execute(sql)
        song = res.fetchall()
        self.close_DB()
        return song

def main_test():
    db = StudentSchoolORM()
    students = db.get_students_in_grade(12)
    for s in students:
        print(s)
    # new_stu = Student("4567891", "Neta", "Lasser", "053271101", 10, "Galili")
    # print(db.insert_new_student(new_stu))
    print(db.update_grades())
    # print(db.update_phone("1234567","0521234567"))
    # print(db.get_principle_and_students("Herzog"))
    # print(db.transfer_schools("1234567","Galili","Herzog"))


if __name__ == "__main__":
    main_test()

import os.path

from objects import Song
import sqlite3
import hashlib


class ClientORM():
    def __init__(self):
        """
        Initializes the SongsORM object.

        :param db_file: The path to the SQLite database file.
        """
        self.db_file = ''
        self.conn = None
        self.cursor = None

    def set_username_path(self, username, cli_path):
        self.username = username
        self.cli_path = cli_path
        self.db_file = os.path.join(cli_path, f'{username}_songs_table.db')

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

    def check_files_in_table(self, files_list):
        if not os.path.exists(self.db_file):
            with open(self.db_file, 'w') as f:
                f.write('')
        # Check if the table already exists
        self.open_DB()
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='client_songs'")
        table_exists = self.cursor.fetchone()

        # Create the table if it doesn't exist
        if not table_exists:
            self.cursor.execute('''CREATE TABLE client_songs
                              (md5 TEXT, file_name TEXT, song_name TEXT, artist TEXT, genre TEXT, size INTEGER)''')
            print("Table created successfully!")

        # Calculate MD5 hashes for each file and check if they are in the table
        files_not_exist = []
        files_in_table = []

        for file_path in files_list:
            md5_hash = hashlib.md5(open(os.path.join(self.cli_path, file_path), 'rb').read()).hexdigest()
            self.cursor.execute(f"SELECT * FROM client_songs WHERE md5= '{md5_hash}';")
            result = self.cursor.fetchone()

            if result is None:
                files_not_exist.append(file_path)
            else:
                song = Song(md5_hash, result[1], result[2], result[3], result[4], self.username, size=result[5])
                files_in_table.append(song)

        # Commit the changes and close the connection
        self.conn.commit()
        self.conn.close()

        return files_not_exist, files_in_table

    def save_all_songs(self, files_dict):
        """
        getting a files dictionery that contains {md5:Song object,...} to be saved in the table
        :param files_dict:
        :return:
        """
        try:
            self.open_DB()
            self.cursor.execute("SELECT md5 FROM client_songs")
            existing_md5s = [row[0] for row in self.cursor.fetchall()]

            # Insert new songs into the table
            for md5, song in files_dict.items():
                if md5 in existing_md5s:
                    # Remove MD5 from the existing MD5s list
                    existing_md5s.remove(md5)
                else:
                    # Insert the song information into the table
                    self.cursor.execute("INSERT INTO client_songs VALUES (?, ?, ?, ?, ?, ?)",
                                        (song.md5, song.file_name, song.song_name, song.artist, song.genre, song.size))

            # Remove MD5 entries that don't exist in the given files path's list
            for md5 in existing_md5s:
                self.cursor.execute("DELETE FROM client_songs WHERE md5=?", (md5,))

            # Commit the changes and close the connection
            self.conn.commit()
            self.close_DB()
            return True

        except Exception as e:
            print(e)
            # Rollback changes and close the connection
            self.conn.rollback()
            self.close_DB()
            return False

    def add_song(self, song):
        try:
            self.open_DB()
            self.cursor.execute("INSERT INTO client_songs VALUES (?, ?, ?, ?, ?, ?)",
                                (song.md5, song.file_name, song.song_name, song.artist, song.genre, song.size))
            self.commit()
            self.close_DB()
            return True
        except Exception as e:
            print(e)
            # Rollback changes and close the connection
            self.conn.rollback()
            self.close_DB()
            return False


def main():
    CLI_PATH = 'client_songs'
    all_files = [f for f in os.listdir(CLI_PATH) if
                 os.path.isfile(os.path.join(CLI_PATH, f)) and f.endswith('.wav')]
    client_orm = ClientORM('agam8', CLI_PATH)
    not_existing, existing = client_orm.check_files_in_table(all_files)
    print(not_existing, existing)


if __name__ == '__main__':
    main()

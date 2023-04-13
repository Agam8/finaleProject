import sqlCommands
songs_database = sqlCommands.SongsORM('server_database.db')
print(songs_database.get_song_by_file('Brakhage - No Coincidence.mp3'))
import sqlCommands
songs_database = sqlCommands.SongsORM(r'server_database.db')
song = songs_database.get_song_by_file('Brakhage - No Coincidence.mp3')[0]
print(song.ip)

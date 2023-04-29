import customtkinter as ctk

class SearchResult(ctk.CTkFrame):
    def __init__(self, master, fields, search_word):
        self.master = master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center', relx=0.5, rely=0.5, relheight=0.95, relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Search Results', font=('Arial', 18))
        title_label.pack(pady=10)

        # Create a table to display the search results
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(pady=10)

        # Create the headers for the table
        headers = ['Song', 'Artist', 'Genre', 'Size', 'Username', 'Available']
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(table_frame, text=header, font=('Arial', 12), padx=10, pady=5,
                                        borderwidth=1, relief='solid')
            header_label.grid(row=0, column=i, sticky='w')

        # Add the search results to the table
        i = 1
        for f in fields:
            info = f.split("~")
            if len(info) > 1:
                song_label = ctk.CTkLabel(table_frame, text=info[0], font=('Arial', 12), padx=10,
                                          pady=5,
                                          borderwidth=1, relief='solid')
                song_label.grid(row=i + 1, column=0, sticky='w')

                artist_label = ctk.CTkLabel(table_frame, text=info[1], font=('Arial', 12), padx=10,
                                            pady=5, borderwidth=1, relief='solid')
                artist_label.grid(row=i + 1, column=1, sticky='w')

                genre_label = ctk.CTkLabel(table_frame, text=info[2], font=('Arial', 12), padx=10,
                                           pady=5,
                                           borderwidth=1, relief='solid')
                genre_label.grid(row=i + 1, column=2, sticky='w')

                size_label = ctk.CTkLabel(table_frame, text=info[3], font=('Arial', 12), padx=10,
                                          pady=5,
                                          borderwidth=1, relief='solid')
                size_label.grid(row=i + 1, column=4, sticky='w')

                username_label = ctk.CTkLabel(table_frame, text=info[4], font=('Arial', 12),
                                              padx=10, pady=5, borderwidth=1, relief='solid')
                username_label.grid(row=i + 1, column=3, sticky='w')

                available_label = ctk.CTkLabel(table_frame, text=info[5], font=('Arial', 12),
                                               padx=10, pady=5, borderwidth=1, relief='solid')
                available_label.grid(row=i + 1, column=3, sticky='w')

                print("\t{} {} {} {} {} {} {}\n".format(info[0], info[1], info[2], info[3], info[4], info[5], info[6]),
                      end=' ')
            else:
                empty_label = ctk.CTkLabel(table_frame, text=f"No search results for '{search_word}'")
                empty_label.pack(pady=10)
            i += 1

sr = SearchResult()
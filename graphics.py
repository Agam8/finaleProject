import customtkinter as ctk
from tkinter import Tk, font
root = Tk()
all_fonts = font.families()
app = ctk.CTk()
app.geometry('900x900')
file_name = ctk.CTkLabel(app, text='Comfortaa', font=('Comfortaa', 14), padx=10, pady=5)
file_name.pack(pady=10)
for f in all_fonts:
    if f=='Comfortaa':
        print(f)
"""app = ctk.CTk()
app.geometry('900x900')
table_frame = ctk.CTkFrame(app)
table_frame.pack(pady=10)
i = 0
j = 0
for f in all_fonts:
    file_name = ctk.CTkLabel(table_frame, text=f, font=(f, 14), padx=10, pady=5)
    file_name.grid(row=i + 1, column=j, sticky='w')
    i+=1
    if i==25:
        i=0
        j+=1
app.mainloop()"""

app.mainloop()

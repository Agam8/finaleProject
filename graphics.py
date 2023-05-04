import customtkinter as ctk
app = ctk.CTk()
app.geometry('900x900')
progress_bar = ctk.CTkProgressBar(app,determinate_speed=0.2)
progress_bar.place(relx=0.4, rely=0.6)
progress_bar.start()
app.mainloop()
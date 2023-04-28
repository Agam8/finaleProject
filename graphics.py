import customtkinter as ctk

class App(ctk.CTk):
    def __init__(self):
        ctk.set_appearance_mode("dark")
        ctk.CTk.__init__(self)
        # self.attributes('-fullscreen', True)
        self.geometry('1000x1000')
        self._frame = None
        self.switch_frame(LoginOrSignUp)

    def switch_frame(self, frame_class):
        new_frame = frame_class(self)
        if self._frame is not None:
            self._frame.destroy()
        self._frame = new_frame
        print('new frame: ',self._frame)

    def get_username(self):
        pass

class LoginOrSignUp(ctk.CTkFrame):
    def __init__(self, master):
        self.master=master
        ctk.CTkFrame.__init__(self, master)
        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)

        #self.cli_s = master.cli_s
        signed = True
        title_label = ctk.CTkLabel(self, text='Welcome!', font=('Arial', 18))
        title_label.pack(pady=10)

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12),command=lambda: self.master.switch_frame(Login))
        login_button.pack(pady=10)

        signup_button = ctk.CTkButton(self, text='Sign up', font=('Arial', 12),command=lambda: self.master.switch_frame(Signup))
        signup_button.pack(pady=10)


class Signup(ctk.CTkFrame):
    def __init__(self, master):
        print('got to signup frame')
        ctk.CTkFrame.__init__(self, master)
        self.logged = False
        self.signed = False
        self.username = ''
        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Signup', font=('Arial', 18),text_color='#6DC868')
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=('Arial', 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=('Arial', 12), )
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=('Arial', 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='signup', font=('Arial', 12), command=self.signup)
        login_button.pack(pady=10)
    def signup(self):
        print('got to login')

class Login(ctk.CTkFrame):
    def __init__(self, master):
        print('got to login frame')
        ctk.CTkFrame.__init__(self, master)
        self.logged = False
        self.signed = False
        self.username = ''
        self.place(anchor='center',relx=0.5,rely=0.5,relheight=0.95,relwidth=0.95)
        title_label = ctk.CTkLabel(self, text='Login', font=('Arial', 18),text_color='#6DC868')
        title_label.pack(pady=10)

        username_label = ctk.CTkLabel(self, text='Username:', font=('Arial', 12))
        username_label.pack(pady=5)

        self.username_entry = ctk.CTkEntry(self, font=('Arial', 12))
        self.username_entry.pack(pady=5)

        password_label = ctk.CTkLabel(self, text='Password:', font=('Arial', 12), )
        password_label.pack(pady=5)

        self.password_entry = ctk.CTkEntry(self, show='*', font=('Arial', 12))
        self.password_entry.pack(pady=5)

        login_button = ctk.CTkButton(self, text='Login', font=('Arial', 12), command=self.login)
        login_button.pack(pady=10)
    def login(self):
        print('got to login')
app = App()
app.mainloop()
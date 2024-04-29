class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

    def check_password(self, password):
        return self.password == password

    def check_user(self, username):
        return self.username == username


def create_user_from_json(json_data):
    username = json_data.get("username")
    password = json_data.get("password")
    if username and password:
        return User(username, password)
    else:
        raise ValueError("Username and password are required")

from flask_login import UserMixin
from flask import url_for


class UserLogin(UserMixin):
    def create(self, user):
        self.__user = user
        return self

    def get_id(self):
        return str(self.__user['id'])

    def getName(self):
        return self.__user['name'] if self.__user else "Без имени"


    def getAvatar(self, app):
        img = None
        if not self.__user['avatar']:
            with app.open_resource(app.root_path + url_for('static', filename='avatars/default.png'), "rb") as file:
                img = file.read()
        else:
            img = self.__user['avatar']

        return img

    def verify_image(self, filename):
        ext = filename.rsplit('.', 1)[1]
        if ext == "png" or ext == "PNG":
            return True
        else:
            return False

import sqlite3 as sql
from flask_login import UserMixin
from flask import url_for
from random import randint
from os.path import exists



def get(cur):
    try:
        return str(cur.fetchone()[0])
    except TypeError:
        return ''


def get_user(name):
    connector = sql.connect('databases/users.db')
    cursor = connector.cursor()
    returned = get(cursor.execute(f'''SELECT id FROM users WHERE nickname = "{name}"'''))
    if returned: return returned


def collect_articles():
    connector = sql.connect('databases/content.db')
    cursor = connector.cursor()
    return [i[0] for i in cursor.execute(f'''SELECT id FROM articles''').fetchall()]



class Page:
    pass


class Meta:
    def __init__(self, meta_string=None):
        self.title = None
        self.datetime = None
        self.author = None
        self.tags = None
        self.access = None

        if meta_string:
            self.load(meta_string)

    def __str__(self):
        return f'{self.title};{self.datetime};{self.author};{",".join(self.tags)};{self.access}'

    def load(self, meta_string):
        separated = meta_string.split(';')
        self.title = separated[0]
        self.datetime = separated[1]
        self.author = separated[2]
        self.tags = separated[3].split(',')
        self.access = separated[4]


class Img_Meta:
    def __init__(self, title, description, datetime, author, tags, access):
        self.title = title
        self.description = description
        self.datetime = datetime
        self.author = author
        self.tags = tags
        self.access = access


class Article:
    def __init__(self, article_id=None):
        self.id = str()
        self.page_content = str()
        self.meta = Meta()
        self.commends = list()
        self.comments = list()

        if article_id:
            self.id = article_id
            self.load(self.id)

    def __str__(self):
        return f'''
                meta: {self.meta}
                commends: {self.commends}
                comments: {self.comments}
                content: {self.page_content}
                '''

    def load(self, article_id):
        connector = sql.connect('databases/content.db')
        cursor = connector.cursor()

        self.id = article_id
        self.page_content = get(cursor.execute(f'''SELECT [text-content] FROM articles WHERE id = {article_id}'''))
        self.meta = Meta(get(cursor.execute(f'''SELECT meta FROM articles WHERE id = {article_id}''')))
        for commend in get(cursor.execute(f'''SELECT commends FROM articles WHERE id = {article_id}''')).split(','):
            if commend != 'None' and commend:
                commend_connector = sql.connect('databases/reactions.db')
                commend_cursor = commend_connector.cursor()
                author_connector = sql.connect('databases/users.db')
                author_cursor = author_connector.cursor()
                if exists(f"static/avatars/{get(commend_cursor.execute(f'''SELECT author FROM commends WHERE id = {commend}'''))}.png"):
                    author_avatar_id = f"avatars/{get(commend_cursor.execute(f'''SELECT author FROM commends WHERE id = {commend}'''))}.png"
                else:
                    author_avatar_id = f"avatars/default.png"
                author_id = get(commend_cursor.execute(f'''SELECT author FROM commends WHERE id = {commend}'''))
                author_name = get(author_cursor.execute(f'''SELECT nickname FROM users WHERE id = {author_id}'''))
                self.commends.append((author_id, author_name, author_avatar_id, commend))
                commend_connector.close()
                author_connector.close()
        for comment in get(cursor.execute(f'''SELECT comments FROM articles WHERE id = {article_id}''')).split(','):
            if comment != 'None' and comment:
                comment_connector = sql.connect('databases/reactions.db')
                comment_cursor = comment_connector.cursor()
                author_connector = sql.connect('databases/users.db')
                author_cursor = author_connector.cursor()
                if exists(f"static/avatars/{get(comment_cursor.execute(f'''SELECT author FROM comments WHERE id = {comment}'''))}.png"):
                    author_avatar_id = f"avatars/{get(comment_cursor.execute(f'''SELECT author FROM comments WHERE id = {comment}'''))}.png"
                else:
                    author_avatar_id = f"avatars/default.png"
                author_id = get(comment_cursor.execute(f'''SELECT author FROM comments WHERE id = {comment}'''))
                author_name = get(author_cursor.execute(f'''SELECT nickname FROM users WHERE id = {author_id}'''))
                comment_content = get(comment_cursor.execute(f'''SELECT content FROM comments WHERE id = {comment}'''))
                comment_connector.close()
                author_connector.close()
                self.comments.append((author_id, author_name, comment_content, author_avatar_id, comment))


    def edit(self):
        article_connector = sql.connect('databases/content.db')
        article_cursor = article_connector.cursor()
        article_cursor.execute(
            f'''UPDATE articles SET meta = "{self.meta}", commends = "{','.join([i[3] for i in self.commends])}",comments = "{','.join([i[4] for i in self.comments])}" WHERE id = {self.id}''')
        article_connector.commit()
        return 'Успех'

    def add_comment(self, author, content):
        comment_connector = sql.connect('databases/reactions.db')
        comment_cursor = comment_connector.cursor()
        author_connector = sql.connect('databases/users.db')
        author_cursor = author_connector.cursor()
        author_avatar_id = f"avatars/{author}.png"
        author_id = author
        author_name = get(author_cursor.execute(f'''SELECT nickname FROM users WHERE id = {author_id}'''))
        comment_content = content
        key = randint(0, 10**10)
        comment_cursor.execute(f'''INSERT INTO comments (content, author, ext_key) VALUES ("{comment_content}", "{author}", {key})''')
        comment_connector.commit()
        self.comments.append((author_id, author_name, comment_content, author_avatar_id, get(comment_cursor.execute(f'''SELECT id FROM comments WHERE ext_key = {key}'''))))
        comment_connector.close()
        author_connector.close()
        self.edit()

    def upload(self):
        connector = sql.connect('databases/content.db')
        cursor = connector.cursor()
        cursor.execute(f'''INSERT INTO articles (meta, [text-content]) VALUES ("{self.meta}", "{self.page_content}")''')
        connector.commit()

class User:
    def __init__(self, user_id=None):
        self.name = str()
        self.access_level = str()
        self.commends = list()
        self.messages = list()
        self.password = str()
        self.id = None

        if user_id != 'None' and user_id:
            self.id = user_id
            self.load(self.id)

    def __bool__(self):
        return bool(self.id) and self.id != 'None'

    def __getitem__(self, item):
        results = {
            'id': self.id,
            'name': self.name,
            'access': self.access_level,
            'commends': self.commends,
            'messages': self.messages,
            'password': self.password,
            'avatar': f"avatars/{self.id}.png"
        }
        return results[item]

    def load(self, user_id):
        user_connector = sql.connect('databases/users.db')
        commends_connector = sql.connect('databases/reactions.db')
        user_cursor = user_connector.cursor()
        reaction_cursor = commends_connector.cursor()

        self.name = get(user_cursor.execute(f'''SELECT nickname FROM users WHERE id = {user_id}'''))
        self.password = get(user_cursor.execute(f'''SELECT password FROM users WHERE id = {user_id}'''))
        self.access_level = get(user_cursor.execute(f'''SELECT access FROM users WHERE id = {user_id}'''))
        self.commends.clear()
        commends_list = get(user_cursor.execute(f'''SELECT commends FROM users WHERE id = {user_id}''')).split(',')
        messages_list = get(user_cursor.execute(f'''SELECT messages FROM users WHERE id = {user_id}''')).split(',')
        if commends_list[0] != 'None':
            for commend in commends_list:
                author_avatar_id = f"avatars/{get(reaction_cursor.execute(f'''SELECT author FROM commends WHERE id = {commend}'''))}.png"
                author_id = get(reaction_cursor.execute(f'''SELECT author FROM commends WHERE id = {commend}'''))
                author_name = get(user_cursor.execute(f'''SELECT nickname FROM users WHERE id = {author_id}'''))
                self.commends.append((author_id, author_name, author_avatar_id, commend))
        if messages_list[0] != 'None':
            for message in messages_list:
                meta = get(reaction_cursor.execute(f'''SELECT meta FROM messages WHERE id = {message}'''))
                content = get(reaction_cursor.execute(f'''SELECT content FROM messages WHERE id = {message}'''))
                self.messages.append((meta, content, message))

        return self

    def save(self):
        user_connector = sql.connect('databases/users.db')
        user_cursor = user_connector.cursor()
        if get(user_cursor.execute(f'''SELECT nickname FROM users WHERE nickname = "{self.name}"''')):
            return 'Никнейм занят'
        else:
            user_cursor.execute(f'''INSERT INTO users (nickname, access, password) VALUES ("{self.name}", "{self.access_level}", "{self.password}")''')
            user_connector.commit()
            return 'Успех'

    def edit(self):
        user_connector = sql.connect('databases/users.db')
        user_cursor = user_connector.cursor()
        user_cursor.execute(
            f'''UPDATE users SET nickname = "{self.name}", access = "{self.access_level}", commends = "{','.join([i[3] for i in self.commends])}", messages =  "{','.join([i[2] for i in self.messages])}" WHERE id = {self.id}''')
        user_connector.commit()
        return 'Успех'


class UserLogin(UserMixin):
    def get(self, user_id, db):
        self.__user = db.load(user_id)
        return self

    def create(self, user_obj):
        self.__user = user_obj
        return self

    def is_authenticated(self): return True
    def is_active(self): return True
    def is_anonymous(self): return False
    def get_id(self): return str(self.__user['id'])


collect_articles()

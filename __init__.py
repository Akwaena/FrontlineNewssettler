import re

from flask import Flask, render_template, url_for, flash, redirect, request, make_response, g
import datetime
import dynamic_set

# import os

app = Flask(__name__)
app.config['DEBUG'] = True
SECRET_KEY = 'f1267efdquwytfdo6823'
app.config['SECRET_KEY'] = SECRET_KEY


def get_auth():
    if request.cookies.get('auth'):
        return {
            'id': request.cookies.get('auth').split('#|#')[0],
            'name': request.cookies.get('auth').split('#|#')[1],
            'pass': request.cookies.get('auth').split('#|#')[2],
            'access': request.cookies.get('auth').split('#|#')[3]
        }
    else:
        return False


def is_auth(): return bool(get_auth())


def is_journo():
    if is_auth():
        return get_auth()['access'] == 'full' or get_auth()['access'] == 'reporter_w' or get_auth()[
            'access'] == 'reporter_c'


@app.route('/')
def index():
    return render_template('index.html', title='Главная страница', is_auth=is_auth(), is_journo=is_journo())


@app.route('/issues')
def issues():
    articles = [dynamic_set.Article(i) for i in dynamic_set.collect_articles()]
    return render_template('issues.html', title='Выпуски', articles=articles, issues_num=len(articles))


@app.route('/post', methods=['POST', 'GET'])
def post():
    if is_journo():
        if request.method == 'POST':
            article_obj = dynamic_set.Article()
            article_obj.meta.title = request.form['name']
            article_obj.meta.datetime = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            article_obj.meta.author = get_auth()['name']
            article_obj.meta.access = request.form['access']
            # article_obj.meta.tags = request.form['tags'].split(',')
            article_obj.meta.tags = ['placeholder1', 'placeholder2', 'placeholder3']
            article_obj.page_content = request.form['content']
            article_obj.upload()
            return redirect(url_for('issues'))

        return render_template('post.html', title='Публикация')
    else:
        return redirect(url_for('index'))


@app.route('/credits')
def credits():
    return render_template('credits.html', title='Выпуски')


@app.route('/articles/<article_id>', methods=('POST', 'GET'))
def article(article_id):
    article_obj = dynamic_set.Article()
    article_obj.load(article_id)
    base = url_for('static', filename='img')

    text = re.sub(r"(?P<tag><img\s+[^>]*src=)(?P<quote>[\"'])(?P<url>.+?)(?P=quote)>", "\\g<tag>" + base + "/\\g<url>>",
                  article_obj.page_content)

    if request.method == 'POST':
        article_obj.add_comment(get_auth()['id'], request.form['comment_content'])
        return redirect(url_for('article', article_id=article_id))

    return render_template('article.html', article_id=article_id, title=article_obj.meta.title,
                           date=article_obj.meta.datetime, author=article_obj.meta.author,
                           comments=article_obj.comments, commends=len(article_obj.commends),
                           comments_number=len(article_obj.comments), article=text, is_auth=is_auth())


@app.route('/articles/<article_id>/commends')
def commends(article_id):
    article_obj = dynamic_set.Article()
    article_obj.load(article_id)
    return render_template('commends.html', title=article_obj.meta.title, date=article_obj.meta.datetime,
                           author=article_obj.meta.author, commends=len(article_obj.commends),
                           commends_list=article_obj.commends)


@app.route('/user/<user_id>')
def user(user_id):
    user_obj = dynamic_set.User(user_id)
    user_obj.load(user_id)
    localize_n_color = {
        'non-authorized': ('Не авторизован', '#696969'),
        'neutral': ('Нейтрал', '#2F4F4F'),
        'colonial': ('Мезеец', '#808000'),
        'warden': ('Варден', '#000080'),
        'reporter_w': ('Репортер', '#0000FF'),
        'reporter_c': ('Репортер', '#008000'),
        'full': ('Администратор', '#800000')
    }
    user_avatar_id = f'avatars/{user_obj.id}.png'
    return render_template('user.html', user_id=user_id, title=user_obj.name, commends=len(user_obj.commends),
                           localized_access=localize_n_color[user_obj.access_level][0],
                           color=localize_n_color[user_obj.access_level][1], user_avatar_id=user_avatar_id)


@app.route('/user/<user_id>/commends')
def user_commends(user_id):
    user_obj = dynamic_set.User(user_id)
    return render_template('user_commends.html', title=user_obj.name, commends=len(user_obj.commends),
                           commends_list=user_obj.commends)


@app.route('/sign_up', methods=('POST', 'GET'))
def sign_up():
    if request.method == 'POST':
        if 4 < len(request.form['name']) < 16 and 4 < len(request.form['pass']) < 16:
            returned = dynamic_set.User()
            returned.name = request.form['name']
            returned.access_level = 'non-authorized'
            returned.password = request.form['pass']
            flash(returned.save())
            return redirect(url_for('sign_in'))
        else:
            flash('Имя и пароль должны состоять из не большего количества символов, чем 16 и не меньшего чем 4')

    return render_template('authorization.html', title='Регистрация')


@app.route('/sign_in', methods=('POST', 'GET'))
def sign_in():
    if request.method == 'POST':
        user_obj = dynamic_set.User(user_id=dynamic_set.get_user(request.form['name']))
        if user_obj:
            if user_obj.password == request.form['pass']:
                res = make_response(redirect(url_for('index')))
                res.set_cookie('auth',
                               f'{user_obj["id"]}#|#{user_obj["name"]}#|#{user_obj["password"]}#|#{user_obj["access"]}',
                               max_age=60 * 60 * 24 * 365)
                return res
            else:
                flash('Неверный пароль')
        else:
            flash('Пользователь не найден!')
    return render_template('authorization.html', title='Вход')

@app.route('/sign_out')
def sign_out():
    returned = make_response(redirect(url_for('index')))
    returned.set_cookie('auth', 'None', max_age=0)
    return returned


if __name__ == '__main__':
    app.run(debug=True)

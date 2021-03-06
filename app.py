from flask import Flask, render_template, request, session, redirect, url_for, flash
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "graduathion"


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/alllink')
def all_link():
    return render_template('alllink.html')

# 記事詳細ページの記事呼び出し

# ちょっといじりました  0624寺尾


@app.route('/main/<int:pageid>')
def main(pageid):
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()
    # pageidでタイトル情報の呼び出し
    c.execute(
        "select title, prefectures, month, date, period from page where ID=?", (pageid,))
    page = c.fetchone()
    # pageidで記事情報の呼び出し
    c.execute(
        "select image, content, datetime,id from post where flag=0 and pageID=?", (pageid,))
    story = []
    for row in c.fetchall():
        story.append(
            {"image": row[0], "content": row[1], "datetime": row[2], "id": row[3]})
    # ページ情報の都道府県Noを日本語に変換
    c.execute("select prefectures from page where ID=?", (pageid,))
    areas = c.fetchone()

    c.execute("select area from Prefecture where No=?", (areas))
    area = c.fetchone()

    c.close()

    print(pageid)
    print(page)
    print(story)
    print(area)
    return render_template('main.html', pageid=pageid, page=page, story=story, area=area)

# マイページのユーザー情報・記事一覧表示


@app.route('/mypage')
def mypage():
    if "user_id" in session:
        # sessionからuser_idを取得
        user_id = session["user_id"]
        conn = sqlite3.connect('flaskapp.db')
        c = conn.cursor()
    # usersのid＝[user_id]で呼び出し
        c.execute("select name, adress, pass from users where id=?", (user_id,))
        user_info = c.fetchone()
    # page のUserID=[user_id]で呼び出し
        c.execute(
            "select prefectures, month, date, title, id, editPASS from page where flag=0 and UserID=?", (user_id,))
        page = []
        for row in c.fetchall():
            page.append({"area": row[0], "month": row[1],
                         "date": row[2], "title": row[3], "pageid": row[4], "editPASS": row[5]}) #ページ編集パスも呼んでくる
        c.close()

        print(user_info)
        print(page)
        print(user_id)
        return render_template('mypage.html', page=page, user_info=user_info)
    else:
        return redirect("/login")

# 記事一覧ページ  都道府県指定


@app.route('/thread/<int:areaid>', methods=["GET"])
def thread(areaid):
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()
    # areaidで都道府県のひらがな表示を呼んでくる
    c.execute("select area from Prefecture where No=?", (areaid,))
    area = c.fetchone()
    # areaidで表示記事を絞り込む
    c.execute(
        "select prefectures, month, date, title, id from page where flag=0 and prefectures=?", (areaid,))
    page = []
    for row in c.fetchall():
        page.append({"area": row[0], "month": row[1],
                     "date": row[2], "title": row[3], "pageid": row[4]})
    c.close()
    print(area)
    print(page)
    return render_template('thread.html', page=page, area=area)


# アカウント作成ページ
@app.route('/new')
def new():
    return render_template('new.html')


@app.route("/register", methods=["POST"])  # ユーザー情報をDBに追加する
def useraddpost():
    name = request.form.get("name")
    adress = request.form.get("adress")
    password = request.form.get("password")
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()

    error_message = None
    if not name:
        error_message = 'ユーザー名の入力は必須です'
    elif not adress:
        error_message = 'アドレスの入力は必須です'
    elif not password:
        error_message = 'パスワードの入力は必須です'
    elif c.execute('SELECT id FROM users WHERE name = ?', (adress,)).fetchone() is not None:
        error_message = 'そのアドレスはすでに使用されているため別のアドレスご入力ください'

    if error_message is not None:
        # エラーがあれば、それを画面に表示させる
        flash(error_message, category='alert alert-danger')
        return redirect('/new')
    else:
        c.execute("insert into users values (null,?,?,?)",
                  (name, adress, password))
        conn.commit()
        c.close()
        # ページ作成ページへ飛ばす
        return redirect("/pageadd")


@ app.route("/login")  # ログインページの表示
def login_get():
    return render_template("login.html")


@ app.route("/login", methods=["POST"])  # ログインページの機能実装
def login_post():
    adress = request.form.get("adress")
    password = request.form.get("password")
    conn = sqlite3.connect("flaskapp.db")
    c = conn.cursor()

    c.execute("select id from users where adress = ? and pass = ?",
              (adress, password))
    user_id = c.fetchone()
    c.close()

    error_message = " "
    # ログインできなかった場合どこに飛ばしましょうか？
    if user_id is None:
        error_message = 'ユーザー名またはパスワードが正しくありません'
        flash(error_message, category='alert alert-danger')
        return redirect('/login')
    # ログインできた場合は新規作成ページに飛ばす
    else:
        session.clear()
        session["user_id"] = user_id[0]
        return redirect("/pageadd")


@app.route("/deletepage/<int:pageid>")  # ページ削除 1が削除
def deletepage(pageid):
    conn = sqlite3.connect("flaskapp.db")
    c = conn.cursor()
    c.execute("update page set flag = 1 where id = ?", (pageid,))
    conn.commit()
    conn.close()
    return redirect("/mypage")


@app.route("/deletepost/<int:postid>")  # 投稿削除 1が削除
def deletepost(postid):
    conn = sqlite3.connect("flaskapp.db")
    c = conn.cursor()
    c.execute("SELECT pageid from post where id = ?", (postid,))
    pageid = c.fetchone()
    pageid = pageid[0]
    c.execute("update post set flag = 1 where ID = ?", (postid,))
    conn.commit()
    print(pageid)
    conn.close()
    return redirect(url_for('main', pageid=pageid))


@app.route("/pageadd")  # 記事作成の画面を表示
def pageadd_get():
    if "user_id" in session:
        return render_template("pageadd.html")
    else:
        return redirect("/login")


@app.route("/pageadd", methods=["POST"])  # 記事のデータを登録
def pageadd_post():
    user_id = session["user_id"]
    title = request.form.get("title")
    month = request.form.get("month")
    date = request.form.get("date")
    month = request.form.get("month")
    period = request.form.get("period")
    prefecture = request.form.get("prefecture")
    editpass = request.form.get("editpass")
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()
    c.execute("insert into page values(null,?,?,?,?,?,?,0,?)",
              (user_id, editpass, title, prefecture, month, date, period))
    conn.commit()
    # つくった記事詳細ページへ飛ばすだめに作成した記事IDを取得
    c.execute("SELECT ID from page where userID = ? and title = ?",
              (user_id, title))
    id = c.fetchone()
    id = id[0]
    conn.close()
    print(id)
    return redirect(url_for('main', pageid=id))  # 記事詳細へ変更


@app.route("/postadd/<int:pageid>")  # 記事作成の画面を表示
def postadd_get(pageid):
    if "user_id" in session:
        return render_template("postadd.html", pageid=pageid)
    else:
        return redirect("/login")


@app.route('/postadd/<int:pageid>', methods=["POST"])
def postadd_post(pageid):
    upload = request.files['image']
    # uploadで取得したファイル名をlower()で全部小文字にして、ファイルの最後尾の拡張子が'.png', '.jpg', '.jpeg'ではない場合、returnさせる。
    if not upload.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        return 'png,jpg,jpeg形式のファイルを選択してください'

    # 下の def get_save_path()関数を使用して "./static/img/" パスを戻り値として取得する。
    save_path = get_save_path()
    # ファイルネームをfilename変数に代入
    filename = upload.filename
    # 画像ファイルを./static/imgフォルダに保存。 os.path.join()は、パスとファイル名をつないで返してくれます。
    upload.save(os.path.join(save_path, filename))
    # ファイル名が取れることを確認、あとで使うよ
    print(filename)
    # コンテンツ取得
    content = request.form.get("content")
    # 投稿時間を取得
    posttime = datetime.now().strftime("%Y/%m/%d %H:%m")
    print(posttime)
    # パスを取得
    editpass = request.form.get("editpass")
    # DB内にある編集パスを取得
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()
    c.execute("SELECT editPASS from page where ID = ?", (pageid,))
    page_editpass = c.fetchone()
    page_editpass = page_editpass[0]
    print(editpass)
    print(page_editpass)

    # 入力したパスと登録されたパスがk異なる場合
    if editpass != page_editpass:
        return "passが間違っております"
    else:
        conn = sqlite3.connect('flaskapp.db')
        c = conn.cursor()
        c.execute("insert into post values(null,?,?,?,?,0)",
                  (pageid, filename, content, posttime))
        conn.commit()
        conn.close()
        return redirect(url_for('main', pageid=pageid))

# 画像の保存場所をstaticsのimg


def get_save_path():
    path_dir = "./static/img"
    return path_dir

# 編集ページの表示


@app.route("/edit/<int:pageid>")
def edit(pageid):
    if "user_id" in session:
        conn = sqlite3.connect("flaskapp.db")
        c = conn.cursor()
        c.execute(
            "select title,prefectures,month,date,period from page where id = ?", (pageid,))
        page = c.fetchone()  # タプル型で取得している
        c.close()

    # タスクが取得できない場合の例外処理
        return render_template("pageedit.html", pageid=pageid, page=page)
    else:
        return redirect("/login")


@app.route("/edit", methods=["POST"])
def update_task():
    user_id = session["user_id"]
    title = request.form.get("title")
    month = request.form.get("month")
    date = request.form.get("date")
    month = request.form.get("month")
    period = request.form.get("period")
    prefecture = request.form.get("prefecture")
    editpass = request.form.get("editpass")
    conn = sqlite3.connect('flaskapp.db')
    c = conn.cursor()
    c.execute("update page set title=?,prefectures=?,month=?,date=?,period=?.editpass=? where = id",
              (title, prefecture, month, date, period, editpass, user_id))
    conn.commit()
    # つくった記事詳細ページへ飛ばすだめに作成した記事IDを取得
    c.execute("SELECT ID from page where userID = ? and title = ?",
              (user_id, title))
    id = c.fetchone()
    id = id[0]
    conn.close()
    print(id)
    return redirect(url_for('main', pageid=id))


@app.route("/editmypage")
def editmypage():
    if "user_id" in session:
        # sessionからuser_idを取得
        user_id = session["user_id"]
        conn = sqlite3.connect('flaskapp.db')
        c = conn.cursor()
    # usersのid＝[user_id]で呼び出し
        c.execute("select name, adress, pass from users where id=?", (user_id,))
        user_info = c.fetchone()
        c.close()
        return render_template('mypage.html', user_info=user_info)

    else:
        return redirect("/login")


@app.route('/top')
def top():
    return render_template('top.html')


@app.route('/second')
def second():
    return render_template('second.html')


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect("/login")


@app.errorhandler(404)
def notfound(code):
    return "404.エラーです。TOPに戻りましょう"


if __name__ == "__main__":
    app.run(debug=True)

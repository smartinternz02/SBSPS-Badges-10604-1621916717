# -*- coding: utf-8 -*-
"""
Created on Mon May 10 20:32:50 2021

@author: Tejaswi
"""
from flask import Flask, render_template, request, session
from flask_mysqldb import MySQL
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import hashlib
import requests
import datetime
import config

app = Flask(__name__)
app.config['MYSQL_HOST'] = 'remotemysql.com'
app.config['MYSQL_USER'] = config.ak1
app.config['MYSQL_PASSWORD'] = config.ak2
app.config['MYSQL_DB'] = config.ak1
mysql = MySQL(app)
app.secret_key = 'a'


def sendgridmail(user, TEXT, sub):
    sg = sendgrid.SendGridAPIClient(config.ak3)
    # Change to your verified sender
    from_email = Email("tejpatna@gmail.com")
    to_email = To(user)  # Change to your recipient
    subject = sub
    content = Content("text/plain", TEXT)
    mail = Mail(from_email, to_email, subject, content)

    # Get a JSON-ready representation of the Mail object
    mail_json = mail.get()
    # Send an HTTP POST request to /mail/send
    response = sg.client.mail.send.post(request_body=mail_json)


@app.route('/', methods=['GET', 'POST'])
def homer():
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def supd1():
    if request.method == 'POST':
        email = request.form['eid']
        name = request.form['name']
        pass1 = request.form['pass1']
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT email FROM per WHERE email = %s', (email,))
        acc = cursor.fetchone()
        if acc != None:
            return render_template('index.html', t1="ACCOUNT Already Exists")
        currentKey = hashlib.sha1(email.encode())
        cusid = "CUS"+str(currentKey.hexdigest())[:7]
        cursor.execute('INSERT INTO per VALUES (% s, % s, % s, %s)',
                       (cusid, name, email, pass1))
        mysql.connection.commit()
        tex = "Hi "+name+",\n Thank you for registering with us. You can now proceed and sign in to set your default budget and explore many more functionality of our expense tracker."
        sub = "Registered Successfully!"
        sendgridmail(email, tex, sub)
    return render_template('index.html', t1="Registered Succesfully, Now Sign in to access your account!")


@app.route('/login', methods=['GET', 'POST'])
def supd2():
    if request.method == 'POST':
        email = request.form['sid']
        pass1 = request.form['pass2']
        session['useremail'] = email
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT password,cusid,name FROM per WHERE email = %s', (email,))
        acc = cursor.fetchone()
        if acc != None:
            account = acc[0]
            session['userid'] = acc[1]
            session['username'] = acc[2]
            if pass1 == account:
                return render_template('dashboard.html', us=acc[2])
        return render_template('index.html', t2="Account not found")


@app.route('/news', methods=['GET', 'POST'])
def news():
    response = requests.get(
        "https://newsapi.org/v2/top-headlines?country=in&category=business&apiKey=fe4edc17e1024626a198b950a65437d7")
    news = response.json()
    return render_template('news.html', news=news['articles'])


@app.route('/set', methods=['GET', 'POST'])
def set1():
    return render_template('set.html')


@app.route('/setvalue', methods=['GET', 'POST'])
def set2():
    if request.method == 'POST':
        lim1 = request.form['lim1']
        lim2 = request.form['lim2']
        cursor = mysql.connection.cursor()
        xid = session['userid']
        if lim1 == "" and lim2 == "":
            return render_template('set.html', er="No amount selected!")
        if lim1 != "":
            cursor.execute(
                'SELECT * FROM transaction WHERE cusid = %s', (xid,))
            x = cursor.fetchone()
            if x != None:
                cursor.execute(
                    'update transaction set deflim=%s WHERE cusid = %s', (lim1, xid,))
                mysql.connection.commit()
                cursor.execute(
                    'update transaction set lim=%s WHERE cusid = %s', (lim1, xid,))
                mysql.connection.commit()
            else:
                now = datetime.datetime.now()
                formatted_date = now.strftime('%Y-%m-%d')
                cursor.execute('INSERT INTO transaction VALUES (% s, % s, % s, %s, %s, %s)',
                               (xid, 'limit update', '-1', lim1, formatted_date, lim1))
                mysql.connection.commit()
        elif lim2 != "":
            now = datetime.datetime.now()
            formatted_date = now.strftime('%Y-%m-%d')
            cursor.execute('INSERT INTO transaction VALUES (% s, % s, % s, %s, %s,%s)',
                           (xid, 'limit update', '-1', lim2, formatted_date, lim2))
            mysql.connection.commit()

    return render_template('set.html', er="Limit set!")


@app.route('/add', methods=['GET', 'POST'])
def add1():
    return render_template('add.html')


@app.route('/added', methods=['GET', 'POST'])
def add2():
    if request.method == 'POST':
        exp = request.form['amt']
        date = request.form['date']
        name = request.form['exp']
        xid = session['userid']
        now = datetime.datetime.strptime(date, '%Y-%m-%d')
        formatted_date = now.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT lim,deflim FROM transaction WHERE cusid = %s and expense= %s order by date desc', (xid, str(-1),))
        x = cursor.fetchone()
        if x != None:
            d1 = x[0]
            d2 = x[1]
            cursor.execute('INSERT INTO transaction VALUES (% s, % s, % s, %s, %s,%s)',
                           (xid, name, exp, d1, formatted_date, d2))
            mysql.connection.commit()
        else:
            return render_template('add.html', er="First set the limit!")
        cursor.execute(
            'SELECT expense FROM transaction WHERE cusid = %s and expense!= %s order by date desc', (xid, str(-1),))
        x = cursor.fetchall()
        e = 0
        for i in x:
            e += int(i[0])
        if e > int(d1):
            tex = "Your expense for the month has exceeded its limit! Please check your account."
            sub = "Limit exceeded!"
            sendgridmail(session['useremail'], tex, sub)
        return render_template('add.html', er="Expense added!")


@app.route('/check', methods=['GET', 'POST'])
def check1():
    return render_template('check.html')


@app.route('/checked', methods=['GET', 'POST'])
def check2():
    if request.method == 'POST':
        date1 = request.form['date1']
        date2 = request.form['date2']
        xid = session['userid']
        now1 = datetime.datetime.strptime(date1, '%Y-%m-%d')
        formatted_date1 = now1.strftime('%Y-%m-%d')
        now2 = datetime.datetime.strptime(date2, '%Y-%m-%d')
        formatted_date2 = now2.strftime('%Y-%m-%d')
        cursor = mysql.connection.cursor()
        cursor.execute(
            'SELECT name,expense,date FROM transaction WHERE cusid = %s and expense!= %s and date between %s and %s order by date asc', (xid, str(-1), formatted_date1, formatted_date2,))
        x = cursor.fetchall()
        if x != None:
            t = 0
            for i in x:
                t += int(i[1])
            f = "Total Expense: "+str(t)
            return render_template('check.html', news=x, total=f)
        else:
            return render_template('check.html', er="no data found")


@app.route('/change', methods=['GET', 'POST'])
def pass1():
    return render_template('change.html')


@app.route('/changed', methods=['GET', 'POST'])
def pass2():
    if request.method == 'POST':
        xid = session['userid']
        current = request.form['psw']
        npsw = request.form['npsw']
        cpsw = request.form['cpsw']
        if cpsw != npsw:
            return render_template('change.html', er="New password and Confirm password are not the same")
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT password FROM per WHERE cusid = %s', (xid,))
        acc = cursor.fetchone()
        if acc != None:
            account = acc[0]
            if current != account:
                return render_template('change.html', er="Current password is not right")
        cursor.execute(
            'Update per set password=%s WHERE cusid = %s', (npsw, xid,))
        mysql.connection.commit()
        return render_template('change.html', er="Password Updated!")


if __name__ == '__main__':
    app.run(host='0.0.0.0', port="8080")

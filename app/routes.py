from flask import Flask, render_template, flash, redirect, url_for, request, g
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from app import app, db, secrets
from app.auth.forms import LoginForm, RegistrationForm
from app.forms import LanguageForm, LoginForm, GetLanguage
from app.ticket.forms import TicketForm
from app.models import User
from app import secrets
import requests
bearer_token = secrets.bearer_token

# sanitize form inputs
#flask-user implementation
from flask_user import roles_required

# #flask-security & flask-principal implementation
# from flask_security import roles_required
# from flask_principal import Principal, Permission, RoleNeed
#
# # Create a permission with a single Need, in this case a RoleNeed.
# admin_permission = Permission(RoleNeed('admin'))

@app.route('/')
@app.route('/index')
@login_required
def index():
    return render_template('index.html', title='Home')

@app.route('/ticket', methods=['GET', 'POST'])
#@login_required
def ticket():
    form = TicketForm()
    if form.validate_on_submit():
        options = form.options.data
        category = form.category.data
        details = form.details.data

        flash('Your ticket has been submitted.')
        return redirect(url_for('index'))
    return render_template('ticket.html', title='Ticket', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password', 'error')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        # Tell Flask-Principal the identity changed
        # identity_changed.send(current_app._get_current_object(), identity=Identity(user.id))
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index', user_data= current_user)
        return redirect(next_page)
    return render_template('login.html', title='Sign In', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

# @app.route('/admin')
@app.route('/submissions')
@login_required
@roles_required('admin')
# @admin_permission.require() #flask-security & flask-principal implementation
def submissions():
    return render_template('submissions.html', title='Submissions')


@app.route('/api/')
def apipage():
    clusterForm = LanguageForm()
    getLangForm = GetLanguage()
    return render_template("apicall.html", get_language="", text_cluster="", getlangform=getLangForm,
                           clusterform=clusterForm)

bearer_token = secrets.bearer_token

value = ""
text_cluster = ""


@app.route('/api/languagecheck', methods=["GET", "POST"])
def getLanguage():
    url = "https://ug-api.acnapiv3.io/swivel/language-identification/lang-2.0?of=json&txt="
    clusterForm = LanguageForm()
    getLangForm = GetLanguage()

    text = getLangForm.text2.data
    print(text)
    url = url + text

    headers = {"Server-Token": bearer_token}

    response = requests.get(url, headers=headers)
    try:
        print(response.json())
    except:
        pass
    get_language = str(response.json()['language_list'][0])
    return render_template("apicall.html", get_language=get_language, getlangform=getLangForm,
                           clusterform=clusterForm)


@app.route('/api/textclustering', methods=["GET", "POST"])
def textCluster():
    url = "https://ug-api.acnapiv3.io/swivel/text-clustering/clustering-1.1?of=json&txt="
    getLangForm = GetLanguage()
    clusterForm = LanguageForm()
    data = {}
    if clusterForm.validate():
        text = clusterForm.text.data
        textlist = text.split('.')
        textlist = [i for i in textlist if i != ""]
        for enum, i in enumerate(textlist):
            data["text" + "{enum+1:02}"] = i
        language = '&lang=' + clusterForm.language.data
        for (key, value) in data.items():
            url += '"{}":"{}" \n'.format(key, value)
        url += language
        print(url)
        headers = {"Server-Token": bearer_token}

        response = requests.get(url, headers=headers)
        try:
            print(response.json())
        except:
            pass
        text_cluster = str(response.json()["cluster_list"])
        return render_template("apicall.html", text_cluster=text_cluster, getlangform=getLangForm,
                               clusterform=clusterForm)
    else:
        return render_template("apicall.html", text_cluster="Please Enter Text", getlangform=getLangForm,
                               clusterform=clusterForm)

@app.route('/email', methods=["GET", "POST"])
def emailsending(ticketnumber, ):
    form = LoginForm()
    user = "faith"
    ticketnumber = ticketnumber
    content = "Dear {user}, <br><br>Thank you for contacting accenture!<p>We have received your ticket " \
              "submission #{ticketnumber}, and our development team will be looking into the issue shortly " \
              "and will send you a follow up email once it has been reviewed.</p>You can view your " \
              "existing tickets at accenture.com <br>Thanks and have a great day.<br><br> Best regards, <br>" \
              "Accenture Service Team".format(user=user, ticketnumber=ticketnumber)
    url = "https://ug-api.acnapiv3.io/swivel/email-services/api/mailer"
    headers = {"Server-Token": bearer_token}
    body = {"subject": "Accenture: Confirmation of ticket submission",
            "sender": "weijin_tan@mymail.sutd.edu.sg",
            "recipient": "weijin_tan@mymail.sutd.edu.sg",
            "html": content
            }
    response = requests.post(url, headers=headers, json=body)
    return redirect(url_for("index"))

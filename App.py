from flask import Flask, request, url_for, render_template, redirect, flash
import json
import requests
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from flask_bcrypt import Bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from flask_login import LoginManager
from flask_mail import Mail, Message
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.resources import CDN
from bokeh.models.tools import HoverTool
from bokeh.palettes import viridis
from bokeh.transform import factor_cmap
import secrets
from PIL import Image
import os

import forms


app = Flask(__name__, static_folder='<static folder path>')
app.config['SECRET_KEY'] = '<secret key>'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["MAIL_SERVER"] = 'smtp.googlemail.com'
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "<email>"
app.config["MAIL_PASSWORD"] = "<password>"
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)#nullable - ze mozna dac null
    image_file = db.Column(db.String(60), nullable=False, default="default.jpg")
    password = db.Column(db.String(60), nullable=False)
    api_keys = db.relationship('ApiKeys', backref='key', lazy=True)

    def get_reset_token(self, expires_sec=1800):
        s = Serializer(app.config['SECRET_KEY'], expires_sec)
        return s.dumps({'user_id': self.id}).decode('utf-8')

    @staticmethod  # Nie uzywa selfa (instancji klasy)
    def verify_reset_token(token):
        s = Serializer(app.config['SECRET_KEY'])
        try:
            user_id = s.loads(token)['user_id']
        except:
            return None
        return User.query.get(user_id)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class ApiKeys(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    api_key = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return self.api_key


def update():
    global api
    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    api_request = requests.get(url)
    api = json.loads(api_request.content)


@app.route("/")
def about():
    return render_template("about.html", title="About")


@app.route("/courses", methods=['POST', 'GET'])
def courses():
    if request.method == "POST":
        name = request.form["search_input"]
        return redirect(url_for("search", name=name))
    elif request.method == "GET":
        update()
        return render_template("courses.html", title="Courses", api=api)


@app.route("/courses/<name>")
def search(name):
    update()
    api2 = api
    global name1
    name1 = name
    api_single = ''
    try:
        api_request = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=" + name1.lower())
        api_single = json.loads(api_request.content)
        return render_template("course_name.html", api_single=api_single, name=name1, api2=api2, title=name1)
    except Exception as e:
        return render_template("error.html", title="error 404")


@app.route('/courses/<name>/result', methods=['POST'])
def send(name):
    update()
    api2 = api
    if request.method == 'POST':
        num1 = request.form['num1']
        api_request = requests.get("https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd&ids=" + name)
        api_single = json.loads(api_request.content)
        sum = ""
        try:
            sum = float(num1) * float(api_single[0]['current_price'])
            sum = round(sum, 3)
        except:
            pass
        return render_template("course_name.html", name=name, sum=sum, api_single=api_single, api2=api2, title=name)


@app.route("/courses/<name>/plot")
def plot(name):

    url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
    api_request = requests.get(url)
    api = json.loads(api_request.content)
    names_list = []
    full_names_list = []
    lista_kursow = []
    lista_linkow = []
    lista_kapitalizacji = []
    lista_wolumenow = []
    lista_obiegow = []
    lista_zmian = []

    for i in range(20):
        names_list.append(api[i]['symbol'].upper())
        full_names_list.append(api[i]['name'])
        lista_kursow.append(str(api[i]['current_price']))
        lista_linkow.append(api[i]['image'])
        lista_kapitalizacji.append(str(api[i]['market_cap']))
        lista_wolumenow.append(str(api[i]['total_volume']))
        lista_obiegow.append(str(api[i]['circulating_supply']))
        lista_zmian.append(str(api[i]['price_change_percentage_24h']))

    # Bohehowe rzeczy
    source = {
        "Name": names_list,
        "FullNames": full_names_list,
        "Price": lista_kursow,
        "Image": lista_linkow,
        "Cap": lista_kapitalizacji,
        "Volume": lista_wolumenow,
        "Circulation": lista_obiegow,
        "Change": lista_zmian
    }
    p = figure(
        x_range=names_list,
        plot_width=700,
        plot_height=600,
        y_axis_label="Price in USD",
        tools="pan,box_select,zoom_in,zoom_out,save,reset"
    )
    p.vbar(
        x="Name",
        top="Price",
        bottom=0,
        width=0.4,
        source=source,
        legend_field='Name',
        fill_color=factor_cmap(
            'Name',
            palette=viridis(20),
            factors=names_list
        ),
    )

    # Add Legend
    p.legend.orientation = 'vertical'
    p.legend.location = 'top_right'
    p.legend.label_text_font_size = '10px'

    hover = HoverTool()
    hover.tooltips = """
      <div>
        <h3>@Name</h3>
        <div><strong>Full name: </strong>@FullNames</div>
        <div><strong>Price: </strong>@Price USD</div>
        <div><strong>Capitalization: </strong>@Cap</div>
        <div><strong>Volume: </strong>@Volume</div>
        <div><strong>Circulation: </strong>@Circulation</div>
        <div><strong>Change: </strong>@Change %</div>
        <div><img src="@Image" alt="" width="200" /></div>
      </div>
    """
    p.add_tools(hover)
    script1, div1 = components(p)
    cdn_js = CDN.js_files
    cdn_css = CDN.css_files

    return render_template("plot.html", script1=script1, div1=div1, cdn_js=cdn_js, name=name, title=name + " plot",
                           chart_title="Price in USD")


@app.route('/courses/<name>/plot/g', methods=['POST'])
def plot2(name):
    if request.method == "POST":
        url = "https://api.coingecko.com/api/v3/coins/markets?vs_currency=usd"
        api_request = requests.get(url)
        api = json.loads(api_request.content)
        names_list = []
        full_names_list = []
        lista_kursow = []
        lista_linkow = []
        lista_kapitalizacji = []
        lista_wolumenow = []
        lista_obiegow = []
        lista_zmian = []

        for i in range(20):
            names_list.append(api[i]['symbol'].upper())
            full_names_list.append(api[i]['name'])
            lista_kursow.append(str(api[i]['current_price']))
            lista_linkow.append(api[i]['image'])
            lista_kapitalizacji.append(str(api[i]['market_cap']))
            lista_wolumenow.append(str(api[i]['total_volume']))
            lista_obiegow.append(str(api[i]['circulating_supply']))
            lista_zmian.append(str(api[i]['price_change_percentage_24h']))

        oper = ""
        chart_title = ""
        value = request.form['btn']

        if value == "Price":
            oper = "Price"
            chart_title = "Price in USD"
        elif value == "Cap":
            oper = "Cap"
            chart_title = "Capitalization"
        elif value == "Volume":
            oper = "Volume"
            chart_title = "Total volume"
        elif value == "Change":
            oper = "Change"
            chart_title = "Change percentage"
        elif value == "Circulation":
            oper = "Circulation"
            chart_title = "Circulation"
        print(value)

        # Bohehowe rzeczy
        source = {
            "Name": names_list,
            "FullNames": full_names_list,
            "Price": lista_kursow,
            "Image": lista_linkow,
            "Cap": lista_kapitalizacji,
            "Volume": lista_wolumenow,
            "Circulation": lista_obiegow,
            "Change": lista_zmian
        }

        p = figure(
            x_range=names_list,
            plot_width=700,
            plot_height=600,
            y_axis_label=oper,
            tools="pan,box_select,zoom_in,zoom_out,save,reset",
        )

        p.vbar(
            x="Name",
            top=oper,
            bottom=0,
            width=0.4,
            source=source,
            legend_field='Name',
            fill_color=factor_cmap(
                'Name',
                palette=viridis(20),
                factors=names_list
            ),

        )
        # Add Legend
        p.legend.orientation = 'vertical'
        p.legend.location = 'top_right'
        p.legend.label_text_font_size = '10px'
        hover = HoverTool()
        hover.tooltips = """
             <div>
               <h3>@Name</h3>
               <div><strong>Full name: </strong>@FullNames</div>
               <div><strong>Price: </strong>@Price USD</div>
               <div><strong>Capitalization: </strong>@Cap</div>
               <div><strong>Volume: </strong>@Volume</div>
               <div><strong>Circulation: </strong>@Circulation</div>
               <div><strong>Change: </strong>@Change %</div>
               <div><img src="@Image" alt="" width="200" /></div>
             </div>
           """
        p.add_tools(hover)
        script1, div1 = components(p)
        cdn_js = CDN.js_files
        cdn_css = CDN.css_files

        return render_template("plot.html", script1=script1, div1=div1, cdn_js=cdn_js, name=name, title=name + " plot",
                               chart_title=chart_title)


@app.route("/register", methods=['GET', 'POST'])
def register():
    form = forms.RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account has been created. Now you can log in!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login",  methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        redirect(url_for('about'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('about'))
        else:
            flash('Username or password is not valid! Check your spelling and try again.', 'danger')
    return render_template("login.html", title='Login', form=form)


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'Static/images', picture_fn)

    output_size = (125, 125)
    image = Image.open(form_picture)
    image.thumbnail(output_size)
    image.save(picture_path)

    return picture_fn


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = forms.UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your account has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == "GET":
        form.username.data = current_user.username
        form.email.data = current_user.email

    return render_template("account.html", title="Account", form=form)


@app.route('/account/delete_account', methods=['POST'])
@login_required
def delete_account():
    User.query.filter_by(username=current_user.username).delete()
    db.session.commit()
    flash("Your account has been deleted", "success")
    return redirect(url_for('about'))


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('about'))


def send_reset_key(user):
    token = user.get_reset_token()
    msg = Message('Api Key', sender='noreply@demo.com', recipients=[user.email])
    msg.body = \
f'''Thank you for requesting our api key :)
Now you just have to visit that link:
{url_for('reset_token', token=token, _external=True)}

Have fun - CryptoBoiz team.
'''
    mail.send(msg)
    #_external=True - daje pelny link


@app.route('/about-api')
def about_api():
    return render_template("about_api.html", title="About Api")


@app.route('/about_api/api', methods=['GET', 'POST'])
@login_required
def api():
    if current_user.is_authenticated:
        form = forms.GetApiKeyForm()
        if form.validate_on_submit():
            user = User.query.filter_by(email=current_user.email).first()
            send_reset_key(user)
            flash("An email has been sent. Check your mail box.", "info")
            return redirect(url_for('account'))
        return render_template("api.html", form=form, title="request api key")


@app.route('/about_api/api/<token>', methods=['GET', 'POST'])
@login_required
def reset_token(token):
    if current_user.is_authenticated:
        user = User.verify_reset_token(token)
        if user is None:
            flash('That is invalid or expired token.', 'warning')
            return redirect(url_for('about_api'))
        else:
            ApiKeys.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
            form = forms.GetApiKeyForm()
            api_key = secrets.token_hex(16)
            key = ApiKeys(api_key=api_key, user_id=current_user.id)
            db.session.add(key)
            db.session.commit()

        return redirect(url_for('account'))


def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request', sender='noreply@demo.com', recipients=[user.email])
    msg.body = f'''To reset your password visit the following link:
{url_for('reset_email_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)
    #_external=True - daje pelny link


@app.route('/reset-password', methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for("about"))
    form = forms.RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash("An email has been sent with instructions to reset your password.", "info")
        return redirect(url_for('login'))
    return render_template("reset_password.html", title='Reset Password', form=form)


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_email_token(token):
    if current_user.is_authenticated:
        return redirect(url_for("about"))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is invalid or expired token.', 'warning')
        return redirect(url_for('reset_request'))
    form = forms.ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode("utf-8")
        user.password = hashed_password
        db.session.commit()
        flash(f"Your password has been updated!", "success")
        return redirect(url_for("login"))
    return render_template("reset_password_token.html", title='Reset Password', form=form)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)

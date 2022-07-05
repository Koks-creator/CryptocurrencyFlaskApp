from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from flask_wtf.file import FileField, FileAllowed
from StronkaJakas import App


class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField("Create account")

    @staticmethod
    def validate_username(_, username):
        user = App.User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError("This username is already taken!")

    @staticmethod
    def validate_email(_, email):
        user = App.User.query.filter_by(username=email.data).first()
        if user:
            raise ValidationError("This email is already taken!")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField('Remember me')

    submit = SubmitField("Log in")


class GetApiKeyForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])

    submit = SubmitField("Send request")


class UpdateAccountForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired(), Length(min=2, max=30)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    picture = FileField("Update profile picture", validators=[FileAllowed(['jpg', 'png'])])

    submit = SubmitField("Update")


class RequestPasswordResetForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])

    submit = SubmitField("Send request")

    @staticmethod
    def validate_email(_, email):
        user = App.User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError("There is no user with this email! Check your spelling and try again")


class ResetPasswordForm(FlaskForm):
    password = PasswordField("Password", validators=[DataRequired()])
    confirm_password = PasswordField("Confirm password", validators=[DataRequired(), EqualTo('password')])

    submit = SubmitField('Reset Password')

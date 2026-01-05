from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    TextAreaField,
    FloatField,
    SelectField
)
from wtforms.validators import DataRequired, Email, Length
from wtforms import StringField, PasswordField, SubmitField, EmailField, SelectField
from wtforms.validators import DataRequired, Email, EqualTo, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')


class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

CATEGORY_CHOICES = [
    ('mountains', 'მთები'),
    ('waterfalls', 'ჩანჩქერები/კანიონები'),
    ('historic', 'ისტორიული'),
    ('forests', 'ტყეები'),
    ('views', 'ხედები'),
    ('hiking', 'ლაშქრობა'),
    ('lakes', 'ტბები'),
    ('sunrise', 'მზის ამოსვლა'),
]

REGION_CHOICES = [
    ('Tbilisi', 'თბილისი'),
    ('Adjara', 'აჭარა'),
    ('Abkhazia', 'აფხაზეთი'),
    ('Samegrelo', 'სამეგრელო'),
    ('Guria', 'გურია'),
    ('Adjara', 'აჭარა'),
    ('Imereti', 'იმერეთი'),
    ('Kakheti', 'კახეთი'),
    ('Racha-Lechkhumi', 'რაჭა-ლეჩხუმი'),
    ('Mtskheta-Mtianeti', 'მცხეთა-მთიანეთი'),
    ('Samtskhe-Javakheti', 'სამცხე-ჯავახეთი'),
    ('Svaneti', 'სვანეთი'),
    ('Shida Kartli', 'შიდა ქართლი'),
    ('Kvemo Kartli', 'ქვემო ქართლი'),

]

class PlaceForm(FlaskForm):
    name = StringField("ადგილის სახელი", validators=[DataRequired(), Length(max=150)])
    description = TextAreaField("აღწერა", validators=[DataRequired()])
    category = SelectField("კატეგორია", choices=CATEGORY_CHOICES, validators=[DataRequired()])
    region = SelectField("რეგიონი", choices=REGION_CHOICES)
    image = FileField("ატვირთე ფოტო", validators=[FileAllowed(['jpg', 'png', 'jpeg'], 'მხოლოდ ფოტო!')])
    submit = SubmitField("დაამატე ადგილი")

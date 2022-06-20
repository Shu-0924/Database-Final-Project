from flask_wtf import FlaskForm
from wtforms import IntegerField, FloatField, StringField, PasswordField, SubmitField, validators
from flask_wtf.file import FileField, FileAllowed, FileRequired
import tables
import main


def validate_notnull():
    message = "This field is required."

    def _validate_notnull(form, field):
        if str(field.data).strip() == "":
            raise validators.ValidationError(message)

    return _validate_notnull


def validate_alpha():
    message = "Only letters are allowed."

    def _validate_alpha(form, field):
        if not str(field.data).isalpha():
            raise validators.ValidationError(message)

    return _validate_alpha


def validate_alnum():
    message = "Only letters and numbers are allowed."

    def _validate_alnum(form, field):
        if not str(field.data).isalnum():
            raise validators.ValidationError(message)

    return _validate_alnum


def validate_phone():
    message = "Invalid phone number."

    def _validate_phone(form, field):
        num = str(field.data)
        if not num.isdigit() or len(num) != 10 or num[0] != '0' or num[1] != '9':
            raise validators.ValidationError(message)

    return _validate_phone


def validate_account_unique():
    message = "This account already exists."

    def _validate_account_unique(form, field):
        result = main.db.session.query(tables.User).filter_by(account=field.data).first()
        if result is not None:
            raise validators.ValidationError(message)

    return _validate_account_unique


def validate_shop_unique():
    message = "This shop name already exists."

    def _validate_shop_unique(form, field):
        result = main.db.session.query(tables.Shop).filter_by(shop_name=str(field.data).strip()).first()
        if result is not None:
            raise validators.ValidationError(message)

    return _validate_shop_unique


class SignUp(FlaskForm):
    name = StringField('Name',
                       render_kw={"placeholder": "Name",
                                  "autocomplete": "off"},
                       validators=[
                           validators.InputRequired(),
                           validate_alpha()
                       ])
    phone_number = StringField('Phone Number',
                               render_kw={"placeholder": "PhoneNumber",
                                          "autocomplete": "off"},
                               validators=[
                                   validators.InputRequired(),
                                   validate_phone()
                               ])
    account = StringField('Account',
                          render_kw={"placeholder": "Account",
                                     "autocomplete": "off"},
                          validators=[
                              validators.InputRequired(),
                              validate_alnum(),
                              validate_account_unique()
                          ])
    password = PasswordField('Password',
                             render_kw={"placeholder": "Password",
                                        "autocomplete": "off"},
                             validators=[
                                 validators.InputRequired(),
                                 validate_alnum()
                             ])
    password2 = PasswordField('Confirm Password',
                              render_kw={"placeholder": "Re-type Password",
                                         "autocomplete": "off"},
                              validators=[
                                  validators.InputRequired(),
                                  validators.EqualTo('password', message='Passwords do not match.')
                              ])
    latitude = FloatField('Latitude',
                          render_kw={"placeholder": "Latitude",
                                     "autocomplete": "off"},
                          validators=[
                              validators.InputRequired(),
                              validators.NumberRange(min=-90.0, max=90.0)
                          ])
    longitude = FloatField('Longitude',
                           render_kw={"placeholder": "Longitude",
                                      "autocomplete": "off"},
                           validators=[
                               validators.InputRequired(),
                               validators.NumberRange(min=-180.0, max=180.0)
                           ])
    submit = SubmitField('Sign Up')


class Login(FlaskForm):
    account = StringField('Account',
                          render_kw={"placeholder": "Account",
                                     "autocomplete": "off"},
                          validators=[
                              validators.InputRequired(),
                              validate_alnum()
                          ])
    password = PasswordField('Password',
                             render_kw={"placeholder": "Password",
                                        "autocomplete": "off"},
                             validators=[
                                 validators.InputRequired(),
                                 validate_alnum()
                             ])
    submit = SubmitField('Sign In')


class EditLocation(FlaskForm):
    latitude = FloatField('Latitude',
                          render_kw={"placeholder": "Enter latitude",
                                     "autocomplete": "off"},
                          validators=[
                              validators.InputRequired(),
                              validators.NumberRange(min=-90.0, max=90.0)
                          ])
    longitude = FloatField('Longitude',
                           render_kw={"placeholder": "Enter longitude",
                                      "autocomplete": "off"},
                           validators=[
                               validators.InputRequired(),
                               validators.NumberRange(min=-180.0, max=180.0)
                           ])
    submit = SubmitField('Edit')


class Register(FlaskForm):
    shop_name = StringField('Shop Name',
                            render_kw={"placeholder": "macdonald",
                                       "autocomplete": "off"},
                            validators=[
                                validate_notnull(),
                                validate_shop_unique()
                            ])
    shop_category = StringField('Shop Category',
                                render_kw={"placeholder": "fast food",
                                           "autocomplete": "off"},
                                validators=[
                                    validate_notnull()
                                ])
    latitude = FloatField('Latitude',
                          render_kw={"placeholder": "24.78472733371133",
                                     "autocomplete": "off"},
                          validators=[
                              validators.InputRequired(),
                              validators.NumberRange(min=-90.0, max=90.0)
                          ])
    longitude = FloatField('Longitude',
                           render_kw={"placeholder": "121.00028167648875",
                                      "autocomplete": "off"},
                           validators=[
                               validators.InputRequired(),
                               validators.NumberRange(min=-180.0, max=180.0)
                           ])
    submit = SubmitField('Register')


class AddMeal(FlaskForm):
    picture = FileField('Picture',
                        validators=[
                            FileRequired('Please upload image'),
                            FileAllowed(main.upload, 'Image only')
                        ])
    meal_name = StringField('Meal Name',
                            render_kw={"autocomplete": "off"},
                            validators=[
                                validate_notnull()
                            ])
    price = IntegerField('Price',
                         render_kw={"autocomplete": "off"},
                         validators=[
                             validators.InputRequired(),
                             validators.NumberRange(min=0)
                         ])
    quantity = IntegerField('Quantity',
                            render_kw={"autocomplete": "off"},
                            validators=[
                                validators.InputRequired(),
                                validators.NumberRange(min=0)
                            ])
    submit = SubmitField('Add')


from wtforms import Form, StringField, RadioField, SelectField, TextAreaField, validators, BooleanField
from wtforms.fields import EmailField, DateField, EmailField, PasswordField
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired, NumberRange
from wtforms import StringField, IntegerField, SubmitField, SelectField
from flask_wtf import FlaskForm, RecaptchaField

class CreateCartForm(Form):
        product = SelectField('Product', [validators.DataRequired()],choices=[('', 'Select'), ('F. Classic Artisan T', 'F. Classic Artisan T ($140.00)'), ('Linen SS shirt', 'Linen SS shirt ($250.00)'), ('Linen shorts', 'Linen shorts ($280.00)')], default='')
        price = StringField('Price', [validators.Length(min=1, max=3), validators.DataRequired()])
        quantity = StringField('Quantity', [validators.Length(min=1, max=3), validators.DataRequired()])
        remarks = TextAreaField('Remarks', [validators.Optional()])


class CreateUserForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=150), validators.DataRequired(),validators.regexp(r'^[a-zA-Z]+$', message='Username must only contain letters')])
    password = PasswordField('Password', [validators.Length(min=8, message='Too short'), validators.DataRequired()])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired()])
    role = RadioField('Role', choices=[('Manager'), ('Operator')], default='')
    recaptcha = RecaptchaField()


class CreateCustomerForm(Form):
    username = StringField('Username', [validators.Length(min=1, max=150), validators.DataRequired(), validators.regexp(r'^[a-zA-Z]+$', message='Username must only contain letters')])
    gender = SelectField('Gender', [validators.DataRequired()], choices=[('', 'Select'), ('F', 'Female'), ('M', 'Male')], default='')
    email = EmailField('Email', [validators.length(max=200),validators.DataRequired(),validators.Regexp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')])
    email_verified = BooleanField('Email Verified', default=False)
    address = TextAreaField('Mailing Address', [validators.length(max=200), validators.DataRequired()])
    payment = RadioField('Payment', choices=[('AmericanExpress'), ('MasterCard'), ('Visa')], default='')
    password = PasswordField('Password', [validators.Length(min=8, message='Too short')])
    confirm_password = PasswordField('Confirm Password', [validators.DataRequired()])
    recaptcha = RecaptchaField()


class CreateFeedbackForm(Form):
    first_name = StringField('First Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    last_name = StringField('Last Name', [validators.Length(min=1, max=150), validators.DataRequired()])
    email = EmailField('Email', [validators.Email(), validators.DataRequired()])
    topic = SelectField('Topic', [validators.DataRequired()], choices=[('', 'Select'), ('Complain', 'Complain'), ('Review', 'Review')], default='')
    date_joined = DateField('Current Date(yy/mm/dd)', format='%Y-%m-%d')
    rating = SelectField('Rating', [validators.DataRequired()], choices=[('', 'Select'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], default='')
    message = TextAreaField('Message', [validators.length(max=200), validators.DataRequired()])
    recaptcha = RecaptchaField()


class ProductForm(FlaskForm):
    product_id = StringField('Product ID', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    category = SelectField(
        'Category',
        choices=[('Shirts', 'Shirts'), ('T-Shirts', 'T-Shirts'), ('Bottoms', 'Bottoms')],
        validators=[DataRequired()]
    )
    price = IntegerField('Price', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Stock', validators=[DataRequired(), NumberRange(min=0)])
    image_url = StringField('Image URL')
    submit = SubmitField('Submit')

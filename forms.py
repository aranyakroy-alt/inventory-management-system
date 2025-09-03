from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from models import User, UserRole

class LoginForm(FlaskForm):
    """User login form with validation"""
    username = StringField('Username or Email', validators=[
        DataRequired(message="Username or email is required"),
        Length(min=3, max=80, message="Username must be 3-80 characters")
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required")
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Login')

class UserRegistrationForm(FlaskForm):
    """Admin form for creating new users"""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=80, message="Username must be 3-80 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email too long")
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message="First name is required"),
        Length(min=1, max=50, message="First name must be 1-50 characters")
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message="Last name is required"),
        Length(min=1, max=50, message="Last name must be 1-50 characters")
    ])
    role = SelectField('Role', choices=[
        (UserRole.EMPLOYEE.value, 'Employee - Basic inventory operations'),
        (UserRole.MANAGER.value, 'Manager - Full inventory + analytics'),
        (UserRole.ADMIN.value, 'Administrator - Complete system access')
    ], validators=[DataRequired()])
    password = PasswordField('Password', validators=[
        DataRequired(message="Password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    password_confirm = PasswordField('Confirm Password', validators=[
        DataRequired(message="Please confirm the password"),
        EqualTo('password', message="Passwords must match")
    ])
    is_active = BooleanField('Active Account', default=True)
    submit = SubmitField('Create User')
    
    def validate_username(self, username):
        """Check if username is already taken"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose another.')
    
    def validate_email(self, email):
        """Check if email is already registered"""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose another.')

class UserEditForm(FlaskForm):
    """Form for editing existing users"""
    username = StringField('Username', validators=[
        DataRequired(message="Username is required"),
        Length(min=3, max=80, message="Username must be 3-80 characters")
    ])
    email = StringField('Email', validators=[
        DataRequired(message="Email is required"),
        Email(message="Please enter a valid email address"),
        Length(max=120, message="Email too long")
    ])
    first_name = StringField('First Name', validators=[
        DataRequired(message="First name is required"),
        Length(min=1, max=50, message="First name must be 1-50 characters")
    ])
    last_name = StringField('Last Name', validators=[
        DataRequired(message="Last name is required"),
        Length(min=1, max=50, message="Last name must be 1-50 characters")
    ])
    role = SelectField('Role', choices=[
        (UserRole.EMPLOYEE.value, 'Employee - Basic inventory operations'),
        (UserRole.MANAGER.value, 'Manager - Full inventory + analytics'),
        (UserRole.ADMIN.value, 'Administrator - Complete system access')
    ], validators=[DataRequired()])
    is_active = BooleanField('Active Account')
    submit = SubmitField('Update User')
    
    def __init__(self, original_user=None, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.original_user = original_user
    
    def validate_username(self, username):
        """Check if username is already taken by another user"""
        if self.original_user and username.data == self.original_user.username:
            return  # Username unchanged
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose another.')
    
    def validate_email(self, email):
        """Check if email is already registered by another user"""
        if self.original_user and email.data == self.original_user.email:
            return  # Email unchanged
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please choose another.')

class PasswordChangeForm(FlaskForm):
    """Form for users to change their password"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    new_password_confirm = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm the new password"),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Change Password')

class AdminPasswordResetForm(FlaskForm):
    """Admin form for resetting user passwords"""
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required"),
        Length(min=6, message="Password must be at least 6 characters")
    ])
    new_password_confirm = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm the new password"),
        EqualTo('new_password', message="Passwords must match")
    ])
    submit = SubmitField('Reset Password')
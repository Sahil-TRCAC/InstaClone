from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, TextAreaField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError

# REMOVE THIS LINE (causes circular dependency):
# from models import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', 
                          validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    password = PasswordField('Password', 
                            validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', 
                                    validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')
    # Remove validation methods that use User model
    
class PostForm(FlaskForm):
    image = FileField('Upload Image', 
                     validators=[DataRequired(), 
                                FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')])
    caption = TextAreaField('Caption', 
                           validators=[Length(max=500)])
    submit = SubmitField('Share Post')

class ReelForm(FlaskForm):
    video = FileField('Upload Video', 
                     validators=[DataRequired(),
                                FileAllowed(['mp4', 'mov', 'avi', 'mkv'], 'Videos only!')])
    caption = TextAreaField('Caption', 
                           validators=[Length(max=500)])
    submit = SubmitField('Upload Reel')

class CommentForm(FlaskForm):
    content = TextAreaField('Comment', 
                           validators=[DataRequired(), Length(max=300)])
    submit = SubmitField('Post Comment')

class EditProfileForm(FlaskForm):
    username = StringField('Username', 
                          validators=[DataRequired(), Length(min=3, max=20)])
    email = StringField('Email', 
                       validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio', 
                       validators=[Length(max=150)])
    profile_pic = FileField('Profile Picture', 
                           validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'Images only!')])
    submit = SubmitField('Update Profile')

class SearchForm(FlaskForm):
    query = StringField('Search', validators=[DataRequired()])
    submit = SubmitField('Search')

class MessageForm(FlaskForm):
    content = TextAreaField('Message', 
                           validators=[DataRequired(), Length(max=1000)])
    submit = SubmitField('Send')
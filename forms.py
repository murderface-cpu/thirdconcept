from flask_wtf import FlaskForm # type: ignore
from wtforms import StringField, TextAreaField, EmailField, SubmitField, PasswordField, SelectField, BooleanField, SelectField, URLField, FileField # type: ignore
from wtforms.validators import DataRequired, Email, Length, Optional # type: ignore

# Forms
class ContactForm(FlaskForm):
    name = StringField('Full Name', validators=[DataRequired()])
    email = EmailField('Email Address', validators=[DataRequired(), Email()])
    organization = StringField('Organization')
    subject = StringField('Subject', validators=[DataRequired()])
    message = TextAreaField('Message', validators=[DataRequired()])
    submit = SubmitField('Send Message')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class UserForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=20)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=6)])
    role = SelectField('Role', choices=[('user', 'User'), ('admin', 'Admin')])
    is_active = BooleanField('Active')
    submit = SubmitField('Save User')

class ProjectForm(FlaskForm):
    title = StringField('Project Title', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    icon = SelectField('Icon/Emoji', choices=[
        ('🌱', '🌱 Leaf'),
        ('📖', '📖 Book'),
        ('🎓', '🎓 Graduation Cap'),
        ('🤝', '🤝 Handshake'),
        ('🏫', '🏫 School'),
        ('💡', '💡 Lightbulb'),
        ('🎨', '🎨 Art'),
        ('🧑‍🏫', '🧑‍🏫 Teacher'),
        ('🌍', '🌍 Globe'),
        ('📚', '📚 Books'),
        ('📝', '📝 Note'),
        ('🎶', '🎶 Music'),
        ('🧒', '🧒 Child'),
        ('🏃', '🏃 Activity'),
        ('🏆', '🏆 Trophy'),
        ('💖', '💖 Heart'),
        ('✨', '✨ Sparkle'),
        ('📷', '📷 Camera'),
        ('📊', '📊 Chart'),
        ('📦', '📦 Package'),
        ('🛠️', '🛠️ Tools')
    ], validators=[DataRequired()])
    tags = StringField('Tags (comma-separated)')
    status = SelectField('Status', choices=[('active', 'Active'), ('inactive', 'InActive'), ('completed', 'Completed'), ('paused', 'Paused')])
    image = FileField('Project Image')
    content = TextAreaField('Detailed Content (Markdown)')
    submit = SubmitField('Save Project')

class TeamMemberForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    role = StringField('Role', validators=[DataRequired()])
    bio = TextAreaField('Bio', validators=[DataRequired()])
    avatar = StringField('Avatar (Initials)')
    is_active = BooleanField('Active')
    submit = SubmitField('Save Team Member')

class SettingsForm(FlaskForm):
    site_name = StringField('Site Name', validators=[DataRequired()])
    site_description = TextAreaField('Site Description')
    contact_email = EmailField('Contact Email', validators=[DataRequired(), Email()])
    phone = StringField('Phone Number')
    address = StringField('Address')
    maintenance_mode = BooleanField('Maintenance Mode')
    submit = SubmitField('Save Settings')
from flask import render_template, flash, redirect, url_for, request
from flask_login import login_user, login_required, current_user, logout_user
from werkzeug.utils import secure_filename
import os
from app.email import send_reset_password_mail
from app import app, bcrypt, db
from app.forms import *
from app.models import User, Post
from app.text_detection import imageProcess
import string
import random
import boto3

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}


def allowed_file(filename):
    return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostTweetForm()

    if form.validate_on_submit():
        f = form.text.data

        if f.filename == '':
            flash('No file selected', category='danger')

        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            new_filename = ''

            # Connect to S3
            s3 = boto3.resource('s3')
            bucket_name = 'ece1779a1s3'
            bucket = s3.Bucket(bucket_name)

            # Check if the file exist in S3
            for obj in bucket.objects.filter(Prefix=filename):
                if obj.key == filename:
                    # File already exist, change the filename by adding a number
                    new_filename = filename.split('.')[0] + '_' + \
                               str(sum(1 for _ in bucket.objects.filter(Prefix=filename.split('.')[0]).all())) + '.' + \
                               filename.split('.')[1]
                    filename = new_filename
                    break

            # Upload file to s3
            f.save(os.path.join('app', 'static', 'asset', filename))
            s3.Object(bucket_name, filename).upload_file(os.path.join('app', 'static', 'asset', filename))
            '''
            if new_filename == '':
                f.save(os.path.join('app', 'static', 'asset', filename))
                s3.Object(bucket_name, filename).upload_file(os.path.join('app', 'static', 'asset', filename))
            else:
                f.save(os.path.join('app', 'static', 'asset', new_filename))
                s3.Object(bucket_name, new_filename).upload_file(os.path.join('app', 'static', 'asset', new_filename))
            '''
        else:
            flash("png, jpg, jpeg file only ", category='danger')
            return redirect(url_for('index'))

        imageProcess('app/static/asset/', filename)
        post = Post(body="/static/asset/" + filename, east="/static/asset/EAST_" + filename)
        s3.Object(bucket_name, "EAST_"+filename).upload_file("app/static/asset/EAST_" + filename)
        current_user.posts.append(post)
        db.session.commit()
        print(filename)
        flash('Upload Successfully, process done', category='success')

    page = request.args.get('page', 1, type=int)
    posts = Post.query.filter_by(user_id=current_user.id).order_by(Post.timestamp.desc()).paginate(page, 5, False)
    return render_template('index.html', form=form, posts=posts)


@app.route('/user_page/<username>', methods=['GET', 'POST'])
@login_required
def user_page(username):
    user = User.query.filter_by(username=username).first()
    if user:
        page = request.args.get('page', 1, type=int)
        posts = Post.query.filter_by(user_id=user.id).order_by(Post.timestamp.desc()).paginate(page, 5, False)
        return render_template('user_page.html', user=user, posts=posts)
    else:
        return '404'


@app.route('/edit_profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = UploadPhotoForm()
    if form.validate_on_submit():
        f = form.photo.data

        if f.filename == '':
            flash('No file selected', category='danger')
            return render_template('edit_profile.html', form=form)
        if f and allowed_file(f.filename):
            filename = secure_filename(f.filename)
            f.save(os.path.join('app', 'static', 'asset', filename))
            current_user.avatar_img = '/static/asset/' + filename
            db.session.commit()
            return redirect(url_for('user_page', username=current_user.username))
    return render_template('edit_profile.html', form=form)


@app.route('/register/', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data)
        print(password)
        #password = bcrypt.hashpw(form.password.data.encode('utf8'), bcrypt.gensalt()).decode('utf-8')
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, registration successfully!', category='success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/api/register/', methods=['POST'])
def api_register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegisterForm()
    if form.validate_on_submit():
        username = form.username.data
        #email = form.email.data
        password = bcrypt.generate_password_hash(form.password.data)
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, registration successfully!', category='success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/api/upload/', methods=['POST'])
def api_upload():

    form = UploadApiForm()
    #if form.validate_on_submit():
    username = form.username.data
    password = form.password.data
    remember = form.remember.data
    user = User.query.filter_by(username=username).first()

    if user and bcrypt.check_password_hash(user.password, password):
        login_user(user, remember=remember)
    else:
        return {"status": "login-error", "text": "User not exist or password not match"}

    f = form.file.data

    if f.filename == '':
       return {"status": "file-error", "text": "No such files"}


    filename = secure_filename(f.filename).split('.')[0] + \
               '_' + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6)) + \
               '.' + secure_filename(f.filename).split('.')[1]

    f.save(os.path.join('app', 'static', 'asset', filename))

    imageProcess('app/static/asset/', filename)

    post = Post(body="/static/asset/" + filename, east="/static/asset/EAST_" + filename)
    current_user.posts.append(post)
    db.session.commit()
    #print(filename)

    db.session.add(user)
    db.session.commit()
    return {"status": "success", "text": "Login and image processed"}


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        remember = form.remember.data
        user = User.query.filter_by(username=username).first()
        print(user.password)
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user, remember=remember)
            flash('Login success', category='info')
            if request.args.get('next'):
                next_page = request.args.get('next')
                return redirect(next_page)
            return redirect(url_for('index'))
        flash('User not exist or password not match', category='danger')

    return render_template('login.html', form=form)


@app.route('/logout/')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/send_password_reset_request', methods=['GET', 'POST'])
def send_password_reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = PasswordResetRequestForm()
    if form.validate_on_submit():
        email = form.email.data
        user = User.query.filter_by(email=email).first()
        token = user.generate_reset_password_token()
        send_reset_password_mail(user, token)
        flash('Password reset link already sent to your email.', category='info')
    return render_template('send_password_reset_request.html', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user = User.check_reset_password_token(token)
        if user:
            user.password = bcrypt.generate_password_hash(form.password.data)
            db.session.commit()
            flash('Password reset done', category='info')
            return redirect(url_for('login'))
        else:
            flash('The user is not exist', category='info')

            return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)

from flask import Blueprint,render_template,request,session,redirect,url_for,abort
import bcrypt 
import bson

from party.models import Party
from user.models import User
from user.forms import RegistrationForm,LoginForm,EditProfileForm,PasswordForm
from user.decorators import login_required 
from utilities.storage import upload_image_file

user_page = Blueprint('user_page',__name__)

@user_page.route('/login',methods=['GET','POST'])
def login():
    form = LoginForm(request.form)
    error = None

    if request.method == 'POST' and form.validate():
        user = User.objects.filter(email=form.email.data.lower()).first()
        if user:
            if bcrypt.checkpw(form.password.data.encode('utf8'),user.password.encode('utf8')):
                session['email'] = user.email
                return redirect(request.args.get('next') or url_for('home'))
            else:
                user = None
        if not user:
            error = 'Your email or password was entered incorrectly'

    return render_template('user/login.html',form=form,error=error)
    #user = User(name='Raymond',password='123',email='email@gmail.com')
    #user.save()
    #return 'Hello {}! Your email address is {}'.format(user.name,user.email)
    #return "this is login page"

@user_page.route('/logout')
def logout():
    try:
        session.pop('email')
        return redirect(url_for('user_page.login'))
    except:
        return redirect(url_for('user_page.login'))


    
@user_page.route('/signup',methods=['GET','POST'])
def signup():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(form.password.data.encode('utf8'),salt)

        user = User(
            name=form.name.data,
            email=form.email.data.lower(),
            password=hashed_password
        )
        user.save()

        return redirect(url_for('user_page.login'))
    return render_template('user/signup.html',form=form)

@user_page.route('/edit',methods=['GET','POST'])
@login_required
def edit():
    user = User.objects.filter(email=session['email']).first()
    if user:
        error = None 
        message = None
        form = EditProfileForm(obj=user)

        if request.method =='POST' and form.validate():
            if user.email != form.email.data.lower():
                if User.objects.filter(email=form.email.data.lower()).first():
                    error = "Email is already in use"
                else:
                    session['email'] = form.email.data.lower()
            if not error:
                form.populate_obj(user)
                image_url = upload_image_file(request.files.get('image'),'profile_image/',str(user.id))
                if image_url:
                    user.profile_image = image_url
                user.save()
                message = "Profile updated"
            
        return render_template('user/edit.html',user=user,form=form,error=error,message=message)
    else:
        abort(404)

@user_page.route('/password',methods=['GET','POST'])
@login_required
def password():
    user = User.objects.filter(email=session.get('email')).first()
    if user:
        error = None
        message = None
        form = PasswordForm()
        if request.method == "POST" and form.validate(): 
            if bcrypt.checkpw(form.old_password.data.encode('utf8'),user.password.encode('utf8')):
                salt = bcrypt.gensalt()
                hashed_password = bcrypt.hashpw(form.new_password.data.encode('utf8'),salt)
                user.password = hashed_password.decode("utf-8")   # s.decode("utf-8") == str(s, 'utf-8') 
                # "password": "b'$2b$12$YtBDv2A/cRftPCE2gqh58e2TW0j3Otya1llxMpaefBhUab6BwVpzm'",  b'<hash>' is redundency. =b' ' 
                '''
                user = User(
                    password=hashed_password 
                )
                '''
                user.save()
                message = 'Password updated'
            else:
                error = 'Your old password was incorrect'
        return render_template('user/password.html',form=form,error=error,message=message)
    else:
        abort(404)

@user_page.route('/<id>/<int:party_page_number>', methods=['GET'])
@user_page.route('/<id>')
def profile(id, party_page_number=1):
    try:
        user = User.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)
    if user:
        parties = Party.objects(attendees__in=[user], cancel=False).order_by('-start_datetime').paginate(page=party_page_number, per_page=4)
        return render_template('user/profile.html',user=user, parties=parties)
    else:
        abort(404)
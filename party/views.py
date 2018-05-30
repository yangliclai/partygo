from flask import Blueprint,render_template,request,session,redirect,url_for,abort
import bson

from party.forms import BasicPartyForm,EditPartyForm,CancelPartyForm
from user.decorators import login_required
from party.models import Party
from user.models import User 
from utilities.storage import upload_image_file

party_page =Blueprint('party_page',__name__)

@party_page.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = BasicPartyForm()
    error = None
    if request.method == 'POST' and form.validate():
        if form.end_datetime.data < form.start_datetime.data:
            error = "A party must end after it starts!"
        if not error:
            user = User.objects.filter(email=session.get('email')).first()

            party = Party(
                 name=form.name.data,
                 place=form.place.data,
                 location=[form.lng.data,form.lat.data],
                 start_datetime=form.start_datetime.data,
                 end_datetime=form.end_datetime.data,
                 description=form.description.data,
                 host=user.id,
                 attendees=[user]
            )
            party.save()
            #return '{} created.'.format(party.name)
            return redirect(url_for('party_page.edit', id=party.id))
    return render_template('party/create.html', form=form, error=error)

@party_page.route('/<id>/edit',methods=['GET','POST'])
@login_required
def edit(id):
    try :
        party = Party.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)

    user = User.objects.filter(email=session.get('email')).first()

    if party and party.host == user.id:
        error = None
        message = None 
        form = EditPartyForm(obj=party)
        if request.method == 'POST' and form.validate():
            if form.end_datetime.data < form.start_datetime.data:
                error = 'A party must end after it starts!'
            if not error: 
                form.populate_obj(party)
                if form.lng.data and form.lat.data: 
                    party.location = [form.lng.data,form.lat.data]
                image_url = upload_image_file(request.files.get('photo'),'party_photo/',str(party.id))
                if image_url:
                    party.party_photo = image_url
                party.save()
                message = 'Party updated'
        return render_template('party/edit.html', form=form, error=error, message=message, party=party)
    else:
        abort(404)

@party_page.route('/testphoto')
def testphoto():
    return render_template('party/testphoto.html')
'''
@app.route('/')
def hello_world():
    return 'Hello, World!'
'''

@party_page.route('/<id>/cancel', methods=['GET','POST'])
@login_required
def cancel(id):
    try:
        party = Party.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)
        
    user = User.objects.filter(email=session.get('email')).first()
    
    if party and party.host == user.id and party.cancel == False:
        error = None
        form = CancelPartyForm()
        if request.method == 'POST' and form.validate():
            if form.confirm.data == 'yes':
                party.cancel = True
                party.save()
                return redirect(url_for('party_page.edit', id=party.id))
            else:
                error = 'Say yes if you want to cancel'
        return render_template('party/cancel.html', form=form, error=error, party=party)
    else:
        abort(404)

@party_page.route('/<id>', methods=['GET'])
def public(id):
    try:
        party = Party.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)

    if party:
        host = User.objects.filter(id=party.host).first()
        user = User.objects.filter(email=session.get('email')).first()
        return render_template('party/public.html', party=party, host=host, user=user)
    else:
        abort(404)

@party_page.route('/<id>/join', methods=['GET'])
@login_required
def join(id):
    user = User.objects.filter(email=session.get('email')).first()
    try:
        party = Party.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)    

    if user and party:
        if user not in party.attendees:
            party.attendees.append(user)
            party.save()
        return redirect(url_for('party_page.public',id=id))
    else:
        abort(404)

@party_page.route('/<id>/leave', methods=['GET'])
@login_required
def leave(id):
    user = User.objects.filter(email=session.get('email')).first()
    try:
        party = Party.objects.filter(id=bson.ObjectId(id)).first()
    except bson.errors.InvalidId:
        abort(404)    

    if user and party:
        if user in party.attendees:
            party.attendees.remove(user)
            party.save()
        return redirect(url_for('party_page.public',id=id))
    else:
        abort(404)        

@party_page.route('/manage/<int:party_page_number>',methods=['GET'])
@party_page.route('/manage', methods=['GET'])
@login_required 
def manage(party_page_number=1):
    user = User.objects.filter(email=session.get('email')).first()
    if user:
        parties = Party.objects.filter(host=user.id).order_by('-start_datetime').paginate(page=party_page_number, per_page=4)
        return render_template('party/manage.html', parties=parties)
    else:
        abort(404)

@party_page.route('/explore/<int:party_page_number>', methods=['GET'])
@party_page.route('/explore', methods=['GET'])
def explore(party_page_number=1):
    place = request.args.get('place')
    try:
        lng = float(request.args.get('lng'))
        lat = float(request.args.get('lat'))
        parties = Party.objects(location__near=[lng,lat], location__max_distance=10000,
                                 cancel=False).order_by('-start_datetime').paginate(page=party_page_number, per_page=4)
        return render_template('party/explore.html', parties=parties, place=place, lng=lng, lat=lat)
    except:
        return render_template('party/explore.html', place=place)



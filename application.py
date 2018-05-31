from flask import Flask, redirect, url_for
from flask_mongoengine import MongoEngine
#import config

db = MongoEngine()
app = Flask(__name__)

app.config.from_object('config')

db.init_app(app)

from user.views import user_page
app.register_blueprint(user_page,url_prefix="/user")

from party.views import party_page
app.register_blueprint(party_page,url_prefix="/party")

@app.route('/')
def home():
    return redirect(url_for('party_page.explore'))

#def index():
#    return '<h1>Hello World For Test10!</h1>'


if __name__ == '__main__':
    #app = create_app(config='config')
    app.run(debug=False)
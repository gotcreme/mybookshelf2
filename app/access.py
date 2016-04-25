from flask import request, redirect, flash, render_template, url_for, jsonify, Blueprint, abort
from flask.ext.login import LoginManager, login_user, logout_user
from app.utils import check_pwd, create_token
import app.model as model
from sqlalchemy import or_
from sqlalchemy.orm.exc import NoResultFound


bp=Blueprint('access', __name__)
lm=LoginManager()

@bp.record_once
def on_load(state):
    lm.init_app(state.app)


@lm.user_loader
def load_user(user_id):
    return model.User.query.get(int(user_id))  # @UndefinedVariable


@bp.route('/login', methods=['GET', 'POST'])
def login():
    def check_user(username, pwd):
        user= model.User.query.filter(or_(model.User.user_name == username, model.User.email ==username))\
                            .one_or_none()  
        if user and check_pwd(pwd, user.password):
            return user
        
    username=""
    if request.method=='POST':
        if request.mimetype == 'application/json':
            credentials=request.get_json()
    
            if credentials and (credentials.get('email') or credentials.get('username')) and credentials.get('password'):
                q=model.User.query
                if 'username' in credentials:
                    q=q.filter(model.User.user_name == credentials['username'])
                else:
                    q=q.filter(model.User.email == credentials['email'] )
                
                try:
                    user=q.one()
                except NoResultFound:
                    return jsonify(error= 'Invalid Login')
                if not user.is_active:
                    return jsonify(error= 'Invalid Login')
                if not check_pwd(credentials['password'], user.password):
                    return jsonify(error= 'Invalid Login')
                resp= jsonify(access_token=create_token(user, bp.config['SECRET_KEY'], bp.config.get('TOKEN_VALIDITY_HOURS') or 4))
                #resp.headers.extend(cors_headers)
                return resp
            else:
                print (credentials)
                abort(400,'Provide credentials')
        else:
            
            user=check_user(request.form['username'], request.form['password'] )
            
            if user:
                print('Login user ', user)
                login_user(user)
                #request.args.get("next")
                return redirect('/')
            else:
                flash('Invalid user name or password!')
        
    return render_template('login.html', username=username)

@bp.route('/logoff')
def logoff():
    logout_user()
    return redirect(url_for('access.login'))
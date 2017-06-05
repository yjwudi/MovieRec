#from gevent import monkey
import time
import random
from flask import Flask, render_template, request, g, session, redirect, flash, url_for
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import json 
import requests
from elasticsearch import Elasticsearch
import sqlalchemy
import predictionio
from CFModel import *

#monkey.patch_all()
application = Flask(__name__)
application.config['SECRET_KEY'] = 'secret!'
eventserver_url = 'http://52.87.217.221:7070'
access_key = 'fWPlsqEj5AOv4EQSzkCvz-yoOpjeuPnMyWimv_nZS1pT5ndWzEme8S0hspWVzfo-'

pio_client = predictionio.EventClient(
    access_key=access_key,
    url=eventserver_url,
    threads=5,
    qsize=500
)
disp_process_pref = "===[Process]===: "
cf = CFModel()
cf.load_data()
id_dic = {}
    

#####################################
#
# For hanlding PostGreSQL
#
#####################################
#conn_str = 'postgresql://movie:nerds@52.87.217.221:5432/movie'
conn_str = 'postgresql://movieusr:nopasswd@localhost:5432/movierec'
engine_url = 'https://52.87.217.221:8000/queries.json'

engine = sqlalchemy.create_engine(conn_str)


@application.before_request
def before_request():
    try:
        print("before request")
        g.conn = engine.connect()
        print("connect finished")
    except:
        g.conn = None


@application.teardown_request
def teardown_request(_):
    if g.conn is not None:
        g.conn.close()



# Render home page
@application.route('/')
def index():

    return redirect(url_for('signin'))

    if 'username' not in session:
        return redirect(url_for('signin'))


    response = requests.post(engine_url, json.dumps({'user': session['username'], 'num': 20}), verify=False)
    response = json.loads(response.text)['itemScores']
    print len(response)
    if len(response) == 0:

        cur = g.conn.execute('''
        SELECT *
        FROM movies
        WHERE random() < 0.01
        LIMIT %s''', 20)  

        movie_dict = get_movie(cur)

        
        return render_template('index.html', this_username = session['username'], show_what = "Top Picks", movie_info_list = movie_dict)


    return render_template('index.html', this_username = session['username'], show_what = "Top Picks", movie_info_list = '')

# Render home page
@application.route('/index')
def index_():

    #print("index_")
    username = session['username']
    cur = g.conn.execute('''SELECT * FROM ratings WHERE username=%s LIMIT %s''', (username,20))
    '''
    print("cur:")
    for row in cur:
        print(row)
    '''
    movie_list = []
    rating_list = []
    for row in cur:
        movie_list.append(row[1])
        rating_list.append(row[2])
    print("movie_list")
    print(movie_list)
    print("rating_list")
    print(rating_list)

    movie_dict=[]
    if(len(movie_list)==0):
        cur = g.conn.execute('''SELECT * FROM movies WHERE random() < 0.01 LIMIT %s''', 20)
        movie_dict = get_movie(cur)
    else:
        cf.load_data()
        id_list = cf.co_filter_pre(movie_list, rating_list)
        movie_dict = get_movie_fromdb(id_list)


    
    return render_template('index.html', this_username = session['username'], show_what = "Top Picks", movie_info_list = movie_dict)

def get_movie_fromdb(id_list):
    ans_list = []
    for idx in id_list:
        cur = g.conn.execute('''SELECT * FROM movies WHERE movie_id = %s''', str(idx))
        tmp_list = get_movie(cur)
        ans_list.append(tmp_list[0])
    print("recommend list")
    print(ans_list)
    return ans_list
    

@application.route('/signin', methods = ['GET', 'POST'])
def signin():
    error = None
    print("sinin page")

    if request.method == 'POST':
        username = request.form.get('user-username')
        password = request.form.get('user-password')
        print(username+": "+password)
        cur = g.conn.execute('''SELECT * FROM users WHERE username = %s AND password = %s''', (username, password))
        user = cur.fetchone()
        if user is None:
            print("user is None")
            return render_template('signin.html')

        else:
            
            session['username'] = username
        
        #return redirect(url_for('index'))
        cur = g.conn.execute('''SELECT * FROM movies WHERE random() < 0.01 LIMIT %s''', 20)
        movie_dict = get_movie(cur)
        return render_template('index.html', this_username = session['username'], show_what = "Top Picks", movie_info_list = movie_dict)

    return render_template('signin.html')



@application.route('/signup', methods = ['GET', 'POST'])
def signup():

    if request.method == 'POST':
        username = request.form.get('user-username')
        password = request.form.get('user-password')
        session['username'] = username
        try:
            g.conn.execute('''INSERT INTO users (username, password) VALUES (%s, %s)''', (username, password))
            g.conn.execute('''INSERT INTO userinfo (username) VALUES (%s)''', (username))
            session['username'] = username
        except Exception as e:
            return render_template('signup.html')



        return redirect(url_for('signin'))#render_template('index.html', this_username = session['username'], show_what = "Top Picks", movie_info_list = '')



    return render_template('signup.html')



@application.route('/search_movie', methods = ["POST"])
def search_movie():

    movie_name = request.form.get('search-box')
    movie_name0= movie_name
    movie_name = '%'+movie_name+'%'
    cur = g.conn.execute('SELECT * FROM movies WHERE title like %s LIMIT 20',movie_name)

    movie_dict = get_movie(cur)
        

    return render_template('index.html', this_username = session['username'], show_what = "Search Results: "+movie_name0, movie_info_list = movie_dict)




@application.route('/show_movie')
def show_movie():
    movie_genre = request.args.get('genre')
    genre=[];
    movie_info_list = []
    if movie_genre == 'action':

        genre='%'+'Action'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01 LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Action Movies"
    elif movie_genre == 'romance':
        genre='%'+'Romance'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01 LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Romance Movies"

    elif movie_genre == 'documentary':
        genre='%'+'Documentary'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01 LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Documentary Movies"

    elif movie_genre == 'comedy':
        genre='%'+'Comedy'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01 LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Comedy Movies"

    elif movie_genre == 'drama':
        genre='%'+'Drama'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01  LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Drama Movies"
    elif movie_genre == 'thriller':
        genre='%'+'Thriller'+'%'
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE genre like %s AND random() < 0.01 LIMIT 20',genre)
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)

        show = "Thriller Movies"

    else:
        cur = g.conn.execute('SELECT * FROM movie_genres WHERE random() < 0.01 LIMIT 20')
        
        id_list = get_movieid(cur)
        movie_dict = get_movie_fromdb(id_list)
        
        show = "Others"

    return render_template('index.html', this_username = session['username'], show_what = show, movie_info_list = movie_dict)



@application.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('signin'))



@application.route('/profile')
def profile():
    cur = g.conn.execute('SELECT fullname,gender,mobile,email, description FROM userinfo WHERE username=%s',session['username'])
    userinfo=[row for row in cur]
    print userinfo
    return render_template('profile.html', this_username = session['username'],user_info_list=userinfo)

@application.route('/movie', methods = ["GET", "POST"])
def inbox():

    movie_id = request.args.get('movie_id')
    user_comment = []
    print(request.method)
    if request.method == 'POST':
        
        new_comment = request.form.get('user-comment')
        print(new_comment)

        if new_comment != None:
            print("!!!")
            try:
                g.conn.execute('INSERT INTO comments (username, movie_id, comments) VALUES (%s, %s, %s)', (session['username'], movie_id, new_comment))

            except:
                pass

        else:
            print("???")
            if request.form["btn_cl"] == "1":
                user_rate = 1
                send_rating(session['username'], movie_id, user_rate)
            elif request.form["btn_cl"] == "2":
                user_rate = 2
                send_rating(session['username'], movie_id, user_rate)
            elif request.form["btn_cl"] == "3":
                user_rate = 3
                send_rating(session['username'], movie_id, user_rate)
            elif request.form["btn_cl"] == "4":
                user_rate = 4
                send_rating(session['username'], movie_id, user_rate)
            elif request.form["btn_cl"] == "5":
                user_rate = 5
                send_rating(session['username'], movie_id, user_rate)
            else:
                user_rate = 3
                send_rating(session['username'], movie_id, user_rate)
        
    try:
        cur = g.conn.execute('SELECT comments, username FROM comments WHERE movie_id=%s', (movie_id))
        
        for each in cur:
            user_comment.append([each[1], each[0]])
    except:
        pass

    if user_comment == "None":
        user_comment = []
    cur = g.conn.execute('SELECT * FROM movies WHERE movie_id=%s',movie_id)
    
    movie_dict = get_movie(cur)[0]
    if(movie_dict['movie_id'] in id_dic):
        movie_dict['num'] = id_dic[movie_dict['movie_id']]
    else:
        movie_dict['num'] = random.randint(1, 100)
        id_dic[movie_dict['movie_id']] = movie_dict['num']

    return render_template('movie_page.html', this_username = session['username'], this_movie = movie_dict, this_movie_comment = user_comment)


def send_rating(page_user, movie_id, user_rate):
    print("page_user:")
    print(page_user)

    with g.conn.begin() as _:
        g.conn.execute('DELETE FROM ratings WHERE username = %s AND movie_id = %s', (page_user, movie_id))
        g.conn.execute('INSERT INTO ratings (username, movie_id, rating) VALUES (%s, %s, %s)', (page_user, movie_id, user_rate))
    '''
    pio_client.create_event(
            event="rate",
            entity_type="user",
            entity_id=page_user,
            target_entity_type="item",
            target_entity_id=str(movie_id),
            properties={"rating": user_rate}
        )
    '''

@application.route('/profile-edit',methods = ["GET", "POST"])
def profile_edit():
    fullname = request.form.get('user-fullname')
    gender = request.form.get('user-gender')
    mobile = request.form.get('user-mobile')
    email = request.form.get('user-email')
    description = request.form.get('user-description')
    # username=session['username']
    print (session['username'],fullname,gender,mobile,email, description)
    g.conn.execute('Delete from userinfo where username=%s', session['username'])
    g.conn.execute('INSERT INTO userinfo (username,fullname,gender,mobile,email, description) VALUES (%s,%s, %s, %s,%s,%s)', (session['username'],fullname,gender,mobile,email, description))
    # if fullname!=[]
    #     flag=1;
    # flash('You profile has been updated.')


    return render_template('profile-edit.html', this_username = session['username'])

def get_movieid(cur):
    ans_list = [row[0] for row in cur]
    print("genre ans_list:")
    print(ans_list)
    return ans_list

def get_movie(cur):
    '''
    print("cur:")
    for row in cur:
        print(len(row))
        print(row)
    '''

    movie_info = {row[0]: (row[1], row[2],row[3],row[4]) for row in cur}
    genre_info = {}
    for key in movie_info:
        cur2 = g.conn.execute('''SELECT * FROM movie_genres WHERE movie_id = %s''', str(key))
        for row in cur2:
            if(row[0] not in genre_info.keys()):
                genre_info[row[0]] = row[1]
            else:
                genre_info[row[0]] += "tmp"+row[1]

    print("genre_info:")
    print(genre_info)
    movies = []
    for key in movie_info:
        movies.append({'movie_id': key,
                       'imdb_id': movie_info[key][0],
                       'tmdb_id': movie_info[key][1],
                       'title': movie_info[key][2],
                       'year': movie_info[key][3],
                       'genre': genre_info[key]})
        '''
                       ,
                       'plot': movie_info[key][4],
                       'rated': movie_info[key][5],
                       'released': movie_info[key][6],
                       'runtime': movie_info[key][7],
                       'genre': movie_info[key][8],
                       'director': movie_info[key][9],
                       'writer': movie_info[key][10],
                       'actors': movie_info[key][11],
                       'language': movie_info[key][12],
                       'country': movie_info[key][13],
                       'awards': movie_info[key][14],
                       'poster': movie_info[key][15],
                       'metascore': movie_info[key][16],
                       'imdbrating': movie_info[key][17],
                       'imdbvotes': movie_info[key][18],
                       'type': movie_info[key][19]})
        '''
    return movies
# Main function
if __name__ == '__main__':
    application.run(debug=True, host="0.0.0.0", port=5000)
    #application.run()



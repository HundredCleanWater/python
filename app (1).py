from bson.json_util import dumps
from googleapiclient.discovery import build
from flask import Flask, render_template, jsonify, request
from pymongo import MongoClient
from datetime import datetime, timedelta
import random
import jwt
import hashlib

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True
app.config['UPLOAD_FOLDER'] = "./static/profile_pics"

SECRET_KEY = 'SPARTA'

client = MongoClient('localhost', 27017)
db = client.youtuberandomplaylist

api_key = 'AIzaSyDoc0GN-_nBuANpy8f893HDttg71tF5szs'
youtube = build('youtube', 'v3', developerKey=api_key)


## Key = 설정되는 쿠키의 키 (이름) / Value = 쿠키의 값 / path = 쿠키를 지정된 경로로 제한 parameter = 매개변((함수를 정의할 때 사용되는 변수)
def get_user_info():
    token_receive = request.cookies.get('mytoken')  #token을 생성하고 request.cookies.get('mytoken')을 통해 쿠키를 불러 온다.
    render_params = {}  # code가 길어 지기 때문에 render_template에서 전달 할 값들을 명시하지 않고 다른 dictionary 객체를 만들고 키워드 인자로 전달(dictionary 객체 에 대해서는 노션에 기록)
    #그리고 하나의 route함수에서 조건에 따라 N개의 화면을 로드해야 하는 경우(하나의 render_params이지만 각기 다른 데이터를 넣을 수 있음)에 쓰인다고 하는데 아마 이게 맞을 것 같다.
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256']) #payload 는 JWT에 대한 내용을 적는다. payload안에 있는 속성들을 클레임 셋 (Claim Set)이라 부른다.
        #클레임 셋은 JWT에 대한 내용(토큰 생성자(클라이언트)의 정보, 생성 일시 등)이나 클라이언트와 서버 간 주고 받기로 한 값들로 구성(현재는 주고받는 값으로 되어 있는 것 같다)
        user_info = db.users.find_one({"id": payload["id"]}) #mongo db에서 id를 가져와 user에 대한 정보를 얻는다.
        render_params = user_info #유저의 정보를 render_params에게 준다. data type -> list
    except jwt.ExpiredSignatureError: #유효시간이 지난 토큰 에러를 먼저 잡는다.// list형식을 맞춰주기 위해 (json은 **형식 같은게 되지 않아서 list형식으로 맞춰줌)
        render_params['msg'] = '로그인 시간이 만료되었습니다.'
    except jwt.exceptions.DecodeError: #토큰이 빈 문자열이거나 payload가 손상되었을 때 에러를 잡아준다.(유효한 토큰이 존재하지 않는 것)
        render_params['msg'] = '로그인 정보가 존재하지 않습니다..'
    finally:
        return render_params #render_params 의 값을 반환한다.




# HTML을 주는 부분
@app.route('/')
def home():
    # 가장 많이 추가한 상위 3개의 태그 목록만 출력
    top_tags = list(db.tag.find({}, {'_id': False}).distinct('tag')) #tag db에서 tag값들을 중복제거하여 찾는다.
    random.shuffle(top_tags) #무작위로 섞어준다.
    top_tags_response = top_tags[:3] #상위 3개 태그만 top_tags_response에 입력한다. -> 서치바 밑에 부분인듯

    user_info = get_user_info() #위 def get_user_info()에서 얻은 user_info를 준다.
    return render_template('index.html',
                           toptags=top_tags_response,
                           **user_info) #render_template에서 주의 할 점은 template 폴더 내에 있는 html값만 불러 올 수 있다.
#toptags는 html 내에서 사용 할 변수 이름이고 top_tags_response는 py에 있는 변수 값이다. **이란 list를 풀어주는 명령어..!(parameter에 입력되는 데이터 형식이 딕셔너리 형태)


@app.route('/index') #localhost:5000/index page
def index():
    # 가장 많이 추가한 상위 3개의 태그 목록만 출력
    top_tags = list(db.tag.find({}, {'_id': False}).distinct('tag'))
    random.shuffle(top_tags)
    top_tags_response = top_tags[:3]

    user_info = get_user_info()
    return render_template('index.html',
                           toptags=top_tags_response,
                           **user_info)
#GET,POST : https://rural-coach-cc5.notion.site/GET-POST-8e4d3a7a7cb743fca7aff3368d98b89a 에 기록
#GET -> url에 던져주는 것(/index?id  / POST ->url에 추가x
@app.route('/login')
def login():
    user_info = get_user_info()
    return render_template('login.html', **user_info)


@app.route('/agreement', methods=['GET']) #동의 페이지는 단순히 조회만 하기때문에 GET을 쓴듯 ?
def agreement():
    user_info = get_user_info()
    return render_template('agreement.html', **user_info)


@app.route('/sign_up', methods=['GET'])
def sign():
    user_info = get_user_info()
    return render_template('sign_up.html', **user_info)


@app.route('/randomplaylist', methods=['GET'])
def play():
    # 무작위 태그 목록을 5개 출력
    top_tags = list(db.tag.find({}, {'_id': False}).distinct('tag')) #tag db에서 tag값들을 중복제거하여 찾는다.
    random.shuffle(top_tags)
    top_tags_response = top_tags[:5]

    playlistId_receive = request.args.get('playlistId') #args.get는 딕셔너리 형태로 {key:value}로 나오게 됨. 하나의 매개변수(playlistId)만 전달한다./
    #playlistId를 조회하여 바로 원하는 데이터를 준다.
    author_receive = request.args.get('author')

    # 플레이리스트
    likes = list(db.like_playlist.find({'playlistId': playlistId_receive}, {'_id': False})) # like_playlist에서 playlistId_receive를 이용하여 정보를 찾아냄
    likes_response = likes[:2] #likes목록에서 2개만 가져온다.  0:2 -> 0,1 0:3 -> 0,1,2
    likes_cnt = len(likes) - 2 #+몇개인지 보기위해 설정 (2개는 위에서 가져왔으니 -2)
    comments = list(db.comment.find({'author': author_receive, 'playlistId': playlistId_receive}, {'_id': False}))

    user_info = get_user_info()

    return render_template("randomplaylist.html",
                           playlistId=playlistId_receive,
                           toptags=top_tags_response,
                           likes=likes_response,
                           likes_cnt=likes_cnt,
                           comments=comments,
                           **user_info)
    ## jinja 형식 사용


@app.route('/feed')
def feed():
    user_info = get_user_info() #재사용성을 높이기 위해
    if 'id' not in user_info:
        return render_template('index.html') #id가 user_info에 없으면 index.html로 돌아가 !

    # 내가 추가한 태그 목록을 출력
    tags = list(db.tag.find({'id': user_info['id']}, {'_id': False}))
    random.shuffle(tags) #찾은 tags를 랜덤하게 출력해줌 매번 a b c d 로 나오는게 아니라 b c d a 이런식으로도 나오게 하기 위해 이렇게 하신건가요?

    # 내가 만든 플레이리스트 목록을 출력
    my_playlists = list(db.user_playlist.find({'id': user_info['id']}, {'_id': False}))

    # 내가 좋아요 한 플레이리스트 목록을 출력
    like_playlists = list(db.like_playlist.find({'id': user_info['id']}, {'_id': False}))

    # 다른 사람들이 만든 플레이리스트 목록을 출력
    other_playlists = list(db.user_playlist.find({'id': {'$nin': [user_info['id']]}}, {'_id': False}))

    return render_template('feed.html',
                           tags=tags,
                           my_playlists=my_playlists,
                           like_playlists=like_playlists,
                           other_playlists=other_playlists,
                           **user_info)


@app.route('/modal')
def modal():
    return render_template('modal.html')


@app.route('/header')
def header():
    return render_template('header.html')


# API 역할을 하는 부분
# login.html
@app.route('/sign_in', methods=['POST']) #데이터 저장부분(requset.form 부분이 있기때문에 POST로 하신 듯 ? )
def sign_in():
    # 로그인
    id_receive = request.form['id_give'] #id_give로 넘어 온 정보를 저장
    password_receive = request.form['password_give']

    pw_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest() #이건 암호화 인듯?
    result = db.users.find_one({'id': id_receive, 'password': pw_hash}) #db에 지금 정보들이 있엉? 결과값으로 나타내봐!

    if result is not None: #결과값이 있다면 payload로 jwt정보값을 읽는다.
        payload = {
            'id': id_receive,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 24)  # 로그인 24시간 유지 exp: 토큰의 만료시간(expiration)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')  # jwt.encode({<유저정보>}, <시크릿키>, algorithm = '특정 알고리즘')   # 명령어 구성

        return jsonify({'result': 'success', 'token': token}) #사용자가 json data를 내보내도록 제공하는 flask 함수./결과값은 성공이고 token을 준다.
    # 찾지 못하면
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/sign_up/save', methods=['POST'])
def sign_up():
    id_receive = request.form['id_give']
    password_receive = request.form['password_give']
    nickname_receive = request.form['nickname_give']
    password_hash = hashlib.sha256(password_receive.encode('utf-8')).hexdigest()
    doc = {
        "id": id_receive,  # 아이디
        "password": password_hash,  # 비밀번호
        "nickname": nickname_receive,  # 닉네임
    }
    db.users.insert_one(doc)
    return jsonify({'result': 'success'})


@app.route('/sign_up/check_dup', methods=['POST'])
def check_dup():
    id_receive = request.form['id_give']
    exists = bool(db.users.find_one({"id": id_receive}))  #db에 현재 이 아이디가 존재하냐? bool(참거짓)으로 판단.
    return jsonify({'result': 'success', 'exists': exists})


@app.route('/sign_up/check_dup2', methods=['POST'])
def check_dup2():
    nickname_receive = request.form['nickname_give']
    exists = bool(db.users.find_one({"nickname": nickname_receive}))
    return jsonify({'result': 'success', 'exists': exists})


#randomplaylist.html
@app.route('/search', methods=['GET'])
def listing():
    query_receive = request.args.get('q') # q라는 정보를 조회 해 줘 /serch?q= youtube 인자형식때문에 q로받음

    # 키워드 검색 결과 받아오기 ( Youtube Data Api 사용 )
    search_response = youtube.search().list(
        q=query_receive,
        order="viewCount", #조회수
        part="snippet",
        maxResults=10
    ).execute()

    return jsonify({'list': search_response})


@app.route('/playlist/search', methods=['POST'])
def search_playlist():
    playlistId_receive = request.form['playlistId_give']
    author_receive = request.form['author_give']
    playlist = db.user_playlist.find_one({'id': author_receive, 'playlistId': playlistId_receive})

    if playlist is not None:
        author_info = db.users.find_one({'id': author_receive},
                                        {'nickname': True}) #playlist에 있으면 작성자 정보를 찾아줘(닉네임으로 받을거야)
        msg = playlist
    else:
        msg = '존재하지 않는 플레이리스트입니다.'

    return jsonify({'playlist': dumps(msg), 'nickname': dumps(author_info)}) #작성자 정보를 닉네임으로 준다?-> 혹시 한글때문인지?
    #list형식은 인수를 넣지 못함. dump -> json형식의 string으로 바꿔 줌(Json은 아님..!)

#modal.html
@app.route('/playlist/insert', methods=['POST'])
def insert_playlist():
    playlistId_receive = request.form['playlistId_give']
    title_receive = request.form['title_give']
    id_receive = request.form['id_give']

    # 1. 이미 등록한 플레이리스트인지 확인
    playlist = db.user_playlist.find_one({'playlistId': playlistId_receive, 'id': id_receive})

    # 2. 유효한 playlistId인지 확인(Youtube Data Api 사용)
    search_response = youtube.playlists().list(
        id=playlistId_receive,
        part="snippet"
    ).execute()

    thumbnail = ''

    msg = 'Hi!'

    if search_response is not None:
        thumbnail = search_response['items'][0]['snippet']['thumbnails']['high']['url']
        if playlist is None:
            doc = {'id': id_receive,
                   'title': title_receive,
                   'playlistId': playlistId_receive,
                   'thumbnail': thumbnail}
            db.user_playlist.insert_one(doc) #playlist에 없다면 정보들을 저장해줘.
            msg = '작성 완료!'
        else:
            msg = '작성 실패! 이미 등록한 재생목록입니다.'
    else:
        msg = '작성 실패! 잘못된 재생목록입니다.'

    return jsonify({'msg': msg})


@app.route('/tag', methods=['GET']) #find는 조회기때문에 GET? 찾기만 해주는 기능이여서
def tag_show():
    id = 'test'
    tag = list(db.tag.find({'id': id}, {'_id': False}))

    return jsonify({'tags': tag})


@app.route('/tag/insert', methods=['POST'])
def tag_insert():
    id_receive = request.form['id_give']
    tag_receive = request.form['tag_give']
    videoId_receive = request.form['videoId_give']

    doc = {
        'id': id_receive,
        'tag': tag_receive,
        'videoId': videoId_receive
    }

    db.tag.insert_one(doc)

    return jsonify({'msg': '저장 완료!'})


@app.route('/tag/delete', methods=['POST'])
def tag_delete():
    id_receive = request.form['id_give']
    tag_receive = request.form['tag_give']
    db.tag.delete_one({'id': id_receive, 'tag': tag_receive}) #태그삭제
    return jsonify({'msg': '삭제 완료!'})


@app.route('/tag/popular', methods=['GET'])
def tag_popular():
    lists = db.tag.aggregate([ #data 처리 pipeline(이전 단계 연산결과를 단계연산에 이용)/
        {"$group": {"_id": {"tag": "$tag", "status": "$status"}, "count": {"$sum": 1}}}, #_id가 태그 했으면 합 1을 올려줌 (status의 기능은 모르겠음)
        {"$sort": {"_id.source": -1}} #_id.source를 내림차순
    ])

    tag = []
    for list in lists:
        tag.append(list)

    return jsonify({'tags': tag})


@app.route('/tag/user_list', methods=['GET'])
def tag_user():
    tag_receive = request.args.get('tag_give')
    tag = list(db.tag.find({'tag': tag_receive}, {'_id': False}))

    return jsonify({'tags': tag})


@app.route('/tag/what_tag', methods=['GET'])
def what_tag():
    videoId_receive = request.args.get('videoId_give')
    tag = db.tag.distinct('tag', {'videoId': videoId_receive})

    return tag


# @app.route('/comment', methods=['GET'])
# def comment():
#     videoId_receive = request.args.get('videoId_give')
#     comments = list(db.comment.find({'videoId': videoId_receive}, {'_id': False}))
#
#     return jsonify({'comments': comments})
#
#
# @app.route('/comment/my_comment', methods=['GET'])
# def user_comment():
#     id_receive = request.args.get('id_give')
#     comments = list(db.comment.find({'id': id_receive}, {'_id': False}))
#
#     return jsonify({'comments': comments})


@app.route('/comment/insert', methods=['POST'])
def comment_insert():
    id_receive = request.form['id_give']
    comment_receive = request.form['comment_give']
    playlistId_receive = request.form['playlistId_give']
    author_receive = request.form['author_give']

    db.comment.insert_one({'id': id_receive,
                           'comment': comment_receive,
                           'playlistId': playlistId_receive,
                           'author': author_receive})

    return jsonify({'msg': '작성 완료!'})


@app.route('/comment/delete', methods=['POST'])
def comment_delete():
    id_receive = request.form['id_give']
    comment_receive = request.form['comment_give']
    videoId_receive = request.form['videoId_give']

    db.comment.delete_one({'id': id_receive,
                       'comment': comment_receive,
                       'videoId': videoId_receive})

    return jsonify({'msg': '삭제 완료!'})


if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)


@app.route('/user/playlist', methods=['GET'])
def user_playlist():
    id_receive = request.args.get('id_give')
    playlistId = list(db.user_playlist.find({'id': id_receive}, {'_id': False}))
    return jsonify({'playlist': playlistId})


@app.route('/user/likelist', methods=['GET'])
def user_likelist():
    id_receive = request.form['id_give']
    likelistId = list(db.like_playlist.find({'id': id_receive}, {'_id': False}))
    return jsonify({'playlist': likelistId})


@app.route('/likelist', methods=['POST'])
def user_like():
    user_info = get_user_info()
    if 'id' not in user_info:
        return jsonify({'msg': "유효하지 않은 회원입니다."})

    author_receive = request.form['author_give']
    playlistId_receive = request.form['playlistId_give']
    print(author_receive, playlistId_receive)
    like_playlist = db.like_playlist.find_one({'id': user_info['id'],
                                               'author': author_receive,
                                               'playlistId': playlistId_receive})

    thumbnail = db.user_playlist.find_one({'id': author_receive, 'playlistId': playlistId_receive},
                                          {'thumbnail': True})

    doc = {'id': user_info['id'],
           'author': author_receive,
           'playlistId': playlistId_receive,
           'thumbnail': thumbnail['thumbnail']}

    if like_playlist is None:
        db.like_playlist.insert_one(doc)
        msg = '작성 완료!'
    else:
        db.like_playlist.delete_one(doc)
        msg = '삭제 완료!'

    return jsonify({'msg': msg})
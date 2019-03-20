from socket import timeout
from threading import Thread
import sqlite3
import time, json, database
from datetime import datetime, timedelta

class Matcher:
    def __init__(self,):
        self._rooms_dict = {}

    def add_room(self, room):
        self._rooms_dict[room.name] = room

    def match_by_room_name(self, room_name, player):
        self._rooms_dict[room_name].add_player(player)



class Room(Thread):
    def __init__(self, name, capacity, min_bet, max_bet):
        Thread.__init__(self)
        self._counter       = -1
        self._players       = []

        self.name           = name
        self.min_bet        = min_bet
        self.max_bet        = max_bet
        self.capacity       = capacity




class Player(Thread):
    PLAYER_ID = -1
    
    def __init__(self, socket):
        Thread.__init__(self)

        Player.PLAYER_ID   += 1
        self._joined_room   = None

        socket.settimeout(5)

        self._server_id     = Player.PLAYER_ID
        self._socket        = socket
        self.request_queue  = []

        self._player_name   = None
        self._player_id     = None


    @property
    def player_info(self,):
        return {"NAME":str(self._player_name) ,"SERVER_ID":str(self._server_id) ,"MONEY":"50000"}


    def run(self,):
        self.on_client_connect()
        while True:
            requests = self.recv_data()

            if requests is None: break
            if requests is "TIMEOUT": continue

            for request in requests:
                self.process_request(request)


    def on_client_connect(self,):
        self.send_data({"TYPE": "CONNECTED", "SERVER_ID": str(self._server_id)})


    def on_client_timeout(self,):
        if self._player_name is None:
            self.send_data({"TYPE": "GET_PLAYER_INFO", "MSG": "Server is asking you to send your info. username, userID and accessToken"})


    def on_client_disconnect(self,):
        print("CLIENT ID:%s HAS DISCONNECTED" % (self._server_id))
        quit()


    def send_data(self, data_dict):
        """ Convert the dict into json and append the EndOfFile mark """

        json_form = json.dumps(data_dict) + "<EOF>"
        valid_socket_form = json_form.encode('ascii')
        try:
            return self._socket.send(valid_socket_form)
        except Exception as e:
            self.on_client_disconnect()
            return None


    def recv_data(self,):
        """ This function will return a list of valid socket segments transmitted over the network """

        frame, eof = bytes('', 'ascii'), '<EOF>'
        try:
            while not frame.endswith(bytes(eof, 'ascii')):
                tmp_frame = self._socket.recv(1024)
                frame += tmp_frame

                if tmp_frame is None or len(tmp_frame) == 0:
                    if len(frame) > 0:
                        break
                    else:
                        raise Exception("CLIENT DISCONNECTED")

        except timeout as e:
            self.on_client_timeout()
            return "TIMEOUT"
        except Exception as e:
            self.on_client_disconnect()
            return None

        string_frames = []
        for single_frame in frame.decode('ascii').split(eof):
            try:
                string_frames.append(json.loads(single_frame))
            except Exception as e:
                continue
        return string_frames


    def process_request(self, request):
        if not 'TYPE' in request: return

        if request['TYPE'] == "REQUEST_PLAYER_INFO":
            self._player_name = request['DEVICE_ID']
            print("Got requestplayerinfo request from ", request['DEVICE_ID'])
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()
            t = (request['DEVICE_ID'],)
            c.execute("SELECT id FROM users WHERE devid=?", t)
            conn.commit()

            tempResult = c.fetchall()

            if len(tempResult) == 0:
                print("User Not found in database. adding user" , request['DEVICE_ID'] , "to database")

                c.execute("SELECT * FROM users")

                user = [self.PLAYER_ID, request['DEVICE_ID'], "DUMMYNAME", "100", "1", "0", "0", "0", "0"]

                print("about to add this: " , user)

                c.execute("insert into users VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (user[0], user[1], user[2], user[3], user[4], user[5], user[6], user[7], user[8]))

                conn.commit()

                t = [request['DEVICE_ID']]

                c.execute("SELECT * FROM users WHERE devid=?", t)

                playerData = c.fetchone()

                # Find player rank
                c.execute("SELECT id FROM users ORDER BY points DESC")

                sortedUsers = c.fetchall()

                playerRank = sortedUsers.index((playerData[0], )) + 1

                self.send_data({"TYPE": "PLAYER_INFO", "PLAYER_ID": str(playerData[0]), "PLAYER_NAME": playerData[2], "PLAYER_POINTS": playerData[3], "PLAYER_LEVEL": playerData[4], "PLAYER_QUESTIONS_COUNT": playerData[5], "PLAYER_HELPFUL_COUNT": playerData[6], "PLAYER_EVALUATIONS_COUNT": playerData[7], "PLAYER_ANSWERS_COUNT": playerData[8], "PLAYER_RANK": str(playerRank)})
                
            else:

                print("Found user!")

                c.execute("SELECT * FROM users WHERE devid=?", t)

                playerData = c.fetchone()

                # Find player rank
                c.execute("SELECT id FROM users ORDER BY points DESC")

                sortedUsers = c.fetchall()

                print(sortedUsers, ", Gonna try to find index of ", (playerData[0], ))

                playerRank = str( sortedUsers.index((playerData[0], )) + 1 )

                print("found index! Player rank is ", playerRank)

                self.send_data({"TYPE": "PLAYER_INFO", "PLAYER_ID": str(playerData[0]), "PLAYER_NAME": playerData[2], "PLAYER_POINTS": playerData[3], "PLAYER_LEVEL": playerData[4], "PLAYER_QUESTIONS_COUNT": playerData[5], "PLAYER_HELPFUL_COUNT": playerData[6], "PLAYER_EVALUATIONS_COUNT": playerData[7], "PLAYER_ANSWERS_COUNT": playerData[8], "PLAYER_RANK": "test"})

                self.send_data({"TYPE": "PLAYER_RANK", "PLAYER_RANK": playerRank})

            conn.close()

            return

        if request['TYPE'] == "GET_POSTS_REQUEST":

            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()
            c.execute("SELECT * FROM posts ORDER BY date DESC LIMIT 10")
            top10posts = c.fetchall()

            for post in top10posts:
                t = [str(post[0])]
                c.execute("SELECT userid FROM postlikes WHERE postid=?", t)
                likers = c.fetchall()
                likedByCurrentUser = "NO"
                if len(likers) > 0:
                    if request["PLAYER_ID"] in likers[0]:
                        likedByCurrentUser = "YES"
                    else:
                        likedByCurrentUser = "NO"
                else:
                        likedByCurrentUser = "NO"

                for key, value in request.items():
                    print ("Key is: ", key, ", Value is: ", value)
                #Check if post has filters and apply them

                #MY_QUESTIONS filter

                MyQuestionsCheck = request["MY_QUESTION"]
                if MyQuestionsCheck == "YES":
                    t = [str(post[0])]
                    c.execute("SELECT posterid FROM posts WHERE postid=?", t)
                    posterid = c.fetchone()[0]
                    print("Going to compare posterid ", posterid, " with PLAYER_ID ", request['PLAYER_ID'])
                    if request['PLAYER_ID'] != posterid:
                        continue


                #GENRE filter

                QuestionGenre = request["QUESTIONS_GENRE"]
                if QuestionGenre != "NONE":
                    t = [str(post[0])]
                    c.execute("SELECT genre FROM posts WHERE postid=?", t)
                    genre = c.fetchone()[0]
                    print("Going to compare QuestionGenre ", QuestionGenre, " with genre ", genre)
                    if QuestionGenre != genre:
                        continue

                #Check whether question expired
                t = [str(post[0])]
                c.execute("SELECT date FROM posts WHERE postid=?", t)
                postdate = datetime.strptime(c.fetchone()[0], '%Y-%m-%d %H:%M:%S.%f') + timedelta(weeks=1)
                print("About to compare ", datetime.now(), ", With ", postdate)
                if postdate < datetime.now():
                    continue


                self.send_data({"TYPE": "POST_INFO", "POST_ID": str(post[0]), "USER_ID": post[1], "DATE": post[2], "POINTS": str(post[3]), "CONTENT": post[4], 'LIKED': likedByCurrentUser})

            conn.close()

            return

        if request['TYPE'] == "SEND_POST_REQUEST":
            print("Got SEND_POST_REQUEST. About to connect to database file.")
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()
            print("Connected to database file.")
            c.execute("SELECT COUNT(*) FROM posts")
            conn.commit()
            postsCount = c.fetchone()

            t = [str(postsCount[0]), request["PLAYER_ID"], datetime.now(), str(request["POST_POINTS"]), request["POST_CONTENT"], request["POST_GENRE"]]

            c.execute("insert into posts values(?,?,?,?,?,?)", (t[0], t[1], t[2], t[3], t[4], t[5]))
            conn.commit()

            # Get poster points
            t = request["PLAYER_ID"]
            c.execute("SELECT points FROM users WHERE id = ?", t)
            posterPoints = float(c.fetchone()[0])
            # Get post points
            postPoints = request["POST_POINTS"]
            print("Trying to convert ", postPoints, " into an int like : ", int(postPoints))
            posterPoints += float(postPoints)/2
            # Add points to poster
            t = [posterPoints, request["PLAYER_ID"]]
            c.execute("UPDATE users SET points=? WHERE id=?", (t[0], t[1]))
            conn.commit()
            newLevel = calcLevel(posterPoints)
            t = [str(newLevel)]
            print("new level should be ", t)
            c.execute("UPDATE users SET level=?", t)
            conn.commit()

            self.send_data({"TYPE": "POST_ADDED"})

            conn.close()

            return

        if request['TYPE'] == "SEND_COMMENT_REQUEST":
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()
            c.execute("SELECT COUNT(*) FROM comments")
            conn.commit()
            commentsCount = c.fetchone()

            t = [str(commentsCount[0]), request["PLAYER_ID"], str(request["CONTENT"]), request["POST_ID"], datetime.now()]
            

            c.execute("insert into comments values(?,?,?,?,?)", (t[0], t[1], t[2], t[3], t[4]))
            conn.commit()

            # Get commenter points
            t = request["PLAYER_ID"]
            c.execute("SELECT points FROM users WHERE id = ?", t)
            commenterPoints = float(c.fetchone()[0])
            # Get comment points
            t = [commentsCount[0]]
            c.execute("SELECT postid from comments WHERE id = ?", t)
            postid = c.fetchone()[0]
            t = [postid]
            c.execute("SELECT points from posts WHERE postid = ?", t)
            commentPoints = c.fetchone()[0]
            commenterPoints += float(commentPoints)/2
            # Add points to commenter
            t = [commenterPoints, request["PLAYER_ID"]]
            c.execute("UPDATE users SET points=? WHERE id=?", (t[0], t[1]))
            conn.commit()
            newLevel = calcLevel(commenterPoints)
            t = [str(newLevel)]
            c.execute("UPDATE users SET level=?", t)
            conn.commit()

            self.send_data({"TYPE": "COMMENT_ADDED"})

            conn.close()

            return

        """if request['TYPE'] == "SEND_COMMENT_LIKE_REQUEST":
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()

            # Will need to :
            # Check if user already liked comment.
            # If he already did, remove him from likers list.
            # If not, Add a new row to commentlikes table, fill it with userid, postid and commentid

            t = [request['COMMENT_ID'], request['PLAYER_ID'], request['POST_ID']]

            c.execute("SELECT * FROM commentlikes WHERE commentid=? AND userid=? AND postid=?", (t[0], t[1], t[2]))

            result = c.fetchone()

            if (result is None):

                c.execute("INSERT INTO commentlikes VALUES (?,?,?)", (t[0], t[1], t[2]))
                conn.commit()
                conn.close()

            else:

                c.execute("DELETE FROM commentlikes WHERE commentid=? AND userid=? AND postid=?", (t[0], t[1], t[2]))
                conn.commit()
                conn.close()

            self.send_data({"TYPE": "COMMENT_LIKE_ADDED"})

            return"""

        if request['TYPE'] == "SEND_USER_EVALUATION_REQUEST":
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()

            # Will need to :
            # Check if user already evaluated comment.
            # If he already did, change his evaluation string into the new value.
            # If not, Add a new row to evaluations table, fill it with userid, postid, commentid and evaluation string

            t = [request['COMMENT_ID'], request['PLAYER_ID'], request['POST_ID'], request['USER_EVALUATION']]

            c.execute("SELECT * FROM evaluations WHERE commentid=? AND userid=? AND postid=?", (t[0], t[1], t[2]))

            result = c.fetchone()

            if (result is None):

                c.execute("INSERT INTO evaluations VALUES (?,?,?, ?)", (t[0], t[1], t[2], t[3]))
                conn.commit()

            else:

                c.execute("UPDATE evaluations SET evaluation=? WHERE commentid=? AND userid=? AND postid=?", (t[3], t[0], t[1], t[2]))
                conn.commit()

            self.send_data({"TYPE": "EVALUATION_ADDED"})

            # Give points to comment owner if this user evaluated him as Helpful

            if request['USER_EVALUATION'] == 'HELPFUL':
                # Get commenter ID
                t = [request['COMMENT_ID'], request['POST_ID']]
                c.execute("SELECT userid FROM comments WHERE id=? AND postid =?", (t[0], t[1]))
                commenterId = c.fetchone()[0]
                # Get commenter points
                t = [commenterId]
                c.execute("SELECT points FROM users WHERE id = ?", t)
                commenterPoints = int(c.fetchone()[0])
                # Get post points
                t = request['POST_ID']
                c.execute("SELECT points FROM posts WHERE postid=?", t)
                postPoints = c.fetchone()[0]
                pointsToAdd = postPoints
                commenterPoints += pointsToAdd
                # Add new points to commenter
                t = [commenterPoints, commenterId]
                c.execute("UPDATE users SET points=? AND level=? WHERE id=?", (t[0], t[1], t[2]))
                conn.commit()
                newLevel = calcLevel(commenterPoints)
                t = [str(newLevel)]
                c.execute("UPDATE users SET level=?", t)
                conn.commit()
                

            # Deduce points from comment owner if this user evaluated him as Not Helpful
            elif request['USER_EVALUATION'] == 'NOT_HELPFUL':
                # Get commenter ID
                t = [request['COMMENT_ID'], request['POST_ID']]
                c.execute("SELECT userid FROM comments WHERE id=? AND postid =?", (t[0], t[1]))
                commenterId = c.fetchone()[0]
                # Get commenter points
                t = [commenterId]
                c.execute("SELECT points FROM users WHERE id = ?", t)
                commenterPoints = int(c.fetchone()[0])
                # Get post points
                t = request['POST_ID']
                c.execute("SELECT points FROM posts WHERE postid=?", t)
                postPoints = c.fetchone()[0]
                pointsToAdd = postPoints
                commenterPoints -= pointsToAdd
                if commenterPoints > 0:
                    # Deduce points from commenter
                    t = [commenterPoints, commenterId]
                    c.execute("UPDATE users SET points=? WHERE id=?", (t[0], t[1]))
                    conn.commit()
                    newLevel = calcLevel(commenterPoints)
                    t = [str(newLevel)]
                    c.execute("UPDATE users SET level=?", t)
                    conn.commit()

            conn.close()

            return

        if request['TYPE'] == "SEND_POST_LIKE_REQUEST":
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()

            # Will need to :
            # Check if user already liked comment.
            # If he already did, remove him from likers list.
            # If not, Add a new row to commentlikes table, fill it with userid, postid and commentid

            t = [ request['PLAYER_ID'], request['POST_ID']]

            c.execute("SELECT * FROM postlikes WHERE userid=? AND postid=?", (t[0], t[1]))

            result = c.fetchone()

            if result is None:
                c.execute("INSERT INTO postlikes VALUES (?,?)", (t[1], t[0]))
                conn.commit()
                conn.close()

            else:
                print("Removing like")
                c.execute("DELETE FROM postlikes WHERE userid=? AND postid=?", (t[0], t[1]))
                conn.commit()
                conn.close()

            self.send_data({"TYPE": "POST_LIKE_ADDED"})

            return

        if request['TYPE'] == "GET_COMMENTS_REQUEST":

            
            conn = sqlite3.connect('sharex.db')
            c = conn.cursor()

            #Retrieve all comments on that post

            t = [request["POST_ID"]]
            print("t is: ", t , " because request POST_ID is: ", request["POST_ID"])
            c.execute("SELECT * FROM comments WHERE postid=? ORDER BY date DESC ", t)
            comments = c.fetchall()
            print("comments is: " , comments)
            conn.commit()

            #Check if current user evaluated that comment, and send his evaluation
            #Send total evaluations of each type for each comment

            for cmnt in comments:
                t = [cmnt[0]]
                print("cmnt is: ", cmnt, ", but cmnt[0] is: ", cmnt[0])

                #Check if comment is posted by current user, to forbid him from evaluating his own comment
                c.execute("SELECT userid FROM comments WHERE id=?", t)
                commenters = c.fetchall()
                print("commenters are: ", commenters)
                canEvaluate = "YES"
                if len(commenters) > 0:
                    if request["PLAYER_ID"] in commenters[0]:
                        canEvaluate = "NO"
                        print("User owns this comment, thus he CAN'T evaluate it")

                c.execute("SELECT userid FROM evaluations WHERE commentid=?", t)
                evaluators = c.fetchall()
                print("evaluators are: " , evaluators)
                userEvaluation = "NONE"
                if len(evaluators) > 0:
                    if request["PLAYER_ID"] in evaluators[0]:
                        print("user", request["PLAYER_ID"], " EVALUATED that comment")
                        t = [ cmnt[0], request['PLAYER_ID']]
                        c.execute("SELECT evaluation FROM evaluations WHERE commentid=? AND userid=?", (t[0], t[1]))
                        userEvaluation = c.fetchone()[0]
                        print("User evaluation on this comment is: ", userEvaluation)
                    else:
                        print("user", request["PLAYER_ID"], " DID NOT EVALUATE that comment")
                else:
                        print("user", request["PLAYER_ID"], " DID NOT EVALUATE that comment")

                #Now need to find evaluations count for each evaluation type
                helpfulEvs = 0
                unsureEvs = 0
                notHelpfulEvs = 0

                #Find how many users evaluated as helpful
                t = [cmnt[0], "HELPFUL"]
                c.execute("SELECT COUNT(*) FROM evaluations WHERE commentid=? AND evaluation=?", (t[0], t[1]))
                helpfulEvs = c.fetchone()[0]

                #Find how many users evaluated as unsure
                t = [cmnt[0], "UNSURE"]
                c.execute("SELECT COUNT(*) FROM evaluations WHERE commentid=? AND evaluation=?", (t[0], t[1]))
                unsureEvs = c.fetchone()[0]

                #Find how many users evaluated as not helpful
                t = [cmnt[0], "NOT_HELPFUL"]
                c.execute("SELECT COUNT(*) FROM evaluations WHERE commentid=? AND evaluation=?", (t[0], t[1]))
                notHelpfulEvs = c.fetchone()[0]

                print("About to send the following comment to user: ", {"TYPE": "COMMENT_INFO", "COMMENT_ID": str(cmnt[0]), "USER_ID": str(cmnt[1]), "CONTENT": cmnt[2], "USER_EVALUATION": userEvaluation, "HELPFUL_EVALUATIONS": str(helpfulEvs), "UNSURE_EVALUATIONS": str(unsureEvs), "NOT_HELPFUL_EVALUATIONS": str(notHelpfulEvs), "DATE": cmnt[4], "CAN_EVALUATE": canEvaluate})
                self.send_data({"TYPE": "COMMENT_INFO", "COMMENT_ID": str(cmnt[0]), "USER_ID": str(cmnt[1]), "CONTENT": cmnt[2], "USER_EVALUATION": userEvaluation, "HELPFUL_EVALUATIONS": str(helpfulEvs), "UNSURE_EVALUATIONS": str(unsureEvs), "NOT_HELPFUL_EVALUATIONS": str(notHelpfulEvs), "DATE": cmnt[4], "CAN_EVALUATE": canEvaluate})
                
            conn.close()

            return
    
def calcLevel(points):
    if float(points) < 120:
        return 1
    elif float(points) > 120 and float(points) < 150:
        return 2
    elif float(points) > 150:
        tempItem = float(points)
        tempItem-= 150
        level = 2 + (tempItem / 100)
        return int(level)

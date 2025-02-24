from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    code = "".join(random.choices(ascii_uppercase, k=length))
    if code in rooms:
        return generate_unique_code(length)
    return code

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form.get("name")
        code = request.form.get("code")
        join = request.form.get("join", False)
        create = request.form.get("create", False)
        
        if not name:
            return render_template("home.html", error="Please enter your name", code=code, name=name)
        if join != False and not code:
            return render_template("home.html", error="Please enter the room code", code=code, name=name)
        
        room = code
        if create != False:
            room = generate_unique_code(4)
            rooms[room] = {"members": 0, "messages": []}
        elif code not in rooms:
            return render_template("home.html", error="Room not found", code=code, name=name)
    
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))
        
    return render_template("home.html")


@app.route("/room")
def room():
    room = session.get("room")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))
    return render_template("room.html")

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": f"{name} has joined the chat"}, to=room)
    rooms[room]["members"] += 1
    print(f"{name} has joined {room}")
    
@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)
    
    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] == 0:
            del rooms[room]
        else:
            send({"name": name, "message": f"{name} has left the chat"}, to=room)
        print(f"{name} has left {room}")
    

if __name__ == "__main__":
    socketio.run(app, debug=True)
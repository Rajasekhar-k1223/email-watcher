# import socketio
# import eventlet
# import redis
# from urllib.parse import quote
# password = "UmFqYXNla2hhcmthbmFtYWx1cmlAMTIyMw=="
# safe_password = quote(password)
# redis_client = redis.StrictRedis(
#     host='157.173.199.49',  # Redis server IP
#     port=6379,              # Redis server port
#     db=0,                   # Redis database (0 by default)
#     password="UmFqYXNla2hhcmthbmFtYWx1cmlAMTIyMw==",  # Replace 'your_password' with the actual Redis password
#     decode_responses=True   # Decode responses to strings (useful for Python 3)
# )
# # Update the allowed origins to include your front-end domain or IP
# sio = socketio.Server(cors_allowed_origins=["http://localhost:3000", "http://157.173.199.49:3000","http://127.0.0.1:3000", "*"],    logger=True,            # Logs Socket.IO events
#     engineio_logger=True)    # Logs Engine.IO events (underlying transport layer))  # Replace with your front-end's domain or IP
# app = socketio.WSGIApp(sio)
# # Socket.IO server setup
# # sio = socketio.Server(cors_allowed_origins="*")
# # app = socketio.WSGIApp(sio)

# # Dictionary to track user connections (user_email: socket_id)
# user_connections = {}

# # Socket.IO event handlers
# # @sio.event
# # def connect(sid, environ):
# #     print(f"Client connected: {sid}")

# # @sio.event
# # def register_user(sid, user_email):
# #     """Register a user with their email."""
# #     user_connections[user_email] = sid
# #     print(f"User registered: {user_email} with SID: {sid}")

# # @sio.event
# # def disconnect(sid):
# #     """Remove the disconnected user."""
# #     user_email = next((k for k, v in user_connections.items() if v == sid), None)
# #     if user_email:
# #         del user_connections[user_email]
# #         print(f"User disconnected: {user_email}")

# @sio.event
# def connect(sid, environ):
#     print(f"Client connected: {sid}")

# # @sio.event
# # def register_user(sid, user_email):
# #     global user_connections
# #     print(f"Registering SID: {sid}, user_email: {user_email}")  # Debug input
# #     if not user_email:
# #         print("Error: Missing user_email.")
# #         return
# #     user_connections[user_email] = sid  # Add user to the dictionary
# #     print(f"Updated user_connections: {user_connections}")  # Debug dictionary

# @sio.event
# def register_user(sid, user_email):
#     if not user_email:
#         print("Error: Missing user_email.")
#         return

#     # Store user_email and SID in Redis
#     redis_client.set(f"user:{user_email}", sid)
#     redis_client.set(f"sid:{sid}", user_email)
#     print(f"User registered: {user_email} with SID: {sid}")


# @sio.event
# def disconnect(sid):
#     """Handle user disconnection."""
#     user_email = redis_client.get(f"sid:{sid}")
#     if user_email:
#         redis_client.delete(f"user:{user_email}")
#         redis_client.delete(f"sid:{sid}")
#         print(f"User {user_email} disconnected.")
#     else:
#         print(f"No user found for SID: {sid}.")
#     print(f"Client disconnected: {sid}")

# # @sio.event
# # def email_processed(data):
# #     """Handle notifications from Celery tasks."""
# #     print(data)
# #     print("Data")
# #     user_email = data["to"]
# #     print(user_email)
# #     print(user_connections)
# #     print("user Connections")
# #     if user_email in user_connections:
# #         sid = user_connections[user_email]
# #         sio.emit("email_processed", data, to=sid)
# #         print(f"Notification sent to {user_email}")

# # def email_processed(data):
# #     global user_connections
# #     print(f"Processing email notification: {data}")
# #     user_email = data.get("to")
# #     if not user_email:
# #         print("Error: 'to' field missing in data.")
# #         return

# #     print(f"user_connections in email_processed: {user_connections}")
# #     if user_email in user_connections:
# #         sid = user_connections[user_email]
# #         sio.emit("email_processed", data, to=sid)
# #         print(f"Notification sent to {user_email} with SID: {sid}")
# #     else:
# #         print(f"No active connection found for {user_email}")

# def email_processed(data):
#     user_email = data.get("to")
#     if not user_email:
#         print("Error: 'to' field missing in data.")
#         return

#     sid = redis_client.get(f"user:{user_email}")
#     if sid:
#         print(sid)
#         sio.emit("email_processed", data, to=sid)
#         print(f"Notification sent to {user_email} with SID: {sid}")
#     else:
#         print(f"No active connection found for {user_email}")

# # Start the server
# if __name__ == "__main__":
#     eventlet.wsgi.server(eventlet.listen(("0.0.0.0", 8765)), app)
import eventlet
import eventlet.wsgi
import redis
import socketio
from flask import Flask
from urllib.parse import quote

# Password and Redis setup
password = "$2a$12$sDztpY8S1HX0NhnNNDcctezevP95TjwYJMkjHsA9anKzL7u92vUV2"
safe_password = quote(password)

redis_client = redis.StrictRedis(
    host='157.173.199.49',  # Redis server IP
    port=6379,              # Redis server port
    db=0,                   # Redis database (0 by default)
    password="UmFqYXNla2hhcmthbmFtYWx1cmlAMTIyMw==",  # Replace 'your_password' with the actual Redis password
    decode_responses=True   # Decode responses to strings (useful for Python 3)
)

# Flask app setup
app = Flask(__name__)

# SocketIO server setup
sio = socketio.Server(
    cors_allowed_origins=["http://localhost:3000", "http://157.173.199.49:3000", "http://127.0.0.1:3000", "*"],
    logger=True,            # Logs Socket.IO events
    engineio_logger=True    # Logs Engine.IO events (underlying transport layer)
)

# Attach the socketio instance to Flask app
app.wsgi_app = socketio.WSGIApp(sio, app.wsgi_app)

# Dictionary to track user connections (user_email: socket_id)
user_connections = {}


# Define routes
@app.route('/')
def hello():
    return "Hello, Flask with Socket.IO!"

# Socket.IO event handlers

@sio.event
def connect(sid, environ):
    print(f"Client connected: {sid}")

@sio.event
def register_user(sid, user_email):
    if not user_email:
        print("Error: Missing user_email.")
        return

    # Store user_email and SID in Redis
    redis_client.set(f"user:{user_email}", sid)
    redis_client.set(f"sid:{sid}", user_email)
    print(f"User registered: {user_email} with SID: {sid}")

@sio.event
def disconnect(sid):
    """Handle user disconnection."""
    user_email = redis_client.get(f"sid:{sid}")
    if user_email:
        redis_client.delete(f"user:{user_email}")
        redis_client.delete(f"sid:{sid}")
        print(f"User {user_email} disconnected.")
    else:
        print(f"No user found for SID: {sid}.")
    print(f"Client disconnected: {sid}")

def email_processed(data):
    user_email = data.get("to")
    if not user_email:
        print("Error: 'to' field missing in data.")
        return

    sid = redis_client.get(f"user:{user_email}")
    if sid:
        print(sid)
        sio.emit("email_processed", data, to=sid)
        print(f"Notification sent to {user_email} with SID: {sid}")
    else:
        print(f"No active connection found for {user_email}")

# Start the server
if __name__ == "__main__":
    # Run the Flask app with SocketIO support
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 8765)), app)

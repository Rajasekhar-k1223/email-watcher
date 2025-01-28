import re
import uuid
from cryptography.fernet import Fernet
import pymongo
from email import policy
from email.parser import BytesParser
from celery_app import celery_app
import socketio
import redis
from bson import ObjectId
from socket_server import email_processed
# MongoDB setup
client = pymongo.MongoClient("mongodb://157.173.199.49:25312/")
db = client["mail_database"]
collection = db["emails"]
redis_client = redis.StrictRedis(
    host='157.173.199.49',  # Redis server IP
    port=6379,              # Redis server port
    db=0,                   # Redis database (0 by default)
    password="$2a$12$sDztpY8S1HX0NhnNNDcctezevP95TjwYJMkjHsA9anKzL7u92vUV2",  # Replace 'your_password' with the actual Redis password
    decode_responses=True   # Decode responses to strings (useful for Python 3)
)

with open("fernet_key.txt", "rb") as file:
    key = file.read()
cipher = Fernet(key)

# Socket.IO client for communicating with the Socket.IO server
# sio = socketio.Client()

# @sio.event
# def connect():
#     print("Connected to Socket.IO server")

# @sio.event
# def disconnect():
#     print("Disconnected from Socket.IO server")

# # Connect to the Socket.IO server
# try:
#     sio.connect("http://157.173.199.49:8765")
# except Exception as e:
#     print(f"Could not connect to Socket.IO server: {e}")

# Socket.IO client setup
sio = socketio.Client()
# Connect to the Socket.IO server
# Define a function to ensure proper connection
def connect_to_socket():
    if not sio.connected:
        try:
            sio.connect("http://157.173.199.49:8765")
            print("Connected successfully!")
        except Exception as e:
            print(f"Error connecting to socket: {e}")
    else:
        print("Already connected.")

# Celery task to parse and insert a single email
@celery_app.task
def process_email(file_path, user_email):
    print(file_path)
    print(user_email)
    try:
        with open(file_path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)
            # Extract Message-ID and filter only the unique ID
            raw_message_id = msg['Message-ID'] if msg['Message-ID'] else str(uuid.uuid4())
            match = re.search(r'<([^@>]+)@', raw_message_id)
            unique_message_id = match.group(1) if match else str(uuid.uuid4())
            # Extract email data
            email_data = {
                'message_id': unique_message_id,
                'subject': msg['subject'],
                'from': msg['from'],
                'to': msg['to'],
                'date': msg['date'],
                'plain_body': None,
                'html_body': None,
                'raw_email': msg.as_string()
            }

            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    email_data['plain_body'] = part.get_payload(decode=True).decode()
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    email_data['html_body'] = part.get_payload(decode=True).decode()
            
            fields_to_encrypt = ["plain_body", "html_body","raw_email"]

            # Encrypt specific fields
            encrypted_email_data = {
                key: cipher.encrypt(value.encode()).decode() if key in fields_to_encrypt else value
                for key, value in email_data.items()
            }
            # Insert email into MongoDB
            result = collection.insert_one(encrypted_email_data)
            email_data["_id"] = str(result.inserted_id)  # Convert ObjectId to string for JSON compatibility

            print(f"Processed and inserted email: {email_data['subject']}")
            print(email_data)
            print(user_email)
            connect_to_socket()
            socketId = redis_client.get(user_email)
            print(socketId)
            # Emit the event to the Socket.IO server
            sio.emit("email_inserted", {"email_data": email_data,'socket_id':socketId,'user_email':user_email})
            print("Event sent to Node.js Socket.IO server")
            # email_processed(email_data)
            # Notify the Socket.IO server
            # sio.emit("email_processed", {
            #     "message": f"New email processed: {email_data['subject']}",
            #     "email_data": email_data,
            #     "user_email": user_email
            # })
            
            
            # Retrieve and decrypt specific fields
            # retrieved_data = collection.find_one({}, {"_id": 0})
            # decrypted_email_data = {
            #     key: cipher.decrypt(value.encode()).decode() if key in fields_to_encrypt else value
            #     for key, value in retrieved_data.items()
            # }
            # print("Decrypted Data:")
            # print(json.dumps(decrypted_email_data, indent=2))
    except Exception as e:
        print(f"Error processing email: {e}")

    sio.wait()

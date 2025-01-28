import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import multiprocessing
from tasks import process_email  # Celery task for email processing

# SQLAlchemy setup
DATABASE_URI = 'mysql+pymysql://root:Admin!123@localhost/vmail'

engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# Define Mailbox model
class Mailbox(Base):
    __tablename__ = 'mailbox'
    id = Column(Integer, primary_key=True)
    username = Column(String(255))
    mailboxformat = Column(String(50))
    mailboxfolder = Column(String(255))
    storagebasedirectory = Column(String(255))
    storagenode = Column(String(255))
    maildir = Column(String(255))

# Watchdog Event Handler
class WatcherHandler(FileSystemEventHandler):
    def __init__(self, user_email):
        super().__init__()
        self.user_email = user_email

    def on_created(self, event):
        if event.is_directory:
            return
        print(f"New email file detected: {event.src_path} for {self.user_email}")
        process_email.delay(event.src_path, self.user_email)

# Function to monitor a single mail directory
def watch_user_maildir(user_maildir, user_email):
    if not os.path.exists(user_maildir):
        print(f"Directory does not exist: {user_maildir} for user {user_email}")
        return
    
    event_handler = WatcherHandler(user_email)
    observer = Observer()
    observer.schedule(event_handler, user_maildir, recursive=True)
    observer.start()
    print(f"Started watching {user_maildir} for {user_email}")
    
    try:
        observer.join()
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Main function to monitor all mail directories
def monitor_mail_directories():
    users = session.query(Mailbox).all()
    print(f"Total users to monitor: {len(users)}")
    
    processes = []
    for user in users:
        try:
            maildir = user.maildir.rstrip('/')
            user_maildir = os.path.join(user.storagebasedirectory, user.storagenode, maildir, user.mailboxfolder, 'new')
            
            if os.path.exists(user_maildir):
                process = multiprocessing.Process(target=watch_user_maildir, args=(user_maildir, user.username))
                processes.append(process)
                process.start()
                print(f"Process started for {user_maildir} (User: {user.username})")
            else:
                print(f"Mail directory not found for user {user.username}: {user_maildir}")
        except Exception as e:
            print(f"Error starting process for user {user.username}: {e}")
    
    # Wait for all processes to complete
    for process in processes:
        process.join()

if __name__ == "__main__":
    try:
        monitor_mail_directories()
    except KeyboardInterrupt:
        print("Monitoring stopped by user.")
    except Exception as e:
        print(f"Unexpected error occurred: {e}")

import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import multiprocessing
from tasks import process_email

# SQLAlchemy setup without Flask
DATABASE_URI = 'mysql+pymysql://root:Admin!123@localhost/vmail'

engine = create_engine(DATABASE_URI)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

class Mailbox(Base):
    __tablename__ = 'mailbox'  # Replace with your actual table name
    id = Column(Integer, primary_key=True)  # Primary Key
    username = Column(String(255))  # Optional, if needed
    mailboxformat = Column(String(50))
    mailboxfolder = Column(String(255))
    storagebasedirectory = Column(String(255))
    storagenode = Column(String(255))
    maildir = Column(String(255))

# Watchdog Handler
class WatcherHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        # Send the task to Celery
        print(f"New email file detected: {event.src_path}")
        process_email.delay(event.src_path)  # Asynchronous Celery task

# Function to start monitoring a single mail directory
def watch_user_maildir(user_maildir):
    event_handler = WatcherHandler()
    observer = Observer()
    observer.schedule(event_handler, user_maildir, recursive=True)
    observer.start()
    print(f"Started watching {user_maildir}")

    try:
        observer.join()  # Block here to keep the observer running
    except KeyboardInterrupt:
        observer.stop()

# Fetch user mail directories from MySQL and start monitoring
def monitor_mail_directories():
    # Fetch all user maildir paths using SQLAlchemy
    users = session.query(Mailbox).all()  # Fetch all rows from the users table
    print(f"Total users to monitor: {len(users)}")
    
    processes = []
    
    # Start monitoring each user's mail directory in a separate process
    for user in users:
        maildir = user.maildir
        if maildir.endswith('/'):
            maildir = maildir[:-1]
        user_maildir = user.storagebasedirectory + '/' + user.storagenode + '/' + maildir + '/new'

        # Start a new process for each mail directory
        process = multiprocessing.Process(target=watch_user_maildir, args=(user_maildir,))
        processes.append(process)
        process.start()
        print(f"Process started for {user_maildir}")

    # Optionally wait for all processes to complete
    for process in processes:
        process.join()

if __name__ == "__main__":
    monitor_mail_directories()

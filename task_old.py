import pymongo
from email import policy
from email.parser import BytesParser
from celery_app import celery_app

# MongoDB setup
client = pymongo.MongoClient("mongodb://157.173.199.49:25312/")
db = client["mail_database"]
collection = db["emails"]

# Celery task to parse and insert a single email
@celery_app.task
def process_email(file_path):
    print(file_path)
    try:
        with open(file_path, 'rb') as f:
            msg = BytesParser(policy=policy.default).parse(f)

            # Extract email data
            # email_data = {
            #     'subject': msg['subject'],
            #     'from': msg['from'],
            #     'to': msg['to'],
            #     'date': msg['date'],
            #     'body': msg.get_body(preferencelist=('plain')).get_payload(decode=True).decode(),
            #     'raw_email': msg.as_string()
            # }
            email_data = {
                'subject': msg['subject'],
                'from': msg['from'],
                'to': msg['to'],
                'date': msg['date'],
                'plain_body': None,  # To store the plain text part
                'html_body': None,   # To store the HTML part
                'raw_email': msg.as_string()
            }

            # Loop through email parts to extract plain text and HTML content
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))

                if content_type == "text/plain" and "attachment" not in content_disposition:
                    email_data['plain_body'] = part.get_payload(decode=True).decode()  # Decode plain text
                elif content_type == "text/html" and "attachment" not in content_disposition:
                    email_data['html_body'] = part.get_payload(decode=True).decode()  # Decode HTML

            # Now email_data contains both plain and HTML parts

            # Insert email into MongoDB
            collection.insert_one(email_data)
            print(f"Processed and inserted email: {email_data['subject']}")
    except Exception as e:
        print(f"Error processing email: {e}")

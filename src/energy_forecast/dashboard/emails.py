"""Manage emails for the dashboard."""
import os
import smtplib
from email.mime.text import MIMEText
from cryptography.fernet import Fernet

from energy_forecast import ROOT_DIR
import dotenv

dotenv.load_dotenv(ROOT_DIR / ".env")

def send_email(subject, body, to):
    """Send an email with the given subject and body to the given recipient."""
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "contact@antoinetavant.fr"
    msg["To"] = to
    
    # Send the email
    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    s = smtplib.SMTP(host=smtp_host, port=smtp_port)
    s.starttls()
    s.login(smtp_user, smtp_pass)
    s.sendmail(msg)
    s.quit()
    
def store_email(email):
    """Store the given email in the database."""
    # Store the email in the database using Fernet encryption
    key = os.getenv("ENCRYPTION_KEY", None)
    if key is None:
        key = Fernet.generate_key()
        # Save the key in the environment variable
        os.environ["ENCRYPTION_KEY"] = key.decode()
        with open(ROOT_DIR / ".env", "a") as f:
            f.write(f"ENCRYPTION_KEY={key.decode()}\n")
        print(f"ENCRYPTION_KEY={key.decode()}")

    filename = ROOT_DIR / "emails_newsletter.txt"
    if filename.exists():
        mode = "a"
    else:
        mode = "w"
    with open(filename, mode+"b") as f:
        cipher_suite = Fernet(key)
        encrypted_email = cipher_suite.encrypt(email.encode())
        f.write(encrypted_email + b"\n")
          
    
def load_emails():
    """Load the emails from the database."""
    key = os.getenv("ENCRYPTION_KEY", None)
    if key is None:
        raise ValueError("ENCRYPTION_KEY is not set.")
    cipher_suite = Fernet(key)
    
    filename = ROOT_DIR / "emails_newsletter.txt"
    emails = []
    with open(filename, "rb") as f:
        for line in f:
            email = cipher_suite.decrypt(line).decode()
            emails.append(email)
    return emails



def subscribe_to_newsletter(email):
    """Subscribe the given email to the newsletter."""
    store_email(email)

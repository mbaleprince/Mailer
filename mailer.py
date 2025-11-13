import smtplib
import ssl
import csv
import time
from email.mime.text import MIMEText
from email.message import EmailMessage
import sys

SENDER_ACCOUNTS = [
    {
        "email": "uraugandaofficial@gmail.com",
        "password": "rrwv jhjd agnn gtws" 
    },
    {
        "email": "eservicesura@gmail.com",
        "password": "hfml lcqn mzad ubfa"
    },
    {
        "email": "uraugandaemails@gmail.com",
        "password": "nwgz yvzw juha amyu"
    }
]

# File names
CSV_FILE = "data.csv"
HTML_TEMPLATE_FILE = "email.html"

# SMTP Settings
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465 # Use 465 for SSL/TLS

# Throttling
# We send one email every 60 seconds (1 minute).
# Since there are 3 senders, each individual sender waits 3 * 60 = 180 seconds (3 minutes)
# between their sends, meeting the requirement.
INTERVAL_SECONDS = 60 

# --- END CONFIGURATION ---

def load_recipients(filename):
    """Reads recipient data (tin, full_name, email) from the CSV file."""
    recipients = []
    
    max_limit = 524288 
    try:
        csv.field_size_limit(max_limit)
    except OverflowError:
        # Fallback for very high limits on 32-bit systems
        csv.field_size_limit(sys.maxsize)
    # --- END OF FIX ---
    
    try:
        # ... (rest of the function)
        with open(filename, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Basic validation: ensure necessary fields exist and are not empty
                if all(row.get(k) for k in ['tin', 'full_name', 'email']):
                    recipients.append(row)
        print(f"Loaded {len(recipients)} recipients from {filename}.")
        return recipients
    except FileNotFoundError:
        print(f"ERROR: Recipient file '{filename}' not found.")
        return []

def load_template(filename):
    """Loads and returns the HTML template content."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"ERROR: HTML template file '{filename}' not found.")
        return None

def send_single_email(sender_account, recipient_data, html_template):
    """
    Connects to the SMTP server, constructs the personalized email, and sends it.
    
    Spam Prevention focus: Proper MIME structure (EmailMessage), SSL, and professional headers.
    """
    sender_email = sender_account["email"]
    sender_password = sender_account["password"]
    
    # Personalize the template content
    personalized_html = html_template.replace("{{FULL_NAME}}", recipient_data['full_name'])
    personalized_html = personalized_html.replace("{{TIN_ID}}", recipient_data['tin'])

    # Prepare the email message
    msg = EmailMessage()
    msg['Subject'] = "URGENT ACTION REQUIRED: Tax Account Verification Notice for TIN " + recipient_data['tin']
    msg['From'] = sender_email
    msg['To'] = recipient_data['email']
    
    # Attach HTML content
    msg.set_content('This is an HTML email. Please view it in an HTML-compatible client.') # Plain text fallback
    msg.add_alternative(personalized_html, subtype='html')

    # Establish secure connection
    context = ssl.create_default_context()
    
    try:
        # Use SMTP_SSL for port 465
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(sender_email, sender_password)
            server.send_message(msg)
            return True

    except smtplib.SMTPAuthenticationError:
        print(f"    ❌ AUTH ERROR: Sender {sender_email} failed to log in. Check App Password.")
    except smtplib.SMTPRecipientsRefused:
        print(f"    ❌ RECIPIENT ERROR: Recipient {recipient_data['email']} refused by server.")
    except smtplib.SMTPException as e:
        print(f"    ❌ SMTP ERROR: An SMTP error occurred: {e}")
    except Exception as e:
        print(f"    ❌ UNEXPECTED ERROR: {e}")
        
    return False

def main():
    """Main function to orchestrate the rotational bulk sending."""
    print("--- Starting Rotational Bulk Sender ---")
    
    # 1. Load Data and Template
    recipients = load_recipients(CSV_FILE)
    html_template = load_template(HTML_TEMPLATE_FILE)
    
    if not recipients or not html_template:
        print("Aborting due to missing data or template.")
        return
    
    if any(account['password'] == 'your_sender1_app_password' for account in SENDER_ACCOUNTS):
        print("\nCRITICAL ERROR: Please update SENDER_ACCOUNTS with valid emails and App Passwords.")
        return

    num_senders = len(SENDER_ACCOUNTS)
    total_recipients = len(recipients)
    
    print(f"Total recipients to process: {total_recipients}")
    print(f"Using {num_senders} sender accounts.")
    print("-" * 35)

    sender_index = 0
    sent_count = 0
    
    for i, recipient in enumerate(recipients):
        current_sender = SENDER_ACCOUNTS[sender_index]
        
        print(f"[{i + 1}/{total_recipients}] Sending to {recipient['email']}")
        print(f"    (Sender: {current_sender['email']})")

        success = send_single_email(current_sender, recipient, html_template)

        if success:
            sent_count += 1
            print(f"    ✅ Success. Sleeping for {INTERVAL_SECONDS} seconds...")
        else:
            print(f"    ⚠️ Failed to send. Still sleeping for {INTERVAL_SECONDS} seconds before next attempt.")

        # Move to the next sender in the list
        sender_index = (sender_index + 1) % num_senders
        
        # Pause for the required interval before sending the next email
        # This ensures each sender waits 3*60 = 180 seconds between sends.
        if i < total_recipients - 1:
            time.sleep(INTERVAL_SECONDS)

    print("-" * 35)
    print(f"Process complete. Successfully sent {sent_count} emails.")
    print(f"Failed or skipped {total_recipients - sent_count} emails.")

if __name__ == "__main__":
    main()
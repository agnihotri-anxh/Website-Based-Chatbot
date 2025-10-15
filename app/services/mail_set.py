import os
from flask_mail import Mail, Message


def configure_mail(app):
    return Mail(app)


def send_appointment_confirmation(mail, app, to_email, name, phone, subject, appointment_id):
    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    import threading
    
    print(f"Email attempt - Thread: {threading.current_thread().name}")
    email_username = app.config.get('MAIL_USERNAME', '')
    email_password = app.config.get('MAIL_PASSWORD', '')
    
    try:
        msg = MIMEMultipart()
        from_address = app.config.get('MAIL_DEFAULT_SENDER') or email_username
        msg['From'] = from_address
        msg['To'] = to_email
        msg['Subject'] = f"Appointment Confirmed - {subject}"
        
        body = f"""Dear {name},

Thank you for booking an appointment with Sybrant Technologies!

Appointment Details:
- Name: {name}
- Email: {to_email}
- Phone: {phone}
- Subject: {subject}
- Appointment ID: #{appointment_id}
- Status: Confirmed
- Date: Auto-generated at confirmation

Our team will contact you within 24 hours.

Contact: +91-44-2445-3822 | connect@sybrant.com

Best regards,
Sybrant Technologies Team"""
        
        msg.attach(MIMEText(body, 'plain'))
        server_host = app.config.get('MAIL_SERVER', 'smtp.gmail.com')
        server_port = int(app.config.get('MAIL_PORT', 587))
        use_tls = bool(app.config.get('MAIL_USE_TLS', True))
        use_ssl = bool(app.config.get('MAIL_USE_SSL', False))
        
        if not email_username or not email_password:
            raise RuntimeError('Email credentials not configured')

        if use_ssl:
            server = smtplib.SMTP_SSL(server_host, server_port, timeout=30)
        elif use_tls:
            # STARTTLS on port 587
            server = smtplib.SMTP(server_host, server_port, timeout=30)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            # Plain SMTP (rare; not recommended)
            server = smtplib.SMTP(server_host, server_port, timeout=30)

        server.login(email_username, email_password)
        
        text = msg.as_string()
        server.sendmail(msg['From'], to_email, text)
        server.quit()
        
        return True
    except Exception as e:
        print(f"❌ Email sending failed: {e}")
        return False



from django.core.mail import send_mail
from django.conf import settings
from babel.dates import format_timedelta
from datetime import timedelta


class EmailDispatcher:
    @staticmethod
    def reset_password_otp(otp: str, email: str, web_data_url: str | None = None) -> None:
        exp_time = getattr(settings, 'OTP_EXPIRATION_TIME', 600)
        # Convert expiration time (seconds) to timedelta
        exp_time_delta = timedelta(seconds=exp_time)
        # Format the duration into human-readable text
        exp_time_text = format_timedelta(exp_time_delta, locale='en_US')
        html_message = f'<p>Your OTP is <strong>{otp}</strong>. It expires in <strong>{exp_time_text}</strong>.</p>'
        if web_data_url:
            html_message += f'<p>Click <a href="{web_data_url}">here</a> to reset your password.</p>'
        
        send_mail(
            subject='Reset Password',
            message=f'Your OTP is {otp}. It expires in {exp_time_text}.',
            html_message=html_message,
            recipient_list=[email],
            from_email=None,  # Use default email settings from Django settings
            fail_silently=False,
        )

    @staticmethod
    def verify_email_otp(otp: str, email: str, web_data_url: str | None = None) -> None:
        exp_time = getattr(settings, 'OTP_EXPIRATION_TIME', 600)
        # Convert expiration time (seconds) to timedelta
        exp_time_delta = timedelta(seconds=exp_time)
        # Format the duration into human-readable text
        exp_time_text = format_timedelta(exp_time_delta, locale='en_US')
        html_message = f'<p>Your OTP is <strong>{otp}</strong>. It expires in <strong>{exp_time_text}</strong>.</p>'
        if web_data_url:
            html_message += f'<p>Click <a href="{web_data_url}">here</a> to verify your email.</p>'
        
        send_mail(
            subject='Email Verification',
            message=f'Your OTP is {otp}. It expires in {exp_time_text}.',
            html_message=html_message,
            recipient_list=[email],
            from_email=None,  # Use default email settings from Django settings
            fail_silently=False,
        )
import random
import string

# Simulate sending a password reset token via email
def send_password_reset_email(email: str, token: str):
    # You can print or log it (replace with actual sending logic later)
    print(f"[SIMULATED EMAIL] Sending password reset token to {email}: {token}")
    return True


# Optional: Generate random token (can also use secrets.token_urlsafe)
def generate_reset_token(length: int = 6) -> str:
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))

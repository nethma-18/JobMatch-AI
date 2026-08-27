from app.core.security import hash_password, verify_password, create_access_token, decode_token
from datetime import timedelta

def test_password_hashing():
    pwd = "secretpassword"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("wrongpassword", hashed) is False

def test_access_token():
    payload = {"sub": "user_id_123", "role": "seeker"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=10))
    assert token is not None
    assert isinstance(token, str)

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user_id_123"
    assert decoded["role"] == "seeker"
    assert "exp" in decoded

def test_decode_invalid_token():
    assert decode_token("invalid.token.here") is None

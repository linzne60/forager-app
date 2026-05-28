from app.auth.passwords import hash_password, verify_password


def test_hash_password_is_not_plaintext():
    hashed = hash_password("mypassword")
    assert hashed != "mypassword"
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    hashed = hash_password("mypassword")
    assert verify_password("mypassword", hashed) is True


def test_verify_password_wrong():
    hashed = hash_password("mypassword")
    assert verify_password("wrongpassword", hashed) is False


def test_same_password_produces_different_hashes():
    # bcrypt uses a random salt each time
    assert hash_password("mypassword") != hash_password("mypassword")

import re


def verify_strong_password(password: str) -> bool:
    MIN_LEN = 8

    if len(password) < MIN_LEN:
        return False

    has_upper = any(c.isupper() for c in password)
    has_lower = any(c.islower() for c in password)
    has_digit = any(c.isdigit() for c in password)
    has_special = any(not c.isalnum() for c in password)

    return all([has_upper, has_lower, has_digit, has_special])


def verify_length_telephone(telephone: str) -> bool:
    MIN_TELEPHONE_ = 10
    MIN_TELEPHONE__ = 11

    digits = re.sub(r'\D', '', telephone)

    return MIN_TELEPHONE_ <= len(digits) <= MIN_TELEPHONE__


def verify_fullname(fullname: str) -> bool:
    MIN_LEN_NAME = 3
    MIN_NAMES = 2

    name_list = fullname.split(' ')

    for name in name_list:
        name.replace(name, name.strip())

    if len(name_list) < MIN_NAMES:
        return False

    for n in name_list:
        if len(n) < MIN_LEN_NAME:
            return False

    return True

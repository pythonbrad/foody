import random
import string


def generate_restaurant_code():
    from .models import Restaurant
    s = string.ascii_uppercase
    code = None
    retry = 3
    while retry:
        code = ''.join([s[random.randint(0, len(s)-1)] for i in range(6)])
        retry -= 1
        if Restaurant.objects.filter(code=code).exists():
            pass
        else:
            return code
    raise Exception("generate_restaurant_code failed: max retry")

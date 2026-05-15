import random
import string

from apps.urls.models import ShortURL

ALPHABET = string.ascii_letters + string.digits

def generate_short_code():
	while True:
		code = "".join(random.choices(ALPHABET, k=7))
		if not ShortURL.objects.filter(short_code=code).exists():
			return code

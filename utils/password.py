from Cryptodome.PublicKey import RSA

from utils.logmessage import logmessage
from settings import *


def decrypt(password):
	# from https://stackoverflow.com/questions/2490334/simple-way-to-encode-a-string-according-to-a-password

	if len(password) == 0:
		logmessage("Why u no entering password! Top right! Top right!")
		return False

	with open(passwordFile, "rb") as f:
			encoded_key = f.read()

	try:
		key = RSA.import_key(encoded_key, passphrase=password)
		return True
	except ValueError:
		return False
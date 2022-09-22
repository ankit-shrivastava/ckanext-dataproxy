import cryptocode
import base64

def dataproxy_encrypt(message, salt):
  encrypted_message = cryptocode.encrypt(message, salt)
  encoded_encrypted_message = encrypted_message.encode("utf-8")
  base_64_encoded = base64.b64encode(encoded_encrypted_message)
  base_64_string = base_64_encoded.decode("utf-8")
  return base_64_string


def dataproxy_decrypt(message, salt):
  encoded_message = message.encode("utf-8")
  base_64_decoded = base64.b64decode(encoded_message)
  base_64_string = base_64_decoded.decode("utf-8")
  decrtpted_message = cryptocode.decrypt(base_64_string, salt)
  return decrtpted_message

import bcrypt

passwd = b's$cret12'

salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(passwd, salt)

print(passwd.decode('utf-8'))
print(hashed.decode('utf-8'))

if bcrypt.checkpw(passwd, hashed):
    print("match")
else:
    print("does not match")

import socket

s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1.bind(('127.0.0.1', 1000))
s1.listen(10)

s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s2.connect(('127.0.0.1', 1000))


first = True


conn1, addr1 = s1.accept()
print('conn1: ', addr1)
if first:
    s2.send('hello'.encode())
print(conn1.recv(1024))
conn1.send('hello back'.encode())
print(s2.recv(1024))
conn1.close()   

s3 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s3.connect(('127.0.0.1', 1000))
conn, (ip, port) = s1.accept()
print('conn2: ', ip, port)
    
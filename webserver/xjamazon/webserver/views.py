from django.http import HttpResponse
import socket

HOST, PORT = "vcm-8965.vm.duke.edu", 65432

def index(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    app_server_ip = socket.gethostbyname(HOST)
    s.connect((app_server_ip, PORT))
    s.sendall('wo cao ni ma'.encode('utf-8'))
    return HttpResponse("Hello world.")

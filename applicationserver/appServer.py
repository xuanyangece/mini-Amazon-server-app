import socket
from xml.sax import make_parser, parseString
from xml.sax.handler import ContentHandler

class web_requestHandler(ContentHandler) :
    def __init__(self):
        self.CurrentData = ""
        self.id = ""
        self.ups_name = ""
        self.description = ""
        self.count = ""
        self.address = ""

    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "buy":
            print("*******Buy*******")

    def endElement(self, tag):
        if self.CurrentData == "id":
            print(self.id)
        elif self.CurrentData == "ups_name":
            print(self.ups_name)
        elif self.CurrentData == "description":
            print(self.description)
        elif self.CurrentData == "count":
            print(self.count)
        elif self.CurrentData == "address":
            print(self.address)
        self.CurrentData = ""

    def characters(self, content):
        if self.CurrentData == "id":
            self.id = content
        elif self.CurrentData == "ups_name":
            self.ups_name = content
        elif self.CurrentData == "description":
            self.description = content
        elif self.CurrentData == "count":
            self.count = content
        elif self.CurrentData == "address":
            self.address = content






if __name__ == '__main__':


    HOST, PORT = socket.gethostbyname(socket.gethostname()), 65432

    listen_socket_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket_web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket_web.bind((HOST, PORT))
    listen_socket_web.listen(10);

    while True:
        client_connection, client_address = listen_socket_web.accept()
        request = client_connection.recv(10400)
        print(request.decode('utf-8'))

        xml_request = request.decode('utf-8')


        Handler = web_requestHandler()
        parseString(xml_request, Handler)




        client_connection.close()





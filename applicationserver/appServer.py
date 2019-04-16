import socket
from xml.sax import make_parser, parseString
from xml.sax.handler import ContentHandler
import amazon_pb2

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

#host, port for connecting with world
WHOST, WPORT = "vcm-8965.vm.duke.edu", 23456


def send_message(socket, msg):
    hdr = []
    _EncodeVarint(hdr.append, len(msg.SerializeToString()))
    socket.sendall("".join(hdr))
    socket.sendall(msg.SerializeToString())


def recv_message(socket):
    var_int_buff = []
    while True:
        buf = socket.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = socket.recv(msg_len)
    return whole_message






def createWorld():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))

    worldCreate = amazon_pb2.AConnect()
    worldCreate.isAmazon = True

    send_message(s, worldCreate)


    connectResponse = amazon_pb2.AConnected()
    connectResponse.ParseFromString(recv_message(s))


    print("Worldid: ")
    print(connectResponse.worldid)
    print("\n")


    print("Result: ")
    print(connectResponse.result)
    print("\n")





def sendtoWorld():
    HOST, PORT = socket.gethostbyname(socket.gethostname()), 65432

    listen_socket_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket_web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket_web.bind((HOST, PORT))
    listen_socket_web.listen(10)

    while True:
        client_connection, client_address = listen_socket_web.accept()
        request = client_connection.recv(10400)
        print(request.decode('utf-8'))

        xml_request = request.decode('utf-8')

        Handler = web_requestHandler()
        parseString(xml_request, Handler)

       # newproduct = amazon_pb2.AProduct()
       # newproduct.id = Handler.itemid
       # newproduct.description = Handler.description
       # newproduct.item = Handler.count

#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        world_server_ip = socket.gethostbyname(WHOST)
#       s.connect((world_server_ip, WPORT))









def recvfromWorld():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))

    var_int_buff = []
    while True:
        buf = s.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff,0)
        if new_pos != 0:
            break
    whole_message = s.recv(msg_len)
    ourresponse = amazon_pb2.AResponses()







class web_requestHandler(ContentHandler) :
    def __init__(self):
        self.CurrentData = ""
        self.commandtype = ""
        self.itemid = ""
        self.ups_name = ""
        self.description = ""
        self.count = ""
        self.address_X = ""
        self.address_Y = ""


    def startElement(self, tag, attributes):
        self.CurrentData = tag
        if tag == "buyProduct":
            self.commandtype = tag
            print("*******Buy*******")
        elif tag == "createWarehouse":
            self.commandtype = tag
            print("*******iniWarehouse*******")
        elif tag  == "getProduct":
            self.commandtype =  tag
            print("********getStock*******")

    def endElement(self, tag):
        if self.CurrentData == "item_id":
            print(self.itemid)
        elif self.CurrentData == "ups_name":
            print(self.ups_name)
        elif self.CurrentData == "description":
            print(self.description)
        elif self.CurrentData == "count":
            print(self.count)
        elif self.CurrentData == "x":
            print(self.address_X)
        elif self.CurrentData == "y":
            print(self.address_Y)
        self.CurrentData = ""

    def characters(self, content):
        if self.CurrentData == "item_id":
            self.itemid = content
        elif self.CurrentData == "ups_name":
            self.ups_name = content
        elif self.CurrentData == "description":
            self.description = content
        elif self.CurrentData == "count":
            self.count = content
        elif self.CurrentData == "x":
            self.address_X = content
        elif self.CurrentData == "y":
            self.address_Y =  content






if __name__ == '__main__':
     #createWorld()
     while True:
      sendtoWorld()



import socket
from xml.sax import make_parser, parseString
from xml.sax.handler import ContentHandler
import threading
import amazon_pb2

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

#host, port for connecting with world
WHOST, WPORT = "vcm-8965.vm.duke.edu", 23456

Warehouse_id = 1
ship_id = 1
seqnum = 1
ourorderList = []

def uni_string(msg):
    res = msg.encode("utf-8")
    return res

def uni_int(msg):
    s_mess = msg.encode("utf-8")
    res = int(s_mess)
    return res


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






def createWorld(s):

    worldCreate = amazon_pb2.AConnect()
    worldCreate.isAmazon = True
    #wareHouse = worldCreate.initwh.add()
    worldCreate.worldid = 5
    #wareHouse.id = 1
    #wareHouse.x = 2
    #wareHouse.y = 3
    #wh2 = worldCreate.initwh.add()
    #wh2.id = 2
    #wh2.x = 2
    #wh2.y = 3

    send_message(s, worldCreate)


    connectResponse = amazon_pb2.AConnected()
    connectResponse.ParseFromString(recv_message(s))


    print("Worldid: ")
    print(connectResponse.worldid)
    print("\n")


    print("Result: ")
    print(connectResponse.result)
    print("\n")


def createWarehouse(s, msg):
    send_message(s, msg)

    connectResponse = amazon_pb2.AConnected()
    connectResponse.ParseFromString(recv_message(s))

    print("Worldid: ")
    print(connectResponse.worldid)
    print("\n")

    print("Result: ")
    print(connectResponse.result)
    print("\n")

    return


def sendtoWorld(s):
    global ourorderList
    global seqnum
    print("hahahahahahah")
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

#        if Handler.commandtype == "getProduct":
#        s_command = amazon_pb2.AProduct()
#           s_command.id = Handler.itemid
#            s_command.description = Handler.description
#            s_command.count = Handler.count
#           ourorderList.append(s_command)
        if Handler.commandtype == "createWarehouse":
            s_command = amazon_pb2.AConnect()
            s_command.worldid = uni_int(Handler.worldid)
            s_command.isAmazon = True
            warehouse = s_command.initwh.add()
            warehouse.id = uni_int(Handler.wareid)
            warehouse.x = uni_int(Handler.address_X)
            warehouse.y = uni_int(Handler.address_Y)
            createWarehouse(s, s_command)
        elif Handler.commandtype == "buyProduct":
            s_command = amazon_pb2.ACommands()
            buymore = s_command.buy.add()
            buymore.whnum = 1
            buymore.seqnum = seqnum
            seqnum = seqnum + 1
            product = buymore.things.add()
            product.id = uni_int(Handler.itemid)
            product.description = uni_string(Handler.description)
            product.count = uni_int(Handler.count)
            ourorderList.append(Handler)
            send_message(s, s_command)



       # newproduct = amazon_pb2.AProduct()
       # newproduct.id = Handler.itemid
       # newproduct.description = Handler.description
       # newproduct.item = Handler.count

#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        world_server_ip = socket.gethostbyname(WHOST)
#       s.connect((world_server_ip, WPORT))









def recvfromWorld(s):

    global ship_id
    global seqnum
    print("hhhhh")

    while True:
        worldResponse = amazon_pb2.AResponses()
        worldResponse.ParseFromString(recv_message(s))


        if worldResponse.error:
            print("Error: ")
            print(worldResponse.error.err)

        if worldResponse.arrived:
            print("purchaseMore: ")
            print(worldResponse.arrived.whnum)
            print(worldResponse.arrived.seqnum)

            for order in ourorderList:
                if order.itemid == worldResponse.APurchaseMore.AProduct.id and order.count == worldResponse.APurchaseMore.AProduct.count:
                    pack_command = amazon_pb2.APack()
                    pack_command.whnum = worldResponse.arrived.whnum
                    pack_command.AProduct = worldResponse.arrived.things
                    pack_command.shipid =  ship_id
                    ship_id = ship_id + 1
                    pack_command.seqnum = seqnum
                    seqnum = seqnum + 1
                    send_message(s, pack_command)


        if worldResponse.ready:
            print("Packed: ")
            print(worldResponse.ready.shipid)
            print(worldResponse.ready.seqnum)













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
        self.worldid = ""
        self.wareid = ""


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
        elif self.CurrentData == "worldID":
            print(self.worldid)
        elif self.CurrentData == "whID":
            print(self.wareid)
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
        elif self.CurrentData == "worldID":
            self.worldid = content
        elif self.CurrentData == "whID":
            self.wareid = content






if __name__ == '__main__':

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))

    createWorld(s)

    my_thread1 = threading.Thread(target = sendtoWorld, args=(s,))
    my_thread2 = threading.Thread(target = recvfromWorld, args=(s,))
    my_thread1.start()
    my_thread2.start()


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
order_id = 1000
seqnum = 1
WorldMessage = []
socketonly = -1
putontruk_WL = []
ship_truckMap = dict()
orderList = []
UpsMessage = []

class Item:
    def __init__(self, name, quantity, description):
        self.name = str(name)
        self.quantity = str(quantity)
        self.description = str(description)

class Package:
    def __init__(self, id, x, y, upsname, items):
        self.id = str(id)
        self.x = str(x)
        self.y = str(y)
        self.upsname = str(upsname)
        self.items = items

def reqTruckXML(orderID, whID, packages):
    strXML = "<reqTruck>\n\t"
    strXML += "<Order id=\"" + str(orderID) + "\"/>\n\t"
    strXML += "<Warehouse id=\"" + str(whID) + "\"/>\n\t"
    strXML += "<Packages>\n"

    # traverse packages
    for pkg in packages:
        strXML += "\t\t<Package id=\"" + pkg.id + "\">\n"

        strXML += "\t\t\t<destination X=\"" + pkg.x + "\" Y=\"" + pkg.y + "\"/>\n"
        strXML += "\t\t\t<UPS username=\"" + pkg.upsname + "\"/>\n"
        strXML += "\t\t\t<items>\n"

        for item in pkg.items:
            strXML += "\t\t\t\t<item name=\"" + item.name + "\" quantity=\"" + item.quantity + "\" description=\""
            strXML += item.description + "\"/>\n"

        strXML += "\t\t<Package>\n"

    strXML += "\t</Packages>\n"
    strXML += "</reqTruck>\n"

    return strXML


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






def connectWorld(worldconnect):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))
    #worldCreate = amazon_pb2.AConnect()
    #worldCreate.isAmazon = True
    #wareHouse = worldCreate.initwh.add()
    #worldCreate.worldid = 5
    #wareHouse.id = 1
    #wareHouse.x = 2
    #wareHouse.y = 3
    #wh2 = worldCreate.initwh.add()
    #wh2.id = 2
    #wh2.x = 2
    #wh2.y = 3

    send_message(s, worldconnect)


    connectResponse = amazon_pb2.AConnected()
    connectResponse.ParseFromString(recv_message(s))


    print("Worldid: ")
    print(connectResponse.worldid)
    print("\n")


    print("Result: ")
    print(connectResponse.result)
    print("\n")

    return s


def commuWorld(msg,siganl):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))
    flag = 0

    while flag == 0:
        send_message(s,msg)
        flag = recvfromWorld(s,siganl)



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






       # newproduct = amazon_pb2.AProduct()
       # newproduct.id = Handler.itemid
       # newproduct.description = Handler.description
       # newproduct.item = Handler.count

#        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#        world_server_ip = socket.gethostbyname(WHOST)
#       s.connect((world_server_ip, WPORT))

def upsServer():
    print("skip")



def worldServer(s):
    global seqnum
    global ship_id
    while True:
        if(len(WorldMessage) > 0):
            for comamnd in WorldMessage:
                send_message(s, comamnd)

        worldResponse = amazon_pb2.AResponses()
        worldResponse.ParseFromString(recv_message(s))

        if len(worldResponse.error) > 0:
            for errors in worldResponse.error:
                print(errors.err)
                print(errors.originseqnum)
                print(errors.seqnum)

        #recv purchaseMore and create topack
        if len(worldResponse.arrived) > 0:
            for arrive in worldResponse.arrived:
                s_command = amazon_pb2.ACommands()
                apack = s_command.topack.add()
                apack.whnum = arrive.whnum
                apack.seqnum = seqnum
                seqnum = seqnum + 1
                apack.shipid = ship_id
                ship_id = ship_id + 1
                print(arrive.whnum)
                for product in arrive:
                    print(product.id)
                    print(product.description)
                    print(product.count)
                    sproduct = apack.things.add()
                    sproduct.id = product.id
                    sproduct.description = product.description
                    sproduct.count =  product.count
                    for order  in orderList:
                        if order.itemid == sproduct.id and order.description == sproduct.description and order.count == sproduct.count:
                                 items = []
                                 items.append(Item(sproduct.id, sproduct.count, sproduct.description))
                                 packages = []
                                 packages.append(Package(apack.shipid,uni_int(order.address_X), uni_int(order.address_Y),uni_string(order.ups_name),items))
                                 rTruckXml = reqTruckXML(uni_int(order.order_id),arrive.whnum, packages)
                                 UpsMessage.append(rTruckXml)
                                 orderList.remove(order)
                                 break
                print(arrive.seqnum)
                WorldMessage.append(s_command)
                truck_command = amazon_pb2.ACommands()
                truck = truck_command.load.add()
                truck.whnum = arrive.whnum
                truck.shipid = apack.shipid
                apack.seqnum = seqnum
                seqnum = seqnum + 1
                putontruk_WL.append(truck_command)
                #recev packed and create put on truck
        if len(worldResponse.ready) > 0:
            for packed in worldResponse.ready:
                for pot in putontruk_WL:
                    if pot.load[0].shipid == packed.shipid:
                        ship_truckMap[pot.load[0].shipid] = pot
                        putontruk_WL.remove(pot)
                        break


        if len(worldResponse.loaded) > 0:




def amazonWeb(listen_socket_web):
    global seqnum
    global order_id
    while True:
        client_connection, client_address = listen_socket_web.accept()
        request = client_connection.recv(10400)
        print(request.decode('utf-8'))

        xml_request = request.decode('utf-8')

        Handler = web_requestHandler()
        parseString(xml_request, Handler)

        if Handler.commandtype == "buyProduct":
            s_command = amazon_pb2.ACommands()
            ack = s_command.acks.add()
            ack = seqnum
            buymore = s_command.buy.add()
            buymore.whnum = 1
            buymore.seqnum = seqnum
            seqnum = seqnum + 1
            product = buymore.things.add()
            product.id = uni_int(Handler.itemid)
            product.description = uni_string(Handler.description)
            product.count = uni_int(Handler.count)
            WorldMessage.append(s_command)
            Handler.order_id = order_id
            order_id = order_id + 1
            orderList.append(Handler)

        elif Handler.commandtype == "query":
            #skip now
            s_command = amazon_pb2.AQuery()
            WorldMessage.append(s_command)






def recvfromWorld(s,signal):

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
            s_command1 = amazon_pb2.ACommands()
            pack = s_command1.topack.add()
            pack.whnum = worldResponse.arrived.whnum
            thing = pack.things.add()
            thing.id = worldResponse.arrived.things
            #for order in ourorderList:
             #   if order.itemid == worldResponse.APurchaseMore.AProduct.id and order.count == worldResponse.APurchaseMore.AProduct.count:
              #      pack_command = amazon_pb2.APack()
              #      pack_command.whnum = worldResponse.arrived.whnum
              #      pack_command.AProduct = worldResponse.arrived.things
              #      pack_command.shipid =  ship_id
              #      ship_id = ship_id + 1
              #      pack_command.seqnum = seqnum
              #      seqnum = seqnum + 1
              #      send_message(s, pack_command)



        if worldResponse.ready:
            print("Packed: ")
            print(worldResponse.ready.shipid)
            print(worldResponse.ready.seqnum)

        for i in worldResponse.acks:
            if i == signal:
                return i
            else:
                return 0













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
        self.order_id = ""
        self.ship_id = ""


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


    HOST, PORT = socket.gethostbyname(socket.gethostname()), 65432

    listen_socket_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket_web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket_web.bind((HOST, PORT))
    listen_socket_web.listen(200)


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
                socketonly = connectWorld(s_command)
                break

            threadamazon = threading.Thread(target=amazonWeb, args=(listen_socket_web,))
            threadworld = threading.Thread(target=worldServer, args=(socketonly,))
            threadUPS = threading.Thread(target=upsServer,args=())
            threadUPS.start()
            threadamazon.start()



import socket
from xml.sax import make_parser, parseString
from xml.sax.handler import ContentHandler
import threading
import amazon_pb2
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import xml.sax
import select

from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

# this host and port for amazon
HOST, PORT = socket.gethostbyname(socket.gethostname()), 65432

# host, port for connecting with world
WHOST, WPORT = "vcm-8513.vm.duke.edu", 23456

#global variable used for create unique warehouseid shipid sequm and orderid
Warehouse_id = 1
ship_id = 1
order_id = 1000
seqnum = 1

#store <sequm, Acommand> pair
WorldMessage = dict()

#the only one socket used to communicate with world
socketonly = -1

#store the the Aputontruck command at eariler stage
putontruck_WL = []

#store <ship_id, putontructcommand> for UPShandle
ship_truckMap = dict()

#store all the order after receive from amazonweb
orderList = []

#store all the messgae need to send to UPS
UPSMessage = []

#used to find all package on truck by truck_id
truck_packageMap = dict()


# host for UPS
UPSHOST, UPSPORTR, UPSPORTS = "vcm-8513.vm.duke.edu", 12346, 12347


#product info
class Item:
    def __init__(self, name, quantity, description):
        self.name = str(name)
        self.quantity = str(quantity)
        self.description = str(description)

#package info
class Package:
    def __init__(self, id, x, y, upsname, items):
        self.id = str(id)
        self.x = str(x)
        self.y = str(y)
        self.upsname = str(upsname)
        self.items = items

#used to create reqtruck message
def reqTruckXML(orderID, whID, packages):
    strXML = "<reqTruck>\n\t"
    strXML += "<Order id=\"" + str(orderID) + "\"/>\n\t"
    strXML += "<Warehouse id=\"" + str(whID) + "\"/>\n"
    # strXML += "<Packages>\n"

    # traverse packages
    for pkg in packages:
        strXML += "\t<Package id=\"" + pkg.id + "\">\n"

        strXML += "\t\t<destination X=\"" + pkg.x + "\" Y=\"" + pkg.y + "\"/>\n"
        strXML += "\t\t<UPS username=\"" + pkg.upsname + "\">\n"
        #strXML += "\t\t\t<items>\n"

        for item in pkg.items:
            strXML += "\t\t\t<item name=\"" + item.name + "\" quantity=\"" + item.quantity + "\" description=\""
            strXML += item.description + "\"/>\n"
        strXML += "\t\t</UPS>\n"
        strXML += "\t\t</Package>\n"

    #strXML += "\t</Packages>\n"
    strXML += "</reqTruck>\n"

    strXML = str(len(strXML)) + '\n' + strXML
    return strXML



#function used to parsing the truck XML info from UPS
class TruckHandler(xml.sax.ContentHandler):
    def __init__(self):
        self.CurrentData = ""
        self.orderID = ""
        self.truckID = ""
        self.packageID = []

    def startElement(self, tag, attributes):
        self.CurrentData = tag

        if tag == "Order":
            print ("***Order***")
            self.orderID = attributes["id"]
            print ("Order id: ", self.orderID)

        if tag == "Truck":
            print ("***Truck***")
            self.truckID = attributes["id"]
            print ("Truck id: ", self.truckID)

        if tag == "package":
            print ("***package***")
            self.packageID.append(attributes["id"])
            print ("package id: ", attributes["id"])


def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


#used to create the goDeliver command for UPS
def goDeliverXML(truckID):
    str1 = "<goDeliver>\n\t<Truck id=\""
    str1 += truckID + "\"/>\n"
    str1 += "</goDeliver>\n"

    str1 = str(len(str1)) + '\n' + str1

    return str1.encode('utf-8')


# receive from UPS
def recvUPS(s):

    data = s.recv(10240)
    # parse data and do something
    data = str(data)
    print("*******From UPS*******\n")
    print(data)


    if data.find("goLoad") != -1:
        # parse get truck id
        Handler = TruckHandler()  # only use Truck id in it
        xml.sax.parseString(data, Handler)
        tid = Handler.truckID

        # traverse all packageids
        pkgids = truck_packageMap[tid]

        for pkgid in pkgids:
            # get the pot
            pot = ship_truckMap[pkgid]
            for x in pot.load:
                # pot update
                x.truckid = tid

            # put in in WorldMessage
            WorldMessage[pot.load[0].seqnum] = pot

            # remove pot
            ship_truckMap.pop(pkgid)

    elif data.find("reqTruck") != -1:
        # parse
        Handler = TruckHandler()
        xml.sax.parseString(data, Handler)

        # map from truck id to multiple packageid
        tid = Handler.truckID
        pkgids = Handler.packageID

        # check exist
        if tid not in truck_packageMap.keys():
            truck_packageMap[tid] = []

        # update pot for each pkgid
        for pkgid in pkgids:
            truck_packageMap[tid].append(pkgid)


def handleUPS():
    global UPSHOST
    global UPSPORTS
    # poll to check whether there's remaining commands in UPSMessage
    while True:
        global UPSMessage
        # not empty: handle!
        if (len(UPSMessage) != 0):
            # extra info from UPSMessage
            message = UPSMessage.pop(0)

            # send UPSMessage info to UPS
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((UPSHOST, UPSPORTS))

            s.sendall(message.encode('utf-8'))


def handleUPS2(s_recv):
    global UPSPORTR
    while True:
        s_connection, s_address = s_recv.accept()
        recvUPS(s_connection)
        s_connection.close()




def uni_string(msg):
    res = msg.encode("utf-8")
    return res

def uni_int(msg):
    s_mess = msg.encode("utf-8")
    res = int(s_mess)
    return res


#used to send and recv google protocol message with world
def send_message(socket, msg):
    hdr = []
    _EncodeVarint(hdr.append, len(msg.SerializeToString()))
    socket.sendall("".join(hdr))
    socket.sendall(msg.SerializeToString())

#recv with timeout
def recv_tmessage(socket, timeout):
    var_int_buff = []
    ready = select.select([socket], [], [], timeout)
    if ready[0]:
        while True:
            buf = socket.recv(1)
            var_int_buff += buf
            msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
            if new_pos != 0:
                break
        whole_message = socket.recv(msg_len)
        return whole_message
    return ""


#normal recv
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


#used to connect world and initial the warehouse
def connectWorld(worldconnect):

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    world_server_ip = socket.gethostbyname(WHOST)
    s.connect((world_server_ip, WPORT))

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


def  ack_to_world(s, ack):
    ackcommand = amazon_pb2.ACommands()
    ackcommand.acks.extend(ack)
    send_message(s, ackcommand)






#used to send and handle commands and response to/from world
def worldServer(s):
    timeout = 1
    global seqnum
    global ship_id
    while True:
        if(len(WorldMessage) > 0):
            for key in WorldMessage.keys():
                print("key:"+ str(key))
                send_message(s, WorldMessage[key])
                '''
                one time 
                one time 
                one time 
                one time     
                '''
                WorldMessage.pop(key)

        worldResponse = amazon_pb2.AResponses()
        msg =  recv_tmessage(s, timeout)

        if msg == "":
            continue

        worldResponse.ParseFromString(msg)

        for i in worldResponse.acks:
            for key in WorldMessage.keys():
                if i == key:
                    WorldMessage.pop(i)


        if len(worldResponse.error) > 0:
            for errors in worldResponse.error:
                print(errors.err)
                print("error orginsequm:" + str(errors.originseqnum))
                print(errors.seqnum)
                ack_to_world(s, errors.seqnum)

        #recv purchaseMore and create topack
        if len(worldResponse.arrived) > 0:
            for arrive in worldResponse.arrived:
                ack_to_world(s, arrive.seqnum)
                s_command = amazon_pb2.ACommands()
                apack = s_command.topack.add()
                apack.whnum = arrive.whnum
                apack.seqnum = seqnum
                seqnum = seqnum + 1
                apack.shipid = ship_id
                ship_id = ship_id + 1
                print("**************arrived*************")
                print(arrive.whnum)
                for product in arrive.things:
                    print("Product id: " + str(product.id))
                    print("Product description: " + str(product.description))
                    print("Product count: " + str(product.count))

                    sproduct = apack.things.add()
                    sproduct.id = product.id
                    sproduct.description = product.description
                    sproduct.count =  product.count

                    for order  in orderList:
                        print("current order id: " + str(order.itemid))
                        print("current order description: " + str(order.description))
                        print("current order count: " + str(order.count))

                        if str(order.itemid) == str(sproduct.id) and str(order.description) == str(sproduct.description) and str(order.count) == str(sproduct.count):
                                 print("create xml for ups reqTruck")

                                 items = []
                                 items.append(Item(sproduct.id, sproduct.count, sproduct.description))
                                 packages = []
                                 packages.append(Package(apack.shipid,uni_int(order.address_X), uni_int(order.address_Y),uni_string(order.ups_name),items))
                                 rTruckXml = reqTruckXML(order.order_id,arrive.whnum, packages)
                                 print(rTruckXml)
                                 UPSMessage.append(rTruckXml)
                                 orderList.remove(order)
                                 break
                print(arrive.seqnum)
                WorldMessage[apack.seqnum] = s_command
                print("packsequm:" + str(apack.seqnum))
                truck_command = amazon_pb2.ACommands()
                truck = truck_command.load.add()
                truck.whnum = arrive.whnum
                truck.shipid = apack.shipid
                putontruck_WL.append(truck_command)
                #recev packed and create put on truck


        if len(worldResponse.ready) > 0:
            for packed in worldResponse.ready:
                ack_to_world(s, packed.seqnum)
                print("ready shipid:" + str(packed.shipid))
                print("ready seqnum:" + str(packed.seqnum))
                for pot in putontruck_WL:
                    if pot.load[0].shipid == packed.shipid:
                        ship_truckMap[pot.load[0].shipid] = pot
                        putontruck_WL.remove(pot)
                        print("received ready")

        if len(worldResponse.loaded) > 0:
            for load in worldResponse.loaded:
                send_message(s, load.seqnum)
                for key in truck_packageMap.keys():
                    for pakid in truck_packageMap[key]:
                        if pakid == load.shipid:
                            pakid.remove(pakid)

#recv and handle all the message from amazonweb
def amazonWeb(listen_socket_web):
    global seqnum
    global order_id


    while True:
        client_connection, client_address = listen_socket_web.accept()
        request = client_connection.recv(10400)
        client_connection.close()
        print(request.decode('utf-8'))

        xml_request = request.decode('utf-8')

        Handler = web_requestHandler()
        parseString(xml_request, Handler)

        if Handler.commandtype == "buyProduct":
            s_command = amazon_pb2.ACommands()
            buymore = s_command.buy.add()
            buymore.whnum = 1
            buymore.seqnum = seqnum
            seqnum = seqnum + 1
            product = buymore.things.add()
            product.id = uni_int(Handler.itemid)
            product.description = uni_string(Handler.description)
            product.count = uni_int(Handler.count)
            WorldMessage[buymore.seqnum] = s_command
            Handler.order_id = order_id
            order_id = order_id + 1
            orderList.append(Handler)

        elif Handler.commandtype == "query":
            #skip now
            s_command = amazon_pb2.AQuery()

            WorldMessage[seqnum] = s_command
            seqnum = seqnum + 1



#Parsing all the xml message from amazon web
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


#parsing the Worldid xml message from ups
class WorldIDHandler(ContentHandler):
    def __init__(self):
        self.CurrentData = ""
        self.worldID = ""

    def startElement(self, tag, attrs):
        self.CurrentData = tag

        if tag == "Worldid":
            self.worldID = attrs["id"]
            print("World id: ", self.worldID)



if __name__ == '__main__':


    #************* For UPS
    # UPS sockret for world id
    id_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    id_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    id_socket.bind((HOST, UPSPORTR))
    id_socket.listen(200)
    print("Begin listen...")

    id_connection, id_address = id_socket.accept()
    wid_xml = id_connection.recv(100)
    print("World id received:", wid_xml)
    id_connection.close()

    # parse world id
    wid_hander = WorldIDHandler()
    parseString(wid_xml, wid_hander)
    wid = wid_hander.worldID


    #************* For web
    # web socket
    listen_socket_web = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_socket_web.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listen_socket_web.bind((HOST, PORT))
    listen_socket_web.listen(200)

    client_connection, client_address = listen_socket_web.accept()
    request = client_connection.recv(10400)
    print(request.decode('utf-8'))
    client_connection.close()

    xml_request = request.decode('utf-8')

    Handler = web_requestHandler()
    parseString(xml_request, Handler)

    if Handler.commandtype == "createWarehouse":
        s_command = amazon_pb2.AConnect()
        s_command.worldid = int(wid)
        s_command.isAmazon = True
        warehouse = s_command.initwh.add()
        warehouse.id = uni_int(Handler.wareid)
        warehouse.x = uni_int(Handler.address_X)
        warehouse.y = uni_int(Handler.address_Y)
        socketonly = connectWorld(s_command)


    threadamazon = threading.Thread(target=amazonWeb, args=(listen_socket_web,))
    threadworld = threading.Thread(target=worldServer, args=(socketonly,))
    threadUPSsend = threading.Thread(target=handleUPS,args=())
    threadUPSrecv = threading.Thread(target=handleUPS2, args=(id_socket,))

    threadUPSsend.start()
    threadamazon.start()
    threadworld.start()
    threadUPSrecv.start()


import socket
from xml.sax import make_parser, parseString
from xml.sax.handler import ContentHandler
import threading
import amazon_pb2
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import xml.sax
import select
import psycopg2
from random import randint
import smtplib
from email.mime.text import MIMEText
from email.header import Header



from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint

# this host and port for amazon
HOST, PORT = socket.gethostbyname(socket.gethostname()), 65432

# host, port for connecting with world
WHOST, WPORT = "vcm-9387.vm.duke.edu", 23456

#global variable used for create unique warehouseid shipid sequm and orderid
warehouse_num = 0
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

#flag to protect initial goDeliver
gdFlag = False

#used to find all package on truck by truck_id
truck_packageMap = dict()

#used to map package id to tracking number
package_tcknumMap = dict()

# host for UPS
UPSHOST, UPSPORTR, UPSPORTS = "vcm-9387.vm.duke.edu", 12346, 12347


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

    # traverse packages
    for pkg in packages:
        strXML += "\t<Package id=\"" + pkg.id + "\">\n"

        strXML += "\t\t<destination X=\"" + pkg.x + "\" Y=\"" + pkg.y + "\"/>\n"
        strXML += "\t\t<UPS username=\"" + pkg.upsname + "\">\n"

        for item in pkg.items:
            strXML += "\t\t\t<item name=\"" + item.name + "\" quantity=\"" + item.quantity + "\" description=\""
            strXML += item.description + "\"/>\n"
        strXML += "\t\t</UPS>\n"
        strXML += "\t</Package>\n"

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
        self.trackingnumber = []

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

        if tag == "Package":
            print ("***Package***")
            self.packageID.append(attributes["id"])
            print ("Package id: ", attributes["id"])

    def endElement(self, tag):
        self.CurrentData = ""

    def characters(self, content):
        if self.CurrentData == "trackingnumber":
            self.trackingnumber.append(content)
            print("Add tn:" + str(content))


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
def recvUPS(s,conn):
    cursor = conn.cursor()
    global gdFlag
    global truck_packageMap
    global WorldMessage
    global package_tcknumMap
    global ship_truckMap

    data = s.recv(10240)
    # parse data and do something
    data = str(data)
    # skip '\n'
    data = data[data.find("\n") + 1:]
    print("*******From UPS*******\n")
    print(data)

    # when the truck arrived
    if data.find("goDeliver") != -1:
        # parse get truck id
        Handler = TruckHandler()  # only use Truck id in it
        xml.sax.parseString(data, Handler)
        tid = uni_int(Handler.truckID)

        # traverse all packageids
        pkgids = truck_packageMap[tid]

        for pkgid in pkgids:

            while True:
                if len(ship_truckMap.keys()) == 0:
                    continue

                print("type of pkgid " + str(type(pkgid)))
                for i in range(len(ship_truckMap.keys())):
                    keys = ship_truckMap.keys()
                    print("the " + str(i) + " th key is " + str(keys[i]))
                if pkgid in ship_truckMap.keys():
                    break

            # get the pot
            pot = ship_truckMap[pkgid]
            for x in pot.load:
                print("PutOnTruck")
                print("whnum *****: " + str(x.whnum))
                print("shipid: " + str(x.shipid))
                sqlstatusloading = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'LOADING' WHERE PACKAGE_ID = '" + str(x.shipid) + "';"
                cursor.execute(sqlstatusloading)
                conn.commit()

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

        print("Received reqTruck: ")
        print(str(len(Handler.packageID)) + " packages")
        print(str(len(Handler.trackingnumber)) + " tracking numbers")

        # map from truck id to multiple packageid
        tid = uni_int(Handler.truckID)
        pkgids = Handler.packageID
        trknums = Handler.trackingnumber

        # map package id to trk number
        for i in range(len(pkgids)):
            pkg = uni_int(pkgids[i])
            trknum = uni_int(trknums[i])
            package_tcknumMap[pkg] = trknum
            sqltrackingnumber = "UPDATE WEBSERVER_PACKAGE SET TRACKINGNUMBER = '" + str(trknum) + "' WHERE PACKAGE_ID = '" + str(pkg) + "';"
            cursor.execute(sqltrackingnumber)
            conn.commit()
        #flag to prevent race
        gdFlag = True

        # check exist
        if tid not in truck_packageMap.keys():
            truck_packageMap[tid] = []

        # update pot for each pkgid
        for pkgid in pkgids:
            pkgid = uni_int(pkgid)
            truck_packageMap[tid].append(pkgid)

        gdFlag = False

    elif data.find("Delivered") != -1:
        # parse
        Handler = TruckHandler()
        xml.sax.parseString(data, Handler)
        pkgids = Handler.packageID
        for pkgid in pkgids:
            id = uni_string(pkgid)
            sqlstatusdelivered = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'DELIVERED' WHERE PACKAGE_ID = '" + str(id) + "';"
            cursor.execute(sqlstatusdelivered)
            conn.commit()

# send message to ups
def handleUPS():
    global UPSHOST
    global UPSPORTS
    global gdFlag
    global UPSMessage
    global truck_packageMap

    # poll to check whether there's remaining commands in UPSMessage
    while True:
        global UPSMessage
        # not empty: handle everything before goDeliver!
        if (len(UPSMessage) != 0):
            # extra info from UPSMessage
            message = UPSMessage.pop(0)

            # send UPSMessage info to UPS
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((UPSHOST, UPSPORTS))

            s.sendall(message.encode('utf-8'))
        # specially for send goDeliver
        else:
            for key in truck_packageMap.keys():
                if len(truck_packageMap[key]) == 0 and gdFlag == False:
                    print("Ready to goDeliver")
                    msg = goDeliverXML(str(key))
                    UPSMessage.append(msg)
                    truck_packageMap.pop(key)


def handleUPS2(s_recv,conn):
    global UPSPORTR
    while True:
        s_connection, s_address = s_recv.accept()
        recvUPS(s_connection,conn)
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



#use to send ack to world
def  ack_to_world(s, ack):
    ackcommand = amazon_pb2.ACommands()
    ackcommand.acks.append(ack)
    send_message(s, ackcommand)






#used to send and handle commands and response to/from world
def worldServer(s,conn):
    timeout = 3
    global seqnum
    global ship_id
    global truck_packageMap
    global WorldMessage
    global package_tcknumMap
    global ship_truckMap
    global worldspeed
    cursor = conn.cursor()

    while True:

        #send all commands to world including new commands and the command lost in sending process
        if(len(WorldMessage) > 0):
            for key in WorldMessage.keys():
                send_message(s, WorldMessage[key])
                print("SEND TO WORLD with key: " + str(key))
                '''
                one time 
                one time 
                one time 
                one time     
                '''

        worldResponse = amazon_pb2.AResponses()
        msg =  recv_tmessage(s, timeout)

        if msg == "":
            continue

        worldResponse.ParseFromString(msg)

        #check the ack from world, and delete the message world received
        for i in worldResponse.acks:
            for key in WorldMessage.keys():
                if i == key:
                    WorldMessage.pop(i)


        if len(worldResponse.error) > 0:
            for errors in worldResponse.error:
                print("Error:" + errors.err)
                print("Error orginsequm:" + str(errors.originseqnum))
                print("Error seqnum:" + str(errors.seqnum))
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
                print("arrivewhnum:" + str(arrive.whnum))
                for product in arrive.things:
                    print("Product id: " + str(product.id))
                    print("Product description: " + str(product.description))
                    print("Product count: " + str(product.count))

                    sqlSelect = "SELECT * FROM WEBSERVER_PACKAGE WHERE PRODUCT_NAME = '" + str(product.id) + "' AND COUNT = '" + str(product.count) + "' AND DESCRIPTION = '" + str(product.description) + "' AND PACKAGE_ID = 0 ORDER BY ORDER_ID ASC;"
                    cursor.execute(sqlSelect)
                    result = cursor.fetchall()

                    uid =  result[0][11]
                    sqlupdate = "UPDATE WEBSERVER_PACKAGE SET PACKAGE_ID = '" + str(apack.shipid) + "' WHERE UID = '" + str(uid) + "';"
                    cursor.execute(sqlupdate)
                    conn.commit()
                    sproduct = apack.things.add()
                    sproduct.id = product.id
                    sproduct.description = product.description
                    sproduct.count =  product.count

                    for order  in orderList:
                        print("current order id: " + str(order.itemid))
                        print("current order description: " + str(order.description))
                        print("current order count: " + str(order.count))


                        #go to the orderlist to find the suitable order according to the world's arrived response
                        if str(order.itemid) == str(sproduct.id) and str(order.description) == str(sproduct.description) and str(order.count) == str(sproduct.count):
                                 items = []
                                 items.append(Item(sproduct.id, sproduct.count, sproduct.description))
                                 packages = []
                                 packages.append(Package(apack.shipid,uni_int(order.address_X), uni_int(order.address_Y),uni_string(order.ups_name),items))
                                 rTruckXml = reqTruckXML(order.order_id,arrive.whnum, packages)
                                 print(rTruckXml)
                                 UPSMessage.append(rTruckXml)
                                 orderList.remove(order)


                                 #treat VIP and normal customers differently
                                 if str(order.vip) == "yes":
                                     s_command.simspeed = 30000
                                     print("pack vip!")
                                 else:
                                     s_command.simspeed = 1000
                                     print("pack no vip")
                                 break

                WorldMessage[apack.seqnum] = s_command
                sqlstatuspacking = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'PACKING' WHERE PACKAGE_ID = '" + str(apack.shipid) +"';"
                cursor.execute(sqlstatuspacking)
                conn.commit()
                print("packsequm:" + str(apack.seqnum))

                #create the putontruck command for UPS thread, due to only at this time, the world's response has the information we need
                truck_command = amazon_pb2.ACommands()
                truck = truck_command.load.add()
                truck.whnum = arrive.whnum
                truck.shipid = apack.shipid
                truck.seqnum = seqnum
                seqnum = seqnum + 1
                putontruck_WL.append(truck_command)



        if len(worldResponse.ready) > 0:
            print("***********Now ready************")
            for packed in worldResponse.ready:
                ack_to_world(s, packed.seqnum)
                sqlstatuspacked = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'PACKED' WHERE PACKAGE_ID = '" + str(packed.shipid) + "';"
                cursor.execute(sqlstatuspacked)
                conn.commit()
                print("ready shipid:" + str(packed.shipid))
                print("ready seqnum:" + str(packed.seqnum))
                for pot in putontruck_WL:
                    if pot.load[0].shipid == packed.shipid:
                        mykey = int(pot.load[0].shipid)

                        #package packed down!
                        #transfer the putontruck command from waitlist to really map, waiting UPShandle thread send them
                        ship_truckMap[mykey] = pot
                        putontruck_WL.remove(pot)



        if len(worldResponse.loaded) > 0:
            print("***********Now loaded*************")
            for load in worldResponse.loaded:
                ack_to_world(s, load.seqnum)
                sqlstatusdelivering = "UPDATE WEBSERVER_PACKAGE SET STATUS = 'DELIVERED' WHERE PACKAGE_ID = '" + str(load.shipid) + "';"
                cursor.execute(sqlstatusdelivering)
                conn.commit()

                for key in truck_packageMap.keys():
                    for pakid in truck_packageMap[key]:

                        #Remove packageid from the list, UPShandle thread will know all package were loaded down if the len is 0
                        if int(pakid) == int(load.shipid):
                            print("remove:" + str(pakid))
                            truck_packageMap[key].remove(pakid)


        if len(worldResponse.packagestatus) > 0:
            print("************Now status*************")
            for package in  worldResponse.packagestatus:
                ack_to_world(s, package.seqnum)
                print("package id:" + str(package.packageid))
                print("status:" + package.status)
                sqlstatus = "UPDATE WEBSERVER_PACKAGE SET STATUS = '" + package.status + "' WHERE PACKAGE_ID = '" + str(package.packageid) + "'"
                cursor.execute(sqlstatus)
                conn.commit()


        if worldResponse.finished == True:
            closeXML = "<closeWorld>\n</closeWorld>\n"
            print("disconnect: " + str(worldResponse.finished))
            UPSMessage.append(closeXML)



#recv and handle all the message from amazonweb
def amazonWeb(listen_socket_web, conn):
    global seqnum
    global order_id

    #Used to send a order-confirmation email to our customers
    from_addr = 'mynewubber@gmail.com'
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(from_addr, r'dengliwen1997')

    cursor = conn.cursor()

    canceltable = "TRUNCATE TABLE WEBSERVER_PACKAGE;"
    cursor.execute(canceltable)
    conn.commit()
    while True:
        client_connection, client_address = listen_socket_web.accept()
        request = client_connection.recv(10400)
        # client_connection.close()
        print(request.decode('utf-8'))

        xml_request = request.decode('utf-8')

        Handler = web_requestHandler()
        parseString(xml_request, Handler)


        if Handler.commandtype == "buyProduct":
            s_command = amazon_pb2.ACommands()

            #offer a faster speed to our VIP customer
            if uni_string(Handler.vip) == "yes":
                s_command.simspeed = 30000
                print("purchasemore vip!")
            else:
                s_command.simspeed = 1000
                print("purchasemore no vip!")

            #assign the fields in the purchase more command
            buymore = s_command.buy.add()
            buymore.whnum = randint(1, warehouse_num)
            buymore.seqnum = seqnum
            seqnum = seqnum + 1
            product = buymore.things.add()
            email = uni_string(Handler.email)
            product.id = uni_int(Handler.itemid)
            product.description = uni_string(Handler.description)
            product.count = uni_int(Handler.count)
            WorldMessage[buymore.seqnum] = s_command
            Handler.order_id = order_id
            sql = "UPDATE WEBSERVER_PACKAGE SET ORDER_ID = '" + str(order_id) + "' WHERE UID = '" + str(uni_string(Handler.uid)) + "';"
            cursor.execute(sql)
            conn.commit()
            order_id = order_id + 1
            orderList.append(Handler)

            message = MIMEText('Thank you for purchasing on miniAmazon, and your order has been placed. You can check your package status anytime on our website \n\n\n\n\n   miniAmazon Team', 'plain', 'utf-8')
            message['From'] = Header("miniAmazon", 'utf-8')
            message['To'] = Header("Customer", 'utf-8')
            subject = 'Your Order Confirmation!'
            message['Subject'] = Header(subject, 'utf-8')

            try:
                server.sendmail(from_addr, [email], message.as_string())
                print("Email send successfully")
            except smtplib.SMTPException:
                print("Fail to send email")




        elif Handler.commandtype == "query":
            s_command = amazon_pb2.ACommands()
            aquery = s_command.queries.add()
            aquery.packageid = uni_int(Handler.packageid)
            aquery.seqnum = seqnum
            WorldMessage[seqnum] = s_command
            seqnum = seqnum + 1

        elif Handler.commandtype == "closeWorld":
            s_command = amazon_pb2.ACommands()
            s_command.disconnect = True
            WorldMessage[seqnum] = s_command
            seqnum = seqnum + 1


        client_connection.close()



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
        self.uid = ""
        self.packageid = ""
        self.email = ""
        self.vip = ""

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
        elif tag == "query":
            self.commandtype = tag
            print("************query******")
        elif tag == "closeWorld":
            self.commandtype = tag
            print("*********disconnectWorld**********")

    #print all the attributes we received from amazonWeb
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
        elif self.CurrentData == "uid":
            print(self.uid)
        elif self.CurrentData == "packageid":
            print(self.packageid)
        elif self.CurrentData == "email":
            print(self.email)
        elif self.CurrentData == "vip":
            print(self.vip)
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
        elif self.CurrentData == "uid":
            self.uid =  content
        elif self.CurrentData == "packageid":
            self.packageid =  content
        elif self.CurrentData == "email":
            self.email = content
        elif self.CurrentData == "vip":
            self.vip = content


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

    #connect the amazon database
    conn = psycopg2.connect(
    database="scmiwlgi",
    user="scmiwlgi",
    password="TFP9YRYa1EmcciYEEBqsAsrSq9O9qiWV",
    host="isilo.db.elephantsql.com",
    port="5432",
    )
    print("connect amazon database successfull")





    #************* For UPS
    # UPS socket for world id
    id_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    id_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    id_socket.bind((HOST, UPSPORTR))
    id_socket.listen(200)
    print("Begin listen...")

    id_connection, id_address = id_socket.accept()
    wid_xml = id_connection.recv(100)
    wid_xml = wid_xml[wid_xml.find("\n") + 1:]
    print("World id received:", wid_xml)
    id_connection.close()


    # parse world id received from UPS
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


    #Receive the command used to connect the world and create our warehouses
    if Handler.commandtype == "createWarehouse":
        s_command = amazon_pb2.AConnect()
        s_command.worldid = int(wid)
        s_command.isAmazon = True
        warehouse_num = uni_int(Handler.address_X)
        for i in range(1, uni_int(Handler.address_X)+1):
            warehouse = s_command.initwh.add()
            warehouse.id = i
            warehouse.x = i
            warehouse.y = i
        socketonly = connectWorld(s_command)


    #handle the communication with amazonWeb, World and UPS in different thread
    threadamazon = threading.Thread(target=amazonWeb, args=(listen_socket_web,conn,))
    threadworld = threading.Thread(target=worldServer, args=(socketonly,conn))
    threadUPSsend = threading.Thread(target=handleUPS,args=())
    threadUPSrecv = threading.Thread(target=handleUPS2, args=(id_socket,conn))

    threadUPSsend.start()
    threadamazon.start()
    threadworld.start()
    threadUPSrecv.start()



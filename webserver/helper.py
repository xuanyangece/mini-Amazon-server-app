import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import socket
import select

WorldMessage = ["MMP"]

UPSMessage = ["RNM"]

UPSHOST, UPSPORT = "vcm-xxxx.vm.duke.edu", 41414

# helper function for prettify XML from https://stackoverflow.com/questions/17402323/use-xml-etree-elementtree-to-print-nicely-formatted-xml-files
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


def goDeliverXML(truckID):
    str = "<goDeliver>\n\t<Truck id=\""
    str += truckID + "\"/>\n"
    str += "</goDeliver>\n"

    return str.encode('utf-8')


def handleUPS():
    global UPSHOST
    global UPSPORT
    # poll to check whether there's remaining commands in UPSMessage
    while True:
        global UPSMessage
        # not empty: handle!
        if (len(UPSMessage) != 0):
            # extra info from UPSMessage
            message = UPSMessage[0]

            # send UPSMessage info to UPS
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(UPSHOST)
            s.connect((app_server_ip, UPSPORT))
            s.sendall(message.encode('utf-8'))

            # recv, ACK/handle and add
            s.setblocking(0)
            timeout = 60 * 1
            ready = select.select([s], [], [], timeout)
            if ready[0]:
                # pop out UPSMessage
                UPSMessage.pop(0)
                # receive result
                data = s.recv(10240)
                # parse data and do something
                data = str(data)
                if data.find("goLoad") != -1:
                    # send load to world
                    data.find("id")
                    # map from truck id to multiple packageid
                    # map each packageid to (wh, truck, packageid)->world
                    # possibly put truck id in it
                    # move this to WorldMessage
            
        else:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(UPSHOST)
            s.connect((app_server_ip, UPSPORT))
            
            # recv, ACK/handle and add
            s.setblocking(0)
            timeout = 20 * 1
            ready = select.select([s], [], [], timeout)

            if ready[0]:
                # receive result
                data = s.recv(10240)
                # parse data and do something
                data = str(data)
                if data.find("goLoad") != -1:
                    # send load to world
                    data.find("id")
                    # map from truck id to multiple packageid
                    # map each packageid to (wh, truck, packageid)->world
                    # possibly put truck id in it
                    # move this to WorldMessage






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

# packages = [p1, p2, p3, ...]
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


items1 = []
items1.append(Item("1", 10, "AI"))
items1.append(Item("2", 5, "ML"))

packages1 = []
packages1.append(Package(1, 3, 5, "myUPS", items1))

#print(goDeliverXML("1314"))

print(reqTruckXML(99, 88, packages1))

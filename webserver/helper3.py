import xml.sax

# parse reqTruck
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

        if tag == "package":
            print ("***package***")
            self.packageID.append(attributes["id"])
            print ("package id: ", attributes["id"])

    def endElement(self, tag):
        self.CurrentData = ""
            
    def characters(self, content):
        if self.CurrentData == "trackingnumber":
            self.trackingnumber.append(content)
            print("Add tn:" + str(content))
        

string = '''
<reqTruck>
    <Order id="1"/>
    <Truck id="3"/>
    <package id="4">
        <trackingnumber>123</trackingnumber>
    </package>
    <package id="5">
        <trackingnumber>483</trackingnumber>
    </package>
</reqTruck>
'''

Handler = TruckHandler()

xml.sax.parseString(string, Handler)

print(str(len(Handler.trackingnumber)))

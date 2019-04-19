import xml.sax

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

Handler = TruckHandler()

st = """
<reqTruck>
   <Order id="13"/>
   <Truck id="54"/>
   <Packages>
	<package id="9" TrackingNumber="123"/>
    <package id="4" TrackingNumber="666"/>	    
   </Packages>
</reqTruck>
"""

xml.sax.parseString(st, Handler)
print(len(Handler.packageID))

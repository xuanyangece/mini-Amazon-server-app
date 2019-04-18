import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET


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


def reqTruckXML():
    return ""

print(goDeliverXML("1314"))


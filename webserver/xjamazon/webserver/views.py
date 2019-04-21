from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from .forms import BuyProductForm, WarehouseForm

import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import socket


# modify according to app server
HOST, PORT = "vcm-8965.vm.duke.edu", 65432

# helper function for prettify XML from https://stackoverflow.com/questions/17402323/use-xml-etree-elementtree-to-print-nicely-formatted-xml-files
def prettify(elem):
    """Return a pretty-printed XML string for the Element.
    """
    rough_string = ET.tostring(elem, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="\t")


# homepage
def homepage(request):
    return render(request, 'webserver/index.html', {})


# buyProduct page
def buyProduct(request):
    if request.method == 'POST':
        form = BuyProductForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            ups_name = form.cleaned_data['ups_name']
            description = form.cleaned_data['description']
            count = form.cleaned_data['count']
            x = form.cleaned_data['x']
            y = form.cleaned_data['y']

            # generate XML
            buyProductXML = ET.Element('buyProduct')

            itemXML = ET.SubElement(buyProductXML, 'item_id')
            itemXML.text = item_id

            upsXML = ET.SubElement(buyProductXML, 'ups_name')
            upsXML.text = ups_name

            descpXML = ET.SubElement(buyProductXML, 'description')
            descpXML.text = description

            countXML = ET.SubElement(buyProductXML, 'count')
            countXML.text = str(count)

            xCoorXML = ET.SubElement(buyProductXML, 'x')
            xCoorXML.text = str(x)

            yCoorXML = ET.SubElement(buyProductXML, 'y')
            yCoorXML.text = str(y)

            buyProductRequest = prettify(buyProductXML)
    
            # send order info to app server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(HOST)
            s.connect((app_server_ip, PORT))
            s.sendall(buyProductRequest.encode('utf-8'))

            return HttpResponseRedirect("/webserver/homepage/")

    else:
        form = BuyProductForm()

    return render(request, 'webserver/buyProduct.html', {'form': form})

# createWarehouse page
def createWarehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            whID = form.cleaned_data['whID']
            x = form.cleaned_data['x']
            y = form.cleaned_data['y']

            # generate XML
            newWHXML = ET.Element('createWarehouse')

            whIDXML = ET.SubElement(newWHXML, 'whID')
            whIDXML.text = whID

            xCoorXML = ET.SubElement(newWHXML, 'x')
            xCoorXML.text = str(x)

            yCoorXML = ET.SubElement(newWHXML, 'y')
            yCoorXML.text = str(y)

            newWHRequest = prettify(newWHXML)

            # send order info to app server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(HOST)
            s.connect((app_server_ip, PORT))
            s.sendall(newWHRequest.encode('utf-8'))

            return HttpResponseRedirect("/webserver/homepage/")
    else:
        form = WarehouseForm()

    return render(request, 'webserver/createWarehouse.html', {'form': form})

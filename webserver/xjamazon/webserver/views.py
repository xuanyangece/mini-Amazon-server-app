from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from .models import Item
from .forms import BuyForm

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

# buy page
def buy(request):
    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            ups_name = form.cleaned_data['ups_name']
            description = form.cleaned_data['description']
            count = form.cleaned_data['count']
            address = form.cleaned_data['address']

            # generate XML
            buyXML = ET.Element('buy')

            itemXML = ET.SubElement(buyXML, 'item_id')
            itemXML.text = item_id

            upsXML = ET.SubElement(buyXML, 'ups_name')
            upsXML.text = ups_name

            descpXML = ET.SubElement(buyXML, 'description')
            descpXML.text = description

            countXML = ET.SubElement(buyXML, 'count')
            countXML.text = str(count)

            addXML = ET.SubElement(buyXML, 'address')
            addXML.text = address

            buyRequest = prettify(buyXML)
    
            # send order info to app server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(HOST)
            s.connect((app_server_ip, PORT))
            s.sendall(buyRequest.encode('utf-8'))
            return HttpResponseRedirect("/webserver/")

    else:
        form = BuyForm()

    return render(request, 'webserver/buy.html', {'form': form})

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
import xml.etree.ElementTree as ET
import socket

# modify according to app server
HOST, PORT = "vcm-8965.vm.duke.edu", 65432

def index(request):
    return (request, 'webserver/index.html', {})

def buy(request):
    if request.method == 'POST':
        form = BuyForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            ups_name = forms.cleaned_data['ups_name']
            description = forms.cleaned_data['description']
            count = forms.cleaned_data['count']
            address = forms.cleaned_data['address']

            # generate XML
            buyXML = ET.Element('buy')

            itemXML = ET.SubElement(buyXML, 'item_id')
            itemXML.text = item_id

            upsXML = ET.SubElement(buyXML, 'ups_name')
            upsXML.text = ups_name

            descpXML = ET.SubElement(buyXML, 'description')
            descpXML.text = description

            countXML = ET.SubElement(buyXML, 'count')
            countXML.text = count

            addXML = ET.SubElement(buyXML, 'address')
            addXML.text = address

            buyRequest = ET.tostring(buyXML)
    
            # send order info to app server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(HOST)
            s.connect((app_server_ip, PORT))
            s.sendall(buyRequest.encode('utf-8'))
            return HttpResponseRedirect("/webserver/")

    else:
        form = BuyForm()

    return render(request, 'users/buy.html', {'form': form})

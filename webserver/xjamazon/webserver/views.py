from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from .forms import BuyProductForm, WarehouseForm, RegistrationForm, LoginForm
from .models import AmazonUser, Package
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required

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
@login_required
def buyProduct(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = BuyProductForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            _ups_name = form.cleaned_data['ups_name']
            _description = form.cleaned_data['description']
            _count = form.cleaned_data['count']
            _x = form.cleaned_data['x']
            _y = form.cleaned_data['y']


            # store in Package table
            newpackage = Package(username=user.username, order_id=0, package_id=0, trackingnumber=0, status="", product_name=item_id, ups_name=_ups_name, description=_description, count=_count, x=_x, y=_y)
            newpackage.save()


            # generate XML
            buyProductXML = ET.Element('buyProduct')

            uidXML = ET.SubElement(buyProductXML, 'uid')
            uidXML.text = str(newpackage.uid)

            itemXML = ET.SubElement(buyProductXML, 'item_id')
            itemXML.text = item_id

            upsXML = ET.SubElement(buyProductXML, 'ups_name')
            upsXML.text = _ups_name

            descpXML = ET.SubElement(buyProductXML, 'description')
            descpXML.text = _description

            countXML = ET.SubElement(buyProductXML, 'count')
            countXML.text = str(_count)

            xCoorXML = ET.SubElement(buyProductXML, 'x')
            xCoorXML.text = str(_x)

            yCoorXML = ET.SubElement(buyProductXML, 'y')
            yCoorXML.text = str(_y)

            buyProductRequest = prettify(buyProductXML)


            # send order info to app server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            app_server_ip = socket.gethostbyname(HOST)
            s.connect((app_server_ip, PORT))
            s.sendall(buyProductRequest.encode('utf-8'))

            return HttpResponseRedirect(reverse('webserver:dashboard', args=[user.id]))

    else:
        form = BuyProductForm()

    return render(request, 'webserver/buyProduct.html', {'form': form, 'user': user})

# createWarehouse page
def createWarehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            x = form.cleaned_data['x']

            # generate XML
            newWHXML = ET.Element('createWarehouse')

            xCoorXML = ET.SubElement(newWHXML, 'x')
            xCoorXML.text = str(x)

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

# register a new account
def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password2']

            user = User.objects.create_user(username=username, first_name=first_name, last_name=last_name, password=password, email=email)

            user_profile = AmazonUser(user=user)
            user_profile.save()

            return HttpResponseRedirect("/webserver/homepage/")

    else:
        form = RegistrationForm()

    return render(request, 'webserver/registration.html', {'form':form})

# login into your account
def login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = auth.authenticate(username=username, password=password)

            if user is not None and user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(reverse('webserver:dashboard', args=[user.id]))
            else:
                return render(request, 'webserver/login.html', {'form':form, 'message': 'Wrong password. Please try again.'})

    else:
        form = LoginForm()

    return render(request, 'webserver/login.html', {'form': form})

# logout your account
@login_required
def logout(request):
    auth.logout(request)
    return HttpResponseRedirect("/webserver/homepage/")

# dashboard of Amazon account
@login_required
def dashboard(request, id):
    user = get_object_or_404(User, id=id)
    return render(request, 'webserver/dashboard.html', {'user': user})

# query
def query(request, id):
    return HttpResponseRedirect("/webserver/homepage/")

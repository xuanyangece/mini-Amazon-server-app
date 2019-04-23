from django.contrib.auth.models import User
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect, HttpResponse
from .forms import BuyProductForm, WarehouseForm, RegistrationForm, LoginForm, RatingForm
from .models import AmazonUser, Package, Product
from django.urls import reverse
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.db.models import Q

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


# buyProduct page
@login_required
def buyProduct(request, id):
    user = get_object_or_404(User, id=id)
    if request.method == 'POST':
        form = BuyProductForm(request.POST)
        if form.is_valid():
            item_id = form.cleaned_data['item_id']
            _ups_name = form.cleaned_data['ups_name']
            _count = form.cleaned_data['count']
            _x = form.cleaned_data['x']
            _y = form.cleaned_data['y']

            # retrive item description
            items = list(Product.objects.filter(item_id=str(item_id)))
            _description = items[0].description

            # store in Package table
            newpackage = Package(username=user.username, order_id=0, package_id=0, trackingnumber=0, status="", product_name=item_id, ups_name=_ups_name, description=_description, count=_count, x=_x, y=_y)
            newpackage.save()


            # generate XML
            buyProductXML = ET.Element('buyProduct')

            uidXML = ET.SubElement(buyProductXML, 'uid')
            uidXML.text = str(newpackage.uid)

            itemXML = ET.SubElement(buyProductXML, 'item_id')
            itemXML.text = str(item_id)

            upsXML = ET.SubElement(buyProductXML, 'ups_name')
            upsXML.text = str(_ups_name)

            descpXML = ET.SubElement(buyProductXML, 'description')
            descpXML.text = str(_description)

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
        # access all valid items from database
        items = list(Product.objects.all())

        form = BuyProductForm()

        context = {
            'user': user,
            'form': form,
            'items': items
        }

    return render(request, 'webserver/buyProduct.html', context)


# list all packages
@login_required
def query(request, id):
    # get all packages related to this user
    user = get_object_or_404(User, id=id)
    packages = Package.objects.filter(~Q(package_id=0), username=user.username)
    packages = list(packages)

    return render(request, 'webserver/query.html', {'user': user, 'packages': packages})

# query specific package
@login_required
def querypackage(request, id, pid):
    user = get_object_or_404(User, id=id)

    if request.method == 'POST':
        # Handle rating form
        form = RatingForm(request.POST)
        if form.is_valid():
            # get rating
            rating = form.cleaned_data['rating']
            rating = str(rating)
            rating = int(rating)
            rating = float(rating)
            rating = round(rating, 1)

            # update package
            package = get_object_or_404(Package, package_id=int(pid))
            package.rating = rating
            package.save()

            # update product
            product = get_object_or_404(Product, item_id=package.product_name)
            total_score = product.totalscore
            num_ratings = product.num_of_ratings
            total_score += rating
            num_ratings += 1
            new_rating = total_score / num_ratings
            
            product.rating = round(new_rating, 1)
            product.totalscore = total_score
            product.num_of_ratings = num_ratings
            product.save()

            return HttpResponseRedirect(reverse('webserver:dashboard', args=[user.id]))

    else:
        # STEP 1: tell app
        # generate XML
        queryXML = ET.Element('query')

        pidXML = ET.SubElement(queryXML, 'packageid')
        pidXML.text = str(pid)

        queryRequest = prettify(queryXML)

        # send query to app server
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        app_server_ip = socket.gethostbyname(HOST)
        s.connect((app_server_ip, PORT))
        s.sendall(queryRequest.encode('utf-8'))


        # STEP 2: render
        # retrive information
        packages = Package.objects.filter(package_id=int(pid))
        package = list(packages)[0]
        ratable = (package.rating == 0.0 and (package.status == 'delivered' or package.status == 'DELIVERED'))
        showable = ((package.status == 'delivered' or package.status == 'DELIVERED') and package.rating != 0.0)
        form = RatingForm()
        context = {
            'user': user,
            'package': package,
            'ratable': ratable,
            'form': form,
            'showable': showable
        }

    return render(request, 'webserver/queryresult.html', context)

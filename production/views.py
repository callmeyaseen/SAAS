from django.shortcuts import render 

# Create your views here.
def production_home(request):
    return HttpResponse("Production Home")
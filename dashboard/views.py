from django.shortcuts import render

def home(request):
    return render(request, 'layout/base.html')

def home(request):
    return render(request, "home.html")
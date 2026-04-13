from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib import messages
from security.models import Role
from accounts.models import UserProfile
from django.contrib.auth.decorators import login_required
@login_required(login_url='user_login')
def create_user(request):

    roles = Role.objects.all()

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        confirm = request.POST.get("confirm")
        role_id = request.POST.get("role")

        if password != confirm:
            messages.error(request, "Passwords do not match!")
            return redirect("create_user")

        user = User.objects.create_user(
            username=username,
            password=password
        )

        UserProfile.objects.filter(user=user).update(role_id=role_id)

        messages.success(request, "User created successfully!")
        return redirect("create_user")

    return render(request, "accounts/create_user.html", {"roles": roles})

from django.contrib.auth import authenticate, login, logout

# def user_login(request):

#     if request.method == "POST":
#         username = request.POST.get("username")
#         password = request.POST.get("password")

#         user = authenticate(username=username, password=password)

#         if user is not None:
#             login(request, user)
#             # return redirect("/utilities/vendor-entry/")
#         else:
#             messages.error(request, "Invalid username or password")

#     return render(request, "accounts/login.html")
def user_login(request):

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect('home')   # ✅ FIX
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")

def user_logout(request):
    logout(request)
    return redirect("user_login")

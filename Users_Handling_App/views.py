from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model

User = get_user_model()

def loginPage(request):
    
    if request.user.is_authenticated:
        user = request.user
        if user.type == 'normal_user':
            return redirect('normal_user:home')
        elif user.type == 'data_scientist':
            return redirect('data_scientist:home')
        elif user.type == 'admin':
            return redirect('admin_side:home')
        else:
            messages.error(request, "Invalid account type. Please contact support.")
            logout(request)
            return redirect('login')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, 'User does not exist')
            return render(request, 'Users_Handling_App/login.html')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)

            
        if user.type == 'normal_user':
            return redirect('normal_user:home')
        elif user.type == 'data_scientist':
            return redirect('data_scientist:home')
        elif user.type == 'admin':
            return redirect('admin_side:home')
            
        else:
            messages.error(request, 'Email or password is incorrect')

    return render(request, 'Users_Handling_App/login_page.html')



def logoutUser(request):
     logout(request)
     return redirect('users:login')



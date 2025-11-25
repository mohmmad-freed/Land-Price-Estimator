from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from .models import ActivationCode

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
            
            logout(request)
            return redirect('users:login')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
                
            if user.type == 'normal':
                return redirect('normal_user:home')
            elif user.type == 'scientist':
                return redirect('data_scientist:home')
            elif user.type == 'admin':
                return redirect('admin_side:home')
            else:
                messages.error(request, "Invalid account type. Please contact support.")
                logout(request)
                return redirect('users:login')

        
            
        else:
            messages.error(request, 'Email or password is incorrect')
            return render(request, 'Users_Handling_App/login_page.html')

    return render(request, 'Users_Handling_App/login_page.html')



def logoutUser(request):
     logout(request)
     return redirect('users:login')





def register(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        activation_code = request.POST.get('activation_code')

        # Validate activation code
        try:
            code_obj = ActivationCode.objects.get(code=activation_code, is_used=False)
        except ActivationCode.DoesNotExist:
            messages.error(request, "Invalid or expired activation code.")
            return redirect('users:register')

        # Create the user and assign type from the code
        user = User.objects.create_user(name=name, email=email, password=password, type=code_obj.user_type)
        code_obj.is_used = True
        code_obj.assigned_to = user
        code_obj.save()

        login(request, user)
        messages.success(request, f"Account created successfully as {user.type}.")
        return redirect('users:login')

    return render(request, 'Users_Handling_App/register.html')
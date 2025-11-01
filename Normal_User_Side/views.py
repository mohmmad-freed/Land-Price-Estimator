from django.shortcuts import render

def dashboard(request):
    return render(request, 'Normal_User_Side/dashboard.html')

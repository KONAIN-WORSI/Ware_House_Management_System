from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

# Create your views here.

@login_required
def dashboard(request):
    user = request.user
    context = {
        'user': user,
        'role': user.get_role_display()
    }
    
    if user.is_admin:
        return render(request, 'accounts/admin_dashboard.html', context)
    elif user.is_manager:
        return render(request, 'accounts/manager_dashboard.html', context)
    elif user.is_staff_member:
        return render(request, 'accounts/staff_dashboard.html', context)
    else:
        return render(request, 'accounts/dashboard.html', context)

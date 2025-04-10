from django.shortcuts import get_object_or_404, render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.template.loader import get_template
from django.views.decorators.cache import never_cache

@never_cache
@login_required(login_url='sign-in')
def index(request) :
    user = request.user

    return render(request, 'app/index.html', {
        'user' : user,
        "page_name": "Welcome back {user.id}"
    })

# ============================================ Dashboard ======================================================= #
@never_cache
@login_required(login_url='sign-in')
def dashboard(request) :
    user = request.user

    return render(request, 'app/dashboard/dashboard.html', {
        "page_name": "Dashboard",
        'user' : user,
        'user-groups': user.groups.all(),
    })

@never_cache
@login_required(login_url='sign-in')
def dashboard_section(request, section):
    section_map = {
        'overview': 'd_status_overview.html',
        'machines': 'd_assigned_machines.html',
        'recent': 'd_recent_activities.html',
        'alerts': 'd_alerts.html',
        'kpms': 'd_performance_metrics.html',
    }

    template_name = section_map.get(section)
    if not template_name:
        raise Http404("Section not found.")
    
    # Logic to avoid returning just section in render
    if request.headers.get('HX-Request'):
        return render(request, f'app/dashboard/{template_name}')
    
    return render(request, 'app/dashboard/dashboard.html', {
        "page_name": "Dashboard",
        "section_template": f'app/dashboard/{template_name}',
    })
# ============================================ Machines ======================================================= #
@never_cache
@login_required(login_url='sign-in')
def machines(request) :
    return render(request, 'app/machines/machines.html', {
        "page_name": "Machines",
    })

@never_cache
@login_required(login_url='sign-in')
def machines_section(request, section):
    section_map = {
        'grid': 'm_grid.html',
        'table': 'm_table.html',
    }

    template_name = section_map.get(section)
    if not template_name:
        raise Http404("Section not found.")

    # Logic to avoid returning just section in render
    if request.headers.get('HX-Request'):
        return render(request, f'app/machines/{template_name}')
    
    return render(request, 'app/machines/machines.html', {
        "page_name": "Machines",
        "section_template": f'app/machines/{template_name}',
    })

# ============================================ Collections ======================================================= #
@never_cache
@login_required(login_url='sign-in')
def collections(request) :
    return render(request, 'app/collections/collections.html', {
        "page_name": "Collections",
    })

# ============================================ Cases ======================================================= #
@never_cache
@login_required(login_url='sign-in')
def cases(request) :
    return render(request, 'app/cases/cases.html', {
        "page_name": "Cases",
    })

@never_cache
@login_required(login_url='sign-in')
def cases_section(request, section):
    section_map = {
        'open': 'case_open.html',
        'in_progress': 'case_in_progress.html',
        'pending': 'case_pending.html',
        'resolved': 'case_resolved.html',
    }

    template_name = section_map.get(section)
    if not template_name:
        raise Http404("Section not found.")

    # Logic to avoid returning just section in render
    if request.headers.get('HX-Request'):
        return render(request, f'app/cases/{template_name}')
    
    return render(request, 'app/cases/cases.html', {
        "page_name": "Cases",
        "section_template": f'app/cases/{template_name}',
    })

# ============================================ Auth ======================================================= #
def signin(request) :
    return render(request, 'app/sign-in.html', {'hide_navbar': True})

def resetPassword(request) :
    return render(request, 'app/reset-password.html', {'hide_navbar': True})

@never_cache
@login_required(login_url='sign-in')
def static_pages(request) :
    return render(request, 'app/static-pages/static-pages.html', {'hide_navbar': True})

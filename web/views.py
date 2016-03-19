from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Task
from django import forms
from datetime import datetime

# Create your views here.
def index(request):
    responsetxt = ''
    thisuser = User.objects.get(username=request.user.username)

    tasks = Task.objects.filter(user = thisuser, status = 'W')
    tasksDone = Task.objects.filter(user = thisuser, status = 'D')
    context = {'tasks': tasks, 'tasksDone': tasksDone}

    #return redirect('/login/?next=%s' % request.path)
    return render(request, 'index.html', context)

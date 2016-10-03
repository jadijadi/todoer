# -*- coding: utf-8 -*-


from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Task
from django import forms
from datetime import datetime

import time

def RateLimited(maxPerSecond): # a decorator. @RateLimited(10) will let 10 runs in 1 seconds
    minInterval = 1.0 / float(maxPerSecond)
    def decorate(func):
        lastTimeCalled = [0.0]
        def rateLimitedFunction(*args,**kargs):
            elapsed = time.clock() - lastTimeCalled[0]
            leftToWait = minInterval - elapsed
            if leftToWait>0:
                time.sleep(leftToWait)
            ret = func(*args,**kargs)
            lastTimeCalled[0] = time.clock()
            return ret
        return rateLimitedFunction
    return decorate


# Create your views here.
def index(request):
    if request.user.is_anonymous():
        return render(request, 'login.html')

    responsetxt = ''
    #thisuser = User.objects.get(username=request.user.username)

    tasks = Task.objects.filter(status = 'W', user=request.user)
    tasksDone = Task.objects.filter(status = 'D', user=request.user)
    context = {'tasks': tasks, 'tasksDone': tasksDone}

    #return redirect('/login/?next=%s' % request.path)
    return render(request, 'index.html', context)


@login_required
def taskdone(request, taskid):
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    print (thisTask)
    thisTask.status = 'D'
    thisTask.save()
    return redirect('/')

@login_required
def taskadd(request):
    tasktext = request.POST['tasktext']
    savedate = datetime.now()
    thisTask = Task(text=tasktext, status='W', createdate = savedate, user=request.user)
    thisTask.save()
    return redirect('/')

@login_required
def taskredo(request, taskid):
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    print (thisTask)
    thisTask.status = 'W'
    thisTask.save()
    return redirect('/')


def logout_page(request):
    if not request.user.is_anonymous():
        logout(request)
    return redirect('/')

@RateLimited(4)
def login_page(request):
    if ('dologin' in request.POST):
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('/')
            else:
                return HttpResponse('your account is disabled')
        else:
                context = {'message': 'نام کاربری یا کلمه عبور اشتباه بود'}
                return render(request, 'login.html', context)
    else:
        return render(request, 'login.html')

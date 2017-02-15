# -*- coding: utf-8 -*-

import requests
from django.conf import settings
from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.shortcuts import redirect
from .models import Task, Passwordresetcodes
from django import forms
from datetime import datetime
from django.contrib.auth.hashers import make_password
import random
import string
import time

import os
from postmark import PMMail

random_str = lambda N: ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for _ in range(N))

import logging
logger = logging.getLogger(__name__)


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def grecaptcha_verify(request):
    logger.debug("def grecaptcha_verify: " + format(request.POST))
    data = request.POST
    captcha_rs = data.get('g-recaptcha-response')
    url = "https://www.google.com/recaptcha/api/siteverify"
    params = {
        'secret': settings.RECAPTCHA_SECRET_KEY,
        'response': captcha_rs,
        'remoteip': get_client_ip(request)
    }
    verify_rs = requests.get(url, params=params, verify=True)
    verify_rs = verify_rs.json()
    return verify_rs.get("success", False)



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
    logger.debug("def index: " + format(request.POST))
    if request.user.is_anonymous():
        return render(request, 'login.html')

    responsetxt = ''
    #thisuser = User.objects.get(username=request.user.username)

    tasks = Task.objects.filter(status = 'W', user=request.user, mothertask=None)
    waitingtasks = []

    for task in tasks:
        subtasks = Task.objects.filter(status='W', user=request.user, mothertask=task)
        waitingtasks.append({'text': task.text, 'id': task.id, 'subtasks': subtasks})
        #task['subtasks'] = subtask

    tasksDone = Task.objects.filter(status = 'D', user=request.user).order_by('-createdate').all()[:100]
    context = {'tasks': waitingtasks, 'tasksDone': tasksDone}

    #return redirect('/login/?next=%s' % request.path)
    return render(request, 'index.html', context)

@RateLimited(4)
def resetpassword(request):
    logger.debug("def resetpassword")
    if request.POST.has_key('requestcode'): #form is filled. if not spam, generate code and save in db and send email. wait for click on email.

        if not grecaptcha_verify(request): # captcha was not correct
            context = {'message': 'کپچای گوگل درست وارد نشده بود. شاید ربات هستید؟ کد یا کلیک یا تشخیص عکس زیر فرم را درست پر کنید. ببخشید که فرم به شکل اولیه برنگشته!'} #TODO: forgot password
            return render(request, 'register.html', context)

        logger.debug("def register requestcode: " + format(request.POST)) #TODO: password should be asked AFTER user clicked on code - not when asking for reset link!
        code = random_str(28)
        now = datetime.now()
        email = request.POST['email']
        password = request.POST['password']
        if User.objects.filter(email=email).exists(): #does this email exists?
            this_user = User.objects.get(email=email)
            temporarycode = Passwordresetcodes (email = email, time = now, code = code, password=password)
            temporarycode.save()
            message = PMMail(api_key = settings.POSTMARK_API_TOKEN,
                             subject = "ریست پسورد تودویر",
                             sender = "jadi@jadi.net",
                             to = email,
                             text_body = "خطری نیست! نام کاربری شما: «{}» است و برای فعال کردن پسورد جدید خود کافی است اینجا کلیک کنید:\n http://todoer.ir/accounts/resetpassword/?code={}\nدر صورتی که شما در todoer.ir درخواست تغییر پسورد نداده اید، به این ایمیل توجه نکنید".format(this_user.username, code),
                             tag = "Password reset")
            message.send()
            logger.debug("def resetpassword email for http://todoer.ir/accounts/resetpassword/?email={}&code={}".format(email, code))
            context = {'message': 'ایمیلی به شما ارسال شده. در صورتی که روی لینک موجود در آن کلیک کنید، پسورد شما به چیزی که الان وارد کردید تغییر می کند. روش فوق العاده ای نیست ولی کار می کند!'}
            return render(request, 'login.html', context)
        else: # there is no user with that email
            logger.debug("def resetpassword requestcode no user with email ".format(email))
            context = {'message': 'کاربری با این ایمیل در دیتابیس ما وجود ندارد! اگر مشکل واقعا جدی است به http://gapper.ir/channel/todoer مراجعه کنید و مساله را بنویسید'}
            return render(request, 'login.html', context)

    elif request.GET.has_key('code'): #clicked on email, passwd the code
        logger.debug("def resetpassword code: " + format(request.GET))
        code = request.GET['code']
        if Passwordresetcodes.objects.filter(code=code).exists(): #if code is in temporary db, read the data and create the user
            target_tmp_user = Passwordresetcodes.objects.get(code=code) #related email in the resetpassword db
            target_user = User.objects.get(email=target_tmp_user.email)
            logger.debug("def resetpassword user {} with code {}".format(target_user.username, code))
            target_user.set_password(target_tmp_user.password)
            target_user.save()
            Passwordresetcodes.objects.filter(code=code).delete() #delete the temporary activation code from db
            context = {'message': 'پسورد به چیزی که در فرم درخواست داده بودید تغییر یافت. لطفا لاگین کنید. خواهش میکنم!'}
            return render(request, 'login.html', context)
        else:
            context = {'message': 'این کد فعال سازی معتبر نیست. در صورت نیاز دوباره تلاش کنید'}
            return render(request, 'login.html', context)
    else:
        context = {'message': ''}
        return render(request, 'resetpassword.html', context)




@RateLimited(4)
def register(request):
    logger.debug("def register")
    if request.POST.has_key('requestcode'): #form is filled. if not spam, generate code and save in db, wait for email confirmation, return message
        logger.debug("def register requestcode: " + format(request.POST))
        #is this spam? check reCaptcha
        if not grecaptcha_verify(request): # captcha was not correct
            context = {'message': 'کپچای گوگل درست وارد نشده بود. شاید ربات هستید؟ کد یا کلیک یا تشخیص عکس زیر فرم را درست پر کنید. ببخشید که فرم به شکل اولیه برنگشته!'} #TODO: forgot password
            return render(request, 'register.html', context)

        if User.objects.filter(email = request.POST['email']).exists(): # duplicate email
            context = {'message': 'متاسفانه این ایمیل قبلا استفاده شده است. در صورتی که این ایمیل شما است، از صفحه ورود گزینه فراموشی پسورد رو انتخاب کنین. ببخشید که فرم ذخیره نشده. درست می شه'} #TODO: forgot password
            #TODO: keep the form data
            return render(request, 'register.html', context)

        if not User.objects.filter(username = request.POST['username']).exists(): #if user does not exists
                code = random_str(28)
                now = datetime.now()
                email = request.POST['email']
                password = make_password(request.POST['password'])
                username = request.POST['username']
                temporarycode = Passwordresetcodes (email = email, time = now, code = code, username=username, password=password)
                temporarycode.save()
                message = PMMail(api_key = settings.POSTMARK_API_TOKEN,
                                 subject = "فعال سازی اکانت تودو",
                                 sender = "jadi@jadi.net",
                                 to = email,
                                 text_body = "برای فعال سازی ایمیلی تودویر خود روی لینک روبرو کلیک کنید: http://todoer.ir/accounts/register/?email={}&code={}".format(email, code),
                                 tag = "Create account")
                message.send()
                logger.debug("def register email for http://todoer.ir/accounts/register/?email={}&code={}".format(email, code))
                context = {'message': 'ایمیلی حاوی لینک فعال سازی اکانت به شما فرستاده شده، لطفا پس از چک کردن ایمیل، روی لینک کلیک کنید.'}
                return render(request, 'login.html', context)
        else:
            context = {'message': 'متاسفانه این نام کاربری قبلا استفاده شده است. از نام کاربری دیگری استفاده کنید. ببخشید که فرم ذخیره نشده. درست می شه'} #TODO: forgot password
            #TODO: keep the form data
            return render(request, 'register.html', context)
    elif request.GET.has_key('code'): # user clicked on code
        logger.debug("def register code: " + format(request.GET))
        email = request.GET['email']
        code = request.GET['code']
        if Passwordresetcodes.objects.filter(code=code).exists(): #if code is in temporary db, read the data and create the user
            new_temp_user = Passwordresetcodes.objects.get(code=code)
            newuser = User.objects.create(username=new_temp_user.username, password=new_temp_user.password, email=email)
            logger.debug("def register user created: {} with code {}".format(newuser.username, code))
            Passwordresetcodes.objects.filter(code=code).delete() #delete the temporary activation code from db
            context = {'message': 'اکانت شما فعال شد. لاگین کنید - البته اگر دوست داشتی'}
            return render(request, 'login.html', context)
        else:
            context = {'message': 'این کد فعال سازی معتبر نیست. در صورت نیاز دوباره تلاش کنید'}
            return render(request, 'login.html', context)
    else:
        context = {'message': ''}
        return render(request, 'register.html', context)

@login_required
def taskdone(request, taskid):
    logger.debug("def taskdone: " + format(request.POST))
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    thisTask.status = 'D'
    thisTask.save()
    return redirect('/')



@login_required
def taskedit(request):
    logger.debug("def taskedit: " + format(request.POST))
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    taskid = request.POST['taskid']
    tasktext = request.POST['tasktext']
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    thisTask.text = tasktext
    thisTask.save()
    return redirect('/')


@login_required
def taskadd(request):
    logger.debug("def taskadd: " + format(request.POST))
    tasktext = request.POST['tasktext']
    savedate = datetime.now()
    try:
        mothertask = Task.objects.get(id=request.POST['mothertask'], user=request.user)
    except:
        mothertask =  None

    thisTask = Task(text=tasktext, status='W', createdate = savedate, user=request.user, mothertask=mothertask)
    thisTask.save()
    return redirect('/')

@login_required
def taskredo(request, taskid):
    logger.debug("def taskredo: " + format(request.POST))
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    print (thisTask)
    thisTask.status = 'W'
    thisTask.save()
    return redirect('/')


@login_required
def deletetask(request, taskid):
    logger.debug("def deletetask: " + format(request.POST))
    #thiscustomer = Customer.objects.filter(user=User.objects.filter(username=request.POST.get('customername')))[0]
    thisuser = request.user
    thisTask = Task.objects.get(id=taskid, user = thisuser)
    print (thisTask)
    thisTask.status = 'W'
    thisTask.delete()
    return redirect('/')


def logout_page(request):
    logger.debug("def logout_page: " + format(request.POST))
    if not request.user.is_anonymous():
        logout(request)
    return redirect('/')

@RateLimited(4)
def login_page(request):
    logger.debug("def login_page: " + format(request.POST))

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

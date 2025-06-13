from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import Student
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
import json

def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
        return render(request, 'portal/login.html', {'error': 'Invalid credentials'})
    return render(request, 'portal/login.html')

@login_required
def home(request):
    students = Student.objects.all()
    return render(request, 'portal/home.html', {'students': students})

@login_required
def logout_view(request):
    logout(request)
    return redirect('login')

@csrf_exempt
def update_student(request):
    if request.method == "POST":
        data = json.loads(request.body)
        student = Student.objects.get(id=data['id'])
        student.name = data['name']
        student.subject = data['subject']
        student.marks = data['marks']
        student.save()
        return JsonResponse({'status': 'updated'})
    return HttpResponseBadRequest()

@csrf_exempt
def delete_student(request):
    if request.method == "POST":
        data = json.loads(request.body)
        Student.objects.get(id=data['id']).delete()
        return JsonResponse({'status': 'deleted'})
    return HttpResponseBadRequest()

@csrf_exempt
def add_student(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get('name')
            subject = data.get('subject')
            marks = int(data.get('marks', 0))  # Default to 0 if not provided

            if not name or not subject:
                return JsonResponse({'status': 'error', 'message': 'Missing fields'})

            student, created = Student.objects.get_or_create(
                name=name,
                subject=subject,
                defaults={'marks': marks}  # ✅ THIS LINE IS THE FIX
            )

            if not created:
                student.marks += marks
                student.save()

            return JsonResponse({'status': 'success'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    return HttpResponseBadRequest()


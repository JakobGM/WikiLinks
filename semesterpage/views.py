from django.shortcuts import render

# Create your views here.
def semester(request, program_code, semester_number):
    return render(request, 'helloWorld.html')

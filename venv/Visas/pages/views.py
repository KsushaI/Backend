'''
from django.http import HttpResponse

def pages(request):
    return HttpResponse("Hello world!")'''
from django.http import HttpResponseForbidden
# Create your views here.
from django.shortcuts import render, get_object_or_404, redirect
import psycopg2
from datetime import date
from .models import Visa, Application_Visa, Application

visas_list = [
    {
        'id': 1,
        'type': 'Туристическая',
        'price': 18000,
    },
    {
        'id': 2,
        'type': 'Учебная',
        'price': 15000,
    },
    {
        'id': 3,
        'type': 'Рабочая',
        'price': 17000,
    },
    {
        'id': 4,
        'type': 'Частная',
        'price': 12000,
    },
    {
        'id': 5,
        'type': 'Транзитная',
        'price': 13500,
    },
    {
        'id': 6,
        'type': 'Гуманитарная',
        'price': 7000,
    }
]

applications = [
    {
        "id": 1,
        "from": "21.09.2024",
        "duration": 30,
        "visas": [2, 3, 5, 6],
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович",
                 "Моисеев Моисей Моисеевич"]
    },
    {
        "id": 2,
        "from": "22.09.2024",
        "duration": 90,
        "visas": [1, 3, 4, 6, 2],
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович",
                 "Моисеев Моисей Моисеевич", "Петров Пётр Петрович"]
    },
    {
        "id": 3,
        "from": "23.09.2024",
        "duration": 180,
        "visas": [1, 3, 4, 6, 2, 5],
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович",
                 "Моисеев Моисей Моисеевич", "Петров Пётр Петрович", "Тимошин Тимофей Тимофеевич"]
    }

]

'''def ordered(application_id):
    ordered_visas = []
    for v in applications[application_id - 1]['visas']:
        ordered_visas.append(visas_list[v - 1])
    for i in range(len(applications[application_id - 1]['visas'])):
        fio = applications[application_id - 1]['fios'][i].split()
        ordered_visas[i]["last_name"] = fio[0]
        ordered_visas[i]["first_name"] = fio[1]
        ordered_visas[i]["patronymic"] = fio[2]
    return ordered_visas'''




# current trolly
app_id_ = 7
def counter(request):
    application = Application.objects.filter(creator= request.user, status='Черновик').first()
    if application:
        return Application_Visa.objects.filter(app_id=application.id).count()
    else:
        return 0


def visas(request):
    search_query = request.GET.get('search_query', '')
    app = Application.objects.filter(creator=request.user, status='Черновик').first()
    if app:
        app_id = app.id
    else:
        app_id = 0
    if search_query and search_query.isnumeric():
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': counter(request),
                       'visas_list': Visa.objects.filter(price__lte=int(search_query), status='действует')})
    else:
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': counter(request),
                       'visas_list': Visa.objects.filter(status='действует').order_by('id')})


def details(request, visa_id):
    deleted_visas = Visa.objects.filter(status='удалена')
    for v in deleted_visas:
        if visa_id == v.id:
            return render(request, 'deleted.html', {'object': 'услуга'})
    return render(request, 'details.html', {'visa':
                                                Visa.objects.filter(id=visa_id)[0]})


def order(request, application_id):
    deleted_apps = Application.objects.filter(status='Удалена')
    for a in deleted_apps:
        if application_id == a.id:
            return render(request, 'deleted.html', {'object': 'заявка'})
    else:
        return render(request, 'trolly.html',
                      {"ordered_visas": ordered(application_id), "from": Application.objects.get(id =application_id).start_date,
                       "duration": Application.objects.get(id = application_id).duration, 'app_id': application_id})

def ordered(application_id):
    chosen = Application_Visa.objects.filter(app_id=application_id)
    chosen_ids = []
    for c in chosen:
        chosen_ids.append(c.visa_id)
    return Visa.objects.filter(id__in=chosen_ids)


def add(request, visa_id):
    if request.method == 'POST':
        visa = get_object_or_404(Visa, id=visa_id)
        application, new_application = Application.objects.get_or_create(creator=request.user, status='Черновик')
        if application:
            Application_Visa.objects.update_or_create(app_id=application.id, visa_id=visa.id)
        else:
            Application_Visa.objects.create(app_id=new_application.id, visa_id=visa.id)
        return redirect('visas')
    return HttpResponseForbidden



def delete(request, app_id):
    if request.method == 'POST':
        conn = psycopg2.connect(dbname="postgres", host="localhost", user="postgres", password="postgres", port="15432")
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE applications SET status = 'Удалена' where id = %s", [app_id])
        conn.commit()
        cursor.close()
        conn.close()
        return redirect('visas')
    return HttpResponseForbidden()

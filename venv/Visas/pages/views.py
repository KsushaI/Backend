'''
from django.http import HttpResponse

def pages(request):
    return HttpResponse("Hello world!")'''
# Create your views here.
from django.shortcuts import render
from datetime import date

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
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович", "Моисеев Моисей Моисеевич"]
    },
    {
        "id": 2,
        "from": "22.09.2024",
        "duration": 90,
        "visas": [1, 3, 4, 6, 2],
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович", "Моисеев Моисей Моисеевич", "Петров Пётр Петрович"]
    },
    {
        "id": 3,
        "from": "23.09.2024",
        "duration": 180,
        "visas": [1, 3, 4, 6, 2, 5],
        "fios": ["Алексеева Алекса Алексеевна", "Васильев Василий Васильевич", "Иванов Иван Иванович", "Моисеев Моисей Моисеевич", "Петров Пётр Петрович", "Тимошин Тимофей Тимофеевич"]
    }

]


def ordered(application_id):
    ordered_visas = []
    for v in applications[application_id - 1]['visas']:
        ordered_visas.append(visas_list[v - 1])
    for i in range(len(applications[application_id - 1]['visas'])):
        fio = applications[application_id - 1]['fios'][i].split()
        ordered_visas[i]["last_name"] = fio[0]
        ordered_visas[i]["first_name"] = fio[1]
        ordered_visas[i]["patronymic"] = fio[2]
    return ordered_visas


app_id = 2

def details(request, visa_id):
    return render(request, 'details.html', {'visa': visas_list[visa_id - 1]})


def order(request, application_id):
    return render(request, 'trolly.html', {"ordered_visas": ordered(application_id), "from": applications[application_id - 1]["from"], "duration": applications[application_id - 1]["duration"]})



def visas(request):
    search_query = request.GET.get('search_query', '')
    filtered_visas = []
    if search_query and search_query.isnumeric():
        for visa in visas_list:
            if visa['price'] <= int(search_query):
                filtered_visas.append(visa)
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': len(applications[app_id - 1]['visas']),
                       'visas_list': filtered_visas})
    else:
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': len(applications[app_id - 1]['visas']),
                       'visas_list': visas_list})



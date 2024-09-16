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
        'validity': "до 90 дней"
    },
    {
        'id': 2,
        'type': 'Учебная',
        'price': 15000,
        'validity': "до 6 месяцев"
    },
    {
        'id': 3,
        'type': 'Рабочая',
        'price': 17000,
        'validity': "до 30 дней"
    },
    {
        'id': 4,
        'type': 'Частная',
        'price': 12000,
        'validity': "до 1 года"
    },
    {
        'id': 5,
        'type': 'Транзитная',
        'price': 13500,
        'validity': "до 5 лет"
    },
    {
        'id': 6,
        'type': 'Гуманитарная',
        'price': 14600,
        'validity': "до 6 месяцев"
    }
]

applications = [
    {
        "id": 1,
        "visas": [2, 3, 5, 6]
    },
    {
        "id": 2,
        "visas": [1, 3, 4, 6, 2]
    },
    {
        "id": 3,
        "visas": [1, 3, 4, 6, 2, 5]
    }
]


def ordered(application_id):
    ordered_visas = []
    for v in applications[application_id - 1]['visas']:
        ordered_visas.append(visas_list[v - 1])
    return ordered_visas


app_id = 2


def visas(request):
    return render(request, 'paper.html',
                  {'app_id': app_id, 'counter': len(applications[app_id - 1]['visas']), 'visas_list': visas_list,
                   "input_text": "Найти по цене"})


def details(request, visa_id):
    return render(request, 'details.html', {'visa': visas_list[visa_id - 1]})


def order(request, application_id):
    return render(request, 'trolly.html', {"ordered_visas": ordered(application_id)})


def filtered(request):
    input_text = request.POST['text']
    filtered_visas = []
    if input_text.isnumeric():
        for visa in visas_list:
            if visa['price'] <= int(input_text):
                filtered_visas.append(visa)
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': len(applications[app_id - 1]['visas']),
                       'visas_list': filtered_visas,
                       "input_text": input_text})
    else:
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': len(applications[app_id - 1]['visas']),
                       'visas_list': visas_list,
                       "input_text": input_text})

'''
from django.http import HttpResponse

def pages(request):
    return HttpResponse("Hello world!")'''

from django.http import HttpResponseForbidden
# Create your views here.
import psycopg2
from datetime import date, datetime
from django.db.models import Sum
from rest_framework.response import Response
from django.shortcuts import render, get_object_or_404, redirect
from rest_framework import status
from .serializers import VisaSerializer, UserSerializer, ApplicationSerializer, ApplicationVisaSerializer
from .models import Visa, Application_Visa, Application
from django.contrib.auth.models import User
from .minio import add_pic, delete_pic
from rest_framework.views import APIView
from rest_framework.decorators import api_view


def get_user():
    if not hasattr(get_user, 'instance'):
        get_user.instance = User.objects.get(username='ksu')
    return get_user.instance


class VisaList(APIView):
    model_class = Visa
    serializer_class = VisaSerializer

    # Возвращает список of visas
    def get(self, request, format=None):
        visas = self.model_class.objects.filter(status='действует')
        serializer = self.serializer_class(visas, many=True)
        user_draft_apps = Application.objects.filter(creator=get_user(), status='Черновик')
        if user_draft_apps.exists():
            user_draft_app_id = user_draft_apps.first().id
        else:
            user_draft_app_id = None
        return Response({'user_draft_app_id': user_draft_app_id, 'services': serializer.data})

    # Добавляет новую visa
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            visa = serializer.save(creator=get_user())
            pic = request.FILES.get("pic")
            pic_result = add_pic(visa, pic)
            # Если в результате вызова add_pic результат - ошибка, возвращаем его.
            if 'error' in pic_result.data:
                return pic_result
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VisaDetail(APIView):
    model_class = Visa
    serializer_class = VisaSerializer

    # Возвращает информацию о визе
    def get(self, request, pk, format=None):
        visa = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(visa)
        return Response(serializer.data)

    # Обновляет информацию о визе (для модератора)
    def put(self, request, pk, format=None):
        visa = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(visa, data=request.data, partial=True)
        if 'pic' in serializer.initial_data:
            pic_result = add_pic(visa, serializer.initial_data['pic'])
            if 'error' in pic_result.data:
                return pic_result
        if serializer.is_valid():
            serializer.save(creator=get_user())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Удаляет информацию о визе
    def delete(self, request, pk, format=None):
        visa = get_object_or_404(self.model_class, pk=pk)
        visa.delete()
        delete_pic(pk)
        return Response(status=status.HTTP_204_NO_CONTENT)


# Добавление услуги в корзину, создание корзины-черновик, если она не существует
@api_view(['POST'])
def add_to_trolly(request, pk, format=None):
    visa = get_object_or_404(Visa, pk=pk)
    application, new_application = Application.objects.get_or_create(creator=get_user(), status='Черновик')
    if application:
        app_visa, _ = Application_Visa.objects.update_or_create(app_id=application.id, visa_id=visa.id)
    if new_application:
        app_visa, _ = Application_Visa.objects.create(app_id=new_application, visa_id=visa)
    serializer = ApplicationVisaSerializer(app_visa)
    return Response(serializer.data)


class AppList(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer

    def get(self, request, format=None):
        apps = self.model_class.objects.exclude(status="Удалена").exclude(status="Черновик")
        serializer = self.serializer_class(apps, many=True)
        return Response(serializer.data)


class AppDetail(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    serializer_class2 = VisaSerializer

    # Возвращает информацию о заявке
    def get(self, request, pk, format=None):
        app = get_object_or_404(self.model_class, pk=pk)
        visas = ordered(pk)
        serializer = self.serializer_class(app)
        serializer2 = self.serializer_class2(visas, many=True)
        services = [{'type': visa['type'], 'price': visa['price'], 'url': visa['url']} for visa in serializer2.data]
        return Response({'app_fields': serializer.data, "services": services})

    # Обновляет доп поля заявки
    def put(self, request, pk, format=None):
        app = get_object_or_404(self.model_class, pk=pk)
        updated_data = {key: value for key, value in request.data.items() if key in ['start_date', 'duration']}
        serializer = self.serializer_class(app, data=updated_data, partial=True)
        if serializer.is_valid():
            serializer.save(creator=get_user())
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Смена статуса заявки на Удалён создателем
    def delete(self, request, pk, format=None):
        app = get_object_or_404(self.model_class, pk=pk)
        if get_user().id == app.creator_id:
            serializer = self.serializer_class(app, data={'status': 'Удалена'})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def form(request, pk, format=None):
    app = get_object_or_404(Application, pk=pk)
    if get_user().id == app.creator_id:
        #checking all mandatory fields
        serializer = ApplicationSerializer(app, data={'status': 'Сформирована'})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def complete(request, pk, format=None):
    app = get_object_or_404(Application, pk=pk)
    if get_user().is_staff:
        #total = 0
        #app_visas = Application_Visa.objects.filter(app=pk)
        #for app_visa in app_visas:
            #total += app_visa.visa.price
        total = Application_Visa.objects.filter(app=pk).aggregate(total=Sum('visa__price'))['total']
        serializer = ApplicationSerializer(app, data={'status': 'Завершена', 'moderator': get_user(), 'completion_date': datetime.now(), 'total': 33600}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)

@api_view(['PUT'])
def decline(request, pk, format=None):
    app = get_object_or_404(Application, pk=pk)
    if get_user().is_staff:
        #total = 0
        #app_visas = Application_Visa.objects.filter(app=pk)
        #for app_visa in app_visas:
            #total += app_visa.visa.price
        total = Application_Visa.objects.filter(app=pk).aggregate(total=Sum('visa__price'))['total']
        serializer = ApplicationSerializer(app, data={'status': 'Отклонена', 'moderator': get_user(), 'completion_date': datetime.now(), 'total': 33600}, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response(status=status.HTTP_400_BAD_REQUEST)

class AppVisaList(APIView):
    model_class = Application_Visa
    serializer_class = ApplicationVisaSerializer

    def get(self, request, format=None):
        apps_visas = self.model_class.objects.all()
        serializer = self.serializer_class(apps_visas, many=True)
        return Response(serializer.data)

    def delete(self, request, pk, format=None):
        app_visa = get_object_or_404(self.model_class, pk=pk)
        if Application.objects.get(id=app_visa.app_id).status == 'Черновик':
            serializer = self.serializer_class(app_visa, data={'app' : None, 'visa': None, 'fio': None})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)


    def put(self, request, pk, format=None):
        app_visa = get_object_or_404(self.model_class, pk=pk)
        if Application.objects.get(id = app_visa.app_id).status == 'Черновик':
            updated_data = {key: value for key, value in request.data.items() if key in ['fio']}
            serializer = self.serializer_class(app_visa, data=updated_data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

class UserList(APIView):
    model_class = User
    serializer_class = UserSerializer

    def get(self, request, format=None):
        user = self.model_class.objects.all()
        serializer = self.serializer_class(user, many=True)
        return Response(serializer.data)

    # Добавляет нового пользователя
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Изменение данных пользователя(личный кабинет)


class UserDetail(APIView):
    model_class = User
    serializer_class = UserSerializer

    # Возвращает информацию о пользователе
    def get(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    # Обновляет информацию о пользователе (для модератора)
    def put(self, request, pk, format=None):
        user = get_object_or_404(self.model_class, pk=pk)
        serializer = self.serializer_class(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['Put'])
def user_put(self, request, pk, format=None):
    user = get_object_or_404(self.model_class, pk=pk)
    serializer = self.serializer_class(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({serializer.data})
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def authenticate(request):
    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
def deauthorize(request):
    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)

















def counter(request):
    application = Application.objects.filter(creator=request.user, status='Черновик').first()
    if application:
        return Application_Visa.objects.filter(app_id=application.id).count()
    else:
        return 0


def visas(request):
    visa_price = request.GET.get('visa_price', '')
    app = Application.objects.filter(creator=request.user, status='Черновик').first()
    if app:
        app_id = app.id
    else:
        app_id = 0
    if visa_price and visa_price.isnumeric():
        return render(request, 'paper.html',
                      {'app_id': app_id, 'counter': counter(request),
                       'visas_list': Visa.objects.filter(price__lte=int(visa_price), status='действует').order_by(
                           'price')})
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
                      {"ordered_visas": ordered(application_id),
                       "from": Application.objects.get(id=application_id).start_date,
                       "duration": Application.objects.get(id=application_id).duration, 'app_id': application_id})


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

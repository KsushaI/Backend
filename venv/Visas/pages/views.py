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

from rest_framework.viewsets import ModelViewSet
from drf_yasg.utils import swagger_auto_schema
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse
import uuid
from rest_framework.decorators import permission_classes, authentication_classes
from django.views.decorators.csrf import csrf_exempt
from .permissions import IsManager, IsAdmin
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.decorators import authentication_classes
from django.conf import settings
import redis

# Connect to our Redis instance
session_storage = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT)


def get_user():
    if not hasattr(get_user, 'instance'):
        get_user.instance = User.objects.get(username='first')
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
            quantity = Application_Visa.objects.filter(app_id=user_draft_app_id).count()

        else:
            user_draft_app_id = None
            quantity = 0
        return Response(
            {'user_draft_app_id': user_draft_app_id, 'number_of_services': quantity, 'services': serializer.data})

    # Добавляет новую visa
    def post(self, request, format=None):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=get_user())
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def update_pic(request, pk, format=None):
    visa = get_object_or_404(Visa, pk=pk)
    serializer = VisaSerializer(visa)
    pic = request.FILES.get("pic")
    pic_result = add_pic(visa, pic)
    # Если в результате вызова add_pic результат - ошибка, возвращаем его.
    if 'error' in pic_result.data:
        return pic_result
    return Response({"url": serializer.data.get('url')}, status=status.HTTP_201_CREATED)


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
    application, new_application = Application.objects.get_or_create(creator=get_user().id, status='Черновик')
    if application:
        app_visa, _ = Application_Visa.objects.update_or_create(app_id=application.id, visa_id=visa.id)
    if new_application:
        app_visa, _ = Application_Visa.objects.create(app_id=new_application, visa_id=visa)
    serializer = ApplicationVisaSerializer(app_visa)
    return Response(serializer.data)


def method_permission_classes(classes):
    def decorator(func):
        def decorated_func(self, *args, **kwargs):
            self.permission_classes = classes
            self.check_permissions(self.request)
            return func(self, *args, **kwargs)

        return decorated_func

    return decorator


class AppList(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    authentication_classes = [SessionAuthentication, BasicAuthentication]

    permission_classes = [IsAuthenticated]

    def get(self, request, format=None):
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        status_ = request.query_params.get('status')
        object_list = self.model_class.objects.filter(creator=get_user()).exclude(status="Черновик").exclude(
            status="Удалена")
        '''if start_date or end_date:
            if not (start_date):
                object_list = object_list.filter(formation_date__lte=end_date)
            elif not (end_date):
                object_list = object_list.filter(formation_date__gte=start_date)
            else:
                object_list = object_list.filter(formation_date__range=[start_date, end_date])'''
        if status_:
            object_list = object_list.filter(status=status_)

        serializer = self.serializer_class(object_list, many=True)
        return Response(serializer.data)


class AppDetail(APIView):
    model_class = Application
    serializer_class = ApplicationSerializer
    serializer_class2 = VisaSerializer
    application_visa_serializer_class = ApplicationVisaSerializer  # Add this line

    # Возвращает информацию о заявке
    def get(self, request, pk, format=None):
        app = get_object_or_404(self.model_class, pk=pk)
        # Fetch the related Application_Visa instances
        application_visas = Application_Visa.objects.filter(app=app)

        # Serialize the application
        serializer = self.serializer_class(app)

        # Serialize the visas and include the fio field
        services = []
        for app_visa in application_visas:
            visa_serializer = self.serializer_class2(app_visa.visa)
            services.append({
                'type': visa_serializer.data['type'],
                'price': visa_serializer.data['price'],
                'url': visa_serializer.data['url'],
                'fio': app_visa.fio  # Include the fio field here
            })
        return Response({'app_fields': serializer.data, "services": services})

    #@swagger_auto_schema(request_body=ApplicationSerializer)
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
        return Response({"error": "Permission denied"}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT'])
def form(request, pk, format=None):
    app = get_object_or_404(Application, pk=pk)
    if get_user().id == app.creator_id:
        # checking all mandatory fields
        serializer = ApplicationSerializer(app, data={'status': 'Сформирована', 'formation_date': datetime.now()},
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error' : "Permission denied. Isn't the creator!"}, status=status.HTTP_400_BAD_REQUEST)


#@csrf_exempt
#@permission_classes([IsManager])
#@authentication_classes([])
#@api_view(['PUT'])
def update_application_status(request, pk, action):
    app = get_object_or_404(Application, pk=pk)
    if get_user().is_staff:
        app.moderator = get_user()
        if action == 'complete':
            app.total = Application_Visa.objects.filter(app_id=app.id).aggregate(total=Sum('visa__price'))[
                            'total'] or 0
            status_ = "Завершена"
        elif action == 'decline':
            status_ = "Отклонена"
        else:
            return Response({"error": "Invalid action"}, status=status.HTTP_400_BAD_REQUEST)
        serializer = ApplicationSerializer(app, data={'status': status_,
                                                      'completion_date': datetime.now(), },
                                           partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    return Response({'error': "Permissiod denied. Isn't staff!"}, status=status.HTTP_400_BAD_REQUEST)


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
            serializer = self.serializer_class(app_visa, data={'app': None, 'visa': None, 'fio': None})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk, format=None):
        app_visa = get_object_or_404(self.model_class, pk=pk)
        if Application.objects.get(id=app_visa.app_id).status == 'Черновик':
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


'''
@api_view(['POST'])
def authenticate(request):
    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
def deauthorize(request):
    return Response(status=status.HTTP_501_NOT_IMPLEMENTED)'''


class UserViewSet(ModelViewSet):
    """Класс, описывающий методы работы с пользователями
    Осуществляет связь с таблицей пользователей в базе данных
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    model_class = User

    def get_permissions(self):
        if self.action in ['create']:
            permission_classes = [AllowAny]
        elif self.action in ['list']:
            permission_classes = [IsAdmin | IsManager]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]

    def create(self, request):
        """
        Функция регистрации новых пользователей
        Если пользователя c указанным в request username ещё нет, в БД будет добавлен новый пользователь.
        """
        if self.model_class.objects.filter(username=request.data['username']).exists():
            return Response({'status': 'Exist'}, status=400)
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            print(serializer.data)
            self.model_class.objects.create_user(username=serializer.data['username'],
                                                 password=serializer.data['password'],
                                                 is_staff=serializer.data['is_staff'],
                                                 is_superuser=serializer.data['is_superuser'])

            return Response({'status': 'Success'}, status=200)
        return Response({'status': 'Exist', 'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


#@permission_classes([AllowAny])
#@authentication_classes([])
#@csrf_exempt
#@swagger_auto_schema(method='post', request_body=UserSerializer)
@api_view(['Post'])
def login_view(request):
    username = request.data["username"]  # допустим передали username и password
    password = request.data["password"]
    user = authenticate(request, username=username, password=password)
    '''if user is not None:
        login(request, user)
        return HttpResponse("{'status': 'ok', 'session_id': random_key}")
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")'''

    if user is not None:
        random_key = str(uuid.uuid4())
        session_storage.set(random_key, username)

        response = HttpResponse("{'status': 'ok'}")
        response.set_cookie("session_id", random_key)

        return response
    else:
        return HttpResponse("{'status': 'error', 'error': 'login failed'}")


def logout_view(request):
    logout(request._request)
    return Response({'status': 'Success'})


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

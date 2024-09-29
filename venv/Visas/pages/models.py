from django.db import models

from django.contrib.auth.models import User


# Create your models here.
class Visa(models.Model):
    type = models.CharField(max_length=30)
    price = models.IntegerField()
    url = models.CharField(max_length=40)
    status = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)
    class Meta:
        db_table = 'visas'


class Application(models.Model):
    status = models.CharField(max_length=26)

    creation_date = models.DateTimeField(auto_now_add=True)

    formation_date = models.DateTimeField(null=True, blank=True)

    completion_date = models.DateTimeField(null=True, blank=True)

    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='заявки_создателя')

    moderator = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True,
                                  related_name='заявки_модератора')

    start_date = models.DateField(default = '2024-09-30')

    duration = models.IntegerField(default = 30)

    class Meta:
        db_table = 'applications'

class Application_Visa(models.Model):
    app = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='зявка')
    visa = models.ForeignKey(Visa, on_delete=models.CASCADE, related_name='виза')
    fio = models.CharField(max_length=60, null=True, blank=True)
    class Meta:
        db_table = 'applications_visas'
        constraints = [
            models.UniqueConstraint(fields=['app', 'visa'], name='unique app_visa')
        ]
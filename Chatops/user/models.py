from django.db import models
from datetime import datetime


class BotUser(models.Model):
    user_id = models.CharField(max_length=250)
    name = models.CharField(max_length=250, null=True)
    email = models.CharField(max_length=250, null=True)
    channel_id = models.CharField(max_length=250, null=True)
    created_date = models.DateTimeField(default=datetime.utcnow())

    def __str__(self):
        return self.name


class Instance(models.Model):
    instance_id = models.CharField(max_length=250, null=True)
    name = models.CharField(max_length=250)

    def __str__(self):
        return self.name


class InstanceAccess(models.Model):
    user_id = models.ForeignKey(BotUser, on_delete=models.DO_NOTHING)
    instance_id = models.ForeignKey(Instance, on_delete=models.CASCADE)


class Manager(models.Model):
    manager_id = models.ForeignKey(BotUser, on_delete=models.DO_NOTHING)
    instance_id = models.ForeignKey(Instance, on_delete=models.CASCADE)


class InstanceOperation(models.Model):
    requested_user = models.ForeignKey(BotUser, on_delete=models.DO_NOTHING, related_name='requested_user')
    message = models.CharField(max_length=500)
    channel_id = models.CharField(max_length=250)
    status = models.CharField(max_length=50)
    response_by = models.ForeignKey(BotUser, on_delete=models.DO_NOTHING, related_name='response_user', null=True)
    response_date = models.DateTimeField(default=datetime.utcnow(), null=True)
    created_date = models.DateTimeField(default=datetime.utcnow())


class Project(models.Model):
    codeship_project_name = models.CharField(max_length=250)
    gitlab_project_id = models.CharField(max_length=250)

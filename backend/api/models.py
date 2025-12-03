from django.db import models


class TelegramUser(models.Model):
    telegram_id = models.IntegerField(primary_key=True)
    username = models.CharField(max_length=128, unique=True, blank=True, null=True)
    date_joined_bot = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    tasks_done = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Пользователь Telegram"
        verbose_name_plural = "Пользователи Telegram"

    def __str__(self):
        return f"ID: {self.telegram_id} @{self.username}"


class Task(models.Model):
    title = models.CharField(max_length=128)
    description = models.TextField()
    instruction = models.TextField()
    link = models.URLField()
    reward = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

    def __str__(self):
        return f"ID: {self.id} — {self.title}"


class Completed(models.Model):
    STATUS_PENDING = 'PE'
    STATUS_DONE = 'DN'

    STATUS_CHOICES = (
        (STATUS_PENDING, 'Pending'),
        (STATUS_DONE, 'Done'),
    )

    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    task = models.ForeignKey(Task, on_delete=models.CASCADE)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)

    class Meta:
        verbose_name = "Выполненное задание"
        verbose_name_plural = "Выполненные задания"
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'task'],
                name='unique_user_task'
            )
        ]


class WelcomeMessage(models.Model):
    text = models.TextField()
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Приветственное сообщение"
        verbose_name_plural = "Приветственные сообщения"
from django.contrib import admin
from django.apps import apps
from django.conf import settings
from django.utils.html import escape
import logging
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from api.models import Completed

logger = logging.getLogger(__name__)


def _send_telegram_message(chat_id: int, text: str):
    token = getattr(settings, "BOT_TOKEN", "")
    if not token:
        logger.warning("BOT_TOKEN is not set. Skip telegram notify.")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }

    try:
        data = urlencode(payload).encode("utf-8")
        req = Request(url, data=data)
        urlopen(req, timeout=10).read()
    except Exception as e:
        logger.exception("Failed to send telegram message: %s", e)


# ✅ Авто-регистрация всех моделей, НО Completed пропускаем (он ниже вручную)
app = apps.get_app_config("api")
for model_name, model in app.models.items():
    if model == Completed:
        continue

    model_admin = type(model_name + "Admin", (admin.ModelAdmin,), {})

    model_admin.list_display = (
        model.admin_list_display
        if hasattr(model, "admin_list_display")
        else tuple([field.name for field in model._meta.fields])
    )
    model_admin.list_display_links = (
        model.admin_list_display_links if hasattr(model, "admin_list_display_links") else ()
    )
    model_admin.list_editable = (
        model.admin_list_editable if hasattr(model, "admin_list_editable") else ()
    )
    model_admin.search_fields = (
        model.admin_search_fields if hasattr(model, "admin_search_fields") else ()
    )

    admin.site.register(model, model_admin)


@admin.register(Completed)
class CompletedAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "task", "status", "rewarded")
    list_filter = ("status", "rewarded")
    search_fields = ("user__telegram_id", "user__username", "task__title")

    readonly_fields = ("user", "task")

    def save_model(self, request, obj, form, change):
        # старый статус ДО сохранения
        old_status = None
        if obj.pk:
            old_status = Completed.objects.get(pk=obj.pk).status

        super().save_model(request, obj, form, change)

        # ✅ начисляем только при переходе в DONE и если ещё не начисляли
        if obj.status == Completed.STATUS_DONE and not obj.rewarded:
            user = obj.user
            user.points += obj.task.reward
            user.tasks_done += 1
            user.save(update_fields=["points", "tasks_done"])

            obj.rewarded = True
            obj.save(update_fields=["rewarded"])

        # ✅ уведомление пользователю только если статус реально изменился
        if old_status != obj.status:
            comment = (obj.admin_comment or "").strip()
            comment_html = escape(comment) if comment else ""

            if obj.status == Completed.STATUS_DONE:
                text = (
                    f"✅ <b>Задание принято</b>\n\n"
                    f"📌 <b>{escape(obj.task.title)}</b>\n"
                    f"💰 Начислено: <b>{obj.task.reward}</b> Б\n"
                )
                if comment_html:
                    text += f"\n💬 Комментарий админа:\n{comment_html}"

                _send_telegram_message(obj.user.telegram_id, text)

            elif obj.status == Completed.STATUS_REJECTED:
                text = (
                    f"❌ <b>Задание отклонено</b>\n\n"
                    f"📌 <b>{escape(obj.task.title)}</b>\n"
                )
                if comment_html:
                    text += f"\n💬 Причина:\n{comment_html}"
                else:
                    text += "\n💬 Причина: не указана"

                text += "\n\nТы можешь выполнить задание ещё раз — оно снова будет доступно."
                _send_telegram_message(obj.user.telegram_id, text)

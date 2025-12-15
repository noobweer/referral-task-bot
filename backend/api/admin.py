from django.contrib import admin
from django.apps import apps
from api.models import Completed

app = apps.get_app_config('api')
for model_name, model in app.models.items():
    model_admin = type(model_name + "Admin", (admin.ModelAdmin,), {})

    model_admin.list_display = model.admin_list_display if hasattr(model, 'admin_list_display') else tuple([field.name for field in model._meta.fields])
    model_admin.list_display_links = model.admin_list_display_links if hasattr(model, 'admin_list_display_links') else ()
    model_admin.list_editable = model.admin_list_editable if hasattr(model, 'admin_list_editable') else ()
    model_admin.search_fields = model.admin_search_fields if hasattr(model, 'admin_search_fields') else ()

    admin.site.register(model, model_admin)

@admin.register(Completed)
class CompletedAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "task", "status", "rewarded")
    list_filter = ("status", "rewarded")
    search_fields = ("user__telegram_id", "user__username", "task__title")

    readonly_fields = ("user", "task")

    def save_model(self, request, obj, form, change):
        # было ли раньше принято?
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
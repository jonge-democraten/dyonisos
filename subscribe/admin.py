# Copyright (c) 2011, Floor Terra <floort@gmail.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from subscribe.models import Registration, IdealIssuer
from subscribe.models import Event, EventQuestion, EventOption, RegistrationLimit
from subscribe.models import Answer
from django.contrib import admin
from django.http import HttpResponse

from xlwt import Workbook
import cStringIO as StringIO


def export_events(eventadmin, request, queryset):
    """
    Helper function to export registrations to an excel file."""
    wb = Workbook()
    for event in queryset:
        # Put each event in it's own sheet
        s = wb.add_sheet(event.slug[:30])  # this is the max number of characters for an excel tab
        # Write header
        s.write(0, 0, "Voornaam")
        s.write(0, 1, "Achternaam")
        s.write(0, 2, "Email")
        s.write(0, 3, "Betaald")
        s.write(0, 4, "Prijs")
        s.write(0, 5, "Purchase ID")
        col_count = 6

        option_to_col = {}
        event_options = EventOption.objects.filter(event=event)
        for option in event_options:
            option_to_col[option.id] = col_count
            s.write(0, col_count, option.name)
            col_count += 1

        q_to_col = {}
        for question in EventQuestion.objects.filter(event=event):
            q_to_col[question.id] = col_count
            s.write(0, col_count, question.name)
            col_count += 1

        # Write the data
        row = 1
        for reg in event.registration_set.all():
            s.write(row, 0, reg.first_name)
            s.write(row, 1, reg.last_name)
            s.write(row, 2, reg.email)
            s.write(row, 3, reg.payed)
            s.write(row, 4, float(reg.get_price()) / 100)
            s.write(row, 5, reg.id)

            for option in reg.event_options.all():
                s.write(row, option_to_col[option.id], 1)

            for ans in reg.answers.all():
                s.write(row, q_to_col[ans.question.id], ans.get_answer())

            row += 1

    out = StringIO.StringIO()
    wb.save(out)
    response = HttpResponse(out.getvalue(), content_type="application/excel")
    response['Content-Disposition'] = 'attachment; filename=events.xls'
    return response

export_events.short_description = "Export event subscriptions to excel."


class EventOptionInline(admin.TabularInline):
    model = EventOption
    extra = 1
    fields = ['name', 'price', 'active', ]

    def has_delete_permission(self, request, obj=None):
        return False


class EventQuestionInline(admin.TabularInline):
    model = EventQuestion
    extra = 1
    fields = ['name', 'question_type', 'help', 'required', ]


class RegistrationLimitInline(admin.TabularInline):
    model = RegistrationLimit
    extra = 1
    fields = ['limit', 'options', 'description', ]

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super(RegistrationLimitInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        kwargs['queryset'] = db_field.rel.to.objects.filter(event=self.parent_obj)
        return super(RegistrationLimitInline, self).formfield_for_manytomany(db_field, request, **kwargs)


class RegistrationLimitAdmin(admin.ModelAdmin):
    model = RegistrationLimit
    fields = ["limit", "event", "options", "description"]
    list_display = ["event", "limit", "get_num_registrations", "is_reached", "description"]
    extra = 1


class EventAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Event", {
            'fields': [
                ('name', 'slug'),
                ('start_registration', 'end_registration'),
                'description', 'price',
            ]}),
        ("Email", {"fields": ["contact_email", "email_template"]}),
    ]
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'end_registration'
    inlines = [EventQuestionInline, EventOptionInline, RegistrationLimitInline]
    actions = [export_events, ]  # XXX: export
    list_display = ['name', 'form_link', 'subscribed', 'total_payed', 'start_registration', 'end_registration']
    search_fields = ["name", ]


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('registration_date', 'trxid')
    fieldsets = (
        (None, {'fields': ('registration_date', 'first_name', 'last_name',
                           'email', 'event', 'event_options', 'payed', 'trxid', 'status', 'check_ttl'), }),
    )
    list_display = ["id", "event", "first_name", "last_name", "registration_date", "payed", "trxid", "status", 'check_ttl']
    list_filter = ["payed", "event"]
    search_fields = ["first_name", "last_name"]


class IdealIssuerAdmin(admin.ModelAdmin):
    model = IdealIssuer
    list_display = ['issuer_id', 'name']


class EventOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'price_str', 'event', 'active', 'limit_reached']
    list_filter = ['active', 'event']


admin.site.register(EventQuestion)
admin.site.register(Event, EventAdmin)
admin.site.register(EventOption, EventOptionAdmin)
admin.site.register(Answer)
admin.site.register(Registration, RegistrationAdmin)
admin.site.register(IdealIssuer, IdealIssuerAdmin)
admin.site.register(RegistrationLimit, RegistrationLimitAdmin)

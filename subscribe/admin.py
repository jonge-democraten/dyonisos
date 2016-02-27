# -*- coding: utf-8 -*-

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

from subscribe.models import Event, EventQuestion, EventOption, Answer, Registration
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.utils.html import format_html

from xlwt import Workbook
import io as BytesIO


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

        q_to_col = {}
        for question in event.eventquestion_set.all():
            if question.question_type == "TEXT":
                continue
            q_to_col[question.id] = col_count
            s.write(0, col_count, question.name)
            col_count += 1

        # Write the data
        row = 1
        for reg in event.registrations.all():
            s.write(row, 0, reg.first_name)
            s.write(row, 1, reg.last_name)
            s.write(row, 2, reg.email)
            s.write(row, 3, reg.paid)
            s.write(row, 4, float(reg.price) / 100)
            s.write(row, 5, reg.id)

            for ans in reg.answers.all():
                s.write(row, q_to_col[ans.question.id], '{}'.format(ans.get_answer()))

            row += 1

    out = BytesIO.BytesIO()
    wb.save(out)
    response = HttpResponse(out.getvalue(), content_type="application/excel")
    response['Content-Disposition'] = 'attachment; filename=events.xls'
    return response

export_events.short_description = "Export event subscriptions to excel."


class EventQuestionInline(admin.TabularInline):
    model = EventQuestion
    extra = 1
    fields = ['name', 'admin_link', 'order', 'question_type', 'radio', 'required', ]
    readonly_fields = ('admin_link',)
    show_change_link = True  # Django 1.8
    ordering = ('order',)

    def admin_link(self, instance):
        url = reverse('admin:subscribe_eventquestion_change', args=(instance.id,))
        return format_html('<a href="{}">Edit</a>', url)


class EventAdmin(admin.ModelAdmin):
    fieldsets = [
        ("Event", {
            'fields': [
                ('name', 'slug'),
                ('start_registration', 'end_registration'),
                'description', 'price', 'max_registrations',
            ]}),
        ("Email", {"fields": ["contact_email", "email_template"]}),
    ]
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'end_registration'
    inlines = [EventQuestionInline]
    actions = [export_events, ]  # XXX: export
    list_display = ['name', 'form_link', 'subscribed', 'total_paid', 'is_full', 'start_registration', 'end_registration']
    search_fields = ["name", ]


class EventOptionInline(admin.TabularInline):
    model = EventOption
    extra = 1
    fields = ['order', 'name', 'price', 'limit', 'num_registrations', 'active', ]
    readonly_fields = ('num_registrations',)
    ordering = ('order',)

    def has_delete_permission(self, request, obj=None):
        return False

    def num_registrations(self, instance):
        return instance.num_registrations()
    num_registrations.short_description = "Registrations"


class EventQuestionAdmin(admin.ModelAdmin):
    readonly_fields = ('event', )
    list_display = ["name", "event", "order", "question_type", ]
    list_filter = ["event"]
    inlines = [EventOptionInline]


class AnswerInline(admin.TabularInline):
    model = Answer
    fields = ['question', 'int_field', 'txt_field', 'bool_field', 'option']
    readonly_fields = ['question', ]
    extra = 0

    def get_formset(self, request, obj=None, **kwargs):
        self.parent_obj = obj
        return super(AnswerInline, self).get_formset(request, obj, **kwargs)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "option":
            kwargs['queryset'] = db_field.rel.to.objects.filter(question__event=self.parent_obj.event)
        return super(AnswerInline, self).formfield_for_foreignkey(db_field, request, **kwargs)


class RegistrationAdmin(admin.ModelAdmin):
    readonly_fields = ('registration_date', 'trxid')
    list_display = ["id", "event", "first_name", "last_name", "status", "registration_date", "paid", "trxid", ]
    list_filter = ["paid", "event"]
    search_fields = ["first_name", "last_name"]
    inlines = [AnswerInline]


admin.site.register(EventQuestion, EventQuestionAdmin)
admin.site.register(Event, EventAdmin)
admin.site.register(Registration, RegistrationAdmin)

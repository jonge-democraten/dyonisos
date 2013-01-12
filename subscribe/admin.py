###############################################################################
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
############################################################################### 

from subscribe.models import *
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
        s = wb.add_sheet(event.name)
        registrations = Registration.objects.filter(event=event)
        # Write header
        s.write(0,0,"Voornaam")
        s.write(0,1,"Achternaam")
        s.write(0,2,"Email")
        s.write(0,3,"Betaald")
        s.write(0,4,"Prijs")
        s.write(0,5,"Optie")
        s.write(0,6,"Purchase ID")
        i = 7
        q_to_col = {}
        for question in EventQuestion.objects.filter(event=event):
            q_to_col[question.id] = i
            s.write(0,i,question.name)
            i += 1
        # Write the data
        row = 1
        for reg in event.registration_set.all():
            s.write(row, 0, reg.first_name)
            s.write(row, 1, reg.last_name)
            s.write(row, 2, reg.email)
            s.write(row, 3, reg.payed)
            s.write(row, 4, float(reg.event_option.price)/100)
            s.write(row, 5, reg.event_option.name)
            s.write(row, 6, reg.id)
            for ans in reg.answers.all():
                s.write(row, q_to_col[ans.question.id], ans.get_answer())
            row += 1
    out = StringIO.StringIO()
    wb.save(out)
    response = HttpResponse(out.getvalue(), mimetype="application/excel")
    response['Content-Disposition'] = 'attachment; filename=events.xls'
    return response
export_events.short_description = "Export event subscriptions to excel."

class EventOptionInline(admin.TabularInline):
    model = EventOption
    extra = 1
    fields = ['name', 'price', 'active', 'delete_event',]
    readonly_fields = ['delete_event',]
    can_delete = False

class EventQuestionInline(admin.TabularInline):
    model = EventQuestion
    extra = 1
    fields = ['name', 'question_type', 'help', 'required']

class EventAdmin(admin.ModelAdmin):
    fieldsets = [
        (None, {
            'fields': [
                ('name', 'slug'),
                ('start_registration', 'end_registration'),
                'description'
            ]}),
        ("Email", {
            "fields": ["contact_email", "email_template"]
        }),
    ]
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'end_registration'
    inlines = [EventOptionInline, EventQuestionInline]
    actions = [export_events,] #XXX: export
    list_display = ['name', 'form_link', 'subscribed', 'total_payed', 'start_registration', 'end_registration', 'update_all_event_transaction_statuses']
    #list_filter = ['active', ]

class RegistrationAdmin(admin.ModelAdmin):
    #def get_form(self, request, obj=None, **kwargs):
    #    form = super(RegistrationAdmin,self).get_form(self,request, obj,**kwargs)
    #    form.base_fields['event_option'].queryset =
    #        form.base_fields['event_option'].queryset.filter(event_option_event = None)#XXX)
    readonly_fields = ('registration_date', 'trxid') 
    fieldsets = (
        (None, {
            'fields': ('registration_date', 'first_name', 'last_name', 
                        'email', 'event', 'event_option', 'payed', 'trxid', 'check_ttl'),
            }),
    )
    list_display = ["id", "event", "first_name", "last_name", "registration_date", "payed", "trxid", 'check_ttl', "update_transaction_status", "event_option"]
    list_filter = ["payed", "event"]

#admin.site.register(EventQuestion)
admin.site.register(Event, EventAdmin)
#admin.site.register(EventOption)
#admin.site.register(Answer)
admin.site.register(Registration, RegistrationAdmin)
#admin.site.register(IdealIssuer)




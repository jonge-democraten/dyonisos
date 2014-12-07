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


import bleach
from django import forms
from django.db import transaction
from django.utils.safestring import mark_safe

from subscribe.models import Answer, IdealIssuer, Registration, AFDELINGEN


setattr(forms.fields.Field, 'is_checkbox', lambda self: isinstance(self.widget, forms.CheckboxInput))


class SubscribeForm(forms.Form):
    def __init__(self, event, *args, **kwargs):
        if len(args) and 'registration_preview' in args[0]:
            self.preview = True
        else:
            self.preview = False

        super(SubscribeForm, self).__init__(*args, **kwargs)

        self.event = event

        # Check the limits
        closed_options = []
        for limit in event.registrationlimit_set.all():
            if limit.is_reached():
                closed_options += [o.pk for o in limit.options.all()]

        # First the mandatory fields
        self.fields["first_name"] = forms.CharField(max_length=64, required=True, label="Voornaam")
        self.fields["last_name"] = forms.CharField(max_length=64, required=True, label="Achternaam")
        self.fields["email"] = forms.EmailField(required=True, label="Email")

        self._elements = []

        self._elements += [('field', 'first_name')]
        self._elements += [('field', 'last_name')]
        self._elements += [('field', 'email')]

        # The dynamic fields
        for question in event.eventquestion_set.order_by('order'):
            name = question.form_id()
            if question.question_type == "INT":
                self.fields[name] = forms.IntegerField(label=question.name, required=question.required)
                self._elements += [('field', name)]
            elif question.question_type == "TXT":
                self.fields[name] = forms.CharField(max_length=256, label=question.name, required=question.required)
                self._elements += [('field', name)]
            elif question.question_type == "AFD":
                if question.radio:
                    self.fields[name] = forms.CharField(max_length=256, label=question.name, required=question.required,
                                                    widget=forms.RadioSelect(choices=AFDELINGEN))
                else:
                    self.fields[name] = forms.CharField(max_length=256, label=question.name, required=question.required,
                                                    widget=forms.Select(choices=AFDELINGEN))
                self._elements += [('field', name)]
            elif question.question_type == "BOOL":
                options = question.options.all()
                if len(options) and options[0].price != 0:
                    if options[0].price < 0:
                        label = u"%s - \u20AC %.2f korting" % (question.name, float(-options[0].price) / 100)
                    else:
                        label = u"%s - \u20AC %.2f" % (question.name, float(options[0].price) / 100)
                else:
                    label = question.name
                self.fields[name] = forms.BooleanField(label=label, required=question.required)
                self._elements += [('field', name)]
            elif question.question_type == "CHOICE":
                if question.radio:
                    self.fields[name] = forms.ModelChoiceField(widget=forms.RadioSelect(), label=question.name, required=question.required, queryset=question.options.exclude(pk__in=closed_options).exclude(active=False).order_by('order'), empty_label=None)
                else:
                    self.fields[name] = forms.ModelChoiceField(label=question.name, required=question.required, queryset=question.options.exclude(pk__in=closed_options).exclude(active=False).order_by('order'), empty_label=None)
                self._elements += [('field', name)]
            elif question.question_type == "TEXT":
                allowed_tags = ['a', 'b', 'code', 'em', 'h3', 'i', 'img', 'strong', 'ul', 'ol', 'li', 'p', 'br']
                allowed_attrs = {
                    '*': ['class', 'style'],
                    'a': ['href', 'target'],
                    'img': ['src', 'alt'],
                }
                text = mark_safe(bleach.clean(question.text, tags=allowed_tags, attributes=allowed_attrs))
                self._elements += [('text', text)]

        self.fields["issuer"] = forms.ModelChoiceField(queryset=IdealIssuer.objects.all(), label="Bank (iDEAL)", required=False)

    def is_valid(self):
        res = super(SubscribeForm, self).is_valid()
        if not res:
            return False
        if self.preview:
            self.confirm_page()
            self.full_clean()
            res = super(SubscribeForm, self).is_valid()
        return res

    def confirm_page(self):
        self.preview = True

        for f in self.fields:
            self.fields[f].widget.attrs['readonly'] = True

        str = u'<table><tr><th>Omschrijving</th><th>Bedrag</th></tr>'
        price = self.event.price
        if price != 0:
            str += u'<tr><td>Standaard:</td><td>\u20AC {:.2f}</td></tr>'.format(float(price) / 100.)
        for question in self.event.eventquestion_set.order_by('order'):
            if question.question_type == 'CHOICE':
                option = self.cleaned_data[question.form_id()]
                if option is not None:
                    if option.price != 0:
                        price += option.price
                        str += u'<tr><td>{}</td><td>\u20AC {:.2f}</td></tr>'.format(option.name, float(option.price) / 100.)
            if question.question_type == 'BOOL':
                if self.cleaned_data[question.form_id()]:
                    option = list(question.options.all()[:1])
                    if option:
                        option = option[0]
                        if option.price != 0:
                            price += option.price
                            str += u'<tr><td>{}</td><td>\u20AC {:.2f}</td></tr>'.format(option.name, float(option.price) / 100.)
        str += u'<tr><td><strong>Totaal:</strong></td><td><strong>\u20AC {:.2f}</strong></td></tr>'.format(float(price) / 100.)
        str += u'</table>'
        self.price = price
        self.price_description = str

        if self.price > 0:
            self.fields['issuer'].required = True

    def visible_fields(self):
        fields = [f for f in self.fields if not f == 'issuer']
        fields = [self[f] for f in fields]
        return [field for field in fields if not field.is_hidden]

    def issuer_field(self):
        return self['issuer']

    def elements(self):
        res = []
        for element_type, element_value in self._elements:
            if element_type == "text":
                res += [(element_type, element_value)]
            elif element_type == "field":
                res += [(element_type, self[element_value])]
        return res


@transaction.atomic
def fill_subscription(form, event):
    reg = Registration(event=event)
    reg.first_name = form.cleaned_data["first_name"]
    reg.last_name = form.cleaned_data["last_name"]
    reg.email = form.cleaned_data["email"]
    reg.save()

    for question in event.eventquestion_set.all():
        if question.form_id() in form.cleaned_data:
            ans = Answer(registration=reg, question=question)
            ans.set_answer(form.cleaned_data[question.form_id()])
            ans.save()

    reg.calculate_price()
    reg.save()

    return reg

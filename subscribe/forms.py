# -*- coding: utf-8 -*-

# Copyright (c) 2011,2014 Floor Terra <floort@gmail.com>
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
from django.db.models import Q
from django.utils.encoding import force_text
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from subscribe.models import Answer, Registration, AFDELINGEN


setattr(forms.fields.Field, 'is_checkbox', lambda self: isinstance(self.widget, forms.CheckboxInput))


class RadioChoiceInputDisabled(forms.widgets.RadioChoiceInput):
    def __init__(self, *args, **kwargs):
        disabledset = kwargs.pop('disabledset', None)
        super(RadioChoiceInputDisabled, self).__init__(*args, **kwargs)
        self.disabledset = set([str(x.pk) for x in disabledset])
        if self.choice_value in self.disabledset:
            self.attrs['disabled'] = 'disabled'


class RadioFieldDisabledRenderer(forms.widgets.RadioFieldRenderer):
    def choice_input_class(self, *args, **kwargs):
        kwargs = dict(kwargs, disabledset=self.disabledset)
        return RadioChoiceInputDisabled(*args, **kwargs)


class RadioSelectDisabled(forms.widgets.RadioSelect):
    def renderer(self, *args, **kwargs):
        if getattr(self, 'disabledset', None) is not None:
            instance = RadioFieldDisabledRenderer(*args, **kwargs)
            instance.disabledset = self.disabledset
            return instance
        else:
            return super(RadioSelectDisabled, self).renderer(*args, **kwargs)


class SelectDisabled(forms.widgets.Select):
    def render_option(self, selected_choices, option_value, option_label):
        if option_value is None:
            option_value = ''
        option_value = force_text(option_value)
        if getattr(self, 'disabledset', None) is not None and getattr(self, 'disabledstr', None) is None:
            self.disabledstr = set([str(x.pk) for x in self.disabledset])
        if getattr(self, 'disabledstr', None) is not None and option_value in self.disabledstr:
            disabled_html = mark_safe(' disabled="disabled"')
        else:
            disabled_html = ''
        if option_value in selected_choices:
            selected_html = mark_safe(' selected="selected"')
            if not self.allow_multiple_selected:
                # Only allow for a single selection.
                selected_choices.remove(option_value)
        else:
            selected_html = ''
        return format_html('<option value="{0}"{1}{2}>{3}</option>',
                           option_value,
                           selected_html,
                           disabled_html,
                           force_text(option_label))


class SubscribeForm(forms.Form):
    def __init__(self, event, *args, **kwargs):
        if len(args) and 'registration_preview' in args[0]:
            self.preview = True
        else:
            self.preview = False

        kwargs['label_suffix'] = ''

        super(SubscribeForm, self).__init__(*args, **kwargs)

        self.event = event

        # Check the limits
        closed_options = []
        for question in event.eventquestion_set.all():
            for option in question.options.all():
                if option.is_full():
                    closed_options += [option.pk]

        self._elements = []
        inserted_default_fields = False

        # The dynamic fields
        for question in event.eventquestion_set.order_by('order'):
            if question.order >= 0 and not inserted_default_fields:
                self.fields["first_name"] = forms.CharField(max_length=64, required=True, label="Voornaam")
                self._elements += [('field', 'first_name')]
                self.fields["last_name"] = forms.CharField(max_length=64, required=True, label="Achternaam")
                self._elements += [('field', 'last_name')]
                self.fields["email"] = forms.EmailField(required=True, label="Email")
                self._elements += [('field', 'email')]
                inserted_default_fields = True
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
                active = True
                if len(options) and options[0].price != 0:
                    if options[0].price < 0:
                        label = "%s: \u20AC %.2f korting" % (question.name, float(-options[0].price) / 100)
                    else:
                        label = "%s: \u20AC %.2f" % (question.name, float(options[0].price) / 100)
                    if not options[0].active or options[0].is_full():
                        label += " (optie is vol)"
                        active = False
                else:
                    label = question.name
                self.fields[name] = forms.BooleanField(label=label, required=question.required)
                if not active:
                    self.fields[name].widget.attrs['disabled'] = 'disabled'
                self._elements += [('field', name)]
            elif question.question_type == "CHOICE":
                if question.radio:
                    self.fields[name] = forms.ModelChoiceField(widget=RadioSelectDisabled(), label=question.name, required=question.required, queryset=question.options.exclude(active=False).order_by('order'), empty_label=None)
                else:
                    self.fields[name] = forms.ModelChoiceField(widget=SelectDisabled(), label=question.name, required=question.required, queryset=question.options.exclude(active=False).order_by('order'), empty_label=None)
                self._elements += [('field', name)]
                self.fields[name].widget.disabledset = question.options.filter(Q(pk__in=closed_options) | Q(active=False))
            elif question.question_type == "TEXT":
                allowed_tags = ['a', 'b', 'code', 'em', 'h3', 'i', 'img', 'strong', 'ul', 'ol', 'li', 'p', 'br']
                allowed_attrs = {
                    '*': ['class', 'style'],
                    'a': ['href', 'target'],
                    'img': ['src', 'alt'],
                }
                text = mark_safe(bleach.clean(question.text, tags=allowed_tags, attributes=allowed_attrs))
                self._elements += [('text', text)]

        if not inserted_default_fields:
            self.fields["first_name"] = forms.CharField(max_length=64, required=True, label="Voornaam")
            self._elements += [('field', 'first_name')]
            self.fields["last_name"] = forms.CharField(max_length=64, required=True, label="Achternaam")
            self._elements += [('field', 'last_name')]
            self.fields["email"] = forms.EmailField(required=True, label="Email")
            self._elements += [('field', 'email')]

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

        str = '<table><tr><th>Omschrijving</th><th>Bedrag</th></tr>'
        price = self.event.price
        if price != 0:
            str += '<tr><td>Standaard:</td><td>\u20AC {:.2f}</td></tr>'.format(float(price) / 100.)
        for question in self.event.eventquestion_set.order_by('order'):
            if question.question_type == 'CHOICE':
                option = self.cleaned_data[question.form_id()]
                if option is not None:
                    if option.price != 0:
                        price += option.price
                        str += '<tr><td>{}</td><td>\u20AC {:.2f}</td></tr>'.format(option.name, float(option.price) / 100.)
            if question.question_type == 'BOOL':
                if self.cleaned_data[question.form_id()]:
                    option = list(question.options.all()[:1])
                    if option:
                        option = option[0]
                        if option.price != 0:
                            price += option.price
                            str += '<tr><td>{}</td><td>\u20AC {:.2f}</td></tr>'.format(option.name, float(option.price) / 100.)
        str += '<tr><td><strong>Totaal:</strong></td><td><strong>\u20AC {:.2f}</strong></td></tr>'.format(float(price) / 100.)
        str += '</table>'
        self.price = price
        self.price_description = str

    def visible_fields(self):
        fields = [self[f] for f in self.fields]
        return [field for field in fields if not field.is_hidden]

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

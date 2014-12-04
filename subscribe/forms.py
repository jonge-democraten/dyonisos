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


from django import forms

from subscribe.models import Answer, IdealIssuer, Registration, AFDELINGEN


class SubscribeForm(forms.Form):
    def __init__(self, event, *args, **kwargs):
        super(SubscribeForm, self).__init__(*args, **kwargs)

        # Check the limits
        closed_options = []
        for limit in event.registrationlimit_set.all():
            if limit.is_reached():
                closed_options += [o.pk for o in limit.options.all()]

        # First the mandatory fields
        self.fields["first_name"] = forms.CharField(max_length=64, required=True, label="Voornaam")
        self.fields["last_name"] = forms.CharField(max_length=64, required=True, label="Achternaam")
        self.fields["email"] = forms.EmailField(required=True, label="Email")

        # The dynamic fields
        for question in event.eventquestion_set.order_by('order'):
            name = question.form_id()
            if question.question_type == "INT":
                self.fields[name] = forms.IntegerField(label=question.name, required=question.required)
            elif question.question_type == "TXT":
                self.fields[name] = forms.CharField(max_length=256, label=question.name, required=question.required)
            elif question.question_type == "AFD":
                self.fields[name] = forms.CharField(max_length=256, label=question.name, required=question.required,
                                                    widget=forms.Select(choices=AFDELINGEN))
            elif question.question_type == "BOOL":
                options = question.options.all()
                if len(options) and options[0].price != 0:
                    label = u"%s - \u20AC %.2f" % (question.name, float(options[0].price) / 100)
                else:
                    label = question.name
                self.fields[name] = forms.BooleanField(label=label, required=question.required)
            elif question.question_type == "CHOICE":
                self.fields[name] = forms.ModelChoiceField(label=question.name, required=question.required, queryset=question.options.exclude(pk__in=closed_options).exclude(active=False))

        # Only show bank choice if at least one of the options costs money
        if not event.all_free():
            self.fields["issuer"] = forms.ModelChoiceField(queryset=IdealIssuer.objects.all(), label="Bank (iDEAL)")


def fill_subscription(form, event):
    reg = Registration(event=event)
    reg.first_name = form.cleaned_data["first_name"]
    reg.last_name = form.cleaned_data["last_name"]
    reg.email = form.cleaned_data["email"]
    reg.save()

    for question in event.eventquestion_set.all():
        ans = Answer(registration=reg, question=question)
        ans.set_answer(form.cleaned_data[question.form_id()])
        ans.save()

    return reg

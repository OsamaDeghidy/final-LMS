from django import forms
from django.utils import timezone
from .models import Meeting

class MeetingForm(forms.ModelForm):
    """Form for creating and updating meetings"""
    
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'meeting_type', 'start_time', 
                  'duration', 'zoom_link', 'materials']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الاجتماع'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف الاجتماع'}),
            'meeting_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدة بالدقائق'}),
            'zoom_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط اجتماع زووم'}),
            'materials': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def clean_start_time(self):
        """Validate that start_time is in the future"""
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time < timezone.now():
            raise forms.ValidationError("لا يمكن إنشاء اجتماع في الماضي")
        return start_time
    
    def clean(self):
        """Validate that zoom meetings have zoom links"""
        cleaned_data = super().clean()
        meeting_type = cleaned_data.get('meeting_type')
        zoom_link = cleaned_data.get('zoom_link')
        
        if meeting_type == 'ZOOM' and not zoom_link:
            self.add_error('zoom_link', "يجب إضافة رابط زووم للاجتماعات عن بعد")
        
        return cleaned_data


class MeetingFilterForm(forms.Form):
    """Form for filtering meetings"""
    MEETING_TYPE_CHOICES = [('', 'الكل')] + list(Meeting.MEETING_TYPES)
    PAST_CHOICES = [
        ('', 'الكل'),
        ('0', 'الاجتماعات القادمة'),
        ('1', 'الاجتماعات السابقة'),
    ]
    
    meeting_type = forms.ChoiceField(
        choices=MEETING_TYPE_CHOICES, 
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    start_date = forms.DateField(
        required=False, 
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    is_past = forms.ChoiceField(
        choices=PAST_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def clean_is_past(self):
        """Convert string to boolean"""
        is_past = self.cleaned_data.get('is_past')
        if is_past == '1':
            return True
        elif is_past == '0':
            return False
        return None

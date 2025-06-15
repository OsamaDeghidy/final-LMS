from django import forms
from django.utils import timezone
from .models import Meeting

class MeetingForm(forms.ModelForm):
    """Form for creating and updating meetings"""
    
    class Meta:
        model = Meeting
        fields = ['title', 'description', 'meeting_type', 'start_time', 
                  'duration', 'zoom_link', 'materials', 'max_participants',
                  'enable_screen_share', 'enable_chat', 'enable_recording']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'عنوان الاجتماع'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'وصف الاجتماع', 'rows': 4}),
            'meeting_type': forms.Select(attrs={'class': 'form-select'}),
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'المدة بالدقائق'}),
            'zoom_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'رابط اجتماع زووم'}),
            'materials': forms.FileInput(attrs={'class': 'form-control'}),
            'max_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': '2', 'max': '200', 'value': '50'}),
            'enable_screen_share': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_chat': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'enable_recording': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def clean_start_time(self):
        """Validate that start_time is in the future"""
        start_time = self.cleaned_data.get('start_time')
        if start_time and start_time < timezone.now():
            raise forms.ValidationError("لا يمكن إنشاء اجتماع في الماضي")
        return start_time
    
    def clean(self):
        """Validate meeting specific requirements"""
        cleaned_data = super().clean()
        meeting_type = cleaned_data.get('meeting_type')
        zoom_link = cleaned_data.get('zoom_link')
        max_participants = cleaned_data.get('max_participants')
        
        if meeting_type == 'ZOOM' and not zoom_link:
            self.add_error('zoom_link', "يجب إضافة رابط زووم للاجتماعات عن بعد")
        
        if meeting_type == 'LIVE' and max_participants and max_participants < 2:
            self.add_error('max_participants', "يجب أن يكون الحد الأقصى للمشاركين أكثر من 2")
            
        if meeting_type == 'LIVE' and max_participants and max_participants > 200:
            self.add_error('max_participants', "الحد الأقصى للمشاركين لا يمكن أن يتجاوز 200")
        
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

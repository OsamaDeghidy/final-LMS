from django import forms
from django.utils import timezone
from .models import Meeting
from django.contrib.auth.models import User
from django.contrib.auth.forms import PasswordChangeForm
from user.models import Profile

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


# Settings Forms
class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })
    
    old_password = forms.CharField(
        label="كلمة المرور الحالية",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور الحالية'
        })
    )
    
    new_password1 = forms.CharField(
        label="كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور الجديدة'
        })
    )
    
    new_password2 = forms.CharField(
        label="تأكيد كلمة المرور الجديدة",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'تأكيد كلمة المرور الجديدة'
        })
    )


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile"""
    
    class Meta:
        model = Profile
        fields = ['name', 'email', 'phone', 'image_profile', 'shortBio', 'detail', 
                  'github', 'youtube', 'twitter', 'facebook', 'instagram', 'linkedin']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'الاسم الكامل'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'البريد الإلكتروني'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'رقم الهاتف'
            }),
            'image_profile': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'shortBio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'نبذة قصيرة عنك',
                'rows': 3
            }),
            'detail': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'تفاصيل إضافية',
                'rows': 5
            }),
            'github': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://github.com/username'
            }),
            'youtube': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/channel'
            }),
            'twitter': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://twitter.com/username'
            }),
            'facebook': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://facebook.com/username'
            }),
            'instagram': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://instagram.com/username'
            }),
            'linkedin': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://linkedin.com/in/username'
            }),
        }
        labels = {
            'name': 'الاسم الكامل',
            'email': 'البريد الإلكتروني',
            'phone': 'رقم الهاتف',
            'image_profile': 'صورة الملف الشخصي',
            'shortBio': 'نبذة قصيرة',
            'detail': 'تفاصيل إضافية',
            'github': 'حساب GitHub',
            'youtube': 'قناة YouTube',
            'twitter': 'حساب Twitter',
            'facebook': 'حساب Facebook',
            'instagram': 'حساب Instagram',
            'linkedin': 'حساب LinkedIn',
        }


class CertificateTemplateForm(forms.Form):
    """Form for certificate template settings"""
    
    TEMPLATE_CHOICES = [
        ('modern', 'تصميم حديث'),
        ('classic', 'تصميم كلاسيكي'),
        ('elegant', 'تصميم أنيق'),
        ('professional', 'تصميم مهني'),
    ]
    
    COLOR_CHOICES = [
        ('#2a5a7c', 'أزرق'),
        ('#28a745', 'أخضر'),
        ('#dc3545', 'أحمر'),
        ('#ffc107', 'أصفر'),
        ('#6f42c1', 'بنفسجي'),
        ('#fd7e14', 'برتقالي'),
    ]
    
    template_style = forms.ChoiceField(
        choices=TEMPLATE_CHOICES,
        label="نمط الشهادة",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    primary_color = forms.ChoiceField(
        choices=COLOR_CHOICES,
        label="اللون الأساسي",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    institution_name = forms.CharField(
        max_length=255,
        label="اسم المؤسسة",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'أكاديمية التعلم الإلكتروني'
        })
    )
    
    institution_logo = forms.ImageField(
        required=False,
        label="شعار المؤسسة",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    signature_name = forms.CharField(
        max_length=255,
        label="اسم الموقع",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'د. أحمد محمد'
        })
    )
    
    signature_title = forms.CharField(
        max_length=255,
        label="منصب الموقع",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'مدير الأكاديمية'
        })
    )
    
    signature_image = forms.ImageField(
        required=False,
        label="صورة التوقيع",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        })
    )
    
    certificate_text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'هذا يشهد بأن {student_name} قد أكمل بنجاح دورة {course_name} بتاريخ {completion_date}'
        }),
        label="نص الشهادة",
        help_text="يمكنك استخدام المتغيرات: {student_name}, {course_name}, {completion_date}, {institution_name}"
    )
    
    include_qr_code = forms.BooleanField(
        required=False,
        label="إضافة رمز QR للتحقق",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_grade = forms.BooleanField(
        required=False,
        label="إضافة الدرجة في الشهادة",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

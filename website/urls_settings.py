from django.urls import path
from . import views_settings

urlpatterns = [
    # Main settings page
    path('settings/', views_settings.settings_view, name='settings'),
    
    # Password change
    path('settings/change-password/', views_settings.change_password, name='change_password'),
    
    # Profile update
    path('settings/update-profile/', views_settings.update_profile, name='update_profile'),
    
    # Certificate template management
    path('settings/save-certificate-template/', views_settings.save_certificate_template, name='save_certificate_template'),
    path('settings/template/<int:template_id>/default/', views_settings.set_default_template, name='set_default_template'),
    path('settings/template/<int:template_id>/delete/', views_settings.delete_template, name='delete_template'),
    path('settings/template/<int:template_id>/preview/', views_settings.preview_certificate, name='preview_certificate'),
    
    # User signature management
    path('settings/save-signature/', views_settings.save_user_signature, name='save_user_signature'),
    path('settings/signature/<int:signature_id>/delete/', views_settings.delete_signature, name='delete_signature'),
    
    # Preset template management
    path('settings/create-from-preset/', views_settings.create_template_from_preset, name='create_template_from_preset'),
    path('settings/browse-templates/', views_settings.browse_preset_templates, name='browse_preset_templates'),
] 
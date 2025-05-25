from django.http import HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from .models import Profile
from django.contrib import messages
from .models import Teacher, Student, Organization


def coursebase(request):
    return render(request, 'main/course_base.html')


# messages.error(request,'User not found')
# @login_required(login_url='login')

def loginUser(request):
    if request.user.is_authenticated:
        return redirect('index')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        if not email or not password:
            messages.error(request, 'الرجاء إدخال البريد الإلكتروني وكلمة المرور')
            return render(request, 'user/login.html')
        
        # First try to authenticate
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            # Authentication successful
            login(request, user)
            messages.success(request, 'تم تسجيل الدخول بنجاح')
            return redirect('index')
        else:
            # Check if user exists but password is wrong
            try:
                User.objects.get(username=email)
                messages.error(request, 'كلمة المرور غير صحيحة')
            except User.DoesNotExist:
                messages.error(request, 'لا يوجد حساب بهذا البريد الإلكتروني')
    
    return render(request, 'user/login.html')

def logoutUser(request):
    logout(request)
    return redirect('index')

def registerUser(request):
    page='signup'
    if (request.user.is_authenticated):
        return redirect('index')
    else:
        if request.method == 'POST':
            username = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            pwd = request.POST.get('password')
            cnfrm_pwd = request.POST.get('confirmpassword')
            try:
                if pwd == cnfrm_pwd:
                    profile=Profile.objects.filter(email=email)
                    user=User.objects.filter(email=email)

                    if not user.exists():
                        user=User.objects.create_user(username=email,email=email)
                        user.set_password(pwd)
                        profile=Profile.objects.create(user=user,name=username,email=email,phone=phone,status='Student')
                        student=Student.objects.create(profile=profile)
                        user.save()
                        profile.save()
                        student.save()
                        messages.success(request, 'Account created successfully. Please login.')
                        return redirect('login')
                    else:
                        return render(request, 'user/register.html',{"msg": "User already exists"})
                else:
                    return render(request, 'user/register.html',{ "msg":"Confirm Password is not equal to Password" }) 
                   
            except Exception as e:
                return HttpResponse(e)
        return render(request, 'user/register.html')



def update_profile(request):
    print(request.user)
    if request.user.is_authenticated:

        try:
            r_profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            raise ValueError("Profile does not exist for user")
        context = {
            'profile': r_profile
        }
        
        if request.method == 'POST':
            name = request.POST.get('name')
            image_profile = request.FILES.get('image_profile')
            shortBio = request.POST.get('shortBio')
            detail = request.POST.get('detail')
            github = request.POST.get('github')
            youtube = request.POST.get('youtube')
            twitter = request.POST.get('twitter')
            facebook = request.POST.get('facebook')
            instagram = request.POST.get('instagram')
            linkedin = request.POST.get('linkedin')
           
            

            try:
                r_profile = Profile.objects.get(user=request.user)
            except Profile.DoesNotExist:
                raise ValueError("Profile does not exist for user")
            r_profile.name=name    
            r_profile.image_profile=image_profile
            r_profile.shortBio=shortBio
            r_profile.github=github
            r_profile.youtube=youtube
            r_profile.twitter=twitter
            r_profile.facebook=facebook
            r_profile.instagram=instagram
            r_profile.linkedin=linkedin

            r_profile.save()
            if r_profile.status == "Student":
                date_of_birth = request.POST.get('date_of_birth')
                department = request.POST.get('department')
                student = Student.objects.filter(profile=r_profile).first()
                
                if not student:
                    student = Student(profile=r_profile)
                
                student.department = department if department else None
                if date_of_birth:  # Only set if date_of_birth is not empty
                    student.date_of_birth = date_of_birth
                student.save()
                return redirect('profile_detail', profile_id=r_profile.id)

            elif r_profile.status == "Teacher":
                date_of_birth = request.POST.get('date_of_birth')
                department = request.POST.get('department')
                qualification = request.POST.get('qualification')
                bio = request.POST.get('bio')
                research_interests = request.POST.get('research_interests')
                
                teacher = Teacher.objects.filter(profile=r_profile).first()
                if not teacher:
                    teacher = Teacher(profile=r_profile)
                
                teacher.department = department if department else None
                teacher.qualification = qualification if qualification else None
                teacher.bio = bio if bio else None
                teacher.research_interests = research_interests if research_interests else None
                
                if date_of_birth:  # Only set if date_of_birth is not empty
                    teacher.date_of_birth = date_of_birth
                teacher.save()
                return redirect('profile_detail', profile_id=r_profile.id)
            
            elif r_profile.status == "Organization":
                location = request.POST.get('location')
                website = request.POST.get('website')
                founded_year = request.POST.get('founded_year')
                employees = request.POST.get('employees')
                
                organization = Organization.objects.filter(profile=r_profile).first()
                if not organization:
                    organization = Organization(profile=r_profile)
                
                organization.location = location if location else None
                organization.website = website if website else None
                organization.employees = int(employees) if employees and employees.isdigit() else 0
                
                if founded_year:  # Only set if founded_year is not empty
                    organization.founded_year = founded_year
                organization.save()
                return redirect('profile_detail', profile_id=r_profile.id)
            else:
                return HttpResponse("Something went wrong")
        return render(request, 'user/update_profile.html', context)
    else:
        return redirect('index')
    

def profile_detail(request, profile_id):
    
    profile = get_object_or_404(Profile, id=profile_id)
    
    if profile.status == 'Organization':
        organization = get_object_or_404(Organization, profile=profile)
        context = {'organization': organization,'profile': profile}
    
    elif profile.status == 'Teacher':
        teacher = get_object_or_404(Teacher, profile=profile)
        context = {'teacher': teacher,'profile': profile}
    
    else:
        student = get_object_or_404(Student, profile=profile)
        context = {'student': student,'profile': profile}
    return render(request, 'user/user_details.html', context)    



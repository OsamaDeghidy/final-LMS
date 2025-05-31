<h1>A fully responsive Learning Management System with models for Organisation, Teacher and Student. </h1>

## 📊 Project Evaluation / تقييم المشروع

### **Overall Rating: 7.5/10** ⭐

This Learning Management System is a comprehensive educational platform built with Django that provides robust functionality for managing courses, students, teachers, and organizations. The project demonstrates strong architectural design and implementation of core LMS features.

## ✅ Completed Features / الميزات المكتملة

### 🎓 Course Management / إدارة الدورات
- ✅ Create, update, and delete courses
- ✅ Course categories and tags system
- ✅ Image and file uploads for courses
- ✅ Course pricing and ratings
- ✅ Course status management (draft, published, pending)
- ✅ Course modules and content organization
- ✅ PDF syllabus and materials support

### 👥 User Management / إدارة المستخدمين
- ✅ Student, Teacher, and Organization profiles
- ✅ Authentication and authorization system
- ✅ Role-based access control
- ✅ Profile pictures and social media links
- ✅ User progress tracking

### 📚 Educational Content / المحتوى التعليمي
- ✅ Video lectures with progress tracking
- ✅ Notes system for students
- ✅ Advanced quiz system with multiple question types
- ✅ Comments and discussions on videos
- ✅ Assignment management
- ✅ Attendance tracking
- ✅ Certificate generation

### 🛒 E-commerce Features / التجارة الإلكترونية
- ✅ Shopping cart system
- ✅ Course enrollment process
- ✅ Payment integration ready
- ✅ Course reviews and ratings

### 📈 Analytics & Progress / الإحصائيات والتتبع
- ✅ Student progress tracking
- ✅ Teacher dashboard with analytics
- ✅ Course completion certificates
- ✅ Activity monitoring

### 📱 Additional Features / ميزات إضافية
- ✅ Multilingual support (Arabic/English)
- ✅ Rich text editor (CKEditor)
- ✅ Meeting management system
- ✅ Book library system
- ✅ Article/Blog system

## ⚠️ Issues Found / المشاكل المكتشفة

### 🚨 Critical Security Issues / مشاكل أمنية حرجة
- ❌ **Hardcoded Secret Key**: Secret key is exposed in settings.py
- ❌ **Debug Mode in Production**: DEBUG=True should be False in production
- ❌ **No Host Restrictions**: ALLOWED_HOSTS is empty
- ❌ **Missing Environment Variables**: Sensitive data not using environment variables

### 🔧 Programming Issues / مشاكل برمجية
- ⚠️ **Debug Print Statements**: Multiple print() statements should use logging
- ⚠️ **Database Queries**: Some inefficient database queries could be optimized
- ⚠️ **Error Handling**: Some functions lack proper exception handling
- ⚠️ **Code Duplication**: Some repeated code blocks in views
- ⚠️ **Missing Validation**: Some forms lack proper input validation

### 📋 Minor Issues / مشاكل طفيفة
- ⚠️ **Documentation**: Some functions lack docstrings
- ⚠️ **Testing**: No automated tests found
- ⚠️ **Static Files**: Could benefit from CDN for better performance

## 🚀 Development Suggestions / اقتراحات التطوير

### 🛡️ Security Improvements / تحسينات الأمان
1. **Environment Variables**: Use .env file for sensitive configurations
2. **HTTPS**: Implement SSL/TLS certificates
3. **Input Validation**: Add comprehensive form validation
4. **SQL Injection Prevention**: Use parameterized queries
5. **CSRF Protection**: Ensure all forms have CSRF tokens

### 🏗️ Technical Enhancements / تحسينات تقنية
1. **API Development**: Add REST API using Django REST Framework
2. **Caching**: Implement Redis/Memcached for better performance
3. **Database**: Migrate from SQLite to PostgreSQL for production
4. **Search**: Add Elasticsearch for advanced search capabilities
5. **File Storage**: Implement AWS S3 or similar cloud storage

### 📱 New Features / ميزات جديدة
1. **Mobile Apps**: Develop Android and iOS applications
2. **Live Streaming**: Add real-time video conferencing
3. **AI Integration**: Implement AI for personalized recommendations
4. **Offline Mode**: Allow offline content consumption
5. **Advanced Analytics**: Add detailed reporting and insights

### 🎨 UI/UX Improvements / تحسينات واجهة المستخدم
1. **Modern Design**: Implement Material Design or similar
2. **Responsive Design**: Ensure mobile-first approach
3. **Accessibility**: Add support for users with disabilities
4. **Dark Mode**: Implement theme switching
5. **Animations**: Add smooth transitions and micro-interactions

### 💼 Business Features / ميزات تجارية
1. **Payment Gateways**: Multiple payment options
2. **Subscription Model**: Monthly/yearly subscriptions
3. **Affiliate Program**: Referral system for users
4. **Bulk Enrollment**: Corporate training packages
5. **White Labeling**: Custom branding options

## 📅 Development Roadmap / خريطة التطوير

### Phase 1 (Month 1) / المرحلة الأولى
- [ ] Fix all security issues
- [ ] Implement proper logging
- [ ] Add comprehensive error handling
- [ ] Create automated tests
- [ ] Improve documentation

### Phase 2 (Months 2-3) / المرحلة الثانية
- [ ] Develop REST API
- [ ] Implement caching system
- [ ] Add advanced search functionality
- [ ] Improve database performance
- [ ] Enhance UI/UX design

### Phase 3 (Months 4-6) / المرحلة الثالثة
- [ ] Mobile application development
- [ ] AI-powered features
- [ ] Advanced analytics dashboard
- [ ] Live streaming capabilities
- [ ] Multi-tenant architecture

## 🔧 Quick Fixes / إصلاحات سريعة

### Immediate Actions Required:
1. **Create .env file** with proper environment variables
2. **Set DEBUG=False** for production
3. **Configure ALLOWED_HOSTS** properly
4. **Replace print statements** with proper logging
5. **Add form validation** to user inputs

## Description

The project is a web application built using Django, a high-level Python web framework. It provides a comprehensive platform for managing user profiles, organizations, teachers, students, courses, and related entities. The application facilitates collaboration, learning, and progress tracking in an educational setting.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Users Functionality](#users)
- [Technologies](#technologies)
- [Contributing](#contributing)
- [Screenshots](#screenshots)

## Features

- User registration and login system.
- Creation and management of user profiles with personal information and social media links.
- Creation and management of organizations with descriptions, locations, websites, and founding years.
- Creation and management of teachers with associated profiles, organizations, qualifications, and research interests.
- Creation and management of students with associated profiles and departments.
- Categorization of courses using tags.
- Creation and management of courses with associated organizations, teachers, tags, descriptions, and course content.
- Enrollment of students in courses.
- Creation and management of modules within courses with associated videos and notes.
- Uploading and management of videos with associated modules and courses.
- Commenting and sub-commenting on videos and courses.
- Creation and management of notes on videos, modules, and courses.
- Tracking user progress in courses and overall course progress.
- Creation and management of quizzes associated with videos.
- Creation and management of quiz questions and answers.
- Monitoring user quiz attempts.

## Installation

We need to Download a number of libraries and also create an environment before running the site.

Step 1: Create an environment outside the PilotLMS folder to keep the settings local to this project, Then activate it.. reference below
> > https://docs.python.org/3/library/venv.html

Step 2: Create the Folder and clone the project, now Change directory into FOLDER_NAME
> > git clone (https://github.com/ayushsaxenagithub/PilotLMS.git)
> > cd FOLDER_NAME

Step 3: Install the requirements for the project using the command...
> > pip install -r requirements.txt

Step 4: To activate the server 
> > python manage.py migrate

Step 4: To collectstatic files
> > python manage.py collectstaicfiles

Step 6: To activate the server 
> > python manage.py runserver


Step 7 : Open your web browser and visit http://localhost:8000 to access the application.

## Usage
<ul>
  <li>Register a new user account or log in with an existing account.</li>
  <li>Create a profile and fill in the necessary details.</li>
  <li>Create organizations and add descriptions, locations, websites, and founding years.</li>
  <li>Add teachers and students, linking them to their respective profiles and organizations.</li>
  <li>Categorize courses using tags.</li>
  <li>Create courses, specifying the associated organization, teacher, tags, descriptions, and course content.</li>
  <li>Enroll students in courses.</li>
  <li>Create modules within courses and add videos and notes.</li>
  <li>Upload videos, specifying the associated module and course.</li>
  <li>Interact with videos and courses by leaving comments and sub-comments.</li>
  <li>Create notes on videos, modules, and courses.</li>
  <li>Track user progress in courses and monitor overall course progress.</li>
  <li>Create quizzes associated with videos and add questions and answers.</li>
  <li>Monitor user attempts and quiz results.</li>
</ul>



<br>

## Users Functionality

<h3>Student</h3>
<ul>
<li> Login/Signup using tokens and cookies</li>
<li> Dashboard to view courses and their progress</li>
<li> Quiz popups within videos</li>
<li> Doubt section</li>
<li> Personal Notes</li>
</ul>

<h3>Teacher</h3>
<ul>
<li> Teacher Dashboard for administering student progress and analytics</li>
<li> Teacher domain within his Organization</li>
<li> Setup quizes for students</li>
</ul>
<h3>organization</h3>


<ul>
<li> Has the power to appoint a user as an instructor</li>
<li> Has a domain specific to itself only accesible to its teachers</li>
<li> Every teacher should belong to an onganisation</li>
</ul>

## Technologies
<p>The project is built using the following technologies:</p>
<ul>
  <li>Python</li>
  <li>Django - Web framework</li>
  <li>Django REST Framework - Web API framework</li>
  <li>SQLite - Database</li>
</ul>
<p>Front-end:</p>
<ul>
  <li>HTML</li>
  <li>CSS</li>
  <li>JavaScript</li>
</ul>
<p>Authentication:</p>
<ul>
  <li>Django Authentication - User authentication and authorization</li>
</ul>
<p>File Storage:</p>
<ul>
  <li>Amazon S3 (or any other storage service)</li>
</ul>

## Contributing
Contributions are welcome! If you find any issues or have suggestions for improvements, please feel free to create a pull request.

<h2>Screenshots</h2>

![IMG-20230501-WA0016](https://user-images.githubusercontent.com/84840415/235439314-5e89c455-bf77-4fc1-a65f-7696db537d47.jpg)
![IMG-20230501-WA0010](https://user-images.githubusercontent.com/84840415/235439315-5479c46a-d783-4574-bcd8-a33729ff3164.jpg)
![IMG-20230501-WA0012](https://user-images.githubusercontent.com/84840415/235439322-0d3a80b9-de96-40af-b752-7defdaba308a.jpg)
![IMG-20230501-WA0013](https://user-images.githubusercontent.com/84840415/235439325-7ca92fa6-f17e-4dcd-a1bd-b93e18cf3280.jpg)
![IMG-20230501-WA0015](https://user-images.githubusercontent.com/84840415/235439328-b27fe4b3-061a-408b-bdcd-d5a96cc9304f.jpg)





### Backend Setup
1. Create a virtual environment:
   ```bash
   cd server
   python -m venv venv
    venv\Scripts\activate
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install django-ckeditor
pip install pyyaml ua-parser user-agents
pip install django-axes
pip install django-silk
pip install django-menu-generator
pip install moviepy
pip install cryptography
pip install django-user-agents

pip uninstall django django-debug-toolbar
pip install django-debug-toolbar==4.2.0

   ```
3. Apply migrations:
   ```bash
   python manage.py migrate
   ```
4. Create a superuser:
   ```bash
   python manage.py createsuperuser
   ```
5. Run the development server:
   ```bash
   python manage.py runserver

   ```





…or create a new repository on the command line
echo "# final-LMS" >> README.md
git init
git add README.md
git commit -m "first commit"
git branch -M master
git remote add origin https://github.com/OsamaDeghidy/final-LMS.git
git push -u origin master
…or push an existing repository from the command line
git remote add origin https://github.com/OsamaDeghidy/final-LMS.git
git branch -M master
git push -u origin main



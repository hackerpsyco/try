# CLAS Platform - Complete User Guide

## 📚 Table of Contents
1. [Platform Overview](#platform-overview)
2. [Login & Authentication](#login--authentication)
3. [Admin User Guide](#admin-user-guide)
4. [Facilitator User Guide](#facilitator-user-guide)
5. [Common Features](#common-features)
6. [Troubleshooting](#troubleshooting)

---

## 🎯 Platform Overview

**CLAS (Classroom Learning and Assessment System)** is an educational management platform designed for schools, administrators, and facilitators to manage:
- Schools and Classes
- Students and Enrollment
- Session Planning and Curriculum
- Attendance Tracking
- Performance Reports

### User Roles
- **Admin**: Full system access - manages schools, users, curriculum
- **Facilitator**: Class-level access - manages students, sessions, attendance
- **Supervisor**: Oversight access - views reports and analytics

---

## 🔐 Login & Authentication

### How to Login
1. Go to the platform URL
2. Enter your **email** and **password**
3. Click **Login**
4. You'll be redirected to your role-specific dashboard

### First Time Login
- Contact your administrator for login credentials
- Default password should be changed on first login

---

## 👨‍💼 Admin User Guide

### Admin Dashboard Overview
When you login as Admin, you see:
- **System Statistics**: Schools, Facilitators, Students, Sessions
- **Quick Actions**: Create users, add schools, manage curriculum
- **Recent Activity**: Latest system activities
- **Performance Metrics**: Overall system health

### Admin Sidebar Navigation

#### 🏠 Dashboard
- **What it does**: Shows system overview and statistics
- **When to use**: Daily monitoring of platform health
- **Key metrics**: Active schools, facilitators, pending validations

#### 👥 Users
- **What it does**: Manage all platform users (Admin, Facilitator, Supervisor)
- **Key actions**:
  - **Add User**: Create new user accounts
  - **Edit User**: Modify user details and roles
  - **Delete User**: Remove user access
  - **View Users**: List all users with filters

**How to Add a User:**
1. Click **Users** in sidebar
2. Click **Add User** button
3. Fill in: Full Name, Email, Password, Role
4. Click **Create User**

#### 🏫 Schools
- **What it does**: Manage all schools in the system
- **Key actions**:
  - **Add School**: Register new schools
  - **Edit School**: Update school information
  - **View School Details**: See classes, students, facilitators
  - **Delete School**: Remove school (careful!)

**How to Add a School:**
1. Click **Schools** in sidebar
2. Click **Add School** button
3. Fill in: Name, UDISE Code, Block, District, Address
4. Click **Save**

**School Detail Page Shows:**
- School information
- All classes in the school
- Assigned facilitators
- Student enrollment numbers

#### ✅ Attendance
- **What it does**: View attendance reports across all schools
- **Filters available**:
  - School selection
  - Class selection
  - Date range
  - Student filters

#### 📅 Sessions
- **What it does**: Monitor all class sessions across the platform
- **Key features**:
  - Session status (Pending, Conducted, Cancelled, Holiday)
  - Filter by school, class, date
  - Session details and attendance
  - Performance analytics

#### 📖 Curriculum Sessions
- **What it does**: Manage curriculum content and session templates
- **Key actions**:
  - **Create Curriculum**: Add new curriculum content
  - **Edit Content**: Modify existing curriculum
  - **Preview**: View how content appears to facilitators
  - **Delete**: Remove outdated content

**Curriculum Management Flow:**
1. Click **Curriculum Sessions**
2. Click **Create New** 
3. Select: Day Number, Language (English/Hindi), Title
4. Add content using rich text editor
5. Preview before publishing
6. Save and activate

#### 📊 Reports
- **What it does**: Generate comprehensive reports
- **Available reports**:
  - School performance
  - Facilitator activity
  - Student attendance trends
  - Session completion rates
  - Curriculum usage analytics

### Admin Workflow Examples

#### Setting Up a New School
1. **Add School**: Schools → Add School → Fill details
2. **Create Classes**: School Detail → Add Class → Select level/section
3. **Assign Facilitator**: School Detail → Assign Facilitator
4. **Add Students**: School Detail → Students → Add/Import Students
5. **Initialize Sessions**: Classes → Initialize Sessions (creates 150 planned sessions)

#### Managing Users
1. **Create Facilitator**: Users → Add User → Role: Facilitator
2. **Assign to School**: Schools → School Detail → Assign Facilitator
3. **Monitor Activity**: Dashboard → Recent Activity

---

## 👨‍🏫 Facilitator User Guide

### Facilitator Dashboard Overview
When you login as Facilitator, you see:
- **Your Statistics**: Schools, Classes, Students assigned to you
- **Performance Metrics**: Session completion, attendance rates
- **Class Performance**: Individual class attendance stats
- **Quick Actions**: Add students, view classes
- **Recent Activity**: Your recent sessions and students

### Facilitator Sidebar Navigation

#### 🏠 Dashboard
- **What it does**: Shows your personal teaching statistics
- **Key metrics**: 
  - Schools assigned to you
  - Total classes you manage
  - Total students under your care
  - Sessions you've conducted

#### 🎓 My Classes
- **What it does**: Shows all schools assigned to you
- **Navigation flow**: My Classes → School List → View Classes → Class Detail
- **What you see**: School cards with student/class counts

**How to Access Classes:**
1. Click **My Classes** in sidebar
2. See list of schools assigned to you
3. Click **View Classes** on any school card
4. See all classes in that school with details

#### 🏫 My Schools
- **What it does**: Same as "My Classes" - shows your assigned schools
- **Purpose**: Alternative navigation to school list

#### 👥 Students
- **What it does**: Manage students across all your classes
- **Key actions**:
  - **View All Students**: See students from all your classes
  - **Add Student**: Enroll new students
  - **Edit Student**: Update student information
  - **Filter by School/Class**: Find specific students

**How to Add a Student:**
1. Click **Students** in sidebar
2. Click **Add Student** button
3. Fill in: Name, Enrollment Number, Gender
4. Select: School and Class
5. Set start date
6. Click **Save**

#### 📅 Today's Sessions
- **What it does**: Shows classes you need to conduct today
- **Key features**:
  - List of all your classes
  - Session status for each class
  - Quick access to start sessions
  - Curriculum navigation

**Session Management Flow:**
1. Click **Today's Sessions**
2. See list of your classes
3. Click **Start Session** for any class
4. Choose session type:
   - **Conduct Session**: Regular teaching
   - **Mark Holiday**: School holiday
   - **Cancel Session**: Session cancelled
5. For conducted sessions: Mark attendance
6. Complete session workflow

#### ✅ Attendance
- **What it does**: View and manage attendance records
- **Filters available**:
  - Your schools only
  - Your classes only
  - Date range selection
  - Individual student records

### Facilitator Workflow Examples

#### Daily Teaching Routine
1. **Check Dashboard**: See today's overview
2. **Today's Sessions**: View classes to conduct
3. **Start Session**: Click on class → Start Session
4. **Choose Session Type**: Conduct/Holiday/Cancel
5. **Mark Attendance**: Select present/absent students
6. **Complete Session**: Finish and save

#### Managing Students
1. **View Students**: Students → See all your students
2. **Add New Student**: Students → Add Student → Fill details
3. **Edit Student Info**: Find student → Edit → Update details
4. **Check Attendance**: Students → View individual attendance

#### Accessing Curriculum
1. **Go to Class**: Today's Sessions → Select Class
2. **View Curriculum**: Click **Curriculum** button
3. **Navigate Days**: Use day selector (1-150)
4. **Switch Language**: Toggle English/Hindi
5. **Use Content**: View lesson plans and materials

---

## 🔧 Common Features

### Curriculum Navigator
**Available to**: Admin (management), Facilitator (teaching)

**Features:**
- **Day Selection**: Navigate between Day 1-150
- **Language Toggle**: Switch between English and Hindi content
- **Content Display**: Rich text with images, videos, activities
- **Performance Optimized**: Loads one day at a time
- **Cache Management**: Stores recent days for quick access

**How to Use:**
1. Access via class detail page or curriculum section
2. Select day number (1-150)
3. Choose language (English/Hindi)
4. View lesson content
5. Use navigation buttons (Previous/Next)

### Session Management
**Session Types:**
- **Conducted**: Normal teaching session with attendance
- **Holiday**: School holiday (no teaching)
- **Cancelled**: Session cancelled due to circumstances

**Session Workflow:**
1. **Plan**: Sessions are pre-planned (150 days per class)
2. **Conduct**: Facilitator starts and conducts session
3. **Attendance**: Mark student attendance
4. **Complete**: Finish and save session data
5. **Report**: Data flows to admin reports

### Attendance System
**Features:**
- **Real-time marking**: Mark attendance during sessions
- **Bulk operations**: Mark all present/absent quickly
- **Historical data**: View past attendance records
- **Reports**: Generate attendance reports
- **Analytics**: Attendance rate calculations

### User Management (Admin Only)
**User Creation Process:**
1. **Basic Info**: Name, email, password
2. **Role Assignment**: Admin/Facilitator/Supervisor
3. **School Assignment**: Assign facilitators to schools
4. **Access Control**: Role-based permissions
5. **Activity Monitoring**: Track user activities

---

## 🚨 Troubleshooting

### Common Issues & Solutions

#### Login Problems
**Issue**: Can't login
**Solutions**:
- Check email and password spelling
- Contact admin for password reset
- Ensure you have the correct role assigned

#### Performance Issues
**Issue**: Page loads slowly
**Solutions**:
- Clear browser cache
- Check internet connection
- Contact admin if problem persists

#### Curriculum Not Loading
**Issue**: Curriculum content doesn't appear
**Solutions**:
- Try refreshing the page
- Clear cache using the cache button
- Switch between languages
- Contact admin if content is missing

#### Session Problems
**Issue**: Can't start or complete sessions
**Solutions**:
- Check if you're assigned to the class
- Ensure session hasn't already been conducted
- Contact admin for permission issues

#### Student Management Issues
**Issue**: Can't add or edit students
**Solutions**:
- Check if you have access to the school/class
- Verify student enrollment number is unique
- Ensure all required fields are filled

### Getting Help
1. **Check this guide first**
2. **Contact your administrator**
3. **Report technical issues** with:
   - What you were trying to do
   - Error message (if any)
   - Browser and device information

### Best Practices
1. **Regular backups**: Admin should backup data regularly
2. **Update information**: Keep student and school data current
3. **Monitor performance**: Check dashboard metrics regularly
4. **Train users**: Ensure all users understand their roles
5. **Security**: Change default passwords, use strong passwords

---

## 📞 Support & Contact

For technical support or questions about using the platform:
1. Contact your system administrator
2. Refer to this user guide
3. Check the platform's help section

**Remember**: This platform is designed to make education management easier. Take time to explore the features and don't hesitate to ask for help when needed!

---

*Last Updated: January 2025*
*Version: 1.0*
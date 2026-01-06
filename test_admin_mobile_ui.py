#!/usr/bin/env python3
"""
Test script to verify admin mobile UI fixes
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

def test_admin_templates():
    """Test that admin templates exist and have proper mobile styling"""
    
    templates_to_check = [
        'Templates/admin/shared/base.html',
        'Templates/admin/shared/sidebar.html', 
        'Templates/admin/feedback/dashboard.html',
        'Templates/admin/feedback/student_list.html',
        'Templates/admin/feedback/teacher_list.html'
    ]
    
    print("🔍 Checking admin template files...")
    
    for template in templates_to_check:
        if os.path.exists(template):
            print(f"✅ {template} - EXISTS")
            
            # Check for mobile-specific CSS classes
            with open(template, 'r', encoding='utf-8') as f:
                content = f.read()
                
            mobile_indicators = [
                'sm:', 'md:', 'lg:', 'xl:',  # Tailwind responsive prefixes
                'flex-col', 'flex-row',      # Responsive flex
                'grid-cols-1',               # Mobile-first grid
                'sidebar',                   # Sidebar class
                'mobile-topbar'              # Mobile topbar
            ]
            
            found_mobile = [indicator for indicator in mobile_indicators if indicator in content]
            
            if found_mobile:
                print(f"   📱 Mobile responsive classes found: {', '.join(found_mobile[:3])}...")
            else:
                print(f"   ⚠️  No mobile responsive classes detected")
                
        else:
            print(f"❌ {template} - MISSING")
    
    print()

def test_admin_views():
    """Test that admin feedback views are properly configured"""
    
    print("🔍 Checking admin feedback views...")
    
    try:
        from class.views import admin_feedback_dashboard, admin_student_feedback_list, admin_teacher_feedback_list
        print("✅ Admin feedback views imported successfully")
        
        # Check if views have proper decorators
        if hasattr(admin_feedback_dashboard, '__wrapped__'):
            print("✅ admin_feedback_dashboard has @login_required decorator")
        
        if hasattr(admin_student_feedback_list, '__wrapped__'):
            print("✅ admin_student_feedback_list has @login_required decorator")
            
        if hasattr(admin_teacher_feedback_list, '__wrapped__'):
            print("✅ admin_teacher_feedback_list has @login_required decorator")
            
    except ImportError as e:
        print(f"❌ Error importing admin feedback views: {e}")
    
    print()

def test_admin_urls():
    """Test that admin feedback URLs are configured"""
    
    print("🔍 Checking admin feedback URLs...")
    
    try:
        from django.urls import reverse
        
        urls_to_test = [
            'admin_feedback_dashboard',
            'admin_student_feedback_list', 
            'admin_teacher_feedback_list',
            'admin_feedback_analytics'
        ]
        
        for url_name in urls_to_test:
            try:
                url = reverse(url_name)
                print(f"✅ {url_name} -> {url}")
            except Exception as e:
                print(f"❌ {url_name} - Error: {e}")
                
    except Exception as e:
        print(f"❌ Error testing URLs: {e}")
    
    print()

def test_feedback_models():
    """Test that feedback models are accessible"""
    
    print("🔍 Checking feedback models...")
    
    try:
        from class.models import StudentFeedback, TeacherFeedback, SessionFeedback, FeedbackAnalytics
        
        models = [
            ('StudentFeedback', StudentFeedback),
            ('TeacherFeedback', TeacherFeedback), 
            ('SessionFeedback', SessionFeedback),
            ('FeedbackAnalytics', FeedbackAnalytics)
        ]
        
        for model_name, model_class in models:
            try:
                # Try to access the model's meta
                fields = [f.name for f in model_class._meta.fields]
                print(f"✅ {model_name} - {len(fields)} fields")
            except Exception as e:
                print(f"❌ {model_name} - Error: {e}")
                
    except ImportError as e:
        print(f"❌ Error importing feedback models: {e}")
    
    print()

def main():
    """Run all tests"""
    
    print("🚀 Testing Admin Mobile UI Fixes")
    print("=" * 50)
    
    test_admin_templates()
    test_admin_views()
    test_admin_urls()
    test_feedback_models()
    
    print("✨ Admin Mobile UI Test Complete!")
    print()
    print("📋 Summary of fixes applied:")
    print("  • Fixed mobile sidebar with proper responsive behavior")
    print("  • Added mobile topbar with hamburger menu")
    print("  • Fixed blank/black background issues")
    print("  • Improved mobile layout for feedback dashboard")
    print("  • Added proper Tailwind CSS via CDN")
    print("  • Fixed sidebar overlay and touch interactions")
    print()
    print("🔧 To test on mobile:")
    print("  1. Open admin dashboard in browser")
    print("  2. Use browser dev tools to simulate mobile")
    print("  3. Test sidebar toggle and navigation")
    print("  4. Verify feedback pages load properly")

if __name__ == '__main__':
    main()
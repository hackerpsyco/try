# CLAS Application - Complete Dependencies Mapping

## All Dependencies with File Names and Locations

This document provides a complete mapping of all dependencies used in the CLAS application, including package names, versions, and where they are used in the codebase.

---

## 1. CORE DEPENDENCIES

### Django
- **Package Name**: `Django`
- **Version**: `>=5.1,<5.2`
- **PyPI**: https://pypi.org/project/Django/
- **Files Used In**:
  - `CLAS/settings.py` - Main configuration
  - `CLAS/urls.py` - URL routing
  - `CLAS/wsgi.py` - WSGI application
  - `class/views.py` - View functions
  - `class/models/` - All model files
  - `class/forms.py` - Form definitions
  - `class/admin.py` - Admin interface
  - `Templates/` - All template files
- **Purpose**: Core web framework for the entire application

### psycopg2-binary
- **Package Name**: `psycopg2-binary`
- **Version**: `>=2.9.9`
- **PyPI**: https://pypi.org/project/psycopg2-binary/
- **Files Used In**:
  - `CLAS/settings.py` - DATABASE configuration
  - Database connection throughout the app
- **Purpose**: PostgreSQL database adapter for Python

### python-dotenv
- **Package Name**: `python-dotenv`
- **Version**: `>=1.0.1`
- **PyPI**: https://pypi.org/project/python-dotenv/
- **Files Used In**:
  - Application startup (loads .env file)
  - Environment variable management
- **Purpose**: Load environment variables from .env file

### django-environ
- **Package Name**: `django-environ`
- **Version**: `>=0.10.0`
- **PyPI**: https://pypi.org/project/django-environ/
- **Files Used In**:
  - `CLAS/settings.py` - Environment variable access
- **Purpose**: Type-safe environment variable handling for Django

---

## 2. PRODUCTION & DEPLOYMENT

### gunicorn
- **Package Name**: `gunicorn`
- **Version**: `>=22.0.0`
- **PyPI**: https://pypi.org/project/gunicorn/
- **Files Used In**:
  - Deployment configuration (Render, Heroku)
  - `Procfile` (if using Heroku)
- **Purpose**: Production WSGI HTTP server

### whitenoise
- **Package Name**: `whitenoise`
- **Version**: `>=6.7.0`
- **PyPI**: https://pypi.org/project/whitenoise/
- **Files Used In**:
  - `CLAS/settings.py` - MIDDLEWARE, STATICFILES_STORAGE
  - `CLAS/wsgi.py` - WSGI application
- **Purpose**: Serve static files efficiently in production

---

## 3. FRONTEND & UI

### Pillow
- **Package Name**: `Pillow`
- **Version**: `>=10.3.0`
- **PyPI**: https://pypi.org/project/Pillow/
- **Files Used In**:
  - `class/models/students.py` - ImageField for uploads
  - Image processing utilities
- **Purpose**: Image processing for file uploads and manipulation

### django-tailwind
- **Package Name**: `django-tailwind`
- **Version**: `>=3.6.2`
- **PyPI**: https://pypi.org/project/django-tailwind/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, TAILWIND_APP_NAME
  - `theme/` - Tailwind configuration
  - `Templates/` - All HTML templates
- **Purpose**: Tailwind CSS integration with Django

### django-browser-reload
- **Package Name**: `django-browser-reload`
- **Version**: `>=1.2.4`
- **PyPI**: https://pypi.org/project/django-browser-reload/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, MIDDLEWARE
  - Development only
- **Purpose**: Auto-reload browser during development

### django-widget-tweaks
- **Package Name**: `django-widget-tweaks`
- **Version**: `>=1.4.12`
- **PyPI**: https://pypi.org/project/django-widget-tweaks/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS
  - `Templates/` - Form rendering templates
- **Purpose**: Template filters for customizing form widgets

### beautifulsoup4
- **Package Name**: `beautifulsoup4`
- **Version**: `>=4.12.0`
- **PyPI**: https://pypi.org/project/beautifulsoup4/
- **Files Used In**:
  - Content optimization utilities
  - HTML parsing and manipulation
- **Purpose**: HTML parsing and optimization

---

## 4. DATA HANDLING & EXPORT

### openpyxl
- **Package Name**: `openpyxl`
- **Version**: `>=3.1.2`
- **PyPI**: https://pypi.org/project/openpyxl/
- **Files Used In**:
  - `class/views.py` - student_import function
  - Excel file processing
- **Purpose**: Read/write Excel files for student imports

### pandas
- **Package Name**: `pandas`
- **Version**: `>=2.0.0`
- **PyPI**: https://pypi.org/project/pandas/
- **Files Used In**:
  - `class/reports_views.py` - Report generation
  - Data analysis and manipulation
- **Purpose**: Data analysis and report generation

### reportlab
- **Package Name**: `reportlab`
- **Version**: `>=4.0.0`
- **PyPI**: https://pypi.org/project/reportlab/
- **Files Used In**:
  - Report generation views
  - PDF creation utilities
- **Purpose**: PDF generation for reports and documents

---

## 5. CACHING & PERFORMANCE

### psutil
- **Package Name**: `psutil`
- **Version**: `>=5.9.0`
- **PyPI**: https://pypi.org/project/psutil/
- **Files Used In**:
  - `class/performance_middleware.py` - System monitoring
  - Performance tracking
- **Purpose**: System and process monitoring

### redis
- **Package Name**: `redis`
- **Version**: `>=4.6.0`
- **PyPI**: https://pypi.org/project/redis/
- **Files Used In**:
  - `CLAS/settings.py` - CACHES configuration (optional)
  - Redis connection management
- **Purpose**: In-memory data store for caching

### django-redis
- **Package Name**: `django-redis`
- **Version**: `>=5.3.0`
- **PyPI**: https://pypi.org/project/django-redis/
- **Files Used In**:
  - `CLAS/settings.py` - CACHES configuration
- **Purpose**: Django cache backend using Redis

### django-cachalot
- **Package Name**: `django-cachalot`
- **Version**: `>=2.6.1`
- **PyPI**: https://pypi.org/project/django-cachalot/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS
  - Automatic ORM query caching
- **Purpose**: Automatic caching of database queries

### django-compressor
- **Package Name**: `django-compressor`
- **Version**: `>=4.4`
- **PyPI**: https://pypi.org/project/django-compressor/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, compression settings
  - Static file compression
- **Purpose**: Compress CSS and JavaScript files

### django-pipeline
- **Package Name**: `django-pipeline`
- **Version**: `>=3.0.0`
- **PyPI**: https://pypi.org/project/django-pipeline/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, asset pipeline
  - Static file optimization
- **Purpose**: Asset pipeline for CSS/JS optimization

### django-htmlmin
- **Package Name**: `django-htmlmin`
- **Version**: `>=0.11.0`
- **PyPI**: https://pypi.org/project/django-htmlmin/
- **Files Used In**:
  - `CLAS/settings.py` - HTML minification settings
  - Template rendering
- **Purpose**: HTML minification for smaller page sizes

---

## 6. API & REST FRAMEWORK (Optional)

### django-ninja
- **Package Name**: `django-ninja`
- **Version**: `>=1.4.0`
- **PyPI**: https://pypi.org/project/django-ninja/
- **Files Used In**:
  - Currently not used, available for future REST API development
- **Purpose**: Modern API framework for Django

---

## 7. DEVELOPMENT & DEBUGGING

### django-extensions
- **Package Name**: `django-extensions`
- **Version**: `>=3.4.0`
- **PyPI**: https://pypi.org/project/django-extensions/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS
  - Development management commands
- **Purpose**: Additional Django utilities and commands

### django-debug-toolbar
- **Package Name**: `django-debug-toolbar`
- **Version**: `>=4.2.0`
- **PyPI**: https://pypi.org/project/django-debug-toolbar/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, MIDDLEWARE
  - Development only
- **Purpose**: Debug toolbar for SQL queries and templates

### django-silk
- **Package Name**: `django-silk`
- **Version**: `>=5.0.4`
- **PyPI**: https://pypi.org/project/django-silk/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, MIDDLEWARE
  - Request profiling
- **Purpose**: Request profiling and monitoring

### django-cors-headers
- **Package Name**: `django-cors-headers`
- **Version**: `>=4.0.0`
- **PyPI**: https://pypi.org/project/django-cors-headers/
- **Files Used In**:
  - `CLAS/settings.py` - INSTALLED_APPS, MIDDLEWARE, CORS settings
- **Purpose**: CORS handling for APIs

---

## 8. TESTING & QUALITY ASSURANCE

### pytest
- **Package Name**: `pytest`
- **Version**: `>=7.4.0`
- **PyPI**: https://pypi.org/project/pytest/
- **Files Used In**:
  - `class/tests.py` - Test files
  - `class/test_*.py` - Test modules
  - `pytest.ini` - pytest configuration
- **Purpose**: Testing framework

### pytest-django
- **Package Name**: `pytest-django`
- **Version**: `>=4.5.2`
- **PyPI**: https://pypi.org/project/pytest-django/
- **Files Used In**:
  - `pytest.ini` - pytest configuration
  - Test files
- **Purpose**: Django plugin for pytest

### hypothesis
- **Package Name**: `hypothesis`
- **Version**: `>=6.82.0`
- **PyPI**: https://pypi.org/project/hypothesis/
- **Files Used In**:
  - `class/tests.py` - Property-based tests
  - `.hypothesis/` - Hypothesis cache directory
- **Purpose**: Property-based testing library

---

## Summary Statistics

| Category | Count | Packages |
|----------|-------|----------|
| Core | 4 | Django, psycopg2-binary, python-dotenv, django-environ |
| Production | 2 | gunicorn, whitenoise |
| Frontend | 5 | Pillow, django-tailwind, django-browser-reload, django-widget-tweaks, beautifulsoup4 |
| Data Handling | 3 | openpyxl, pandas, reportlab |
| Performance | 7 | psutil, redis, django-redis, django-cachalot, django-compressor, django-pipeline, django-htmlmin |
| API | 1 | django-ninja |
| Development | 4 | django-extensions, django-debug-toolbar, django-silk, django-cors-headers |
| Testing | 3 | pytest, pytest-django, hypothesis |
| **TOTAL** | **29** | **All packages listed above** |

---

## Installation Command

```bash
pip install -r requirements.txt
```

This will install all 29 dependencies with their specified versions.

---

## Key Configuration Files

### Main Settings
- `CLAS/settings.py` - Django configuration (uses most dependencies)
- `CLAS/urls.py` - URL routing
- `CLAS/wsgi.py` - WSGI application

### Application Files
- `class/views.py` - View functions (uses Django, openpyxl, pandas)
- `class/models/` - Database models (uses Django, Pillow)
- `class/forms.py` - Form definitions (uses Django)
- `class/admin.py` - Admin interface (uses Django)

### Frontend Files
- `Templates/` - HTML templates (uses django-tailwind, django-widget-tweaks)
- `theme/` - Tailwind CSS configuration
- `static/` - Static files (CSS, JS, images)

### Testing Files
- `class/tests.py` - Test suite (uses pytest, hypothesis)
- `pytest.ini` - pytest configuration

### Middleware Files
- `class/performance_middleware.py` - Performance optimization (uses psutil)
- `class/db_connection_middleware.py` - Database connection handling
- `class/session_timeout_middleware.py` - Session management

---

## Dependency Relationships

```
Django (Core)
├── psycopg2-binary (Database)
├── django-environ (Configuration)
├── whitenoise (Static files)
├── django-tailwind (Frontend)
├── django-widget-tweaks (Forms)
├── django-extensions (Development)
├── django-debug-toolbar (Development)
├── django-silk (Development)
├── django-cors-headers (API)
├── django-cachalot (Performance)
├── django-compressor (Performance)
├── django-pipeline (Performance)
└── django-htmlmin (Performance)

Data Processing
├── openpyxl (Excel)
├── pandas (Analysis)
└── reportlab (PDF)

Caching
├── redis (Cache store)
└── django-redis (Django integration)

Testing
├── pytest (Framework)
├── pytest-django (Django integration)
└── hypothesis (Property-based testing)

Utilities
├── Pillow (Images)
├── beautifulsoup4 (HTML parsing)
├── psutil (Monitoring)
├── gunicorn (Production server)
└── python-dotenv (Environment)
```

---

## Version Compatibility Matrix

| Package | Min Version | Max Version | Python | Django |
|---------|------------|------------|--------|--------|
| Django | 5.1 | 5.2 | 3.10+ | 5.1.x |
| psycopg2-binary | 2.9.9 | Latest | 3.10+ | 5.1.x |
| gunicorn | 22.0.0 | Latest | 3.10+ | 5.1.x |
| pytest | 7.4.0 | Latest | 3.10+ | 5.1.x |
| hypothesis | 6.82.0 | Latest | 3.10+ | 5.1.x |

---

## Notes

1. All dependencies are production-ready
2. Development-only packages: django-debug-toolbar, django-silk, django-extensions
3. Optional packages: redis, django-redis (for distributed caching)
4. Testing packages: pytest, pytest-django, hypothesis
5. Keep dependencies updated regularly for security patches

---

## Related Documentation

- `requirements.txt` - Actual dependency list
- `DEPENDENCIES.md` - Detailed dependency information
- `REQUIREMENTS_GUIDE.md` - Quick reference guide
- `SETUP_INSTRUCTIONS.md` - Installation instructions

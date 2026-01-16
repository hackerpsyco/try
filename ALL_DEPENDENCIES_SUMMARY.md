# CLAS Application - All Dependencies Summary

## Quick Overview

**Total Dependencies**: 29 packages  
**Installation Command**: `pip install -r requirements.txt`  
**Python Version**: 3.10+  
**Django Version**: 5.1.x  
**Database**: PostgreSQL 12+

---

## Complete Dependency List

### 1. Django>=5.1,<5.2
- **Type**: Core Framework
- **Purpose**: Web framework for the entire application
- **Used In**: CLAS/settings.py, CLAS/urls.py, class/views.py, class/models/, Templates/
- **PyPI**: https://pypi.org/project/Django/

### 2. psycopg2-binary>=2.9.9
- **Type**: Database Adapter
- **Purpose**: PostgreSQL database connection
- **Used In**: CLAS/settings.py (DATABASE configuration)
- **PyPI**: https://pypi.org/project/psycopg2-binary/

### 3. python-dotenv>=1.0.1
- **Type**: Environment Management
- **Purpose**: Load environment variables from .env file
- **Used In**: Application startup
- **PyPI**: https://pypi.org/project/python-dotenv/

### 4. django-environ>=0.10.0
- **Type**: Environment Management
- **Purpose**: Type-safe environment variable handling
- **Used In**: CLAS/settings.py
- **PyPI**: https://pypi.org/project/django-environ/

### 5. gunicorn>=22.0.0
- **Type**: Production Server
- **Purpose**: WSGI HTTP server for production
- **Used In**: Render/Heroku deployment
- **PyPI**: https://pypi.org/project/gunicorn/

### 6. whitenoise>=6.7.0
- **Type**: Static Files
- **Purpose**: Serve static files efficiently in production
- **Used In**: CLAS/settings.py (MIDDLEWARE, STATICFILES_STORAGE)
- **PyPI**: https://pypi.org/project/whitenoise/

### 7. Pillow>=10.3.0
- **Type**: Image Processing
- **Purpose**: Handle image uploads and processing
- **Used In**: class/models/students.py (ImageField)
- **PyPI**: https://pypi.org/project/Pillow/

### 8. django-tailwind>=3.6.2
- **Type**: CSS Framework
- **Purpose**: Tailwind CSS integration
- **Used In**: CLAS/settings.py, theme/, Templates/
- **PyPI**: https://pypi.org/project/django-tailwind/

### 9. django-browser-reload>=1.2.4
- **Type**: Development Tool
- **Purpose**: Auto-reload browser during development
- **Used In**: CLAS/settings.py (MIDDLEWARE)
- **PyPI**: https://pypi.org/project/django-browser-reload/

### 10. django-widget-tweaks>=1.4.12
- **Type**: Form Rendering
- **Purpose**: Customize form widget rendering
- **Used In**: CLAS/settings.py, Templates/
- **PyPI**: https://pypi.org/project/django-widget-tweaks/

### 11. beautifulsoup4>=4.12.0
- **Type**: HTML Parsing
- **Purpose**: Parse and optimize HTML content
- **Used In**: Content optimization utilities
- **PyPI**: https://pypi.org/project/beautifulsoup4/

### 12. openpyxl>=3.1.2
- **Type**: Excel Handling
- **Purpose**: Read/write Excel files for student imports
- **Used In**: class/views.py (student_import function)
- **PyPI**: https://pypi.org/project/openpyxl/

### 13. pandas>=2.0.0
- **Type**: Data Analysis
- **Purpose**: Data manipulation and report generation
- **Used In**: class/reports_views.py
- **PyPI**: https://pypi.org/project/pandas/

### 14. reportlab>=4.0.0
- **Type**: PDF Generation
- **Purpose**: Create PDF reports and documents
- **Used In**: Report generation views
- **PyPI**: https://pypi.org/project/reportlab/

### 15. psutil>=5.9.0
- **Type**: System Monitoring
- **Purpose**: Monitor system and process performance
- **Used In**: class/performance_middleware.py
- **PyPI**: https://pypi.org/project/psutil/

### 16. redis>=4.6.0
- **Type**: Cache Store
- **Purpose**: In-memory data store for caching
- **Used In**: CLAS/settings.py (CACHES configuration)
- **PyPI**: https://pypi.org/project/redis/

### 17. django-redis>=5.3.0
- **Type**: Cache Backend
- **Purpose**: Django cache backend using Redis
- **Used In**: CLAS/settings.py (CACHES)
- **PyPI**: https://pypi.org/project/django-redis/

### 18. django-cachalot>=2.6.1
- **Type**: Query Caching
- **Purpose**: Automatic ORM query caching
- **Used In**: CLAS/settings.py (INSTALLED_APPS)
- **PyPI**: https://pypi.org/project/django-cachalot/

### 19. django-compressor>=4.4
- **Type**: Asset Compression
- **Purpose**: Compress CSS and JavaScript files
- **Used In**: CLAS/settings.py
- **PyPI**: https://pypi.org/project/django-compressor/

### 20. django-pipeline>=3.0.0
- **Type**: Asset Pipeline
- **Purpose**: Optimize CSS/JS assets
- **Used In**: CLAS/settings.py
- **PyPI**: https://pypi.org/project/django-pipeline/

### 21. django-htmlmin>=0.11.0
- **Type**: HTML Minification
- **Purpose**: Reduce HTML file sizes
- **Used In**: CLAS/settings.py
- **PyPI**: https://pypi.org/project/django-htmlmin/

### 22. django-ninja>=1.4.0
- **Type**: API Framework (Optional)
- **Purpose**: Modern API framework for future REST APIs
- **Used In**: Not currently used
- **PyPI**: https://pypi.org/project/django-ninja/

### 23. django-extensions>=3.4.0
- **Type**: Development Utilities
- **Purpose**: Additional Django management commands
- **Used In**: CLAS/settings.py (INSTALLED_APPS)
- **PyPI**: https://pypi.org/project/django-extensions/

### 24. django-debug-toolbar>=4.2.0
- **Type**: Debugging Tool
- **Purpose**: Debug SQL queries and templates
- **Used In**: CLAS/settings.py (MIDDLEWARE)
- **PyPI**: https://pypi.org/project/django-debug-toolbar/

### 25. django-silk>=5.0.4
- **Type**: Profiling Tool
- **Purpose**: Profile request performance
- **Used In**: CLAS/settings.py (MIDDLEWARE)
- **PyPI**: https://pypi.org/project/django-silk/

### 26. django-cors-headers>=4.0.0
- **Type**: CORS Handling
- **Purpose**: Handle cross-origin requests
- **Used In**: CLAS/settings.py (MIDDLEWARE)
- **PyPI**: https://pypi.org/project/django-cors-headers/

### 27. pytest>=7.4.0
- **Type**: Testing Framework
- **Purpose**: Run unit and integration tests
- **Used In**: class/tests.py, pytest.ini
- **PyPI**: https://pypi.org/project/pytest/

### 28. pytest-django>=4.5.2
- **Type**: Django Testing Plugin
- **Purpose**: Django-specific pytest utilities
- **Used In**: pytest.ini, test files
- **PyPI**: https://pypi.org/project/pytest-django/

### 29. hypothesis>=6.82.0
- **Type**: Property-Based Testing
- **Purpose**: Generate test cases automatically
- **Used In**: class/tests.py, .hypothesis/
- **PyPI**: https://pypi.org/project/hypothesis/

---

## Dependencies by Category

### Core (4 packages)
```
Django>=5.1,<5.2
psycopg2-binary>=2.9.9
python-dotenv>=1.0.1
django-environ>=0.10.0
```

### Production (2 packages)
```
gunicorn>=22.0.0
whitenoise>=6.7.0
```

### Frontend (5 packages)
```
Pillow>=10.3.0
django-tailwind>=3.6.2
django-browser-reload>=1.2.4
django-widget-tweaks>=1.4.12
beautifulsoup4>=4.12.0
```

### Data Handling (3 packages)
```
openpyxl>=3.1.2
pandas>=2.0.0
reportlab>=4.0.0
```

### Performance (7 packages)
```
psutil>=5.9.0
redis>=4.6.0
django-redis>=5.3.0
django-cachalot>=2.6.1
django-compressor>=4.4
django-pipeline>=3.0.0
django-htmlmin>=0.11.0
```

### API (1 package - Optional)
```
django-ninja>=1.4.0
```

### Development (4 packages)
```
django-extensions>=3.4.0
django-debug-toolbar>=4.2.0
django-silk>=5.0.4
django-cors-headers>=4.0.0
```

### Testing (3 packages)
```
pytest>=7.4.0
pytest-django>=4.5.2
hypothesis>=6.82.0
```

---

## Installation

### Install All Dependencies
```bash
pip install -r requirements.txt
```

### Install by Category
```bash
# Core only
pip install Django psycopg2-binary python-dotenv django-environ

# Production
pip install gunicorn whitenoise

# Frontend
pip install Pillow django-tailwind django-browser-reload django-widget-tweaks beautifulsoup4

# Data handling
pip install openpyxl pandas reportlab

# Performance
pip install psutil redis django-redis django-cachalot django-compressor django-pipeline django-htmlmin

# Development
pip install django-extensions django-debug-toolbar django-silk django-cors-headers

# Testing
pip install pytest pytest-django hypothesis
```

---

## Key Files Using Dependencies

### CLAS/settings.py
- Django
- psycopg2-binary
- django-environ
- whitenoise
- django-tailwind
- django-browser-reload
- django-widget-tweaks
- django-cachalot
- django-compressor
- django-pipeline
- django-htmlmin
- django-extensions
- django-debug-toolbar
- django-silk
- django-cors-headers

### class/views.py
- Django
- openpyxl
- pandas

### class/models/
- Django
- Pillow

### Templates/
- django-tailwind
- django-widget-tweaks

### class/tests.py
- pytest
- pytest-django
- hypothesis

### class/performance_middleware.py
- psutil

---

## Environment Variables

Create `.env` file:
```env
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://localhost:6379/0
```

---

## Verification Commands

```bash
# Check Django version
python -m django --version

# List all packages
pip list

# Check for issues
pip check

# Show specific package info
pip show package-name

# Run tests
pytest

# Run with coverage
pytest --cov=class
```

---

## Documentation Files

1. **requirements.txt** - Actual dependency list
2. **DEPENDENCIES.md** - Detailed dependency information
3. **DEPENDENCIES_MAPPING.md** - Complete mapping with file locations
4. **DEPENDENCIES_LIST.txt** - Quick reference list
5. **REQUIREMENTS_GUIDE.md** - Quick reference guide
6. **SETUP_INSTRUCTIONS.md** - Installation instructions
7. **ALL_DEPENDENCIES_SUMMARY.md** - This file

---

## Version Compatibility

| Component | Version |
|-----------|---------|
| Python | 3.10+ |
| Django | 5.1.x |
| PostgreSQL | 12+ |
| Redis | 6+ (optional) |
| Node.js | 16+ (for Tailwind) |

---

## Troubleshooting

### PostgreSQL Error
```bash
pip install --force-reinstall psycopg2-binary>=2.9.9
```

### Redis Error
```bash
redis-server
```

### Static Files Error
```bash
python manage.py collectstatic --noinput
```

### Import Error
```bash
pip install -r requirements.txt --upgrade
```

---

## Performance Tips

1. Enable Redis caching for production
2. Use django-cachalot for automatic query caching
3. Enable static file compression with whitenoise
4. Monitor with psutil and django-silk
5. Use gunicorn workers for concurrent requests

---

## Security Checklist

- [ ] Change SECRET_KEY in production
- [ ] Set DEBUG=False in production
- [ ] Use HTTPS in production
- [ ] Set ALLOWED_HOSTS correctly
- [ ] Use environment variables for sensitive data
- [ ] Enable CSRF protection
- [ ] Set secure cookie flags
- [ ] Use strong database passwords
- [ ] Keep dependencies updated
- [ ] Enable security headers

---

## Support Resources

- Django: https://docs.djangoproject.com/
- PostgreSQL: https://www.postgresql.org/docs/
- Tailwind CSS: https://tailwindcss.com/
- pytest: https://docs.pytest.org/
- Redis: https://redis.io/documentation

---

**Last Updated**: 2024  
**Total Dependencies**: 29 packages  
**Status**: Production Ready

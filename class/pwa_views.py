"""
PWA (Progressive Web App) views for offline support.
Note: Manifest is served as static file (static/manifest.json) via Nginx
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
import json


# Manifest is now served as static file - no Django view needed
# This keeps it clean and avoids conflicts between static and dynamic serving


@require_http_methods(["GET"])
def offline(request):
    """
    Serve offline fallback page when user navigates to uncached routes while offline.
    
    Requirements: 4.2, 4.4
    """
    from django.shortcuts import render
    return render(request, 'offline.html')

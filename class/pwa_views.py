"""
PWA (Progressive Web App) views for manifest and offline support.
"""

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.cache import cache_page
import json


@require_http_methods(["GET"])
@cache_page(60 * 60)  # Cache for 1 hour
def manifest(request):
    """
    Serve the Web Manifest file for PWA.
    
    The manifest describes the application to the browser and operating system,
    including app name, icons, colors, and display mode.
    
    Requirements: 1.1, 3.1, 3.3
    """
    manifest_data = {
        "name": "CLAS - Class Learning and Assessment System",
        "short_name": "CLAS",
        "description": "Educational management system for class learning and assessment",
        "start_url": "/",
        "scope": "/",
        "display": "standalone",
        "orientation": "portrait",
        "theme_color": "#3b82f6",
        "background_color": "#ffffff",
        "icons": [
            {
                "src": "/static/icons/icon-72x72.png",
                "sizes": "72x72",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-96x96.png",
                "sizes": "96x96",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-128x128.png",
                "sizes": "128x128",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-144x144.png",
                "sizes": "144x144",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-152x152.png",
                "sizes": "152x152",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-192x192.png",
                "sizes": "192x192",
                "type": "image/png",
                "purpose": "any maskable"
            },
            {
                "src": "/static/icons/icon-384x384.png",
                "sizes": "384x384",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512x512.png",
                "sizes": "512x512",
                "type": "image/png",
                "purpose": "any maskable"
            }
        ],
        "categories": ["education", "productivity"],
        "screenshots": [
            {
                "src": "/static/images/screenshot-1.png",
                "sizes": "540x720",
                "type": "image/png",
                "form_factor": "narrow"
            }
        ]
    }
    
    response = JsonResponse(manifest_data)
    response['Content-Type'] = 'application/manifest+json'
    response['Cache-Control'] = 'public, max-age=3600'
    return response


@require_http_methods(["GET"])
def offline(request):
    """
    Serve offline fallback page when user navigates to uncached routes while offline.
    
    Requirements: 4.2, 4.4
    """
    from django.shortcuts import render
    return render(request, 'offline.html')

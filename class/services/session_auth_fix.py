"""
Session and Authentication Management Fix
Handles proper session cleanup, localStorage management, and URL access control
"""

from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)


class ImprovedSessionTimeoutMiddleware(MiddlewareMixin):
    """
    Improved session timeout middleware with proper cleanup
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)
        # Session timeout: 30 minutes of inactivity
        self.timeout = getattr(settings, 'SESSION_TIMEOUT', 1800)
        
        # URLs that don't require authentication
        self.exempt_urls = [
            '/login/',
            '/logout/',
            '/static/',
            '/media/',
            '/api/auth/',
        ]
    
    def process_request(self, request):
        """Check and enforce session timeout"""
        
        # Skip exempt URLs
        if any(request.path.startswith(url) for url in self.exempt_urls):
            return None
        
        # If user is not authenticated, redirect to login
        if not request.user.is_authenticated:
            if not request.path.startswith('/login'):
                request.session['next_url'] = request.get_full_path()
                messages.warning(request, "Please log in to continue.")
                return redirect('/login/')
            return None
        
        # Check session timeout
        current_time = time.time()
        last_activity = request.session.get('last_activity', current_time)
        
        # If session expired
        if current_time - last_activity > self.timeout:
            logger.warning(f"Session timeout for user {request.user.email}")
            logout(request)
            request.session.flush()  # Clear all session data
            messages.error(request, "Your session has expired. Please log in again.")
            return redirect('/login/')
        
        # Update last activity
        request.session['last_activity'] = current_time
        request.session.modified = True
        
        return None


class LocalStorageCleanupMiddleware(MiddlewareMixin):
    """
    Middleware to ensure localStorage is properly cleared on logout
    """
    
    def process_response(self, request, response):
        """Add headers to clear localStorage on logout"""
        
        # If user just logged out
        if request.path == '/logout/':
            # Add header to signal frontend to clear localStorage
            response['X-Clear-Storage'] = 'true'
            logger.info(f"Logout detected for {request.user.email if request.user.is_authenticated else 'anonymous'}")
        
        # Prevent caching of authenticated pages
        if request.user.is_authenticated:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate, private'
            response['Pragma'] = 'no-cache'
            response['Expires'] = '0'
        
        return response


class URLAccessControlMiddleware(MiddlewareMixin):
    """
    Middleware to control URL access based on user role and authentication
    """
    
    # URL patterns by role
    ROLE_URLS = {
        'Admin': ['/admin/', '/admin/dashboard/'],
        'Supervisor': ['/supervisor/', '/supervisor/dashboard/'],
        'Facilitator': ['/facilitator/', '/facilitator/dashboard/'],
    }
    
    # Public URLs (no authentication required)
    PUBLIC_URLS = ['/login/', '/logout/', '/static/', '/media/']
    
    # API endpoints that handle their own authentication (return JSON errors instead of redirects)
    API_URLS = ['/api/']
    
    def process_request(self, request):
        """Check URL access permissions"""
        
        # Allow public URLs
        if any(request.path.startswith(url) for url in self.PUBLIC_URLS):
            return None
        
        # Skip middleware for API endpoints - they handle their own authentication
        if any(request.path.startswith(url) for url in self.API_URLS):
            return None
        
        # If not authenticated, redirect to login
        if not request.user.is_authenticated:
            request.session['next_url'] = request.get_full_path()
            messages.warning(request, "Please log in to access this page.")
            return redirect('/login/')
        
        # Check role-based access
        user_role = request.user.role.name if request.user.role else None
        
        if not user_role:
            logger.error(f"User {request.user.email} has no role assigned")
            logout(request)
            messages.error(request, "Your account is not properly configured. Contact administrator.")
            return redirect('/login/')
        
        # Check if user has access to this URL
        allowed_urls = self.ROLE_URLS.get(user_role, [])
        
        # Allow access if URL matches user's role
        if any(request.path.startswith(url) for url in allowed_urls):
            return None
        
        # Block access to other role URLs
        logger.warning(f"Unauthorized access attempt by {request.user.email} to {request.path}")
        messages.error(request, "You don't have permission to access this page.")
        
        # Redirect to appropriate dashboard
        dashboard_urls = {
            'Admin': '/admin/dashboard/',
            'Supervisor': '/supervisor/dashboard/',
            'Facilitator': '/facilitator/dashboard/',
        }
        dashboard_url = dashboard_urls.get(user_role, '/login/')
        return redirect(dashboard_url)


class SessionCleanupService:
    """
    Service to properly manage session cleanup and logout
    """
    
    @staticmethod
    def logout_user(request):
        """
        Properly logout user and clear all session data
        """
        try:
            user_email = request.user.email if request.user.is_authenticated else 'anonymous'
            
            # Clear session
            request.session.flush()
            
            # Logout user
            logout(request)
            
            logger.info(f"User {user_email} logged out successfully")
            
            return True
        except Exception as e:
            logger.error(f"Error during logout: {str(e)}")
            return False
    
    @staticmethod
    def clear_session_data(request):
        """
        Clear specific session data without logging out
        """
        try:
            # Clear sensitive data
            keys_to_clear = [
                'last_activity',
                'next_url',
                'session_expired',
                'user_preferences',
            ]
            
            for key in keys_to_clear:
                if key in request.session:
                    del request.session[key]
            
            request.session.modified = True
            return True
        except Exception as e:
            logger.error(f"Error clearing session data: {str(e)}")
            return False
    
    @staticmethod
    def validate_session(request):
        """
        Validate that session is still valid
        """
        if not request.user.is_authenticated:
            return False
        
        # Check if user still exists in database
        try:
            from ..models import User
            User.objects.get(id=request.user.id)
            return True
        except User.DoesNotExist:
            logger.warning(f"User {request.user.id} no longer exists")
            return False
    
    @staticmethod
    def refresh_session(request):
        """
        Refresh session timeout
        """
        try:
            request.session['last_activity'] = time.time()
            request.session.modified = True
            return True
        except Exception as e:
            logger.error(f"Error refreshing session: {str(e)}")
            return False


class LocalStorageManager:
    """
    JavaScript helper to manage localStorage properly
    """
    
    @staticmethod
    def get_clear_storage_script():
        """
        Returns JavaScript code to clear localStorage
        """
        return """
        <script>
        // Clear localStorage on page load if logout was detected
        document.addEventListener('DOMContentLoaded', function() {
            // Check if server sent clear storage signal
            const clearStorage = document.querySelector('meta[name="X-Clear-Storage"]');
            if (clearStorage) {
                localStorage.clear();
                sessionStorage.clear();
                console.log('Storage cleared');
            }
            
            // Also clear on logout link click
            const logoutLinks = document.querySelectorAll('a[href*="logout"]');
            logoutLinks.forEach(link => {
                link.addEventListener('click', function(e) {
                    localStorage.clear();
                    sessionStorage.clear();
                    console.log('Storage cleared before logout');
                });
            });
        });
        </script>
        """
    
    @staticmethod
    def get_session_check_script():
        """
        Returns JavaScript code to check session validity
        """
        return """
        <script>
        // Check session validity periodically
        setInterval(function() {
            fetch('/api/session/check/', {
                method: 'GET',
                credentials: 'include'
            })
            .then(response => {
                if (response.status === 401) {
                    // Session expired
                    localStorage.clear();
                    sessionStorage.clear();
                    window.location.href = '/login/';
                }
            })
            .catch(error => console.error('Session check error:', error));
        }, 60000); // Check every minute
        </script>
        """

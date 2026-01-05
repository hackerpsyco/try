"""
CurriculumContentResolver service for determining and loading curriculum content.
Handles the logic for choosing between admin-managed and static content.
"""

import logging
from typing import Optional, Dict, Any, Tuple
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from dataclasses import dataclass
from pathlib import Path
import os

from ..models import CurriculumSession, ClassSection

logger = logging.getLogger(__name__)


@dataclass
class ContentResult:
    """Result of content resolution with metadata."""
    content: str
    source: str  # 'admin_managed' or 'static_fallback'
    curriculum_session: Optional[CurriculumSession] = None
    last_updated: Optional[timezone.datetime] = None
    cache_key: Optional[str] = None


@dataclass
class AvailabilityStatus:
    """Status of content availability."""
    is_available: bool
    source: str
    last_checked: timezone.datetime
    error_message: Optional[str] = None


@dataclass
class ContentMetadata:
    """Metadata about curriculum content."""
    source: str
    last_updated: Optional[timezone.datetime]
    title: Optional[str] = None
    day_number: int = 0
    language: str = ''
    usage_count: int = 0


class CurriculumContentResolver:
    """
    Service for resolving and loading curriculum content.
    Determines whether to use admin-managed or static content with intelligent fallback.
    """
    
    CACHE_TIMEOUT = 3600  # 1 hour
    STATIC_CONTENT_PATHS = {
        'english': 'Templates/admin/session/English_ ALL DAYS.html',
        'hindi': 'Templates/admin/session/Hindi_ ALL DAYS.html'
    }
    
    def __init__(self):
        self.cache_prefix = 'curriculum_content'
    
    def resolve_content(self, day: int, language: str, class_section: Optional[ClassSection] = None) -> ContentResult:
        """
        Resolve curriculum content for a specific day and language.
        Returns admin-managed content if available, otherwise falls back to static content.
        """
        try:
            # Check cache first
            cache_key = f"{self.cache_prefix}:{language}:{day}"
            cached_result = cache.get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Try to get admin-managed content first
            curriculum_session = self._get_curriculum_session(day, language)
            
            if curriculum_session and curriculum_session.is_active_for_facilitators and not curriculum_session.fallback_to_static:
                content = self._load_admin_content(curriculum_session)
                if content:
                    result = ContentResult(
                        content=content,
                        source='admin_managed',
                        curriculum_session=curriculum_session,
                        last_updated=curriculum_session.updated_at,
                        cache_key=cache_key
                    )
                    
                    # Update usage count
                    self._update_usage_stats(curriculum_session)
                    
                    # Cache the result
                    cache.set(cache_key, result, self.CACHE_TIMEOUT)
                    logger.info(f"Loaded admin-managed content for Day {day} {language}")
                    return result
            
            # Fallback to static content
            static_content = self._load_static_content(day, language)
            result = ContentResult(
                content=static_content,
                source='static_fallback',
                last_updated=None,
                cache_key=cache_key
            )
            
            # Cache static content too (shorter timeout)
            cache.set(cache_key, result, self.CACHE_TIMEOUT // 2)
            logger.info(f"Loaded static fallback content for Day {day} {language}")
            return result
            
        except Exception as e:
            logger.error(f"Error resolving content for Day {day} {language}: {str(e)}")
            # Return empty content as last resort
            return ContentResult(
                content="<p>Content temporarily unavailable. Please try again later.</p>",
                source='error_fallback',
                last_updated=timezone.now()
            )
    
    def load_curriculum_content(self, day: int, language: str) -> str:
        """
        Load curriculum content for a specific day and language.
        Returns the content string directly.
        """
        result = self.resolve_content(day, language)
        return result.content
    
    def check_content_availability(self, day: int, language: str) -> AvailabilityStatus:
        """
        Check if curriculum content is available for a specific day and language.
        """
        try:
            curriculum_session = self._get_curriculum_session(day, language)
            
            if curriculum_session and curriculum_session.is_active_for_facilitators and not curriculum_session.fallback_to_static:
                return AvailabilityStatus(
                    is_available=True,
                    source='admin_managed',
                    last_checked=timezone.now()
                )
            
            # Check if static content exists
            static_available = self._check_static_content_exists(day, language)
            return AvailabilityStatus(
                is_available=static_available,
                source='static_fallback',
                last_checked=timezone.now()
            )
            
        except Exception as e:
            logger.error(f"Error checking content availability for Day {day} {language}: {str(e)}")
            return AvailabilityStatus(
                is_available=False,
                source='error',
                last_checked=timezone.now(),
                error_message=str(e)
            )
    
    def get_content_metadata(self, day: int, language: str) -> ContentMetadata:
        """
        Get metadata about curriculum content for a specific day and language.
        """
        try:
            curriculum_session = self._get_curriculum_session(day, language)
            
            if curriculum_session:
                return ContentMetadata(
                    source='admin_managed',
                    last_updated=curriculum_session.updated_at,
                    title=curriculum_session.title,
                    day_number=curriculum_session.day_number,
                    language=curriculum_session.language,
                    usage_count=curriculum_session.usage_count
                )
            else:
                return ContentMetadata(
                    source='static_fallback',
                    last_updated=None,
                    day_number=day,
                    language=language,
                    usage_count=0
                )
                
        except Exception as e:
            logger.error(f"Error getting content metadata for Day {day} {language}: {str(e)}")
            return ContentMetadata(
                source='error',
                last_updated=timezone.now(),
                day_number=day,
                language=language,
                usage_count=0
            )
    
    def invalidate_cache(self, day: int = None, language: str = None):
        """
        Invalidate cached content for specific day/language or all content.
        """
        if day and language:
            cache_key = f"{self.cache_prefix}:{language}:{day}"
            cache.delete(cache_key)
            logger.info(f"Invalidated cache for Day {day} {language}")
        else:
            # Invalidate all curriculum content cache
            # This is a simplified approach - in production you might want a more sophisticated cache invalidation
            cache.delete_many([
                f"{self.cache_prefix}:{lang}:{d}" 
                for lang in ['english', 'hindi'] 
                for d in range(1, 151)
            ])
            logger.info("Invalidated all curriculum content cache")
    
    def _get_curriculum_session(self, day: int, language: str) -> Optional[CurriculumSession]:
        """
        Get CurriculumSession for specific day and language.
        """
        try:
            return CurriculumSession.objects.get(
                day_number=day,
                language=language,
                status='published'
            )
        except CurriculumSession.DoesNotExist:
            return None
        except Exception as e:
            logger.error(f"Error fetching curriculum session for Day {day} {language}: {str(e)}")
            return None
    
    def _load_admin_content(self, curriculum_session: CurriculumSession) -> str:
        """
        Load content from admin-managed CurriculumSession.
        """
        try:
            # Combine all content fields into a structured HTML format
            content_parts = []
            
            if curriculum_session.title:
                content_parts.append(f"<h1>{curriculum_session.title}</h1>")
            
            if curriculum_session.learning_objectives:
                content_parts.append(f"<h2>Learning Objectives</h2>")
                content_parts.append(f"<div class='learning-objectives'>{curriculum_session.learning_objectives}</div>")
            
            if curriculum_session.content:
                content_parts.append(f"<h2>Session Content</h2>")
                content_parts.append(f"<div class='session-content'>{curriculum_session.content}</div>")
            
            if curriculum_session.activities:
                content_parts.append(f"<h2>Activities</h2>")
                content_parts.append(f"<div class='activities'>{self._format_activities(curriculum_session.activities)}</div>")
            
            if curriculum_session.resources:
                content_parts.append(f"<h2>Resources</h2>")
                content_parts.append(f"<div class='resources'>{self._format_resources(curriculum_session.resources)}</div>")
            
            return "\n".join(content_parts) if content_parts else "<p>No content available.</p>"
            
        except Exception as e:
            logger.error(f"Error loading admin content for session {curriculum_session.id}: {str(e)}")
            return ""
    
    def _load_static_content(self, day: int, language: str) -> str:
        """
        Load content from static HTML files.
        """
        try:
            static_file_path = self.STATIC_CONTENT_PATHS.get(language.lower())
            if not static_file_path:
                return f"<p>No static content available for language: {language}</p>"
            
            # Build full path to static file
            full_path = Path(settings.BASE_DIR) / static_file_path
            
            if not full_path.exists():
                logger.warning(f"Static content file not found: {full_path}")
                return f"<p>Static content file not found for Day {day} in {language}</p>"
            
            # Read the static file content
            with open(full_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # Extract content for specific day if the file contains multiple days
            # This is a simplified approach - you might need more sophisticated parsing
            day_content = self._extract_day_content(content, day)
            return day_content or f"<p>Content for Day {day} not found in static file.</p>"
            
        except Exception as e:
            logger.error(f"Error loading static content for Day {day} {language}: {str(e)}")
            return f"<p>Error loading static content: {str(e)}</p>"
    
    def _check_static_content_exists(self, day: int, language: str) -> bool:
        """
        Check if static content file exists for the given language.
        """
        try:
            static_file_path = self.STATIC_CONTENT_PATHS.get(language.lower())
            if not static_file_path:
                return False
            
            full_path = Path(settings.BASE_DIR) / static_file_path
            return full_path.exists()
            
        except Exception as e:
            logger.error(f"Error checking static content existence for {language}: {str(e)}")
            return False
    
    def _update_usage_stats(self, curriculum_session: CurriculumSession):
        """
        Update usage statistics for the curriculum session.
        """
        try:
            curriculum_session.usage_count += 1
            curriculum_session.last_accessed = timezone.now()
            curriculum_session.save(update_fields=['usage_count', 'last_accessed'])
        except Exception as e:
            logger.error(f"Error updating usage stats for session {curriculum_session.id}: {str(e)}")
    
    def _format_activities(self, activities: Dict[str, Any]) -> str:
        """
        Format activities JSON data into HTML.
        """
        try:
            if not activities:
                return "<p>No activities defined.</p>"
            
            html_parts = []
            for key, value in activities.items():
                if isinstance(value, dict):
                    html_parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
                    for sub_key, sub_value in value.items():
                        html_parts.append(f"<p><strong>{sub_key.replace('_', ' ').title()}:</strong> {sub_value}</p>")
                else:
                    html_parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>")
            
            return "\n".join(html_parts)
            
        except Exception as e:
            logger.error(f"Error formatting activities: {str(e)}")
            return "<p>Error formatting activities.</p>"
    
    def _format_resources(self, resources: Dict[str, Any]) -> str:
        """
        Format resources JSON data into HTML.
        """
        try:
            if not resources:
                return "<p>No resources available.</p>"
            
            html_parts = []
            for key, value in resources.items():
                if isinstance(value, str) and (value.startswith('http') or value.startswith('/')):
                    # It's a link
                    html_parts.append(f"<p><a href='{value}' target='_blank'>{key.replace('_', ' ').title()}</a></p>")
                elif isinstance(value, dict):
                    html_parts.append(f"<h3>{key.replace('_', ' ').title()}</h3>")
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and (sub_value.startswith('http') or sub_value.startswith('/')):
                            html_parts.append(f"<p><a href='{sub_value}' target='_blank'>{sub_key.replace('_', ' ').title()}</a></p>")
                        else:
                            html_parts.append(f"<p><strong>{sub_key.replace('_', ' ').title()}:</strong> {sub_value}</p>")
                else:
                    html_parts.append(f"<p><strong>{key.replace('_', ' ').title()}:</strong> {value}</p>")
            
            return "\n".join(html_parts)
            
        except Exception as e:
            logger.error(f"Error formatting resources: {str(e)}")
            return "<p>Error formatting resources.</p>"
    
    def _extract_day_content(self, full_content: str, day: int) -> str:
        """
        Extract content for a specific day from a file that contains multiple days.
        Handles HTML table structure from Google Sheets exports.
        """
        try:
            from bs4 import BeautifulSoup
            
            # Parse the HTML content
            soup = BeautifulSoup(full_content, 'html.parser')
            
            # Find the table containing the curriculum data
            table = soup.find('table', class_='waffle')
            if not table:
                # Fallback to simple text search if no table found
                return self._extract_day_content_simple(full_content, day)
            
            # Find all rows in the table
            rows = table.find_all('tr')
            
            # Look for the row that contains "Day X" in any cell (usually first cell)
            day_row_index = -1
            next_day_row_index = -1
            
            for i, row in enumerate(rows):
                cells = row.find_all(['td', 'th'])
                if cells:
                    # Check all cells for day pattern, but prioritize first cell
                    for cell in cells[:2]:  # Check first 2 cells
                        cell_text = cell.get_text(strip=True)
                        
                        # Check if this is our target day
                        if cell_text == f"Day {day}":
                            day_row_index = i
                            break
                        
                        # Check if this is the next day (to know where to stop)
                        elif day_row_index != -1 and cell_text.startswith("Day "):
                            try:
                                found_day = int(cell_text.replace("Day ", "").strip())
                                if found_day > day:
                                    next_day_row_index = i
                                    break
                            except ValueError:
                                continue
                    
                    if day_row_index != -1 and next_day_row_index != -1:
                        break
            
            if day_row_index == -1:
                # Day not found, return helpful error message
                return f"""
                <div class="alert alert-warning">
                    <h5><i class="fas fa-exclamation-triangle me-2"></i>Day {day} Content Not Found</h5>
                    <p>The curriculum content for Day {day} could not be located in the static file.</p>
                    <div class="mt-3">
                        <h6>Possible reasons:</h6>
                        <ul class="mb-3">
                            <li>The day number is outside the available range (1-150)</li>
                            <li>The content structure has changed</li>
                            <li>The file is corrupted or incomplete</li>
                        </ul>
                        <div class="d-flex gap-2">
                            <button class="btn btn-outline-primary btn-sm" onclick="loadCurriculumContent(1, '{self._get_current_language()}')">
                                <i class="fas fa-arrow-left me-1"></i>Go to Day 1
                            </button>
                            <button class="btn btn-outline-secondary btn-sm" onclick="location.reload()">
                                <i class="fas fa-redo me-1"></i>Retry
                            </button>
                        </div>
                    </div>
                </div>
                """
            
            # Extract rows from day_row_index to next_day_row_index (or end)
            end_index = next_day_row_index if next_day_row_index != -1 else len(rows)
            day_rows = rows[day_row_index:end_index]
            
            # Convert the extracted rows back to HTML with enhanced styling
            day_content_html = []
            
            for row in day_rows:
                # Clean up the row HTML and add it to our content
                row_html = str(row)
                day_content_html.append(row_html)
            
            # Wrap in a proper table structure with enhanced UI
            extracted_content = f"""
            <div class="curriculum-day-content" data-day="{day}">
                <div class="curriculum-content-wrapper">
                    <div class="table-responsive">
                        <table class="table table-bordered curriculum-table">
                            <tbody>
                                {''.join(day_content_html)}
                            </tbody>
                        </table>
                    </div>
                </div>
                
                <div class="day-footer mt-3">
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">
                                <i class="fas fa-info-circle me-1"></i>
                                Static curriculum content for Day {day}.
                            </small>
                        </div>
                        <div class="col-md-6 text-end">
                            <button class="btn btn-outline-primary btn-sm" onclick="window.print()">
                                <i class="fas fa-print me-1"></i>Print Day {day}
                            </button>
                        </div>
                    </div>
                </div>
            </div>
            """
            
            return extracted_content
            
        except ImportError:
            # BeautifulSoup not available, fall back to simple text extraction
            logger.warning("BeautifulSoup not available, using simple text extraction")
            return self._extract_day_content_simple(full_content, day)
        except Exception as e:
            logger.error(f"Error extracting day {day} content with HTML parsing: {str(e)}")
            # Fall back to simple text extraction
            return self._extract_day_content_simple(full_content, day)
    
    def _get_current_language(self):
        """Helper method to get current language context."""
        return 'english'  # Default, can be enhanced later
    
    def _extract_day_content_simple(self, full_content: str, day: int) -> str:
        """
        Simple text-based extraction as fallback when HTML parsing fails.
        """
        try:
            # Look for day markers in the content
            day_markers = [
                f">Day {day}<",  # HTML cell content
                f"Day {day}",    # Simple text
                f"day {day}",    # Lowercase
            ]
            
            content_lower = full_content.lower()
            day_start = -1
            
            # Find the start of the day content
            for marker in day_markers:
                marker_pos = content_lower.find(marker.lower())
                if marker_pos != -1:
                    day_start = marker_pos
                    break
            
            if day_start == -1:
                # If no specific day marker found, return helpful error message
                return f"""
                <div class="alert alert-info">
                    <h5>Day {day} Content</h5>
                    <p>Unable to locate specific content for Day {day} in the curriculum file.</p>
                    <p>Showing a sample of available content:</p>
                    <div class="content-sample" style="max-height: 300px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; background: #f9f9f9;">
                        {full_content[:1500]}{'...' if len(full_content) > 1500 else ''}
                    </div>
                    <small class="text-muted">
                        Note: This is static content. For better day-specific content, 
                        ask your administrator to create admin-managed curriculum sessions.
                    </small>
                </div>
                """
            
            # Find the end of the day content (next day marker or reasonable chunk)
            next_day_start = -1
            for next_day in range(day + 1, day + 5):  # Check next few days
                next_marker = f">Day {next_day}<"
                next_marker_pos = content_lower.find(next_marker.lower(), day_start + 1)
                if next_marker_pos != -1:
                    next_day_start = next_marker_pos
                    break
            
            if next_day_start != -1:
                extracted = full_content[day_start:next_day_start].strip()
            else:
                # Take a reasonable chunk from day start
                extracted = full_content[day_start:day_start + 3000].strip()
            
            # Wrap in a container with proper styling
            return f"""
            <div class="curriculum-day-content" data-day="{day}">
                <div class="static-content-wrapper">
                    {extracted}
                </div>
                <div class="mt-3">
                    <small class="text-muted">
                        <i class="fas fa-info-circle"></i>
                        Static curriculum content. For enhanced features, ask your administrator to create admin-managed content.
                    </small>
                </div>
            </div>
            """
                
        except Exception as e:
            logger.error(f"Error in simple day {day} content extraction: {str(e)}")
            return f"""
            <div class="alert alert-danger">
                <h5>Content Loading Error</h5>
                <p>There was an error loading the curriculum content for Day {day}.</p>
                <p>Error details: {str(e)}</p>
                <p>Please try refreshing the page or contact your administrator.</p>
            </div>
            """

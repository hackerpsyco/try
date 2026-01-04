"""
Django management command to optimize Tailwind CSS
"""
from django.core.management.base import BaseCommand
from django.conf import settings
import os
import subprocess
from pathlib import Path


class Command(BaseCommand):
    help = 'Optimize Tailwind CSS for better performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            choices=['dev', 'prod'],
            default='dev',
            help='Build mode: dev or prod',
        )
        parser.add_argument(
            '--analyze',
            action='store_true',
            help='Analyze CSS file size and performance',
        )
        parser.add_argument(
            '--purge',
            action='store_true',
            help='Enable CSS purging for smaller file size',
        )

    def handle(self, *args, **options):
        mode = options['mode']
        analyze = options['analyze']
        purge = options['purge']
        
        self.stdout.write("🎨 Optimizing Tailwind CSS...")
        
        # Check if theme directory exists
        theme_dir = Path(settings.BASE_DIR) / 'theme' / 'static_src'
        if not theme_dir.exists():
            self.stdout.write(
                self.style.ERROR("Theme directory not found!")
            )
            return
        
        # Build CSS
        self.build_css(theme_dir, mode, purge)
        
        # Analyze if requested
        if analyze:
            self.analyze_css()
        
        # Provide recommendations
        self.provide_recommendations(mode)

    def build_css(self, theme_dir, mode, purge):
        """Build Tailwind CSS"""
        self.stdout.write(f"🏗️  Building CSS in {mode} mode...")
        
        # Determine build command
        if mode == 'prod':
            cmd = ['npm', 'run', 'build-prod']
            env = {'NODE_ENV': 'production'}
        else:
            cmd = ['npm', 'run', 'build']
            env = {'NODE_ENV': 'development'}
        
        # Add purge flag if requested
        if purge:
            env['PURGE_CSS'] = 'true'
        
        # Set up environment
        current_env = os.environ.copy()
        current_env.update(env)
        
        try:
            result = subprocess.run(
                cmd,
                cwd=theme_dir,
                env=current_env,
                capture_output=True,
                text=True,
                check=True
            )
            self.stdout.write(
                self.style.SUCCESS("✅ CSS build successful!")
            )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f"❌ CSS build failed: {e.stderr}")
            )
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR("❌ npm not found. Please install Node.js and npm.")
            )

    def analyze_css(self):
        """Analyze the generated CSS file"""
        self.stdout.write("📊 Analyzing CSS performance...")
        
        css_file = Path(settings.BASE_DIR) / 'theme' / 'static' / 'css' / 'styles.css'
        
        if not css_file.exists():
            self.stdout.write(
                self.style.WARNING("⚠️  CSS file not found. Run build first.")
            )
            return
        
        # Get file statistics
        file_size = css_file.stat().st_size
        file_size_kb = file_size / 1024
        
        # Read content for analysis
        with open(css_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count CSS rules and selectors
        rule_count = content.count('{')
        selector_count = content.count(',') + rule_count
        
        # Display analysis
        self.stdout.write(f"📁 File size: {file_size_kb:.1f} KB")
        self.stdout.write(f"📏 CSS rules: ~{rule_count}")
        self.stdout.write(f"🎯 Selectors: ~{selector_count}")
        
        # Performance assessment
        if file_size_kb > 500:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Large CSS file (>500KB). Consider enabling purge mode."
                )
            )
        elif file_size_kb > 200:
            self.stdout.write(
                self.style.WARNING(
                    "⚠️  Moderate CSS file size (>200KB). Monitor growth."
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ Optimal CSS file size (<200KB)")
            )
        
        # Check for unused classes (basic heuristic)
        self.check_unused_classes(content)

    def check_unused_classes(self, css_content):
        """Basic check for potentially unused CSS classes"""
        self.stdout.write("🔍 Checking for unused classes...")
        
        # Get all template files
        template_dirs = [
            Path(settings.BASE_DIR) / 'Templates',
            Path(settings.BASE_DIR) / 'class' / 'templates',
        ]
        
        template_content = ""
        template_count = 0
        
        for template_dir in template_dirs:
            if template_dir.exists():
                for html_file in template_dir.rglob("*.html"):
                    try:
                        with open(html_file, 'r', encoding='utf-8') as f:
                            template_content += f.read() + "\n"
                        template_count += 1
                    except Exception:
                        continue
        
        if template_count == 0:
            self.stdout.write(
                self.style.WARNING("⚠️  No templates found for analysis")
            )
            return
        
        self.stdout.write(f"📄 Analyzed {template_count} template files")
        
        # Basic unused class detection (simplified)
        common_classes = [
            'flex', 'grid', 'hidden', 'block', 'inline', 'text-center',
            'bg-white', 'bg-gray-50', 'text-gray-900', 'border', 'rounded'
        ]
        
        unused_count = 0
        for class_name in common_classes:
            if class_name in css_content and class_name not in template_content:
                unused_count += 1
        
        if unused_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️  Found {unused_count} potentially unused common classes"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS("✅ No obviously unused classes detected")
            )

    def provide_recommendations(self, mode):
        """Provide optimization recommendations"""
        self.stdout.write("\n💡 Optimization Recommendations:")
        
        if mode == 'dev':
            self.stdout.write("  🔧 For production, use: --mode=prod --purge")
            self.stdout.write("  🔧 Enable CSS minification in production")
        
        self.stdout.write("  🔧 Use specific content paths in tailwind.config.js")
        self.stdout.write("  🔧 Remove unused Tailwind classes from templates")
        self.stdout.write("  🔧 Consider using custom CSS for repeated patterns")
        self.stdout.write("  🔧 Enable gzip compression on your web server")
        
        self.stdout.write("\n📋 Next steps:")
        self.stdout.write("  1. Run 'python manage.py collectstatic'")
        self.stdout.write("  2. Test admin interface for styling issues")
        self.stdout.write("  3. Monitor CSS file size in production")
        
        self.stdout.write(
            self.style.SUCCESS("\n🎉 Tailwind optimization complete!")
        )
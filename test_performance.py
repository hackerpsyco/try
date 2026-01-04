#!/usr/bin/env python
"""
Performance testing script for CLAS application
Run this script to test the performance optimizations
"""

import os
import sys
import django
import time
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import connection
from class.models import School, CurriculumSession, ClassSection

User = get_user_model()


class PerformanceTester:
    def __init__(self):
        self.client = Client()
        self.base_url = 'http://localhost:8000'
        self.results = {}
        
    def setup_test_user(self):
        """Create a test admin user"""
        try:
            user = User.objects.get(email='admin@test.com')
        except User.DoesNotExist:
            from class.models import Role
            admin_role = Role.objects.get(name='ADMIN')
            user = User.objects.create_user(
                email='admin@test.com',
                password='testpass123',
                full_name='Test Admin',
                role=admin_role
            )
        
        # Login
        self.client.login(email='admin@test.com', password='testpass123')
        return user
    
    def test_database_performance(self):
        """Test database query performance"""
        print("🔍 Testing database performance...")
        
        # Test 1: Simple query
        start_time = time.time()
        schools = list(School.objects.all())
        simple_query_time = time.time() - start_time
        
        # Test 2: Optimized query with relationships
        start_time = time.time()
        schools_optimized = list(School.objects.select_related().prefetch_related(
            'classsection_set', 'facilitators'
        ))
        optimized_query_time = time.time() - start_time
        
        # Test 3: Count queries
        start_time = time.time()
        school_count = School.objects.count()
        curriculum_count = CurriculumSession.objects.count()
        class_count = ClassSection.objects.count()
        count_query_time = time.time() - start_time
        
        self.results['database'] = {
            'simple_query_time': simple_query_time,
            'optimized_query_time': optimized_query_time,
            'count_query_time': count_query_time,
            'schools_count': len(schools),
            'total_queries': len(connection.queries)
        }
        
        print(f"  ✓ Simple query: {simple_query_time:.3f}s ({len(schools)} schools)")
        print(f"  ✓ Optimized query: {optimized_query_time:.3f}s")
        print(f"  ✓ Count queries: {count_query_time:.3f}s")
        print(f"  ✓ Total DB queries: {len(connection.queries)}")
    
    def test_cache_performance(self):
        """Test caching performance"""
        print("💾 Testing cache performance...")
        
        # Clear cache first
        cache.clear()
        
        # Test 1: Cache miss
        start_time = time.time()
        cache.set('test_key', 'test_value', 300)
        cache_set_time = time.time() - start_time
        
        # Test 2: Cache hit
        start_time = time.time()
        value = cache.get('test_key')
        cache_get_time = time.time() - start_time
        
        # Test 3: Cache complex data
        complex_data = {
            'schools': list(School.objects.values('id', 'name')[:10]),
            'timestamp': time.time()
        }
        start_time = time.time()
        cache.set('complex_data', complex_data, 300)
        cache_complex_time = time.time() - start_time
        
        self.results['cache'] = {
            'cache_set_time': cache_set_time,
            'cache_get_time': cache_get_time,
            'cache_complex_time': cache_complex_time,
            'cache_hit': value == 'test_value'
        }
        
        print(f"  ✓ Cache set: {cache_set_time:.6f}s")
        print(f"  ✓ Cache get: {cache_get_time:.6f}s")
        print(f"  ✓ Complex data cache: {cache_complex_time:.6f}s")
        print(f"  ✓ Cache hit: {'Yes' if value == 'test_value' else 'No'}")
    
    def test_view_performance(self):
        """Test view response times"""
        print("🌐 Testing view performance...")
        
        views_to_test = [
            ('admin_dashboard', '/admin/dashboard/'),
            ('schools_list', '/admin/schools/'),
            ('curriculum_sessions', '/admin/curriculum-sessions/'),
            ('sessions_filter', '/admin/sessions/'),
        ]
        
        view_results = {}
        
        for view_name, url in views_to_test:
            # Test 1: Cold request (no cache)
            cache.clear()
            start_time = time.time()
            response = self.client.get(url)
            cold_time = time.time() - start_time
            
            # Test 2: Warm request (with cache)
            start_time = time.time()
            response2 = self.client.get(url)
            warm_time = time.time() - start_time
            
            view_results[view_name] = {
                'cold_time': cold_time,
                'warm_time': warm_time,
                'status_code': response.status_code,
                'improvement': ((cold_time - warm_time) / cold_time * 100) if cold_time > 0 else 0
            }
            
            print(f"  ✓ {view_name}: {cold_time:.3f}s → {warm_time:.3f}s ({view_results[view_name]['improvement']:.1f}% faster)")
        
        self.results['views'] = view_results
    
    def test_api_performance(self):
        """Test API endpoint performance"""
        print("🔌 Testing API performance...")
        
        api_endpoints = [
            '/api/school-classes/?school_id=1',
            '/api/dashboard/stats/',
        ]
        
        api_results = {}
        
        for endpoint in api_endpoints:
            try:
                # Test multiple requests
                times = []
                for i in range(5):
                    start_time = time.time()
                    response = self.client.get(endpoint)
                    request_time = time.time() - start_time
                    times.append(request_time)
                
                avg_time = sum(times) / len(times)
                min_time = min(times)
                max_time = max(times)
                
                api_results[endpoint] = {
                    'avg_time': avg_time,
                    'min_time': min_time,
                    'max_time': max_time,
                    'status_code': response.status_code if 'response' in locals() else 'N/A'
                }
                
                print(f"  ✓ {endpoint}: avg {avg_time:.3f}s (min: {min_time:.3f}s, max: {max_time:.3f}s)")
                
            except Exception as e:
                print(f"  ✗ {endpoint}: Error - {str(e)}")
                api_results[endpoint] = {'error': str(e)}
        
        self.results['api'] = api_results
    
    def test_concurrent_requests(self):
        """Test performance under concurrent load"""
        print("⚡ Testing concurrent request performance...")
        
        def make_request(url):
            start_time = time.time()
            response = self.client.get(url)
            return {
                'time': time.time() - start_time,
                'status': response.status_code
            }
        
        # Test with 10 concurrent requests
        urls = ['/admin/dashboard/'] * 10
        
        start_time = time.time()
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, url) for url in urls]
            results = [future.result() for future in as_completed(futures)]
        
        total_time = time.time() - start_time
        avg_response_time = sum(r['time'] for r in results) / len(results)
        successful_requests = sum(1 for r in results if r['status'] == 200)
        
        self.results['concurrent'] = {
            'total_time': total_time,
            'avg_response_time': avg_response_time,
            'successful_requests': successful_requests,
            'total_requests': len(results)
        }
        
        print(f"  ✓ 10 concurrent requests: {total_time:.3f}s total")
        print(f"  ✓ Average response time: {avg_response_time:.3f}s")
        print(f"  ✓ Success rate: {successful_requests}/{len(results)}")
    
    def generate_report(self):
        """Generate performance report"""
        print("\n" + "="*60)
        print("📊 PERFORMANCE TEST REPORT")
        print("="*60)
        
        # Database Performance
        if 'database' in self.results:
            db = self.results['database']
            print(f"\n🔍 Database Performance:")
            print(f"  Simple Query Time: {db['simple_query_time']:.3f}s")
            print(f"  Optimized Query Time: {db['optimized_query_time']:.3f}s")
            print(f"  Count Query Time: {db['count_query_time']:.3f}s")
            print(f"  Total Queries: {db['total_queries']}")
        
        # Cache Performance
        if 'cache' in self.results:
            cache_data = self.results['cache']
            print(f"\n💾 Cache Performance:")
            print(f"  Cache Set Time: {cache_data['cache_set_time']:.6f}s")
            print(f"  Cache Get Time: {cache_data['cache_get_time']:.6f}s")
            print(f"  Complex Data Cache: {cache_data['cache_complex_time']:.6f}s")
        
        # View Performance
        if 'views' in self.results:
            print(f"\n🌐 View Performance:")
            for view_name, data in self.results['views'].items():
                improvement = data['improvement']
                print(f"  {view_name}: {data['cold_time']:.3f}s → {data['warm_time']:.3f}s ({improvement:.1f}% improvement)")
        
        # API Performance
        if 'api' in self.results:
            print(f"\n🔌 API Performance:")
            for endpoint, data in self.results['api'].items():
                if 'error' not in data:
                    print(f"  {endpoint}: {data['avg_time']:.3f}s average")
        
        # Concurrent Performance
        if 'concurrent' in self.results:
            conc = self.results['concurrent']
            print(f"\n⚡ Concurrent Performance:")
            print(f"  10 concurrent requests: {conc['total_time']:.3f}s")
            print(f"  Average response time: {conc['avg_response_time']:.3f}s")
            print(f"  Success rate: {conc['successful_requests']}/{conc['total_requests']}")
        
        # Performance Score
        self.calculate_performance_score()
    
    def calculate_performance_score(self):
        """Calculate overall performance score"""
        score = 100
        
        # Database performance (max -20 points)
        if 'database' in self.results:
            db_time = self.results['database']['optimized_query_time']
            if db_time > 0.1:  # > 100ms
                score -= min(20, (db_time - 0.1) * 100)
        
        # View performance (max -30 points)
        if 'views' in self.results:
            avg_warm_time = sum(v['warm_time'] for v in self.results['views'].values()) / len(self.results['views'])
            if avg_warm_time > 0.5:  # > 500ms
                score -= min(30, (avg_warm_time - 0.5) * 60)
        
        # API performance (max -25 points)
        if 'api' in self.results:
            api_times = [v['avg_time'] for v in self.results['api'].values() if 'avg_time' in v]
            if api_times:
                avg_api_time = sum(api_times) / len(api_times)
                if avg_api_time > 0.3:  # > 300ms
                    score -= min(25, (avg_api_time - 0.3) * 83)
        
        # Concurrent performance (max -25 points)
        if 'concurrent' in self.results:
            conc_time = self.results['concurrent']['avg_response_time']
            if conc_time > 1.0:  # > 1s
                score -= min(25, (conc_time - 1.0) * 25)
        
        score = max(0, score)
        
        print(f"\n🏆 Overall Performance Score: {score:.1f}/100")
        
        if score >= 90:
            print("   🎉 Excellent performance!")
        elif score >= 75:
            print("   ✅ Good performance")
        elif score >= 60:
            print("   ⚠️  Acceptable performance")
        else:
            print("   ❌ Performance needs improvement")
    
    def run_all_tests(self):
        """Run all performance tests"""
        print("🚀 Starting CLAS Performance Tests...")
        print("="*60)
        
        try:
            self.setup_test_user()
            self.test_database_performance()
            self.test_cache_performance()
            self.test_view_performance()
            self.test_api_performance()
            self.test_concurrent_requests()
            self.generate_report()
            
        except Exception as e:
            print(f"❌ Error during testing: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == '__main__':
    tester = PerformanceTester()
    tester.run_all_tests()
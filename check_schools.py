#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CLAS.settings')
django.setup()

from class.models import School

print("=" * 80)
print("SCHOOL DATABASE CHECK")
print("=" * 80)

# Count total schools
total = School.objects.count()
print(f"\nTotal Schools: {total}")

# Get unique districts
districts = School.objects.values_list('district', flat=True).distinct().order_by('district')
print(f"\nUnique Districts: {len(districts)}")
for d in districts[:10]:
    count = School.objects.filter(district__iexact=d).count()
    print(f"  - {d}: {count} schools")

# Get sample schools
print(f"\nSample Schools (first 5):")
for school in School.objects.all()[:5]:
    print(f"  {school.name}")
    print(f"    District: {school.district}, Block: {school.block}, State: {school.state}")
    print(f"    Coordinates: ({school.latitude}, {school.longitude})")
    print()

# Check schools with default coordinates
default_coords = School.objects.filter(latitude=28.7041, longitude=77.1025).count()
custom_coords = School.objects.exclude(latitude=28.7041, longitude=77.1025).count()
print(f"\nCoordinate Status:")
print(f"  - Schools with default coordinates: {default_coords}")
print(f"  - Schools with custom coordinates: {custom_coords}")

if custom_coords > 0:
    print(f"\n  Sample schools with custom coordinates:")
    for school in School.objects.exclude(latitude=28.7041, longitude=77.1025)[:3]:
        print(f"    {school.name}: ({school.latitude}, {school.longitude})")

print("\n" + "=" * 80)

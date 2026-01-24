# CLAS Platform - System Architecture Diagrams

## 1. High-Level System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                       │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  │  Admin Dashboard │  │Facilitator Dash. │  │Supervisor Dash.  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                        │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
│  │  Admin Views     │  │Facilitator Views │  │Supervisor Views  │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘
│  ┌──────────────────────────────────────────────────────────────┐
│  │  Services: Session Management, Calculations, Integrations   │
│  └──────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATA ACCESS LAYER                           │
│  ┌──────────────────────────────────────────────────────────────┐
│  │  Django ORM: Models, QuerySets, Prefetch, Select Related    │
│  └──────────────────────────────────────────────────────────────┘
│  ┌──────────────────────────────────────────────────────────────┐
│  │  Caching Layer: Local Memory Cache, Session Cache           │
│  └──────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                      DATABASE LAYER                              │
│  ┌──────────────────────────────────────────────────────────────┐
│  │  PostgreSQL (Neon): 31 Models, 300+ Fields, 20+ Indexes    │
│  └──────────────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────────────┘
```

## 2. Data Model Relationships

```
User (Admin, Facilitator, Supervisor)
  ├─ Role (Admin=0, Supervisor=1, Facilitator=2)
  └─ FacilitatorSchool
      └─ School
          ├─ ClassSection
          │   ├─ PlannedSession (Day 1-150)
          │   │   └─ ActualSession (When taught)
          │   │       └─ Attendance (Who attended)
          │   └─ Enrollment
          │       └─ Student
          └─ Cluster
```

## 3. Session Flow (Core Logic)

```
PLANNING PHASE (Admin):
┌─────────────────────────────────────────┐
│ Admin creates PlannedSession             │
│ - Day 1: Introduction                   │
│ - Day 2: Basic Concepts                 │
│ - Day 3: Advanced Topics                │
│ - ... Day 150                           │
└─────────────────────────────────────────┘
                    ↓
EXECUTION PHASE (Facilitator):
┌─────────────────────────────────────────┐
│ Facilitator sees "Today's Session"      │
│ Options:                                │
│ 1. Conduct Session                      │
│    → Creates ActualSession(CONDUCTED)   │
│    → Mark Attendance                    │
│ 2. Mark Holiday                         │
│    → Creates ActualSession(HOLIDAY)     │
│    → Skip to next day                   │
│ 3. Cancel Session                       │
│    → Creates ActualSession(CANCELLED)   │
│    → Skip to next day                   │
└─────────────────────────────────────────┘
                    ↓
AUTOMATIC PROGRESSION:
┌─────────────────────────────────────────┐
│ System finds lowest day_number with:    │
│ - PlannedSession exists                 │
│ - NO ActualSession record               │
│ → Shows as "Today's Session"            │
│                                         │
│ Result: Content never skipped,          │
│ dates are flexible                      │
└─────────────────────────────────────────┘
```

## 4. Admin Dashboard Query Flow (BEFORE - SLOW)

```
Admin Dashboard Request
    ↓
Query 1: SELECT * FROM school
    ↓
For each school (N schools):
    ├─ Query N+1: SELECT * FROM facilitator_school WHERE school_id = X
    ├─ Query N+2: SELECT * FROM class_section WHERE school_id = X
    │
    └─ For each class (M classes):
        ├─ Query N*M+1: SELECT * FROM planned_session WHERE class_id = X
        │
        └─ For each session (K sessions):
            ├─ Query N*M*K+1: SELECT * FROM actual_session WHERE session_id = X
            │
            └─ For each actual session (L records):
                └─ Query N*M*K*L+1: SELECT * FROM attendance WHERE session_id = X

Total Queries: 1 + N + N + N*M + N*M*K + N*M*K*L
Example: 1 + 10 + 10 + 100 + 1000 + 10000 = 11,121 queries
Time: 15-20 seconds
```

## 5. Admin Dashboard Query Flow (AFTER - FAST)

```
Admin Dashboard Request
    ↓
Query 1: SELECT * FROM school
    ↓
Query 2: SELECT * FROM facilitator_school WHERE is_active = true
    ↓
Query 3: SELECT * FROM class_section WHERE school_id IN (...)
    ↓
Query 4: SELECT * FROM planned_session WHERE class_id IN (...)
    ↓
Query 5: SELECT * FROM actual_session WHERE session_id IN (...)
    ↓
Query 6: SELECT * FROM attendance WHERE session_id IN (...)
    ↓
All data loaded in memory, template renders from cache

Total Queries: 6 (instead of 11,121)
Time: 2-3 seconds (85% faster)
```

## 6. Performance Bottleneck Analysis

```
BEFORE OPTIMIZATION:
┌─────────────────────────────────────────────────────────────┐
│ Admin Dashboard Load Time: 15-20 seconds                    │
├─────────────────────────────────────────────────────────────┤
│ Database Queries:        12-15 seconds (75%)                │
│ Template Rendering:      2-3 seconds (15%)                  │
│ Static Files:            500ms (5%)                         │
│ Browser Rendering:       1-2 seconds (5%)                   │
└─────────────────────────────────────────────────────────────┘

AFTER OPTIMIZATION:
┌─────────────────────────────────────────────────────────────┐
│ Admin Dashboard Load Time: 2-3 seconds                      │
├─────────────────────────────────────────────────────────────┤
│ Database Queries:        500ms (25%)                        │
│ Template Rendering:      500ms (25%)                        │
│ Static Files:            500ms (25%)                        │
│ Browser Rendering:       500ms (25%)                        │
└─────────────────────────────────────────────────────────────┘
```

## 7. Caching Strategy

```
Request comes in
    ↓
Check cache for role-based key
    ├─ Cache HIT (80% of time)
    │   └─ Return cached data (10ms)
    │
    └─ Cache MISS (20% of time)
        ├─ Query database (500ms)
        ├─ Calculate stats (100ms)
        ├─ Store in cache (10ms)
        └─ Return data (10ms)

Average Response Time: 0.8 * 10ms + 0.2 * 620ms = 132ms
Without Cache: 620ms
Improvement: 4.7x faster
```

## 8. Database Index Impact

```
WITHOUT INDEX:
SELECT * FROM attendance WHERE actual_session_id = 'xxx'
    ↓
Full table scan: 100,000 rows
    ↓
Time: 2-5 seconds

WITH INDEX:
SELECT * FROM attendance WHERE actual_session_id = 'xxx'
    ↓
Index lookup: O(log n)
    ↓
Time: 10-50ms

Improvement: 100-500x faster
```

## 9. Pagination Impact

```
WITHOUT PAGINATION:
Load 1000 students
    ├─ Database query: 500ms
    ├─ Template rendering: 2-3 seconds (1000 DOM elements)
    ├─ Browser rendering: 1-2 seconds
    └─ Total: 4-6 seconds

WITH PAGINATION (50 per page):
Load 50 students
    ├─ Database query: 50ms
    ├─ Template rendering: 100ms (50 DOM elements)
    ├─ Browser rendering: 200ms
    └─ Total: 350ms

Improvement: 10-15x faster
```

## 10. AJAX Lazy Loading Impact

```
WITHOUT LAZY LOADING:
Page Load
    ├─ Load all schools (500ms)
    ├─ Load all classes (500ms)
    ├─ Load all sessions (500ms)
    ├─ Load all students (500ms)
    └─ Total: 2 seconds

WITH LAZY LOADING:
Page Load
    ├─ Load schools list (100ms)
    └─ Total: 100ms
    
User clicks school
    ├─ Load classes via AJAX (200ms)
    └─ Total: 200ms
    
User clicks class
    ├─ Load sessions via AJAX (200ms)
    └─ Total: 200ms

Improvement: 10x faster initial load
```

## 11. Role-Based Access Control

```
User Login
    ↓
Check Role
    ├─ ADMIN (role_id = 0)
    │   └─ Redirect to /admin/dashboard/
    │       ├─ Can create schools
    │       ├─ Can create classes
    │       ├─ Can create sessions
    │       ├─ Can assign facilitators
    │       └─ Can view all reports
    │
    ├─ FACILITATOR (role_id = 2)
    │   └─ Redirect to /facilitator/dashboard/
    │       ├─ Can view assigned schools
    │       ├─ Can view assigned classes
    │       ├─ Can conduct sessions
    │       ├─ Can mark attendance
    │       └─ Can submit feedback
    │
    └─ SUPERVISOR (role_id = 1)
        └─ Redirect to /supervisor/dashboard/
            ├─ Can view all schools
            ├─ Can view all facilitators
            ├─ Can view session progress
            ├─ Can view attendance trends
            └─ Can generate reports
```

## 12. Optimization Priority Matrix

```
┌─────────────────────────────────────────────────────────────┐
│                    EFFORT vs IMPACT                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  HIGH IMPACT                                               │
│  │                                                         │
│  │  ┌─ Add Indexes (50% improvement, 10 min)             │
│  │  │  ┌─ Fix N+1 Queries (40% improvement, 30 min)     │
│  │  │  │  ┌─ Implement Caching (30% improvement, 20 min)
│  │  │  │  │  ┌─ Paginate Lists (20% improvement, 15 min)
│  │  │  │  │  │  ┌─ AJAX Loading (25% improvement, 20 min)
│  │  │  │  │  │  │
│  └──┴──┴──┴──┴──┴─ LOW EFFORT
│
│  LOW IMPACT
│
└─────────────────────────────────────────────────────────────┘

Recommended Order:
1. Add Indexes (Quick win)
2. Fix N+1 Queries (Biggest impact)
3. Implement Caching (Sustained improvement)
4. Paginate Lists (Better UX)
5. AJAX Loading (Polish)
```

## 13. Expected Timeline

```
Week 1: Database Optimization
├─ Day 1-2: Add indexes
├─ Day 3: Run migrations
└─ Day 4-5: Verify and test

Week 2: Query Optimization
├─ Day 1-2: Fix admin views
├─ Day 3: Fix facilitator views
├─ Day 4: Fix supervisor views
└─ Day 5: Test and verify

Week 3: Caching Strategy
├─ Day 1-2: Implement caching
├─ Day 3: Add cache invalidation
├─ Day 4: Test cache hit rates
└─ Day 5: Monitor and adjust

Week 4: Frontend Optimization
├─ Day 1-2: Implement pagination
├─ Day 2-3: Add AJAX loading
├─ Day 4: Fix static files
└─ Day 5: Performance testing

Week 5: Testing & Deployment
├─ Day 1-2: Load testing
├─ Day 3: Performance monitoring
├─ Day 4: User acceptance testing
└─ Day 5: Production deployment
```

---

**Generated:** January 24, 2026  
**Status:** Ready for Implementation

# RBAC Optimization Strategies

## Current RBAC Issues Analysis

### 1. Database Query Problems

**Critical Finding**: Every permission check potentially triggers database queries!

**Current Flow per API Request**:
```
API Request → JWT Verification (50-100ms) → Permission Check → Database Query (if cache miss)
```

**Permission Check Locations Found**:
- `courses/views.py`: 9 permission checks
- `media_library/views.py`: Multiple permission checks  
- `courses/views_content.py`: Content management permissions
- `accounts/views_permissions.py`: Admin permission checks

### 2. Cache Performance Analysis

**Current Caching**: 
- **Cache Duration**: 5 minutes per user
- **Cache Key**: `user_permissions:{user_id}`
- **Cache Hit Rate**: Unknown (no metrics)
- **Cache Miss Impact**: 20-50ms database query

**Database Query on Cache Miss**:
```python
# accounts/permissions.py:156-159
user_profile = UserProfile.objects.get(supabase_user_id=user_id)
user_roles = UserRole.objects.filter(user=user_profile)\
    .select_related('role').filter(role__is_active=True)
```

**Problem**: Missing `prefetch_related('role__permissions')` - potential N+1 query

## Optimization Strategies

### Strategy 1: Smart Permission Caching

#### 1.1 Multi-Level Cache Architecture
```
Level 1: Request Cache (in-memory, per request)
Level 2: Redis Cache (5-15 minutes)  
Level 3: Database (optimized queries)
```

#### 1.2 Intelligent Cache Warming
**Proactive Approach**: Pre-load permissions for active users
```python
# Warm cache for users with recent activity
def warm_permission_cache():
    active_users = UserProfile.objects.filter(
        last_login__gte=timezone.now() - timedelta(hours=24)
    ).values_list('supabase_user_id', flat=True)
    
    for user_id in active_users:
        PermissionService.get_user_permissions(user_id)
```

#### 1.3 Event-Driven Cache Invalidation
**Trigger Scenarios**:
- User role assignment/removal
- Role permission changes
- User status changes (active/inactive)

### Strategy 2: Permission Pre-Loading

#### 2.1 Middleware-Level Permission Loading
**Instead of**: Multiple permission checks per request
**Do**: Load all permissions once in middleware

```python
class OptimizedAuthMiddleware:
    def __call__(self, request):
        if user_id:
            # Load all user permissions and roles once
            request.user_permissions = self.get_cached_permissions(user_id)
            request.user_roles = self.get_cached_roles(user_id)
```

#### 2.2 View-Level Optimization
**Before**:
```python
if not PermissionService.has_permission(request.user_id, 'course:create'):
    return Response({'error': 'Permission denied'}, status=403)
if not PermissionService.has_permission(request.user_id, 'course:publish'):
    return Response({'error': 'Permission denied'}, status=403)
```

**After**:
```python
# Permissions already loaded in middleware
if 'course:create' not in request.user_permissions:
    return Response({'error': 'Permission denied'}, status=403)
```

### Strategy 3: Database Query Optimization

#### 3.1 Fix N+1 Permission Queries
**Current Problem**:
```python
# This may cause N+1 queries for role permissions
for user_role in user_roles:
    role_permissions = user_role.role.permissions or []
    permissions.update(role_permissions)
```

**Optimized Solution**:
```python
# Single query with prefetch_related
user_roles = UserRole.objects.filter(user=user_profile)\
    .select_related('role')\
    .prefetch_related('role')\
    .filter(role__is_active=True)

# All permissions loaded in single query
permissions = set()
for user_role in user_roles:
    permissions.update(user_role.role.permissions or [])
```

#### 3.2 Role-Permission Denormalization
**Strategy**: Store flattened permissions for faster access

```python
# Add computed field to UserProfile
class UserProfile(models.Model):
    # ... existing fields
    cached_permissions = models.JSONField(default=list)
    permissions_updated_at = models.DateTimeField(auto_now=True)
    
    def refresh_cached_permissions(self):
        # Update cached permissions when roles change
        pass
```

### Strategy 4: Advanced Caching Patterns

#### 4.1 Permission Hierarchy Caching
**Concept**: Cache permission inheritance chains

```python
# Cache permission inheritance for complex role structures
{
    "super_admin": ["*"],  # All permissions
    "admin": ["user:*", "course:*", "analytics:view"],
    "instructor": ["course:create", "course:update", "media:upload"]
}
```

#### 4.2 Time-Based Cache Refresh
**Strategy**: Different cache TTLs based on data volatility

```python
CACHE_DURATIONS = {
    'user_permissions': 900,      # 15 minutes (changes rarely)
    'user_roles': 1800,           # 30 minutes (changes very rarely)
    'role_permissions': 3600,     # 1 hour (admin changes only)
}
```

#### 4.3 Conditional Cache Invalidation
**Smart Invalidation**: Only clear cache when needed

```python
def on_role_assignment_change(user_id, old_roles, new_roles):
    # Only invalidate if permissions actually changed
    old_permissions = get_permissions_for_roles(old_roles)
    new_permissions = get_permissions_for_roles(new_roles)
    
    if old_permissions != new_permissions:
        PermissionService.clear_user_permissions_cache(user_id)
```

## Implementation Roadmap

### Phase 1: Critical Performance Fixes (Week 1)

#### Day 1-2: Database Query Optimization
- [ ] Fix N+1 queries in `PermissionService.get_user_permissions()`
- [ ] Add `prefetch_related` for role permissions
- [ ] Add database indexes for permission queries

#### Day 3-4: Enhanced Caching
- [ ] Implement request-level permission caching
- [ ] Add cache metrics and monitoring
- [ ] Implement cache warming for active users

#### Day 5: Middleware Optimization
- [ ] Pre-load permissions in auth middleware
- [ ] Remove redundant permission checks in views
- [ ] Add performance logging

### Phase 2: Advanced Optimization (Week 2)

#### Day 1-3: Smart Cache Management
- [ ] Implement event-driven cache invalidation
- [ ] Add role-based cache TTL strategies
- [ ] Implement permission hierarchy caching

#### Day 4-5: Performance Monitoring
- [ ] Add permission check performance metrics
- [ ] Implement cache hit rate monitoring
- [ ] Create performance dashboards

### Phase 3: Architecture Refinement (Week 3)

#### Day 1-3: Denormalization Strategy
- [ ] Add cached permissions field to UserProfile
- [ ] Implement permission refresh triggers
- [ ] Migration strategy for existing data

#### Day 4-5: Advanced Features
- [ ] Implement permission inheritance
- [ ] Add bulk permission operations
- [ ] Performance testing and optimization

## Performance Metrics & Goals

### Current Baseline
- **Permission Check Time**: 1-50ms (depending on cache hit/miss)
- **Database Queries per Request**: 0-1 (if cache miss)
- **Cache Hit Rate**: Unknown
- **Permission-Related API Overhead**: 10-100ms

### Target Performance
- **Permission Check Time**: <1ms (90th percentile)
- **Database Queries per Request**: <0.01 (99% cache hit rate)
- **Cache Hit Rate**: >99%
- **Permission-Related API Overhead**: <2ms

### Key Metrics to Monitor
1. **Cache Performance**
   - Hit rate for user permissions
   - Cache warming effectiveness
   - Cache invalidation frequency

2. **Database Performance**
   - Permission-related query count
   - Query execution time
   - Connection pool usage

3. **API Performance**
   - Auth middleware execution time
   - Permission check latency
   - End-to-end request time

## Risk Assessment & Mitigation

### High-Risk Areas
1. **Cache Consistency**: Risk of serving stale permissions
2. **Cache Failure**: Redis unavailability affecting performance
3. **Permission Bypass**: Caching bugs causing security issues

### Mitigation Strategies
1. **Cache Consistency**
   - Implement cache versioning
   - Add checksum validation
   - Periodic cache validation against database

2. **Cache Failure Handling**
   - Graceful degradation to database queries
   - Circuit breaker pattern
   - Cache health monitoring

3. **Security Safeguards**
   - Permission audit logging
   - Cache validation in critical paths
   - Regular security testing

## Success Criteria

### Performance Goals
- [ ] **95% reduction** in permission-related database queries
- [ ] **Sub-1ms** permission check time (90th percentile)
- [ ] **99%** cache hit rate for permission checks
- [ ] **50ms reduction** in average API response time

### Reliability Goals
- [ ] **Zero** permission bypass incidents
- [ ] **99.9%** cache availability
- [ ] **<100ms** cache recovery time

### Operational Goals
- [ ] **Real-time** permission change propagation
- [ ] **Automated** cache warming
- [ ] **Complete** performance monitoring

This RBAC optimization strategy directly addresses your concern about database queries on every API request and provides a comprehensive path to eliminate the performance bottleneck while maintaining security and reliability.
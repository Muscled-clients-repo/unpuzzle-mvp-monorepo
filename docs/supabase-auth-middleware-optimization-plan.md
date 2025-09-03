# Supabase Auth Middleware & RBAC Optimization Plan

## Current Architecture Analysis

### 1. Authentication Flow Issues

**Current Process per Request:**
1. **Supabase Auth Middleware** (`app/middleware/supabase_auth.py:78-84`)
   - JWT token extraction from cookies/headers
   - JWT verification with Supabase secret (50-100ms per request)
   - User ID extraction from payload
   - **Issue**: JWT verification happens on EVERY protected request

2. **Permission System** (`accounts/permissions.py:149-172`)
   - Database query to get UserProfile by `supabase_user_id`
   - Join query to UserRole and Role tables with `select_related`
   - Permission aggregation from multiple roles
   - **Current Caching**: 5 minutes per user

### 2. Performance Bottlenecks Identified

#### Critical Issues:

1. **JWT Verification Overhead**: 50-100ms per request
   - Cryptographic operations on every request
   - No JWT token caching/validation optimization

2. **Database Queries on Permission Checks**: 
   - Found **9 endpoints** using `PermissionService.has_permission()`
   - Each permission check triggers the cached permission lookup
   - Cache misses result in database queries

3. **Inefficient Permission Query**:
   ```python
   # accounts/permissions.py:156-159
   user_roles = UserRole.objects.filter(user=user_profile)\
       .select_related('role').filter(role__is_active=True)
   ```
   - Missing `prefetch_related` optimization

#### Current Performance Impact:
- **JWT Verification**: 50-100ms per request
- **Permission Check** (cache hit): ~1-2ms
- **Permission Check** (cache miss): 20-50ms (database query)
- **Total Auth Overhead**: 51-150ms per protected request

## Optimization Plan

### Phase 1: JWT Optimization (Immediate - High Impact)

#### 1.1 JWT Token Caching
**Problem**: JWT verification happens on every request
**Solution**: Cache verified JWT tokens

**Implementation Strategy**:
```python
# Cache verified JWT tokens for their remaining lifetime
cache_key = f"jwt_verified:{token_hash}"
user_payload = cache.get(cache_key)
if not user_payload:
    # Verify JWT and cache until expiry
    payload = jwt.decode(...)
    ttl = payload['exp'] - int(time.time())
    cache.set(cache_key, payload, ttl)
```

**Expected Gain**: 45-95ms reduction per request

#### 1.2 Smart JWT Re-verification
**Implementation**: Only re-verify JWT if:
- Token not in cache
- Token expires within 5 minutes (for refresh)
- User permissions changed (cache invalidation)

### Phase 2: Permission System Optimization (Immediate - High Impact)

#### 2.1 Enhanced Permission Caching
**Current**: 5-minute cache per user
**Optimization**: Multi-level caching strategy

**Implementation**:
```python
# Level 1: In-memory request cache (for same request multiple checks)
# Level 2: Redis cache with smart invalidation
# Level 3: Database with optimized queries
```

#### 2.2 Batch Permission Loading
**Current**: Individual permission checks per endpoint
**Optimization**: Load all user permissions in middleware

**Strategy**:
```python
# In middleware, after JWT verification:
request.user_permissions = PermissionService.get_user_permissions(user_id)
request.user_roles = PermissionService.get_user_roles(user_id)

# In views, use cached data:
if 'course:create' in request.user_permissions:
    # Allow access
```

#### 2.3 Database Query Optimization
**Fix N+1 Query in Permission Loading**:
```python
# Current inefficient query
user_roles = UserRole.objects.filter(user=user_profile)\
    .select_related('role').filter(role__is_active=True)

# Optimized query
user_roles = UserRole.objects.filter(user=user_profile)\
    .select_related('role')\
    .prefetch_related('role__permissions')\
    .filter(role__is_active=True)
```

### Phase 3: Advanced Caching Strategies (Medium Priority)

#### 3.1 Permission Matrix Caching
**Strategy**: Cache entire user-permission matrix

```python
# Cache structure
{
  "user:123": {
    "roles": ["instructor", "student"],
    "permissions": ["course:create", "course:read", ...],
    "cached_at": "2024-01-01T12:00:00Z",
    "expires_at": "2024-01-01T12:15:00Z"
  }
}
```

#### 3.2 Role-Based Cache Invalidation
**Implementation**: When roles change, invalidate specific user caches

```python
def invalidate_user_permissions(user_id: str):
    # Clear JWT cache
    # Clear permission cache  
    # Clear role cache
    # Trigger cache warming for active users
```

#### 3.3 Warm Cache Strategy
**For High-Traffic Users**: Pre-load permissions for active users

### Phase 4: Middleware Restructure (Long-term)

#### 4.1 Combined Auth Middleware
**Current**: Separate JWT and permission checks
**Optimized**: Single middleware handling both

```python
class OptimizedSupabaseAuthMiddleware:
    def __call__(self, request):
        # 1. Check if route needs auth
        # 2. Extract & verify JWT (with caching)
        # 3. Load user permissions (with caching)
        # 4. Attach to request object
        # 5. Continue to view
```

#### 4.2 Route-Level Permission Declaration
**Instead of**: Permission checks in every view
**Use**: Decorator-based permission requirements

```python
@api_view(['POST'])
@require_permissions(['course:create'])
def create_course(request):
    # Permission already verified by middleware
    # No need for additional checks
```

## Implementation Priority & Timeline

### Week 1: Critical Path (80% Performance Gain)
1. ✅ **JWT Token Caching** (2 days)
   - Expected: 45-95ms reduction per request
2. ✅ **Permission Query Optimization** (1 day)
   - Fix N+1 queries in permission loading
3. ✅ **Batch Permission Loading in Middleware** (2 days)
   - Load permissions once per request

### Week 2: Advanced Optimization (15% Additional Gain)
4. ✅ **Permission Matrix Caching** (3 days)
   - Implement multi-level caching
5. ✅ **Smart Cache Invalidation** (2 days)
   - Role change triggers cache updates

### Week 3: Architecture Refinement (5% Additional Gain)
6. ✅ **Middleware Restructure** (3 days)
   - Combined auth middleware
7. ✅ **Route-Level Permissions** (2 days)
   - Decorator-based approach

## Expected Performance Improvements

### Current Performance:
- **JWT Verification**: 50-100ms
- **Permission Check**: 1-50ms (depending on cache)
- **Total Auth Overhead**: 51-150ms per request

### After Optimization:
- **JWT Verification** (cached): 1-5ms
- **Permission Check** (pre-loaded): 0.1-1ms
- **Total Auth Overhead**: 1-6ms per request

### **Performance Gain: 88-96% reduction in auth overhead**

## Security Considerations

### 1. JWT Cache Security
- Use secure token hashing for cache keys
- Implement cache encryption for sensitive payloads
- Proper TTL management based on token expiry

### 2. Permission Cache Integrity
- Atomic cache updates for role changes
- Cache versioning to prevent stale permission data
- Audit logging for permission changes

### 3. Cache Invalidation Security
- Immediate invalidation on role revocation
- Secure cache key generation
- Protection against cache timing attacks

## Monitoring & Metrics

### Performance Metrics to Track:
1. **Auth Middleware Response Time**
   - Before: 51-150ms
   - Target: <6ms (90th percentile)

2. **Cache Hit Rates**
   - JWT Cache: Target >95%
   - Permission Cache: Target >98%

3. **Database Query Reduction**
   - Permission queries: Target 90% reduction

### Alerts & Monitoring:
- Cache miss rate spikes
- Auth middleware latency increases
- Permission check failures

## Risk Mitigation

### 1. Cache Failure Handling
- Graceful degradation to database queries
- Circuit breaker pattern for cache dependencies
- Health checks for Redis connectivity

### 2. Gradual Rollout Strategy
- Feature flags for each optimization phase
- A/B testing for performance validation
- Rollback procedures for each component

### 3. Security Validation
- JWT signature validation remains intact
- Permission enforcement stays consistent
- Audit trail for all auth decisions

## Success Metrics

### Performance Goals:
- **95% reduction** in auth overhead
- **Sub-6ms** auth processing time
- **90% reduction** in auth-related database queries

### Reliability Goals:
- **99.9%** auth cache availability
- **Zero** permission bypass incidents
- **<1 second** cache warm-up time

This optimization plan addresses your core concern about database queries on every API request and provides a comprehensive approach to dramatically improve authentication and authorization performance while maintaining security.
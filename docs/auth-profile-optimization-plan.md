# Auth Profile Endpoint Optimization Plan

## 🚨 Performance Problem Analysis

### Current Issue Identified:
- **Endpoint**: `GET /api/v1/auth/profile/`
- **Current Performance**: 511ms response time
- **Target Performance**: <50ms response time
- **Performance Goal**: 90%+ improvement

## 🔍 Root Cause Analysis

### 1. **Current Implementation Issues:**

**File**: `apps/backend/accounts/views.py` - `get_profile()` function
```python
def get_profile(request):
    try:
        profile = UserProfile.objects.get(supabase_user_id=user_id)
        return Response(UserProfileSerializer(profile).data, status=status.HTTP_200_OK)
```

### 2. **Identified Performance Bottlenecks:**

#### **A. Database Query Issues (Major Impact: 400-500ms)**
1. **No Caching**: Every request hits the database
2. **Potential N+1 Queries**: UserProfile model has multiple related objects:
   - `subscription` (UserSubscription model)
   - `user_roles` (UserRole relationships) 
   - `sessions` (Session records)
   - `subscription_history` (audit trails)

#### **B. Serializer Performance Issues (Minor Impact: 10-50ms)**
1. **UserProfileSerializer includes many fields** (16+ fields)
2. **Property-based fields trigger additional queries**:
   - `subscription_plan` - queries subscription.plan_id
   - `subscription_status` - queries subscription.status
   - `subscription_display_name` - queries subscription.plan.display_name
   - `ai_daily_limit` - queries subscription.plan.ai_daily_limit
   - Multiple subscription-related properties

#### **C. Related Model Queries (Major Impact: 50-200ms)**
UserProfile properties that trigger database queries:
```python
@property
def subscription_plan(self):
    if hasattr(self, 'subscription') and self.subscription.is_active():
        return self.subscription.plan_id  # Database query!
```

### 3. **Query Analysis:**
**Estimated Queries Per Request:**
- Base UserProfile query: 1 query
- Subscription data: 1-2 queries  
- Subscription plan details: 1 query
- User roles (if accessed): 1-2 queries
- **Total**: 4-6 database queries per profile request

## 📋 Optimization Plan

### **Phase 1: Immediate Performance Fixes (Expected: 60-80% improvement)**

#### **1.1 User Profile Caching**
**Strategy**: Cache the complete serialized user profile data

**Implementation**:
```python
def get_profile(request):
    user_id = request.user_id
    cache_key = f"user_profile:{user_id}"
    
    # Try cache first
    cached_profile = cache.get(cache_key)
    if cached_profile:
        return Response(cached_profile, status=200)
    
    # Database fallback with optimized query
    profile = UserProfile.objects.select_related('subscription', 'subscription__plan')\
        .prefetch_related('user_roles__role').get(supabase_user_id=user_id)
    
    profile_data = UserProfileSerializer(profile).data
    
    # Cache for 15 minutes
    cache.set(cache_key, profile_data, 900)
    return Response(profile_data, status=200)
```

**Expected Impact**: 400-450ms → 50-100ms (80-90% improvement)

#### **1.2 Database Query Optimization**
**Fix N+1 Queries with Proper Prefetching**:

```python
# Optimized query to load all related data in one go
profile = UserProfile.objects.select_related(
    'subscription',
    'subscription__plan'
).prefetch_related(
    'user_roles__role',
    'sessions'
).get(supabase_user_id=user_id)
```

**Expected Impact**: 4-6 queries → 1-2 queries (60-80% query reduction)

#### **1.3 Serializer Optimization**
**Create Cached-Optimized Serializer**:

```python
class FastUserProfileSerializer(serializers.ModelSerializer):
    """Optimized serializer for cached profile data"""
    
    # Pre-compute expensive fields to avoid property calls
    subscription_data = serializers.SerializerMethodField()
    
    def get_subscription_data(self, obj):
        """Get all subscription data in one method to avoid multiple property calls"""
        if hasattr(obj, 'subscription') and obj.subscription:
            return {
                'plan': obj.subscription.plan_id,
                'status': obj.subscription.status,
                'display_name': obj.subscription.plan.display_name if obj.subscription.plan else 'Free',
                'features': obj.subscription.plan.features if obj.subscription.plan else {},
            }
        return {
            'plan': 'free',
            'status': 'free', 
            'display_name': 'Free Plan',
            'features': {}
        }
```

### **Phase 2: Advanced Caching Strategy (Expected: Additional 10-15% improvement)**

#### **2.1 Multi-Level Caching**
```
Level 1: In-Memory Request Cache (0.1ms) - For multiple profile calls in same request
Level 2: Redis Cache (1-5ms) - 15-minute TTL
Level 3: Database (50-100ms) - Optimized queries
```

#### **2.2 Smart Cache Invalidation**
**Triggers for cache invalidation**:
- Profile updates via `update_profile()` endpoint
- Subscription changes (via signals)
- Role assignments/removals
- Manual cache clearing for admin operations

**Implementation via Django Signals**:
```python
@receiver(post_save, sender=UserProfile)
def clear_profile_cache(sender, instance, **kwargs):
    cache_key = f"user_profile:{instance.supabase_user_id}"
    cache.delete(cache_key)

@receiver(post_save, sender=UserSubscription) 
def clear_user_profile_on_subscription_change(sender, instance, **kwargs):
    cache_key = f"user_profile:{instance.user.supabase_user_id}"
    cache.delete(cache_key)
```

#### **2.3 Profile Data Warming**
**Proactive cache warming for active users**:
```python
def warm_profile_cache_for_active_users():
    """Warm cache for users who were active in last 24h"""
    active_users = UserProfile.objects.filter(
        last_login__gte=timezone.now() - timedelta(hours=24)
    ).values_list('supabase_user_id', flat=True)
    
    for user_id in active_users:
        # Pre-load profile data into cache
        get_profile_data(user_id)
```

### **Phase 3: Architecture Improvements (Long-term)**

#### **3.1 Profile Data Denormalization**
**Add computed fields to UserProfile model**:
```python
class UserProfile(TimeStampedModel):
    # ... existing fields
    
    # Denormalized fields for fast access
    cached_subscription_data = models.JSONField(default=dict)
    cached_roles_data = models.JSONField(default=list)
    profile_cache_updated_at = models.DateTimeField(auto_now=True)
```

#### **3.2 Background Profile Updates**
**Async profile enrichment**:
- Update subscription data via background tasks
- Real-time updates through WebSockets for UI
- Batch profile updates during low-traffic periods

## 📊 Expected Performance Improvements

### **Performance Targets**:

| Metric | Before | After Phase 1 | After Phase 2 | After Phase 3 |
|--------|--------|---------------|---------------|---------------|
| **Response Time** | 511ms | 50-100ms | 30-50ms | 10-30ms |
| **Cache Hit Rate** | 0% | 85-90% | 95-98% | 98-99% |
| **DB Queries** | 4-6 queries | 1-2 queries | 0.1 queries | 0.05 queries |
| **Overall Improvement** | Baseline | 80-90% | 90-94% | 94-98% |

### **Expected Results Summary**:
- **Phase 1**: 511ms → 50-100ms (80-90% improvement)
- **Phase 2**: 50-100ms → 30-50ms (additional 40-70% improvement)  
- **Phase 3**: 30-50ms → 10-30ms (additional 60-80% improvement)

**Total Expected Improvement: 94-98% faster profile loading**

## 🔧 Implementation Plan

### **Week 1: Critical Performance Fixes**

#### **Day 1-2: Database Query Optimization**
- [ ] Add `select_related` and `prefetch_related` to profile query
- [ ] Test query performance improvements
- [ ] Validate no breaking changes in data structure

#### **Day 3-4: Basic Profile Caching**
- [ ] Implement Redis-based profile caching
- [ ] 15-minute cache TTL with manual invalidation
- [ ] Add cache hit/miss logging for monitoring

#### **Day 5: Cache Invalidation**
- [ ] Implement Django signals for cache invalidation
- [ ] Test cache invalidation on profile updates
- [ ] Add monitoring for cache effectiveness

### **Week 2: Advanced Optimizations**

#### **Day 1-2: Serializer Optimization**
- [ ] Create `FastUserProfileSerializer` 
- [ ] Optimize subscription data loading
- [ ] Performance testing and validation

#### **Day 3-4: Multi-Level Caching**
- [ ] Request-level caching implementation
- [ ] Cache warming for active users
- [ ] Performance metrics and monitoring

#### **Day 5: Load Testing & Validation**
- [ ] Load test optimized endpoint
- [ ] Validate 90%+ performance improvement
- [ ] Monitor production metrics

### **Week 3: Architecture Improvements**
- [ ] Profile data denormalization (if needed)
- [ ] Background profile updates
- [ ] Advanced monitoring and alerting

## 🛡️ Security & Compatibility Considerations

### **Security Maintained**:
- ✅ **Authentication required** - All profile access still requires valid JWT
- ✅ **User isolation** - Cache keys include user_id to prevent data leakage
- ✅ **Data integrity** - Cache invalidation ensures data consistency
- ✅ **Audit trail** - All profile changes logged and tracked

### **Backward Compatibility**:
- ✅ **Response format unchanged** - Existing frontend code works as-is
- ✅ **API endpoints unchanged** - Same URLs and request formats
- ✅ **Error handling preserved** - Same error responses for edge cases
- ✅ **Graceful degradation** - System works if cache fails

### **Risk Mitigation**:
1. **Cache Failure Handling**: Automatic fallback to database queries
2. **Data Consistency**: Smart invalidation on profile changes
3. **Memory Management**: Cache size limits and TTL management
4. **Monitoring**: Performance metrics and alerting

## 📈 Success Metrics

### **Performance KPIs**:
- [ ] **90%+ response time improvement** (511ms → <50ms)
- [ ] **95%+ cache hit rate** for profile requests
- [ ] **80%+ database query reduction** 
- [ ] **Zero** data consistency issues

### **User Experience KPIs**:
- [ ] **Sub-50ms** profile loading (perceived as instant)
- [ ] **Zero** breaking changes for frontend
- [ ] **Real-time** profile updates after changes
- [ ] **Improved** overall app responsiveness

### **System KPIs**:
- [ ] **Reduced database load** on profile table
- [ ] **Lower server CPU usage** for profile requests
- [ ] **Improved cache utilization** metrics
- [ ] **Better system scalability** under load

## 🚀 Expected Business Impact

### **User Experience**:
- **Instant profile loading** instead of 500ms+ delays
- **Improved app responsiveness** and perceived performance
- **Better user satisfaction** and reduced bounce rates

### **System Performance**:
- **90% reduction in database load** for profile requests
- **Improved server capacity** to handle more concurrent users
- **Better scalability** for growth in user base

### **Development Benefits**:
- **Faster development cycles** with optimized profile loading
- **Better performance monitoring** and debugging capabilities
- **Improved system reliability** and predictability

---

## ✅ **Ready for Implementation**

This optimization plan provides a clear path to achieve **90%+ performance improvement** for the auth profile endpoint while maintaining all security, compatibility, and functionality requirements.

**Request for Approval**: Please review this plan and approve implementation of Phase 1 optimizations to achieve immediate 80-90% performance improvement for the `/api/v1/auth/profile/` endpoint.
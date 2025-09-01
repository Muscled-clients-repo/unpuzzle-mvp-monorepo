# Database Architecture Improvements

## Current Issues

### 1. **Model Architecture Problems**
- No base model class for shared functionality
- Inconsistent field naming (snake_case vs camelCase in to_dict)
- Business logic mixed with data models
- Missing soft delete across all models
- No audit trail for tracking changes

### 2. **Database Design Issues**
- Missing critical indexes for performance
- Overuse of JSON columns for structured data
- No database constraints for data integrity
- Missing cascade delete configurations
- No version control for optimistic locking

### 3. **Code Organization Problems**
- Models too large (500+ lines in single files)
- No separation between entities and value objects
- Missing repository pattern abstraction
- No domain events for business logic

## Recommended Architecture

### 1. **Base Model Classes**
```python
# app/models/base.py
- BaseModel: Common fields (id, timestamps, soft delete)
- AuditableModel: Adds audit trail (created_by, updated_by)
- VersionedModel: Adds optimistic locking
```

### 2. **Model Organization**
```
app/
├── models/
│   ├── base.py          # Base classes and mixins
│   ├── user/
│   │   ├── __init__.py
│   │   ├── user.py       # User entity
│   │   ├── role.py       # Role and Permission
│   │   └── session.py    # UserSession, UserActivity
│   ├── course/
│   │   ├── __init__.py
│   │   ├── course.py     # Course entity
│   │   ├── video.py      # Video entity
│   │   ├── progress.py   # Progress tracking
│   │   └── quiz.py       # Quiz and attempts
│   └── learning/
│       ├── __init__.py
│       ├── enrollment.py
│       ├── review.py
│       └── ai_chat.py
```

### 3. **Repository Pattern**
```python
# app/repositories/base.py
class BaseRepository:
    def get_by_id(id: str)
    def get_all(filters, pagination)
    def create(data)
    def update(id, data)
    def delete(id)  # Soft delete
    def hard_delete(id)  # Permanent delete
```

### 4. **Service Layer**
```python
# app/services/base.py
class BaseService:
    def __init__(self, repository):
        self.repository = repository
    
    # Business logic methods
```

### 5. **Database Improvements**

#### Add Missing Indexes:
```sql
-- User indexes
CREATE INDEX idx_user_email_status ON users(email, status);
CREATE INDEX idx_user_created_at ON users(created_at DESC);

-- Course indexes  
CREATE INDEX idx_course_rating ON courses(rating DESC);
CREATE INDEX idx_course_enrollment ON courses(enrollment_count DESC);

-- Progress indexes
CREATE INDEX idx_video_progress_completed ON video_progress(completed, user_id);
```

#### Add Database Constraints:
```sql
-- Check constraints
ALTER TABLE courses ADD CONSTRAINT chk_course_rating CHECK (rating >= 0 AND rating <= 5);
ALTER TABLE courses ADD CONSTRAINT chk_course_price CHECK (price >= 0);

-- Unique constraints
ALTER TABLE enrollments ADD CONSTRAINT uq_user_course UNIQUE(user_id, course_id);
```

### 6. **Clean Model Example**

```python
# app/models/course/course.py
from app.models.base import AuditableModel
from app.models.course.value_objects import DifficultyLevel, CourseStatus

class Course(AuditableModel):
    __tablename__ = "courses"
    
    # Fields definition only
    title = Column(String(255), nullable=False, index=True)
    # ... other fields
    
    # Relationships
    instructor = relationship("User", back_populates="taught_courses")
    
    # NO business logic here - moved to services
```

### 7. **Value Objects**
```python
# app/models/course/value_objects.py
from dataclasses import dataclass

@dataclass(frozen=True)
class Price:
    amount: float
    currency: str = "USD"
    
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("Price cannot be negative")
```

### 8. **Domain Events**
```python
# app/events/course_events.py
class CoursePublished:
    def __init__(self, course_id: str, instructor_id: str):
        self.course_id = course_id
        self.instructor_id = instructor_id
        self.occurred_at = datetime.now(timezone.utc)
```

## Implementation Priority

### Phase 1: Foundation (Week 1)
1. Create base model classes with mixins
2. Add soft delete to all models
3. Implement audit trail
4. Add missing database indexes

### Phase 2: Refactoring (Week 2)
1. Split large model files
2. Extract business logic to services
3. Implement repository pattern
4. Standardize field naming

### Phase 3: Enhancement (Week 3)
1. Add value objects for complex types
2. Implement domain events
3. Add optimistic locking
4. Create database migration scripts

## Benefits

1. **Maintainability**: Clear separation of concerns
2. **Performance**: Proper indexing and query optimization
3. **Scalability**: Repository pattern allows easy caching
4. **Testability**: Business logic in services is easier to test
5. **Consistency**: Standardized patterns across all models
6. **Auditability**: Complete audit trail for compliance

## Migration Strategy

1. Create new base classes without breaking existing code
2. Gradually migrate models to inherit from base classes
3. Move business logic to services incrementally
4. Add indexes without downtime using concurrent builds
5. Test thoroughly in staging environment

## Monitoring

- Track query performance before/after indexes
- Monitor soft delete vs hard delete usage
- Audit trail completeness metrics
- Version conflict frequency (optimistic locking)
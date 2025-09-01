# Architecture Decision: Authentication Strategy

## Current Problem
You're using two databases:
1. Supabase (for auth) - requires SQL/API calls
2. Local PostgreSQL (for data) - uses SQLAlchemy ORM

This creates unnecessary complexity.

## Recommended Solution: Local Auth with SQLAlchemy

Since you prefer ORM over SQL, implement authentication locally:

### Benefits:
- ✅ Everything in one database
- ✅ Use SQLAlchemy ORM throughout
- ✅ No SQL needed
- ✅ No synchronization issues
- ✅ Full control over auth logic

### Implementation:

```python
# models/user.py
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import Column, String, DateTime, Boolean
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="student")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

# services/auth_service.py
from app.models.user import User
import jwt

class LocalAuthService:
    def signup(self, email, password):
        user = User(email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return self.generate_token(user)
    
    def login(self, email, password):
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            return self.generate_token(user)
        raise AuthenticationError("Invalid credentials")
    
    def generate_token(self, user):
        payload = {
            'sub': user.id,
            'email': user.email,
            'role': user.role,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }
        return jwt.encode(payload, SECRET_KEY, algorithm='HS256')
```

### Migration Path:
1. Keep your existing User, Role, Permission models
2. Add password_hash field to User model
3. Implement local JWT generation
4. Remove Supabase dependency
5. All auth logic uses SQLAlchemy ORM

## Alternative: Fully Embrace Supabase

If you want to keep Supabase, then:
- Remove ALL local models (User, Role, Permission)
- Use Supabase client for everything
- Accept that some SQL is needed for Supabase functions
- Treat Supabase as your only database

## Decision Criteria

Choose **Local Auth** if:
- You want to use ORM exclusively
- You need complex role/permission logic
- You want full control
- You don't want to write SQL

Choose **Supabase Only** if:
- You want managed auth (password reset, email verification)
- You're okay with SQL for some operations
- You want to reduce infrastructure
- You don't need complex local relationships
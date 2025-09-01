# Core Module Migration Guide

## Summary of Changes

The core module has been consolidated to eliminate duplicate functionality and improve maintainability.

### Key Changes

1. **Removed `DatabaseUtils` class** from `database_manager.py`
   - Functionality moved to `bulk_operations.py`
   
2. **Removed `transactional` decorator** from `database_manager.py`
   - Use Unit of Work pattern from `unit_of_work.py` instead
   
3. **Simplified `database.py`**
   - Now serves as minimal configuration
   - Delegates to `database_manager.py` for advanced features

4. **Enhanced `bulk_operations.py`**
   - Added simple utility functions from `DatabaseUtils`
   - Now the single source for all bulk operations

## Import Updates Required

### Bulk Operations

**OLD:**
```python
from app.core.database_manager import DatabaseUtils

# Usage
DatabaseUtils.bulk_insert(session, Model, data)
DatabaseUtils.bulk_update(session, Model, data)
DatabaseUtils.execute_raw(session, query, params)
```

**NEW:**
```python
from app.core.bulk_operations import simple_bulk_insert, simple_bulk_update, execute_raw_sql

# Usage
simple_bulk_insert(session, Model, data)
simple_bulk_update(session, Model, data)
execute_raw_sql(session, query, params)
```

### Advanced Bulk Operations

**No Change Required:**
```python
from app.core.bulk_operations import bulk_manager

# Usage remains the same
result = bulk_manager.bulk_insert(Model, data)
```

### Transaction Management

**OLD:**
```python
from app.core.database_manager import transactional

@transactional()
def my_method(self):
    pass
```

**NEW:**
```python
from app.core.unit_of_work import UnitOfWorkManager

# Use Unit of Work pattern
with UnitOfWorkManager() as uow:
    # Your transactional code
    uow.commit()
```

### Database Sessions

**No Change Required:**
```python
from app.core.database import get_db
from app.core.database_manager import db_manager

# Both continue to work as before
```

## Files That May Need Updates

Based on usage patterns, these files might need import updates:

1. **Services** that use bulk operations:
   - `app/services/course_service.py`
   - `app/services/enrollment_service.py`
   - Any other service using `DatabaseUtils`

2. **Repositories** using bulk operations:
   - Check all files in `app/repositories/`

3. **API endpoints** using transactions:
   - Check all files in `app/api/`

## Testing Checklist

After updating imports, test the following:

- [ ] Database connections work properly
- [ ] Bulk insert operations succeed
- [ ] Bulk update operations succeed
- [ ] Raw SQL queries execute correctly
- [ ] Transactions commit and rollback properly
- [ ] Unit of Work pattern functions correctly
- [ ] No import errors on application startup

## Benefits of Consolidation

1. **Single Source of Truth**: Each functionality now has one implementation
2. **Reduced Complexity**: ~200 lines of duplicate code removed
3. **Better Performance**: Single set of event listeners and monitors
4. **Easier Maintenance**: Clear separation of concerns
5. **Improved Testing**: Fewer interconnected modules to test

## Rollback Plan

If issues arise, the changes can be reverted by:

1. Restore `DatabaseUtils` class to `database_manager.py`
2. Restore `transactional` decorator to `database_manager.py`
3. Revert `database.py` to original version
4. Update imports back to original paths

## Performance Considerations

The consolidation should have no negative performance impact:
- Connection pooling remains unchanged
- Query optimization unchanged
- Bulk operations are now more efficient with single implementation
- Event listeners reduced from multiple to single set
"""
Core abstract models for the Unpuzzle MVP project.
Shared base models used across all Django apps with RLS support.
"""
import uuid
from django.db import models
from django.utils import timezone
from typing import List, Dict


class UUIDModel(models.Model):
    """Abstract model with UUID as primary key"""
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    class Meta:
        abstract = True


class TimeStampedModel(models.Model):
    """Abstract model with created and updated timestamps"""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)
    
    class Meta:
        abstract = True
        ordering = ['-created_at']


class AuditableModel(UUIDModel, TimeStampedModel):
    """Abstract model with full audit trail using Supabase user IDs"""
    created_by = models.UUIDField(
        null=True,
        blank=True,
        help_text='Supabase User ID who created this'
    )
    updated_by = models.UUIDField(
        null=True,
        blank=True,
        help_text='Supabase User ID who last updated this'
    )
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.UUIDField(
        null=True,
        blank=True,
        help_text='Supabase User ID who deleted this'
    )
    
    class Meta:
        abstract = True
        
    def soft_delete(self, user_id=None):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.deleted_by = user_id
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])
    
    def restore(self):
        """Restore soft deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.save(update_fields=['is_deleted', 'deleted_at', 'deleted_by'])


class RLSModelMixin:
    """
    Mixin to add RLS (Row Level Security) configuration to models.
    Add this to any model that needs RLS policies.
    """
    
    @classmethod
    def get_rls_policies(cls) -> List[Dict[str, str]]:
        """
        Override this method to define RLS policies for the model.
        
        Returns a list of policy dictionaries with keys:
        - name: Policy name
        - operation: SELECT, INSERT, UPDATE, DELETE, or ALL
        - role: authenticated, anon, service_role, or postgres
        - using: SQL expression for existing row checks
        - with_check: SQL expression for new row checks (INSERT/UPDATE)
        """
        return []
    
    @classmethod
    def get_rls_enabled(cls) -> bool:
        """Override to control whether RLS is enabled for this table."""
        return True
    
    @classmethod
    def generate_rls_sql(cls) -> str:
        """Generate SQL statements to enable RLS and create policies."""
        if not cls.get_rls_enabled():
            return ""
        
        table_name = cls._meta.db_table
        sql_statements = []
        
        # Enable RLS
        sql_statements.append(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY;")
        
        # Create policies
        for policy in cls.get_rls_policies():
            policy_sql = f"CREATE POLICY {policy['name']} ON {table_name}"
            policy_sql += f" FOR {policy['operation']}"
            policy_sql += f" TO {policy['role']}"
            
            if 'using' in policy:
                policy_sql += f" USING ({policy['using']})"
            
            if 'with_check' in policy:
                policy_sql += f" WITH CHECK ({policy['with_check']})"
            
            policy_sql += ";"
            sql_statements.append(policy_sql)
        
        return "\n".join(sql_statements)
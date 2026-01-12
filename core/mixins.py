import re
from django.utils.text import slugify
from django.db.models import Q


class AutoCodeMixin:
    """
    Mixin to auto-generate 'code' field from label/name/name_ar when saving.
    
    How to use:
        1. Add this mixin to your model: class MyModel(AutoCodeMixin, models.Model)
        2. Set code field with blank=True: code = models.CharField(max_length=50, blank=True)
        3. Optional: Configure these class attributes:
            _code_source_fields: list = ['label', 'name', 'name_ar']  # Priority order
            _code_parent_field: str = None  # For scoped uniqueness (e.g., 'governorate' for Town)
            _code_fallback_prefix: str = 'CODE'  # Prefix when no source text available
    
    The mixin will:
        - Generate code from first available source field
        - Convert to uppercase slug format (A-Z0-9_)
        - Ensure uniqueness within scope (parent if specified, else global)
        - Ignore soft-deleted rows (deleted_at IS NOT NULL)
        - Append _2, _3, etc. on collision
        - Respect max_length of code field
    """
    
    _code_source_fields = ['label', 'name', 'name_ar']
    _code_parent_field = None  # Set to FK field name for scoped uniqueness
    _code_fallback_prefix = 'CODE'
    
    def save(self, *args, **kwargs):
        # Auto-generate code if empty
        if not self.code:
            self.code = self._generate_unique_code()
        super().save(*args, **kwargs)
    
    def _generate_unique_code(self):
        """Generate a unique code from source fields."""
        # Get the max length of the code field
        max_length = self._meta.get_field('code').max_length
        
        # Try to get source text from configured fields
        source_text = None
        for field_name in self._code_source_fields:
            if hasattr(self, field_name):
                value = getattr(self, field_name, None)
                if value:
                    source_text = value
                    break
        
        # Generate base code
        if source_text:
            base_code = self._slugify_to_code(source_text, max_length)
        else:
            # Fallback: use prefix + number
            base_code = self._code_fallback_prefix
        
        # Ensure uniqueness
        unique_code = self._ensure_unique_code(base_code, max_length)
        
        return unique_code
    
    def _slugify_to_code(self, text, max_length):
        """
        Convert text to code format:
        1. Slugify (handles unicode, spaces, special chars)
        2. Uppercase
        3. Replace hyphens with underscores
        4. Keep only A-Z, 0-9, underscore
        5. Truncate to max_length
        """
        # Slugify the text (handles unicode and special characters)
        slug = slugify(text)
        
        # Uppercase
        code = slug.upper()
        
        # Replace hyphens with underscores
        code = code.replace('-', '_')
        
        # Keep only alphanumeric and underscore
        code = re.sub(r'[^A-Z0-9_]', '', code)
        
        # Remove leading/trailing underscores
        code = code.strip('_')
        
        # Ensure it's not empty after cleaning
        if not code:
            code = self._code_fallback_prefix
        
        # Truncate to max_length
        if len(code) > max_length:
            code = code[:max_length]
        
        return code
    
    def _ensure_unique_code(self, base_code, max_length):
        """
        Ensure code is unique within scope (considering parent field and deleted_at).
        If collision, append _2, _3, etc.
        """
        model_class = self.__class__
        code = base_code
        counter = 2
        
        while self._code_exists(code):
            # Need to append suffix
            suffix = f'_{counter}'
            
            # Calculate available space for base
            available_length = max_length - len(suffix)
            
            if available_length <= 0:
                # Max length too small, just use counter
                code = str(counter)[:max_length]
            else:
                # Truncate base and append suffix
                truncated_base = base_code[:available_length]
                code = f'{truncated_base}{suffix}'
            
            counter += 1
            
            # Safety check to avoid infinite loop
            if counter > 1000:
                # This should never happen, but just in case
                import uuid
                code = str(uuid.uuid4())[:max_length].upper().replace('-', '_')
                break
        
        return code
    
    def _code_exists(self, code):
        """
        Check if code already exists in the database.
        
        Considers:
        - Scope (parent field if configured)
        - Soft delete (ignores deleted_at IS NOT NULL)
        - Excludes current instance (for updates)
        """
        model_class = self.__class__
        
        # Build query
        query = Q(code=code)
        
        # Exclude soft-deleted rows
        if hasattr(model_class, 'deleted_at'):
            query &= Q(deleted_at__isnull=True)
        
        # Add parent scope if configured
        if self._code_parent_field:
            parent_value = getattr(self, self._code_parent_field, None)
            if parent_value:
                query &= Q(**{self._code_parent_field: parent_value})
        
        # Get queryset
        queryset = model_class.objects.filter(query)
        
        # Exclude current instance if updating (has pk)
        if self.pk:
            queryset = queryset.exclude(pk=self.pk)
        
        return queryset.exists()

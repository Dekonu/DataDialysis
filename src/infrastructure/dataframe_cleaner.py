"""DataFrame Cleaning Service.

This module provides utilities for cleaning and normalizing DataFrames before persistence.
It handles format-specific transformations like NaT conversion, enum serialization, and
array normalization.

Security Impact:
    - Ensures data integrity before persistence
    - Prevents database errors from malformed data
    - No PII handling - that's done by RedactorService

Architecture:
    - Infrastructure layer service (format-specific)
    - Composable cleaning functions
    - Extensible for different data formats (pandas, pyarrow, etc.)
    - Stateless - pure transformation functions
"""

import logging
from typing import Any, Callable, List, Optional, Set, Union
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class DataFrameCleaner:
    """Service for cleaning and normalizing DataFrames before persistence.
    
    This service provides composable cleaning functions that can be applied
    selectively based on the target storage system's requirements.
    
    All methods are stateless and return transformed DataFrames without
    modifying the original.
    """
    
    @staticmethod
    def clean_nat_values(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None,
        convert_to_none: bool = True
    ) -> pd.DataFrame:
        """Convert NaT (Not a Time) values to None for datetime columns.
        
        PostgreSQL and many databases can't handle pandas NaT, so they must
        be converted to None (NULL) before persistence.
        
        Parameters:
            df: DataFrame to clean
            columns: Specific columns to clean (None = all datetime columns)
            convert_to_none: If True, convert NaT to None; if False, keep NaT
            
        Returns:
            DataFrame with NaT values converted to None
            
        Security Impact:
            None - this is a format conversion, not a security operation
        """
        df_cleaned = df.copy()
        
        # Determine which columns to process
        if columns is None:
            # Find all datetime columns
            datetime_cols = [
                col for col in df_cleaned.columns
                if df_cleaned[col].dtype.name.startswith('datetime')
            ]
        else:
            datetime_cols = [col for col in columns if col in df_cleaned.columns]
        
        # Convert NaT to None for datetime columns
        if convert_to_none:
            for col in datetime_cols:
                df_cleaned[col] = df_cleaned[col].where(pd.notna(df_cleaned[col]), None)
        
        # Also check object columns for datetime objects that might be NaT
        object_cols = [
            col for col in df_cleaned.columns
            if df_cleaned[col].dtype == 'object' and col not in datetime_cols
        ]
        
        if convert_to_none:
            def convert_nat_to_none(x: Any) -> Any:
                if x is None:
                    return None
                if isinstance(x, pd.Timestamp) and pd.isna(x):
                    return None
                # Handle numpy datetime64 NaT
                if hasattr(x, 'dtype') and 'datetime' in str(x.dtype) and pd.isna(x):
                    return None
                return x
            
            for col in object_cols:
                df_cleaned[col] = df_cleaned[col].apply(convert_nat_to_none)
        
        return df_cleaned
    
    @staticmethod
    def normalize_array_columns(
        df: pd.DataFrame,
        array_columns: List[str],
        empty_value: Any = None
    ) -> pd.DataFrame:
        """Normalize array/list columns to ensure consistent format.
        
        Converts None/NaN/empty strings to empty lists for array columns.
        This is important for PostgreSQL array types.
        
        Parameters:
            df: DataFrame to normalize
            array_columns: List of column names that should be arrays
            empty_value: Value to use for empty arrays (None = use empty list [])
            
        Returns:
            DataFrame with normalized array columns
            
        Security Impact:
            None - this is a format normalization
        """
        df_normalized = df.copy()
        default_empty = [] if empty_value is None else empty_value
        
        for col in array_columns:
            if col not in df_normalized.columns:
                continue
            
            def normalize_array(x: Any) -> Any:
                if isinstance(x, list):
                    return x
                elif isinstance(x, tuple):
                    return list(x)
                elif pd.isna(x) or x is None or x == '[]' or x == '':
                    return default_empty
                elif isinstance(x, str) and x.startswith('[') and x.endswith(']'):
                    # Try to parse string representation of list
                    try:
                        import ast
                        parsed = ast.literal_eval(x)
                        return parsed if isinstance(parsed, list) else [parsed]
                    except:
                        return default_empty
                else:
                    return [x] if x is not None else default_empty
            
            df_normalized[col] = df_normalized[col].apply(normalize_array)
        
        return df_normalized
    
    @staticmethod
    def convert_enums_to_strings(
        df: pd.DataFrame,
        columns: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Convert enum values to their string representations.
        
        Many databases don't support Python enums directly, so they must be
        converted to strings before persistence.
        
        Parameters:
            df: DataFrame to convert
            columns: Specific columns to convert (None = all object columns)
            
        Returns:
            DataFrame with enum values converted to strings
            
        Security Impact:
            None - this is a type conversion
        """
        df_converted = df.copy()
        
        # Determine which columns to process
        if columns is None:
            # Process all object columns (enums are typically object dtype)
            columns_to_process = [
                col for col in df_converted.columns
                if df_converted[col].dtype == 'object'
            ]
        else:
            columns_to_process = [col for col in columns if col in df_converted.columns]
        
        def convert_enum_to_string(x: Any) -> Any:
            if isinstance(x, list):
                return x  # Don't convert lists
            elif hasattr(x, 'value'):
                return x.value  # Convert enum to string
            elif x is None or pd.isna(x):
                return None
            else:
                return str(x) if x is not None else None
        
        for col in columns_to_process:
            df_converted[col] = df_converted[col].apply(convert_enum_to_string)
        
        return df_converted
    
    @staticmethod
    def prepare_for_database(
        df: pd.DataFrame,
        array_columns: Optional[List[str]] = None,
        enum_columns: Optional[List[str]] = None,
        convert_nat: bool = True
    ) -> pd.DataFrame:
        """Apply all cleaning operations needed for database persistence.
        
        This is a convenience method that applies all standard cleaning
        operations in the correct order.
        
        Parameters:
            df: DataFrame to clean
            array_columns: List of column names that should be arrays
            enum_columns: List of column names that contain enums (None = auto-detect)
            convert_nat: Whether to convert NaT values to None
            
        Returns:
            Fully cleaned DataFrame ready for database persistence
            
        Security Impact:
            None - this is a format transformation
        """
        # Step 1: Convert NaT to None (must be first)
        df_cleaned = DataFrameCleaner.clean_nat_values(df, convert_to_none=convert_nat)
        
        # Step 2: Normalize array columns (if specified)
        if array_columns:
            df_cleaned = DataFrameCleaner.normalize_array_columns(
                df_cleaned,
                array_columns
            )
        
        # Step 3: Convert enums to strings (must be after array normalization)
        # Exclude array columns from enum conversion
        array_cols_set = set(array_columns or [])
        if enum_columns is None:
            # Auto-detect: exclude array columns
            enum_columns_to_use = [
                col for col in df_cleaned.columns
                if col not in array_cols_set and df_cleaned[col].dtype == 'object'
            ]
        else:
            # Use provided enum columns, but exclude array columns
            enum_columns_to_use = [col for col in enum_columns if col not in array_cols_set]
        
        if enum_columns_to_use:
            df_cleaned = DataFrameCleaner.convert_enums_to_strings(
                df_cleaned,
                columns=enum_columns_to_use
            )
        
        return df_cleaned
    
    @staticmethod
    def convert_to_tuples(
        df: pd.DataFrame,
        handle_nat: bool = True,
        array_columns: Optional[Set[str]] = None
    ) -> List[tuple]:
        """Convert DataFrame to list of tuples, ensuring proper None handling.
        
        This is the final step before passing data to database drivers.
        It ensures all NaT/NaN values are converted to None and arrays
        are properly handled.
        
        Parameters:
            df: DataFrame to convert
            handle_nat: Whether to convert NaT/NaN to None during conversion
            array_columns: Set of column names that are arrays (for optimization)
            
        Returns:
            List of tuples, one per row, with proper None values
            
        Security Impact:
            None - this is a format conversion
        """
        values = []
        array_cols = array_columns or set()
        
        for idx, row in df.iterrows():
            row_values = []
            for col in df.columns:
                val = row[col]
                
                # Skip NaT/NaN checks for list/array values (they're already handled)
                if isinstance(val, (list, tuple)):
                    row_values.append(list(val) if isinstance(val, tuple) else val)
                # Comprehensive check for NaT/NaN values (only for non-array types)
                elif handle_nat:
                    if val is None:
                        row_values.append(None)
                    elif isinstance(val, pd.Timestamp) and pd.isna(val):
                        row_values.append(None)
                    elif hasattr(val, 'dtype') and 'datetime' in str(val.dtype) and pd.isna(val):
                        row_values.append(None)
                    elif not isinstance(val, (list, tuple)) and pd.isna(val):
                        row_values.append(None)
                    else:
                        row_values.append(val)
                else:
                    row_values.append(val)
            
            values.append(tuple(row_values))
        
        return values


# Convenience functions for direct use (functional style)
def clean_nat_values(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convenience function for cleaning NaT values."""
    return DataFrameCleaner.clean_nat_values(df, **kwargs)


def normalize_array_columns(df: pd.DataFrame, array_columns: List[str], **kwargs) -> pd.DataFrame:
    """Convenience function for normalizing array columns."""
    return DataFrameCleaner.normalize_array_columns(df, array_columns, **kwargs)


def convert_enums_to_strings(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convenience function for converting enums to strings."""
    return DataFrameCleaner.convert_enums_to_strings(df, **kwargs)


def prepare_for_database(df: pd.DataFrame, **kwargs) -> pd.DataFrame:
    """Convenience function for preparing DataFrame for database."""
    return DataFrameCleaner.prepare_for_database(df, **kwargs)


def convert_to_tuples(df: pd.DataFrame, **kwargs) -> List[tuple]:
    """Convenience function for converting DataFrame to tuples."""
    return DataFrameCleaner.convert_to_tuples(df, **kwargs)


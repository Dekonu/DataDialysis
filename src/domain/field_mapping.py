"""Field Mapping Service for FHIR R5 Compliance.

This module provides a FieldMapper class that maps common field name synonyms
to FHIR R5-compliant field names. This allows adapters to work with various
data sources that use different naming conventions while maintaining FHIR compliance
in the domain model.

Security Impact:
    - Field mapping is a pure transformation - no PII redaction happens here
    - All PII redaction is handled by domain model validators
    - Mapping config is validated to prevent injection attacks

Architecture:
    - Pure domain service (no infrastructure dependencies)
    - Follows Hexagonal Architecture: Domain Core is isolated from Adapters
    - Configurable via JSON files for flexibility
    - Default mapping configuration is embedded and can be overridden
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Union

logger = logging.getLogger(__name__)

# Default field mapping configuration (can be overridden by config file)
DEFAULT_FIELD_MAPPING: Dict[str, Dict[str, Any]] = {
    "patient": {
        "mrn": "patient_id",
        "patient_id": "patient_id",
        "medical_record_number": "patient_id",
        "patient_dob": "date_of_birth",
        "birth_date": "date_of_birth",
        "birthDate": "date_of_birth",
        "dob": "date_of_birth",
        "patient_name": {
            "type": "split",
            "target": ["given_names", "family_name"],
            "separator": " ",
            "max_splits": 1
        },
        "full_name": {
            "type": "split",
            "target": ["given_names", "family_name"],
            "separator": " ",
            "max_splits": 1
        },
        "first_name": "given_names",
        "last_name": "family_name",
        "zip_code": "postal_code",
        "zip": "postal_code",
        "postal_code": "postal_code",
        "patient_gender": "gender",
        "gender": "gender"
    },
    "encounter": {
        "encounter_date": "period_start",
        "admit_date": "period_start",
        "admission_date": "period_start",
        "start_date": "period_start",
        "encounter_type": "class_code",
        "visit_type": "class_code",
        "encounter_status": "status",
        "visit_status": "status",
        "primary_diagnosis_code": "diagnosis_codes",
        "dx_code": "diagnosis_codes",
        "diagnosis_code": "diagnosis_codes"
    },
    "observation": {
        "observation_type": "category",
        "observation_code": "code",
        "obs_code": "code",
        "observation_date": "effective_date",
        "obs_date": "effective_date"
    }
}


class FieldMapper:
    """Maps common field name synonyms to FHIR R5-compliant field names.
    
    This class handles:
    - Simple field name mappings (e.g., `mrn` → `patient_id`)
    - Split transformations (e.g., `patient_name` → `given_names` + `family_name`)
    - List transformations (e.g., ensuring `given_names` is a list)
    - Nested mappings for different record types (patient, encounter, observation)
    
    Configuration Format:
        {
            "patient": {
                "mrn": "patient_id",
                "patient_dob": "date_of_birth",
                "patient_name": {
                    "type": "split",
                    "target": ["given_names", "family_name"],
                    "separator": " ",
                    "max_splits": 1
                }
            },
            "encounter": {
                "encounter_date": "period_start",
                "encounter_type": "class_code"
            },
            "observation": {
                "observation_type": "category"
            }
        }
    """
    
    def __init__(self, mapping_config_path: Optional[str] = None, mapping_config_dict: Optional[Dict[str, Any]] = None):
        """Initialize FieldMapper with configuration.
        
        Parameters:
            mapping_config_path: Path to JSON file with field mappings (overrides default)
            mapping_config_dict: Configuration dictionary (alternative to config_path, overrides default)
        
        Raises:
            FileNotFoundError: If mapping_config_path doesn't exist
            json.JSONDecodeError: If config file is invalid JSON
            ValueError: If both mapping_config_path and mapping_config_dict are provided
        
        Note:
            If neither mapping_config_path nor mapping_config_dict is provided,
            the default field mapping configuration will be used.
        """
        if mapping_config_path and mapping_config_dict:
            raise ValueError("Cannot specify both mapping_config_path and mapping_config_dict")
        
        # Start with default configuration
        self.mapping_config = json.loads(json.dumps(DEFAULT_FIELD_MAPPING))  # Deep copy
        
        # Override with provided configuration if specified
        if mapping_config_path:
            config_path_obj = Path(mapping_config_path)
            if not config_path_obj.exists():
                raise FileNotFoundError(f"Field mapping configuration file not found: {mapping_config_path}")
            
            with open(config_path_obj, 'r', encoding='utf-8') as f:
                override_config = json.load(f)
            
            # Merge override config into default (override takes precedence)
            self._merge_config(self.mapping_config, override_config)
            logger.info(f"Loaded field mapping config from {mapping_config_path} (merged with defaults)")
        elif mapping_config_dict:
            # Merge override config dict into default (override takes precedence)
            self._merge_config(self.mapping_config, mapping_config_dict)
            logger.info("Using provided field mapping config dict (merged with defaults)")
        else:
            logger.info("Using default field mapping configuration")
        
        # Validate configuration structure
        self._validate_config()
    
    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]) -> None:
        """Merge override configuration into base configuration.
        
        Parameters:
            base: Base configuration dictionary (modified in place)
            override: Override configuration dictionary
        """
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_config(base[key], value)
            else:
                # Override the base value
                base[key] = value
    
    def _validate_config(self) -> None:
        """Validate mapping configuration structure.
        
        Raises:
            ValueError: If configuration structure is invalid
        """
        if not isinstance(self.mapping_config, dict):
            raise ValueError("Field mapping config must be a dictionary")
        
        # Validate top-level keys (should be record types)
        valid_record_types = {'patient', 'encounter', 'observation'}
        for key in self.mapping_config.keys():
            if key not in valid_record_types:
                logger.warning(
                    f"Unknown record type in mapping config: {key}. "
                    f"Expected one of: {valid_record_types}"
                )
        
        # Validate each record type's mappings
        for record_type, mappings in self.mapping_config.items():
            if not isinstance(mappings, dict):
                raise ValueError(f"Field mappings for '{record_type}' must be a dictionary")
            
            for source_field, target_config in mappings.items():
                if isinstance(target_config, dict):
                    # Split transformation
                    if target_config.get('type') == 'split':
                        if 'target' not in target_config:
                            raise ValueError(
                                f"Split transformation for '{source_field}' in '{record_type}' "
                                "must specify 'target' field names"
                            )
                        if not isinstance(target_config['target'], list):
                            raise ValueError(
                                f"Split transformation 'target' for '{source_field}' in '{record_type}' "
                                "must be a list"
                            )
                        if len(target_config['target']) != 2:
                            raise ValueError(
                                f"Split transformation 'target' for '{source_field}' in '{record_type}' "
                                "must contain exactly 2 field names"
                            )
                elif not isinstance(target_config, str):
                    raise ValueError(
                        f"Field mapping for '{source_field}' in '{record_type}' "
                        "must be a string (target field name) or dict (split transformation)"
                    )
    
    def map_patient_fields(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map patient record fields to FHIR R5 field names.
        
        Parameters:
            record_data: Dictionary with extracted field names (from XPath)
        
        Returns:
            Dictionary with FHIR R5-compliant field names
        """
        return self._map_fields(record_data, 'patient')
    
    def map_encounter_fields(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map encounter record fields to FHIR R5 field names.
        
        Parameters:
            record_data: Dictionary with extracted field names (from XPath)
        
        Returns:
            Dictionary with FHIR R5-compliant field names
        """
        return self._map_fields(record_data, 'encounter')
    
    def map_observation_fields(self, record_data: Dict[str, Any]) -> Dict[str, Any]:
        """Map observation record fields to FHIR R5 field names.
        
        Parameters:
            record_data: Dictionary with extracted field names (from XPath)
        
        Returns:
            Dictionary with FHIR R5-compliant field names
        """
        return self._map_fields(record_data, 'observation')
    
    def _map_fields(self, record_data: Dict[str, Any], record_type: str) -> Dict[str, Any]:
        """Apply field mappings for a specific record type.
        
        Parameters:
            record_data: Dictionary with extracted field names
            record_type: Type of record ('patient', 'encounter', or 'observation')
        
        Returns:
            Dictionary with mapped field names
        """
        if not self.mapping_config or record_type not in self.mapping_config:
            # No mappings for this record type - return as-is (pass-through)
            return record_data.copy()
        
        mappings = self.mapping_config[record_type]
        mapped_data = {}
        
        # Process each field in the record data
        for source_field, value in record_data.items():
            if source_field in mappings:
                # Field has a mapping - apply it
                target_config = mappings[source_field]
                
                if isinstance(target_config, dict):
                    # Split transformation
                    if target_config.get('type') == 'split':
                        mapped_data.update(
                            self._apply_split_transformation(
                                source_field,
                                value,
                                target_config
                            )
                        )
                    else:
                        logger.warning(
                            f"Unknown transformation type '{target_config.get('type')}' "
                            f"for field '{source_field}' in '{record_type}' - skipping"
                        )
                        # Fallback: include original field
                        mapped_data[source_field] = value
                else:
                    # Simple field name mapping
                    target_field = target_config
                    mapped_data[target_field] = value
            else:
                # No mapping for this field - pass through as-is
                # (assumes it already matches FHIR field name)
                mapped_data[source_field] = value
        
        return mapped_data
    
    def _apply_split_transformation(
        self,
        source_field: str,
        value: Any,
        config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply split transformation to a field value.
        
        Parameters:
            source_field: Name of the source field
            value: Value to split
            config: Split transformation configuration
        
        Returns:
            Dictionary with split fields mapped to target field names
        """
        if value is None or value == '':
            return {}
        
        # Convert value to string for splitting
        value_str = str(value).strip()
        if not value_str:
            return {}
        
        # Get split configuration
        separator = config.get('separator', ' ')
        max_splits = config.get('max_splits', 1)
        target_fields = config.get('target', [])
        
        if len(target_fields) != 2:
            logger.warning(
                f"Split transformation for '{source_field}' expects 2 target fields, "
                f"got {len(target_fields)} - skipping"
            )
            return {}
        
        # Split the value
        parts = value_str.split(separator, max_splits)
        
        # Map to target fields
        result = {}
        if len(parts) >= 2:
            # Two parts: first name -> given_names, last name -> family_name
            given_name = parts[0].strip()
            family_name = parts[1].strip()
            
            # Handle given_names as a list (FHIR R5 format)
            if target_fields[0] == 'given_names':
                result['given_names'] = [given_name] if given_name else []
            else:
                result[target_fields[0]] = given_name
            
            # Handle family_name as a string
            if target_fields[1] == 'family_name':
                result['family_name'] = family_name
            else:
                result[target_fields[1]] = family_name
        elif len(parts) == 1:
            # Only one part - treat as family name (common in some cultures)
            family_name = parts[0].strip()
            if target_fields[1] == 'family_name':
                result['family_name'] = family_name
            else:
                result[target_fields[1]] = family_name
            # Empty given_names list
            if target_fields[0] == 'given_names':
                result['given_names'] = []
        
        return result


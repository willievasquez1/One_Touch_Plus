"""Validation logic for scraped outputs.

The OutputValidator checks that the data scraped meets certain criteria or formats.
This can include ensuring required fields are present, values are in expected range, etc.
"""

class OutputValidator:
    """Validates scraped data against expected structure or quality criteria."""
    def __init__(self, config):
        """Initialize the validator with configuration rules.

        Args:
            config (dict): Configuration that may include validation rules or schema.
        """
        self.config = config
        # TODO: Extract or define validation rules from config if applicable
    
    def validate(self, data):
        """Validate a single scraped data item or a collection of data.

        Args:
            data (dict): The data item (or batch of items) to validate.

        Returns:
            bool: True if data is considered valid, False if it fails validation.
        """
        if data is None:
            return False
        if not isinstance(data, dict):
            # Only expecting dictionary data structures for now
            return False
        # TODO: Implement actual validation logic, e.g. required keys present or values format.
        # For now, assume data is valid if it is a non-empty dictionary.
        # Example:
        # required_fields = self.config.get('validation', {}).get('required_fields', [])
        # for field in required_fields:
        #     if field not in data:
        #         return False
        return True if data else False

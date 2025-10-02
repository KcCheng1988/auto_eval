"""Configuration loader for template validation rules and evaluation settings"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class ConfigLoader:
    """Loads and manages configuration files for the auto-evaluation tool"""

    def __init__(self, config_dir: str = "config"):
        """
        Initialize the config loader

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        self._template_config = None
        self._evaluation_config = None
        self._report_config = None

    def load_template_config(self, config_file: str = "template_config.json") -> Dict[str, Any]:
        """
        Load template validation configuration

        Args:
            config_file: Name of the template configuration file

        Returns:
            Dictionary containing template validation rules
        """
        if self._template_config is None:
            config_path = self.config_dir / config_file
            if not config_path.exists():
                logger.warning(f"Template config not found at {config_path}. Using defaults.")
                return self._get_default_template_config()

            with open(config_path, 'r', encoding='utf-8') as f:
                self._template_config = json.load(f)

        return self._template_config

    def load_evaluation_config(self, config_file: str = "evaluation_config.json") -> Dict[str, Any]:
        """
        Load evaluation configuration including thresholds

        Args:
            config_file: Name of the evaluation configuration file

        Returns:
            Dictionary containing evaluation settings and thresholds
        """
        if self._evaluation_config is None:
            config_path = self.config_dir / config_file
            if not config_path.exists():
                logger.warning(f"Evaluation config not found at {config_path}. Using defaults.")
                return self._get_default_evaluation_config()

            with open(config_path, 'r', encoding='utf-8') as f:
                self._evaluation_config = json.load(f)

        return self._evaluation_config

    def load_report_config(self, config_file: str = "report_config.json") -> Dict[str, Any]:
        """
        Load report generation configuration

        Args:
            config_file: Name of the report configuration file

        Returns:
            Dictionary containing report settings
        """
        if self._report_config is None:
            config_path = self.config_dir / config_file
            if not config_path.exists():
                logger.warning(f"Report config not found at {config_path}. Using defaults.")
                return self._get_default_report_config()

            with open(config_path, 'r', encoding='utf-8') as f:
                self._report_config = json.load(f)

        return self._report_config

    def _get_default_template_config(self) -> Dict[str, Any]:
        """Returns default template configuration"""
        return {
            "sheets": [],
            "fields": {},
            "validation_rules": {}
        }

    def _get_default_evaluation_config(self) -> Dict[str, Any]:
        """Returns default evaluation configuration"""
        return {
            "thresholds": {
                "autonomous": {},
                "human_in_loop": {}
            },
            "metrics": []
        }

    def _get_default_report_config(self) -> Dict[str, Any]:
        """Returns default report configuration"""
        return {
            "email_template": "default_template.html",
            "required_sections": []
        }

    def reload_configs(self):
        """Reload all configurations from disk"""
        self._template_config = None
        self._evaluation_config = None
        self._report_config = None
        logger.info("All configurations reloaded")

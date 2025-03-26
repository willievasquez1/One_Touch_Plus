"""Output reporting module for One_Touch_Plus.

This module is responsible for aggregating and outputting scraping results.
The OutputReporter class persists results in either JSON, CSV, or JSONL format based on configuration.
"""

import logging
import os
import json
import csv
from datetime import datetime

logger = logging.getLogger(__name__)

class OutputReporter:
    def __init__(self, config=None):
        """
        Initialize the OutputReporter with configuration details.

        Args:
            config (dict, optional): The scraper configuration.
        """
        self.config = config or {}
        self.output_dir = self.config.get("output_dir", "data")
        self.format = self.config.get("output_format", "json").lower()
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_report(self, results):
        """
        Persist results to a file in the output_dir with a timestamped filename.
        The format is determined by the config (json, csv, or jsonl).

        Args:
            results (dict): The scraped data for one page.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if self.format == "csv":
            self._save_csv(results, timestamp)
        elif self.format == "jsonl":
            self._save_jsonl(results, timestamp)
        else:
            self._save_json(results, timestamp)

    def _save_json(self, results, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved JSON report to {filename}")
        except Exception as e:
            logger.error(f"Failed to save JSON report: {e}")

    def _save_csv(self, results, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.csv")
            with open(filename, "w", encoding="utf-8", newline='') as f:
                writer = csv.DictWriter(f, fieldnames=results.keys())
                writer.writeheader()
                writer.writerow(results)
            logger.info(f"Saved CSV report to {filename}")
        except Exception as e:
            logger.error(f"Failed to save CSV report: {e}")

    def _save_jsonl(self, results, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.jsonl")
            with open(filename, "a", encoding="utf-8") as f:
                json_line = json.dumps(results, ensure_ascii=False)
                f.write(json_line + "\n")
            logger.info(f"Saved JSONL record to {filename}")
        except Exception as e:
            logger.error(f"Failed to save JSONL record: {e}")

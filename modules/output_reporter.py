"""Output reporting module for One_Touch_Plus.

This module is responsible for aggregating and outputting scraping results.
The OutputReporter class supports batch-mode output in JSON, CSV, JSONL, or SQLite,
as determined by configuration.
"""

import logging
import os
import json
import csv
import sqlite3
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
        self.output_format = self.config.get("output_format", "jsonl").lower()
        self.batch_mode = self.config.get("batch_mode", True)
        os.makedirs(self.output_dir, exist_ok=True)
        self.results = []

    def generate_report(self, data):
        """
        Add scraped data to the batch or write immediately if not in batch mode.

        Args:
            data (dict): The scraped data for one page.
        """
        if self.batch_mode:
            self.results.append(data)
        else:
            self._write_single(data)

    def finalize(self):
        """
        Write all accumulated results to a file if in batch mode.
        Supports CSV, JSONL, JSON, or SQLite.
        """
        if not self.batch_mode or not self.results:
            return
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        if self.output_format == "csv":
            self._save_csv(timestamp)
        elif self.output_format == "jsonl":
            self._save_jsonl(timestamp)
        elif self.output_format == "sqlite":
            self._save_sqlite(timestamp)
        else:
            self._save_json(timestamp)

    def _save_json(self, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.json")
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"[OutputReporter] Saved JSON report to {filename}")
        except Exception as e:
            logger.error(f"[OutputReporter] Failed to save JSON report: {e}")

    def _save_csv(self, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.csv")
            keys = self.results[0].keys()
            with open(filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=keys)
                writer.writeheader()
                writer.writerows(self.results)
            logger.info(f"[OutputReporter] Saved CSV report to {filename}")
        except Exception as e:
            logger.error(f"[OutputReporter] Failed to save CSV report: {e}")

    def _save_jsonl(self, timestamp):
        try:
            filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.jsonl")
            with open(filename, "w", encoding="utf-8") as f:
                for record in self.results:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            logger.info(f"[OutputReporter] Saved JSONL report to {filename}")
        except Exception as e:
            logger.error(f"[OutputReporter] Failed to save JSONL report: {e}")

    def _save_sqlite(self, timestamp):
        db_path = self.config.get("db_path", "data/crawler.db")
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scraped_data (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT,
                    title TEXT,
                    snippet TEXT,
                    html TEXT,
                    timestamp TEXT
                )
            """)
            for row in self.results:
                cursor.execute("""
                    INSERT INTO scraped_data (url, title, snippet, html, timestamp)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    row.get("url"),
                    row.get("title"),
                    row.get("snippet"),
                    row.get("html"),
                    timestamp
                ))
            conn.commit()
            conn.close()
            logger.info(f"[OutputReporter] Wrote batch to SQLite: {db_path}")
        except Exception as e:
            logger.error(f"[OutputReporter] SQLite write failed: {e}")

    def _write_single(self, data):
        """
        Write a single record to a file.
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(self.output_dir, f"scrape_results_{timestamp}.{self.output_format}")
        try:
            if self.output_format == "csv":
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=data.keys())
                    writer.writeheader()
                    writer.writerow(data)
            elif self.output_format == "jsonl":
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(json.dumps(data, ensure_ascii=False) + "\n")
            else:
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"[OutputReporter] Saved single record to {filename}")
        except Exception as e:
            logger.error(f"[OutputReporter] Failed to save single record: {e}")

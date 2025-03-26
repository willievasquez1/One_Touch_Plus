"""SQLite Dashboard Metrics for One_Touch_Plus.

Connects to the SQLite database and extracts crawl metrics:
- Total record count
- Domain-wise breakdown
- Latest crawl timestamp
Also:
- Formats the timestamp
- Tracks session ID and duration
- Exports metrics to CSV
"""

import sqlite3
import logging
import csv
import os
from urllib.parse import urlparse
from datetime import datetime, timezone
from uuid import uuid4

logger = logging.getLogger(__name__)

def format_timestamp(raw: str) -> str:
    """Convert '20250326_184130' → 'March 26, 2025 – 6:41 PM UTC'"""
    try:
        dt = datetime.strptime(raw, "%Y%m%d_%H%M%S")
        return dt.strftime("%B %d, %Y – %I:%M %p UTC")
    except Exception:
        logger.warning(f"[Dashboard] Failed to parse timestamp: {raw}")
        return raw or "N/A"

def get_crawl_metrics(db_path: str) -> dict:
    """
    Extract crawl metrics from the SQLite DB.
    """
    metrics = {
        "session_id": str(uuid4()),
        "total_records": 0,
        "domain_counts": {},
        "latest_timestamp": None,
        "formatted_timestamp": "N/A",
        "duration_secs": None,
    }

    if not os.path.exists(db_path):
        logger.error(f"[Dashboard] Database not found: {db_path}")
        metrics["error"] = "Database file not found."
        return metrics

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Total records
        cursor.execute("SELECT COUNT(*) FROM scraped_data")
        metrics["total_records"] = cursor.fetchone()[0]

        if metrics["total_records"] == 0:
            logger.warning("[Dashboard] scraped_data table is empty.")
            conn.close()
            return metrics

        # Domain breakdown
        cursor.execute("SELECT url FROM scraped_data")
        urls = cursor.fetchall()
        for (url,) in urls:
            domain = urlparse(url).netloc or "unknown"
            metrics["domain_counts"][domain] = metrics["domain_counts"].get(domain, 0) + 1

        # Latest timestamp
        cursor.execute("SELECT MAX(timestamp) FROM scraped_data")
        latest_ts = cursor.fetchone()[0]
        metrics["latest_timestamp"] = latest_ts
        metrics["formatted_timestamp"] = format_timestamp(latest_ts)

        # Duration
        cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM scraped_data")
        min_ts, max_ts = cursor.fetchone()
        try:
            dt_min = datetime.strptime(min_ts, "%Y%m%d_%H%M%S")
            dt_max = datetime.strptime(max_ts, "%Y%m%d_%H%M%S")
            metrics["duration_secs"] = int((dt_max - dt_min).total_seconds())
        except Exception as e:
            logger.warning(f"[Dashboard] Timestamp parsing error: {e}")

        conn.close()
        logger.info("[Dashboard] Crawl metrics successfully retrieved.")
    except Exception as e:
        logger.error(f"[Dashboard] Failed to extract metrics: {e}")
        metrics["error"] = str(e)

    return metrics

def export_metrics_to_csv(metrics: dict, output_dir: str = "data"):
    """
    Write a CSV snapshot of metrics.
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        filename = f"dashboard_metrics_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.csv"
        path = os.path.join(output_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Metric", "Value"])
            writer.writerow(["Session ID", metrics["session_id"]])
            writer.writerow(["Total Records", metrics["total_records"]])
            writer.writerow(["Latest Timestamp", metrics["formatted_timestamp"]])
            writer.writerow(["Duration (seconds)", metrics["duration_secs"] or "N/A"])
            writer.writerow([])
            writer.writerow(["Domain", "Record Count"])
            for domain, count in metrics["domain_counts"].items():
                writer.writerow([domain, count])

        logger.info(f"[Dashboard] CSV written to {path}")
    except Exception as e:
        logger.error(f"[Dashboard] CSV export failed: {e}")

def print_dashboard(db_path: str):
    """
    Print dashboard and export CSV.
    """
    print("[DEBUG] Dashboard triggered.")  # Debug print
    metrics = get_crawl_metrics(db_path)
    print(f"[DEBUG] Metrics: {metrics}")   # Debug print

    if "error" in metrics:
        print("Dashboard Error:", metrics["error"])
        return

    print("=== One_Touch_Plus Crawl Dashboard ===")
    print(f"Session ID: {metrics['session_id']}")
    print(f"Total Records: {metrics['total_records']}")
    print("Records per Domain:")
    for domain, count in metrics["domain_counts"].items():
        print(f"  {domain}: {count}")
    print(f"Latest Crawl Timestamp: {metrics['formatted_timestamp']}")
    print(f"Crawl Duration: {metrics['duration_secs']} seconds")
    print("========================================")

    export_metrics_to_csv(metrics)

if __name__ == "__main__":
    db_path = "data/crawler.db"
    print_dashboard(db_path)

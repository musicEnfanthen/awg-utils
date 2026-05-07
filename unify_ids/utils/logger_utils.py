#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared processing statistics and logging for ID unification scripts.
"""


class Logger:
    """Centralized logger for reporting and statistics in ID unification scripts."""

    def __init__(self, verbose=True, dry_run=False):
        self.messages = []
        self.dry_run = dry_run
        self.verbose = verbose
        # Stats counters as a dictionary
        self.stats = {
            "entries_seen": 0,
            "ids_seen": 0,
            "ids_changed": 0,
            "ids_missing": 0,
            "ids_multiple": 0,
            "ids_unchanged": 0,
            "svg_errors": 0,
            "svg_unchanged": 0,
        }

    def bump_stats(self, key, amount=1):
        """Increment a stats counter."""
        if key in self.stats:
            self.stats[key] += amount
        else:
            raise KeyError(f"Logger has no stat '{key}'")

    def log(self, type_, code, entry_id, message):
        """Log a structured message."""
        entry_prefix = f"{entry_id}: " if entry_id else ""
        code_suffix = f" [{code}]" if code else ""
        msg = f" [{type_.upper()}] {entry_prefix}{message}{code_suffix}"
        self.messages.append(msg)
        if self.verbose:
            print(msg)

    def log_processing_entry_start(self, entry_id):
        """Log the start of processing for a textcritics entry in verbose mode."""
        if self.verbose:
            print(f"\nProcessing textcritics entry ID: {entry_id}")

    def log_processing_start(self, process_label):
        """Log the process start banner and dry-run write notice in verbose mode."""
        if not self.verbose:
            return

        print(f"--- Starting {process_label} processing ---")
        if self.dry_run:
            print(" [DRY-RUN] No files will be written.")

    def log_processing_entry_context(self, entry_id, relevant_svgs):
        """Log anchor type and relevant SVG list for an entry in verbose mode."""
        if not self.verbose:
            return

        if "SkRT" in entry_id:
            print(f" SkRT anchor detected: {entry_id}")
        else:
            print(f" Standard anchor: {entry_id}")
        print(f" Relevant SVGs ({len(relevant_svgs)}): {relevant_svgs}")

    def log_id_change(self, old_id, new_id, svg_filename):
        """Record a successful ID change and print JSON/SVG updates in verbose mode."""
        self.bump_stats("ids_changed")

        if not self.verbose:
            return

        self.log_id_change_json(old_id, new_id)
        self.log_id_change_svg(old_id, new_id, svg_filename)

    def log_id_change_json(self, old_id, new_id):
        """Print a JSON-only ID change line in verbose mode."""
        if not self.verbose:
            return

        dry_marker = " [DRY-RUN]" if self.dry_run else ""
        print(f"{dry_marker} [JSON] Changing '{old_id}' -> '{new_id}'")

    def log_id_change_svg(self, old_id, new_id, svg_filename):
        """Print an SVG-only ID change line in verbose mode."""
        if not self.verbose:
            return

        dry_marker = " [DRY-RUN]" if self.dry_run else ""
        print(
            f"{dry_marker} [SVG]  Changing '{old_id}' -> '{new_id}' in {svg_filename}"
        )

    def log_ids_missing(self, entry_id, svg_group_id, css_class):
        """Bump ids_missing stat and log that the ID was not found in any SVG file."""
        self.bump_stats("ids_missing")
        self.log(
            "error",
            "ids_missing",
            entry_id,
            f"'{svg_group_id}' with class '{css_class}' not found in any relevant SVG files",
        )

    def log_ids_multiple(self, entry_id, svg_group_id, matching_files):
        """Bump ids_multiple stat and log that the ID was found in multiple SVG files."""
        self.bump_stats("ids_multiple")
        self.log(
            "warning",
            "ids_multiple",
            entry_id,
            f"'{svg_group_id}' found in {len(matching_files)} files: {matching_files};"
            " skipping — manual review required",
        )

    def log_items_found(self, items, label):
        """Log item count or absence in verbose mode."""
        if not self.verbose:
            return
        if not items:
            print(f" No {label} to process")
        else:
            print(f" Found {len(items)} {label} to process")

    def log_svg_error(self, entry_id, svg_group_id, svg_filename, update_error):
        """Bump svg_errors stat and log the SVG update failure."""
        self.bump_stats("svg_errors")
        self.log(
            "warning",
            "svg_errors",
            entry_id,
            f"Could not update '{svg_group_id}' in {svg_filename}; JSON unchanged ({update_error})",
        )

    def log_svg_unchanged(self, entry_id, new_id, svg_filename):
        """Bump svg_unchanged stat and log that the SVG already had the target ID."""
        self.bump_stats("svg_unchanged")
        self.log(
            "info",
            "svg_unchanged",
            entry_id,
            f"SVG already had '{new_id}' in {svg_filename}; updating JSON only",
        )

    def print_report(self):
        """Print a structured report from collected messages."""
        if self.messages:
            print("\n--- REPORT ---")
            error_warning_msgs = [
                msg
                for msg in self.messages
                if msg.startswith(" [ERROR]") or msg.startswith(" [WARNING]")
            ]
            info_msgs = [msg for msg in self.messages if msg.startswith(" [INFO]")]
            if error_warning_msgs:
                print("\n--- Errors and Warnings ---")
                for msg in error_warning_msgs:
                    print(msg)
            if info_msgs:
                print("\n--- Info Messages ---")
                for msg in info_msgs:
                    print(msg)
        else:
            print("\n [\u2713] All JSON and SVG IDs successfully updated.")

    def print_stats_summary(self):
        """Print a summary string of all counters."""
        # Map keys to display names for summary
        key_map = {
            "entries_seen": "entries",
            "ids_seen": "ids_seen",
            "ids_changed": "changed",
            "ids_missing": "missing",
            "ids_multiple": "multiple",
            "ids_unchanged": "ids_unchanged",
            "svg_errors": "svg_errors",
            "svg_unchanged": "svg_unchanged",
        }
        summary = ", ".join(f"{key_map.get(k, k)}={self.stats[k]}" for k in key_map)
        print(f"\n Summary: {summary}")

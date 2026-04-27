"""Utility functions for file operations. This includes reading from JSON and writing to files."""

import json
import sys
from pathlib import Path
from typing import Any, Dict


class FileUtils:
    """A class that contains utility functions for file operations like reading or writing."""

    @staticmethod
    def read_json(file_path: Path) -> Dict[str, Any]:
        """Read and parse a JSON file, exiting with an error message on failure.

        Args:
            file_path (Path): Path to the JSON file to read.

        Returns:
            Dict[str, Any]: The parsed JSON content as a dictionary.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error reading {file_path}: {e}", file=sys.stderr)
            sys.exit(1)

        if not isinstance(data, dict):
            print(
                f"Error reading {file_path}: expected a JSON object, got {type(data).__name__}",
                file=sys.stderr,
            )
            sys.exit(1)

        return data

    @staticmethod
    def write_file(file_path: Path, content: str) -> None:
        """Write text content to a file, creating parent directories as needed.

        Args:
            file_path (Path): Path to the output file.
            content (str): The text string to write.
        """
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

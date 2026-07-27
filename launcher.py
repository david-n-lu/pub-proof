"""
launcher.py

Backend logic for:
- Creating BioEvidence projects
- Validating projects
"""

from pathlib import Path
import json
import re


class ProjectLauncher:


    def create_project(
        self,
        working_directory: str,
        manufacturer: str,
    ) -> Path:

        working_directory = Path(
            working_directory
        )

        manufacturer = manufacturer.strip()


        if not working_directory.exists():
            raise ValueError(
                "Working directory does not exist."
            )


        if not manufacturer:
            raise ValueError(
                "Manufacturer is empty."
            )


        project_dir = (
            working_directory /
            f"BioEvidence_{safe_filename(manufacturer)}"
        )

        print(project_dir)


        if project_dir.exists():

            raise ValueError(
                "Project already exists."
            )


        folders = [
            "publications",
            "sentences",
            "products",
            "annotations",
            "citations",
        ]


        for folder in folders:

            (
                project_dir /
                folder
            ).mkdir(
                parents=True,
                exist_ok=True
            )


        config = {
            "manufacturer": manufacturer
        }


        with open(
            project_dir / "project.json",
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                config,
                f,
                indent=4,
            )


        return project_dir



    def open_project(
        self,
        project_directory: str,
    ) -> Path:


        project_dir = Path(
            project_directory
        )


        if not project_dir.exists():

            raise ValueError(
                "Project directory does not exist."
            )


        if not (
            project_dir /
            "project.json"
        ).exists():

            raise ValueError(
                "Not a valid BioEvidence project."
            )


        return project_dir




WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

def safe_filename(filename: str) -> str:
    filename = re.sub(r'[<>:"/\\|?*\x00-\x1F]', "_", filename)
    filename = filename.strip(" .")

    if filename.upper().split(".")[0] in WINDOWS_RESERVED:
        filename = "_" + filename

    return filename or "untitled"
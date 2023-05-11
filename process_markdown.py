# /bin/python3

import os
import re
import subprocess
from pathlib import Path
import urllib.request
from collections import defaultdict
import shutil
import argparse
import json

# Define the argument parser
parser = argparse.ArgumentParser(
    description="Process a folder containing .md files with PlantUML diagrams."
)

# Add an optional argument for the input folder
parser.add_argument(
    "-f",
    "--folder",
    default="docs",
    help="Path to the folder containing the .md files (default: 'docs/').",
)

# Parse the command-line arguments
args = parser.parse_args()

input_folder = args.folder

# Remove special characters from a file name, replace spaces with underscores, and convert to lowercase
def sanitize_filename(filename):
    filename = filename.lower()
    filename = filename.replace(" ", "_")
    return re.sub(r'[\\/:"*?<>|()]+', "", filename)

# Replace spaces in a link with '%20'
def sanitize_link(link):
    return link.replace(" ", "%20")


def make_human_readable(s: str) -> str:
    # Read the acronyms from a JSON file
    with open("acronyms.json", "r") as f:
        acronyms = json.load(f)

    # Create a regex pattern for acronyms that should be preserved as is (case-insensitive)
    acronyms_pattern = re.compile(
        r"\b(" + "|".join(acronyms) + r")[sS]?\b", re.IGNORECASE
    )
    # Replace '_' with ' ' and capitalize the first letter of each word
    words = s.replace("_", " ").split()

    # Process each word separately
    processed_words = []
    for word in words:
        match = acronyms_pattern.search(word)
        if match:
            # If the word is an acronym, replace it with the correct acronym from the list
            correct_acronym = next(
                acronym
                for acronym in acronyms
                if acronym.lower() == match.group().lower()
            )
            processed_word = correct_acronym
        else:
            # Otherwise, capitalize the first letter
            processed_word = word.capitalize()
        processed_words.append(processed_word)

    return " ".join(processed_words)


def create_readme_section(title, link):
    return f"### {title}\n[Link]({sanitize_link(link)})\n\n"


# Download plantuml.jar locally
plantuml_jar_url = "https://downloads.sourceforge.net/project/plantuml/plantuml.jar"
plantuml_jar = "plantuml.jar"
urllib.request.urlretrieve(plantuml_jar_url, plantuml_jar)

# Remove the existing 'generated' directory if it exists
if os.path.exists(f"{input_folder}/generated"):
    shutil.rmtree(f"{input_folder}/generated")
# Remove the existing README.md if it exists
if os.path.exists(f"{input_folder}/README.md"):
    os.remove(f"{input_folder}/README.md")

# Find all .md files in the input_folder directory and its subdirectories, excluding the 'generated' subfolder
md_files = [f for f in Path(input_folder).rglob("*.md") if "generated" not in f.parts]

# Regex patterns to match PlantUML code blocks and titles
plantuml_pattern = re.compile(r"```plantuml\n(.*?)\n```", re.DOTALL | re.MULTILINE)
title_pattern = re.compile(r"title\s+(.+)", re.MULTILINE)

readme_entries = []
plantuml_files = []

# Initialize a dictionary to store the file hierarchy
file_hierarchy = defaultdict(list)

for md_file in md_files:
    with open(md_file, "r") as file:
        content = file.read()

    # Check if there are PlantUML diagrams in the .md file
    plantuml_sections = plantuml_pattern.findall(content)
    if not plantuml_sections:
        file_hierarchy[
            len(list(md_file.parent.relative_to(input_folder).parts))
        ].append(
            (
                list(md_file.parent.relative_to(input_folder).parts),
                md_file.relative_to(input_folder),
            )
        )
        continue

    # Find PlantUML code blocks and replace them with generated images
    new_content = content
    for i, plantuml_code in enumerate(plantuml_sections):
        # Extract the title if it exists and sanitize it for use as a file name
        title_match = title_pattern.search(plantuml_code)
        if title_match:
            diagram_name = sanitize_filename(title_match.group(1))
        else:
            diagram_name = f"{sanitize_filename(md_file.stem)}_{i}"

        # Create a temporary .puml file for the PlantUML code block
        temp_puml_file = f"{diagram_name}.puml"
        with open(temp_puml_file, "w") as temp_file:
            temp_file.write(plantuml_code)

        # Generate the PNG diagram in the 'docs/generated/diagrams' subfolder
        output_dir = f"{input_folder}/generated/{md_file.parent.relative_to(input_folder)}/diagrams"
        os.makedirs(output_dir, exist_ok=True)
        output_png = f"{output_dir}/{diagram_name}.png"
        subprocess.run(
            ["java", "-jar", plantuml_jar, "-tpng", "-o", output_dir, temp_puml_file]
        )

        # Replace the PlantUML code block with the generated image
        rel_output_png = os.path.relpath(output_png, start=md_file)
        new_content = new_content.replace(
            f"```plantuml\n{plantuml_code}\n```",
            f"![{diagram_name}]({rel_output_png})",
        )

        # Remove the temporary .puml file
        os.remove(temp_puml_file)

    # Create a new .md file with the generated diagrams included, in the 'docs/generated' subfolder
    new_md_file_path = Path(
        f"{input_folder}/generated/{md_file.relative_to(input_folder)}"
    )
    os.makedirs(os.path.dirname(new_md_file_path), exist_ok=True)
    with open(new_md_file_path, "w") as new_file:
        new_file.write(new_content)

    # Add an entry for the README.md file
    rel_path = new_md_file_path.relative_to(input_folder)
    sections = list(rel_path.parts)[:-1]
    file_hierarchy[len(sections)].append((sections, rel_path))
    # Add the Markdown file containing PlantUML sections to the plantuml_files list
    plantuml_files.append(rel_path)

# Create a list of section dictionaries
doc_structure = []

for nesting_level, entries in file_hierarchy.items():
    for sections, rel_path in entries:
        title = make_human_readable(rel_path.stem)
        link = rel_path
        section_dict = {
            "title": title,
            "level": nesting_level,
            "file_path": str(link),
            "has_plantuml": rel_path in plantuml_files,
        }
        doc_structure.append(section_dict)

# Group sections by their level
sections_by_level = {}
for section in doc_structure:
    level = section["level"]
    if level not in sections_by_level:
        sections_by_level[level] = []
    sections_by_level[level].append(section)

# Sort sections within each level alphabetically
for level in sections_by_level:
    sections_by_level[level] = sorted(
        sections_by_level[level], key=lambda x: x["title"]
    )

# Combine sorted sections back into a single list
sorted_sections = []
for level in sorted(sections_by_level.keys()):
    sorted_sections.extend(sections_by_level[level])

with open(f"{input_folder}/README.md", "w") as readme_file:
    readme_file.write("# Documentation\n")
    readme_file.write(
        "This folder contains the comprehensive documentation for the project, detailing its components, systems, and subsystems. The documentation is organized in a clear hierarchical structure to facilitate easy navigation and understanding.\n\n"
    )

    readme_file.write("## General Documentation\n")
    for section in sorted_sections:
        if not section["has_plantuml"]:
            indent_level = section["level"]
            indent = "  " * (indent_level - 1)
            title = section["title"]
            link = f"{section['file_path']}"
            line = create_readme_section(title, link)
            readme_file.write(line)

    readme_file.write("\n## Design Documentation\n")
    for section in sorted_sections:
        if section["has_plantuml"]:
            indent_level = section["level"]
            indent = "  " * (indent_level - 1)
            title = section["title"]
            link = f"{section['file_path']}"
            line = create_readme_section(title, link)
            readme_file.write(line)

    readme_file.write("\n*Note: This README is autogenerated*\n")

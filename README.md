# PlantUML Generator

This document provides an overview of the PlantUML Generator script, explaining its functionality step by step.

## Overview

The purpose of the script is to automate the generation of PlantUML diagrams in Markdown files within (by default) the `docs` folder. A different folder can be passed into the script with the --folder or -f argument. The script also creates a new folder called `{folder}/generated`, where it saves the updated Markdown files containing the generated diagrams. Additionally, the script generates a `README.md` file in the supplied documentation folder, which lists and links to all the documentation files, separated into "General Documentation" and "Design Documentation" sections based on whether they contain PlantUML diagrams.

## Step by Step Explanation

1. Import necessary modules and define helper functions:
   - Import required libraries and modules.
   - Define `sanitize_filename()`, `make_human_readable()`, and `create_readme_section()` helper functions.

2. Download `plantuml.jar`:
   - Download the PlantUML JAR file from the official source.

3. Clean up existing files and folders:
   - Remove the existing `docs/generated` folder and `docs/README.md` file, if they exist.

4. Find all Markdown files:
   - Find all Markdown files within the `docs` folder and its subdirectories, excluding the `generated` subfolder.

5. Process each Markdown file:
   - For each Markdown file, check for the presence of PlantUML diagrams.
   - If there are no PlantUML diagrams, add the file to the file hierarchy.
   - If there are PlantUML diagrams, replace the code blocks with generated images.

6. Create a new Markdown file with generated diagrams:
   - Save the updated content with generated diagrams in the `docs/generated` subfolder, mirroring the original file structure.

7. Update the file hierarchy:
   - Add the new file to the file hierarchy.

8. Create the `README.md` file:
   - Create a list of section dictionaries based on the file hierarchy.
   - Group the sections by their level, then sort them alphabetically within each level.
   - Write the `README.md` file, separating sections into "General Documentation" and "Design Documentation" based on whether they contain PlantUML diagrams.


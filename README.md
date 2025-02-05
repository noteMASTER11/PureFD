# Directory Structure Explorer

This repository contains a Python script that recursively scans a specified directory, computes file metadata (such as file size and SHA-1 hash), and generates an HTML file that displays the directory structure in a collapsible tree table format. The generated HTML file uses Bootstrap for styling and jQuery along with the jQuery TreeTable plugin for interactive functionality, including sorting columns and toggling directory expansion.

## Features

- **Recursive Directory Scanning**: The script traverses the specified directory and all its subdirectories.
- **File Metadata Extraction**: For each file, the script collects:
  - **Creation Time**: Formatted as `YYYY-MM-DD HH:MM:SS`.
  - **File Size**: Displayed in Bytes, KB, MB, or GB.
  - **SHA-1 Hash**: Computed asynchronously to ensure responsiveness even with large files.
- **Directory Representation**: Directories are marked with a folder icon (&#128193;) and are clickable to expand or collapse their contents.
- **Interactive HTML Output**:
  - **Collapsible Tree Table**: Visualize the folder hierarchy with expandable/collapsible rows.
  - **Sortable Columns**: Clickable headers allow sorting by Name, Creation Time, Size, or SHA-1.
  - **Copy SHA-1 Functionality**: Each file row includes a "Copy SHA-1" button aligned to the right in its SHA-1 column. Clicking the button copies the file's SHA-1 hash to the clipboard.
- **Asynchronous Processing**: Utilizes Python’s `asyncio` module to concurrently process files and directories, which improves performance on large directory structures.
- **Progress Feedback**: Displays the number of processed files in the console during execution.

## How It Works

1. **Directory Scanning**:
   - The script first counts the total number of files in the specified directory.
   - It then asynchronously processes each file and directory to collect metadata (creation time, size, and SHA-1 for files; name and creation time for directories).

2. **HTML Generation**:
   - An HTML page is generated that includes:
     - A Bootstrap-styled table.
     - A row for each file or directory.
     - Directories are displayed with a folder icon and their names wrapped in a clickable element that toggles expansion.
     - Files display their metadata along with a "Copy SHA-1" button.

3. **Interactive Elements**:
   - The generated HTML uses the jQuery TreeTable plugin to allow the tree structure to be expanded and collapsed.
   - Clicking on the header of any column sorts the table by that column.
   - The "Copy SHA-1" button utilizes the Clipboard API to copy the hash value to the clipboard.

## Prerequisites

- **Python 3.7+**: The script uses `asyncio` and other modern Python features.
- **Internet Connection**: The HTML output loads Bootstrap, jQuery, and the jQuery TreeTable plugin from CDNs.

## Usage

1. **Configure the Script**:
   - Open the script and modify the `directory` variable in the `main()` function to point to the directory you want to scan.
   - Set the `output_file` variable in the `main()` function to the desired location and filename for the generated HTML file.

2. **Run the Script**:
   - Execute the script via the command line:
     ```bash
     python your_script_name.py
     ```
   - The console will display progress information as files are processed.

3. **View the HTML Output**:
   - Open the generated HTML file (e.g., `DirectoryStructure.html`) in your web browser.
   - Use the interactive table to expand/collapse directories, sort columns, and copy SHA-1 hashes.

## Customization

- **Styling**: You can modify the embedded CSS in the HTML generation section to change the appearance.
- **Functionality**: The jQuery TreeTable plugin drives the tree and sorting functionality. Refer to its [documentation](https://ludo.cubicphuse.nl/jquery-treetable/) for further customizations.

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgements

- [Bootstrap](https://getbootstrap.com/)
- [jQuery](https://jquery.com/)
- [jQuery TreeTable Plugin](https://ludo.cubicphuse.nl/jquery-treetable/)
- Thanks to the open-source community for providing the libraries and tools that make this project possible.

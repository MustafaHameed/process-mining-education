# Installing Graphviz for Process Mining Visualizations

The process mining visualizations in this project require Graphviz to be installed on your system. The Python package `graphviz` only provides a Python interface to the Graphviz software, not the software itself.

## Windows Installation Instructions

1. Download the Graphviz installer from the official site:
   - Go to: https://graphviz.org/download/
   - Under Windows, download the stable release installer (EXE)

2. Run the installer:
   - Follow the installation prompts
   - **IMPORTANT**: When asked, check the option to add Graphviz to your system PATH

3. Verify the installation:
   - Open a new PowerShell or Command Prompt window
   - Run the command: `dot -v`
   - If you see version information, Graphviz is installed correctly

4. If the verification doesn't work:
   - You may need to add Graphviz to your PATH manually
   - Add the Graphviz `bin` directory to your PATH (usually `C:\Program Files\Graphviz\bin`)

## Manual PATH Configuration (if needed)

If Graphviz is installed but not in your PATH:

1. Find your Graphviz installation directory (typically `C:\Program Files\Graphviz`)
2. Right-click on "This PC" or "My Computer" and select "Properties"
3. Click on "Advanced system settings"
4. Click the "Environment Variables" button
5. Under "System variables", find and select the "Path" variable, then click "Edit"
6. Click "New" and add the path to the Graphviz bin directory (e.g., `C:\Program Files\Graphviz\bin`)
7. Click "OK" on all dialogs to save the changes
8. Restart your terminal or command prompt
9. Test by running `dot -v`

## Troubleshooting

If you still encounter the error "failed to execute WindowsPath('dot'), make sure the Graphviz executables are on your systems' PATH":

1. Make sure you've installed Graphviz, not just the Python package
2. Confirm the Graphviz bin directory is in your PATH
3. Restart your terminal/command prompt after installation
4. Restart your Python IDE or development environment

## For Other Operating Systems

- **MacOS**: Install using Homebrew: `brew install graphviz`
- **Linux**: Install using your package manager:
  - Ubuntu/Debian: `sudo apt-get install graphviz`
  - Fedora/RHEL: `sudo dnf install graphviz`

After installation, run the process discovery visualization again to see if the Graphviz-based visualizations work properly.

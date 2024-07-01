# Project Name
## ABCGovt Web scrapping
### Python Installation Process
Before proceeding, ensure Python is installed on your system. If not, you can download and install Python from [python.org](https://www.python.org/downloads/).
### Clone the Project
```bash
git clone https://github.com/exoticaitsolutions/ABCGovtWebscrapping.git
```

## Navigate to the Project Directory

```bash
  cd ABCGovtWebscrapping
```
```
py -m venv myworld
```
Unix/MacOS:
```
 python3 -m venv myworld
```
Then you have to activate the environment, by typing this command:
Windows:
```
myworld\Scripts\activate.bat
```
Unix/MacOS:
```
source myworld/bin/activate
```

# Install Dependencies
### Using requirements.txt

**Windows:**

```bash
python.exe -m pip install -r requirements.txt
```
**Unix/MacOS/Linux:**
```
pip install -r requirements.txt
```
# Individual Dependencies
***pyppeteer***
```
pip install pyppeteer
```

# Run Project
**Windows:**

```bash
python.exe license_report_gen.py
```

**Unix/MacOS/Linux:**

```bash
python3 license_report_gen.py
```

# To create a windows executable ".exe" file.
```bash
pip install babel
```

# Generates the spec file
#### Optional Step:#### Already completed....
```bash
pyinstaller --onefile license_report_gen.py  
```
# Modify the spec file to include 'babel.numbers' as a hidden import


# Build the executable using the spec file
```bash
pyinstaller license_report_gen.spec
```
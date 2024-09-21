This repository contains Python scripts designed to extract data from [wildberries.ru](wildberries.ru) via its API. You can collect information about specific goods (products) and save it in .xlsx files.
 
## Description
The main script collects the following data fields (it's easily expandable though):
- Link
- ID
- Name
- Brand name
- Brand ID
- Price
- Discounted price
- Rating
- Number of reviews
- Number of sales

The script can scan items for the entire category of goods, or using search keywords.

For development purposes, see the docstrings inside the Parser class.

## Installation
1. Clone and navigate to the repository:
    ```
    git clone git@github.com:avrtt/wildberries-parsers.git
    cd wildberries-parsers
    ```

2. For stable version, navigate to the folder:
    ```
    cd stable-version
    ```

    There is also a legacy version that is still work, but less optimized. If you need, navigate to another folder instead:
    ```
    cd legacy-version
    ```

3. Since using virtual environments is a good practice, I highly recommend you to create one:
    ```
    python3 -m venv venv
    ```

    Then activate the virtual environment:
    - On Linux/macOS:
        ```
        source venv/bin/activate
        ```
    - On Windows:
        ```
        venv\Scripts\activate
        ```

4. Install the required dependencies:
    ```
    pip install -r requirements.txt
    ```

5. Run:
    ```
    python start.py
    ```

## Usage
After running the script, follow the instructions: select parsing method and input your data. You will get an .xlsx file with the parsed content once the program is finished.

Make sure you have a stable connection while parsing items since the script utilizes the `requests` library.

## Contribution
Feel free to open PRs and issues.

## License
These scripts is licensed under the MIT License. See the LICENSE file for details.



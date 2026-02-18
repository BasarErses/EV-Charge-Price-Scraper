# Price Scraper Setup Guide

This guide will walk you through setting up and running the EV Charging Price Scraper system on your computer.

## 1. Prerequisites

Before you begin, ensure you have the following installed on your system:

- **Python 3.10 or higher**: Download from [python.org](https://www.python.org/downloads/).
- **Google Chrome** (recommended for the scraper to work correctly).
- **Git** (optional, useful if you want to clone/update code easily).

## 2. Setting Up

Follow these steps to set up the project environment:

### Step 1: Open Terminal
- **Mac**: Open `Terminal` (Command + Space, type "Terminal").
- **Windows**: Open `Command Prompt` or `PowerShell`.

### Step 2: Navigate to the Project Folder
Use the `cd` command to go to the folder where you have these files.
```bash
cd "path/to/Price Scraper"
```
*(Tip: You can type `cd ` and then drag the folder from Finder/Explorer into the terminal window to auto-fill the path)*

### Step 3: Create a Virtual Environment
This keeps the project dependencies isolated.
```bash
python3 -m venv .venv
```
*(On Windows, you might use `python -m venv .venv`)*

### Step 4: Activate the Virtual Environment
- **Mac/Linux**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows**:
  ```bash
  .venv\Scripts\activate
  ```
*(You should see `(.venv)` appear at the start of your terminal line)*

### Step 5: Install Dependencies
Run this command to install all required libraries:
```bash
pip install -r requirements.txt
```

### Step 6: Install Playwright Browsers
The scraper uses Playwright to browse websites. You need to install its browser binaries:
```bash
playwright install
```

## 3. Configuration

You need to set up the API keys for the AI extraction to work.

1.  **Duplicate the example file**:
    - Locate the file named `.env.example` in the project folder.
    - Copy it and rename the copy to `.env`.

2.  **Edit the `.env` file**:
    - Open `.env` with any text editor (Notepad, TextEdit, VS Code).
    - Add your API key for the AI provider you want to use.

    **Example for Claude (Anthropic):**
    ```ini
    AI_PROVIDER=claude
    ANTHROPIC_API_KEY=sk-ant-api03-YOUR-KEY-HERE
    ```

    **Example for Gemini (Google):**
    ```ini
    AI_PROVIDER=gemini
    GEMINI_API_KEY=AIzaSyD-YOUR-KEY-HERE
    ```

    **Example for Ollama (Local AI - Free, no key needed):**
    - Install [Ollama](https://ollama.com/) separately.
    - Run `ollama pull llama3.1` in your terminal.
    - Set `.env` to:
      ```ini
      AI_PROVIDER=ollama
      OLLAMA_MODEL=llama3.1
      ```

3.  **Check Links File**:
    - Ensure `links copy.txt` is in the folder. This file contains the list of URLs to scrape. You can edit it to add or remove links.

## 4. Running the Application

Now you are ready to start the scraper.

1.  Ensure you are still in the project folder and the virtual environment is active (if not, run `source .venv/bin/activate` again).
2.  Run the web server:
    ```bash
    python app.py
    ```
3.  You should see output indicating the server has started on `http://0.0.0.0:8000`.

## 5. Using the System

1.  Open your web browser (Chrome, Safari, etc.).
2.  Go to: [http://localhost:8000](http://localhost:8000)
3.  You will see the "EV Price Assistant" chat interface.
4.  Click the **"Start Full Scrape"** button.
    - The system will start visiting the URLs in `links copy.txt`.
    - You will see a progress bar updating in real-time.
    - *Note: Scraping 160+ sites can take some time.*
5.  **Download Results**:
    - When the scraping reaches 100%, a message "**✅ Scraping Complete!**" will appear.
    - A **"Download Prices"** green button will appear below it.
    - Click it to download `prices_flat.csv`, which contains all the extracted data formatted for Excel.

## 6. Troubleshooting

-   **"Module not found" error**:
    - Make sure you activated the virtual environment (`source .venv/bin/activate`) before running `python app.py`.
    - Try running `pip install -r requirements.txt` again.

-   **Browser crashes or execution hangs**:
    - Ensure you ran `playwright install` successfully.
    - Check your internet connection.

-   **API Errors (e.g., 401 Unauthorized)**:
    - Double-check your API key in the `.env` file. Ensure there are no extra spaces.

-   **Address already in use**:
    - If `python app.py` says port 8000 is busy, another instance might be running. 
    - You can find and kill it, or just restart your computer.

---
**Enjoy your scraping!**

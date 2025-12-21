# 🚀 Complete Setup Guide

## Step-by-Step Instructions

### Step 1: Create Project Folder Structure

Open your terminal/command prompt and run:

```bash
# Create main folder
mkdir data-organizer
cd data-organizer

# Create utils subfolder
mkdir utils
```

Your structure should look like:
```
data-organizer/
└── utils/
```

### Step 2: Create All Files

Create these files in your project folder:

#### Root Directory Files:
1. **app.py** - Copy the main app code
2. **requirements.txt** - Copy the dependencies
3. **README.md** - Copy the documentation

#### Utils Directory Files:
1. **utils/__init__.py** - Copy the package initializer (can be empty)
2. **utils/parser.py** - Copy the parsing module
3. **utils/scraping.py** - Copy the scraping module
4. **utils/detection.py** - Copy the detection module
5. **utils/cleaning.py** - Copy the cleaning module
6. **utils/organization.py** - Copy the organization module
7. **utils/export.py** - Copy the export module

### Step 3: Install Python (if needed)

Check if Python is installed:
```bash
python --version
```

If not installed, download from: https://www.python.org/downloads/
- Get Python 3.9 or higher

### Step 4: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate it
# On Windows:
venv\Scripts\activate

# On Mac/Linux:
source venv/bin/activate
```

You should see `(venv)` in your terminal prompt.

### Step 5: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs:
- streamlit
- pandas
- requests
- beautifulsoup4
- lxml
- openpyxl

### Step 6: Test Run Locally

```bash
streamlit run app.py
```

Or:

```bash
python -m streamlit run app.py
```

Your browser should automatically open to `http://localhost:8501`

### Step 7: Test the App

Try these tests:

**Test 1: Paste Text**
```
Date, Sales
2024-01-01, 1500
2024-01-02, 2300
2024-01-03, 1800
```

**Test 2: Web Scraping**
Try URL: `https://en.wikipedia.org/wiki/List_of_countries_by_GDP_(nominal)`

**Test 3: Upload File**
Create a simple CSV and upload it.

---

## Deploying to Internet (FREE)

### Option 1: Streamlit Community Cloud (Recommended)

#### A. Create GitHub Account
1. Go to https://github.com
2. Sign up (free)
3. Verify your email

#### B. Create Repository
1. Click "+" → "New repository"
2. Name: `data-organizer`
3. Make it **Public**
4. Don't initialize with README (we have our own)
5. Click "Create repository"

#### C. Upload Your Code

**Option C1: Using GitHub Website (Easiest)**
1. In your new repository, click "uploading an existing file"
2. Drag and drop ALL your files (including utils folder)
3. Click "Commit changes"

**Option C2: Using Git Command Line**
```bash
# In your project folder
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/data-organizer.git
git push -u origin main
```

#### D. Deploy on Streamlit Cloud
1. Go to https://share.streamlit.io
2. Click "Sign in" → Use your GitHub account
3. Click "New app"
4. Repository: `your-username/data-organizer`
5. Branch: `main`
6. Main file path: `app.py`
7. Click "Deploy!"

Wait 2-5 minutes for deployment.

Your app will be live at: `https://YOUR-APP-NAME.streamlit.app`

---

## Troubleshooting Common Issues

### Issue 1: "ModuleNotFoundError: No module named 'utils'"

**Solution:**
- Make sure `utils/__init__.py` exists (even if empty)
- Run `streamlit run app.py` from the project root folder
- Check your folder structure matches exactly

### Issue 2: "streamlit: command not found"

**Solution:**
```bash
pip install streamlit
# or
pip install --upgrade streamlit
```

### Issue 3: Excel Export Fails

**Solution:**
```bash
pip install openpyxl
```

### Issue 4: Web Scraping Returns None

**Reasons:**
- Website blocks scrapers
- No tables on page
- Network issue

**Solution:**
- Try a different URL
- Check if site has tables
- Add `time.sleep(1)` in scraping code

### Issue 5: Import Errors on Streamlit Cloud

**Solution:**
Make sure `requirements.txt` has all dependencies listed

### Issue 6: App Crashes with Large Data

**Solution:**
- Streamlit Cloud free tier has memory limits
- Try smaller datasets
- Consider upgrading Streamlit Cloud plan

---

## File Checklist

Before deploying, make sure you have:

```
✓ app.py
✓ requirements.txt
✓ README.md
✓ utils/__init__.py
✓ utils/parser.py
✓ utils/scraping.py
✓ utils/detection.py
✓ utils/cleaning.py
✓ utils/organization.py
✓ utils/export.py
```

---

## Next Steps After Deployment

1. **Test Your Live App** - Try all features
2. **Share the Link** - Give it to potential users
3. **Get Feedback** - See what people need
4. **Start Phase 2** - Add payments, user accounts
5. **Monitor Usage** - Check Streamlit analytics

---

## Quick Commands Reference

```bash
# Create project
mkdir data-organizer && cd data-organizer
mkdir utils

# Install packages
pip install -r requirements.txt

# Run locally
streamlit run app.py

# Git commands
git init
git add .
git commit -m "message"
git push

# Update deployment
git add .
git commit -m "updates"
git push
# Streamlit Cloud auto-updates!
```

---

## Getting Help

- **Streamlit Docs**: https://docs.streamlit.io
- **Pandas Docs**: https://pandas.pydata.org/docs/
- **Python Docs**: https://docs.python.org/3/

---

**Good luck! 🚀 You're ready to launch your app!**
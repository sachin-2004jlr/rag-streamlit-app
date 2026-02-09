# Push and Deploy Benchmark Report - Step by Step

## Step 1: Verify Files Are Ready

Run this to check everything is in place:

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
python check_pages.py
```

You should see:
- ✓ pages/1_Benchmark_Report.py exists

## Step 2: Add All Files to Git

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
git add .
git status
```

**Check that you see:**
- `pages/1_Benchmark_Report.py` (modified or new)
- `.streamlit/config.toml` (new)

## Step 3: Commit and Push

```powershell
git commit -m "Fix Benchmark Report page for Streamlit Cloud"
git push origin main
```

## Step 4: Force Streamlit Cloud to Redeploy

**Option A - Via Dashboard (Recommended):**
1. Go to https://share.streamlit.io
2. Sign in
3. Click on your app
4. Click **⋮** (three dots menu) → **Reboot app**
5. Wait 30-60 seconds

**Option B - Via Settings:**
1. Go to your app dashboard
2. Click **Settings**
3. Scroll down and click **Reboot app**
4. Wait 30-60 seconds

## Step 5: Check Your App

1. Open your Streamlit Cloud URL
2. **Hard refresh** the page: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
3. Look at the **left sidebar** - you should see:
   - Your main app name (or "Multi Model RAG")
   - **Benchmark Report** ← This should appear!

## Step 6: If Still Not Showing

### Check Streamlit Cloud Logs:

1. Go to https://share.streamlit.io
2. Click your app
3. Click **Manage app** → **Logs**
4. Look for errors mentioning:
   - `1_Benchmark_Report.py`
   - `pages`
   - Any Python errors

### Verify File Was Pushed:

```powershell
git log --oneline -3
git ls-tree -r HEAD --name-only | findstr pages
```

You should see `pages/1_Benchmark_Report.py` in the output.

### Try Creating a Simple Test Page:

If the Benchmark Report still doesn't show, let's test with a minimal page:

Create `pages/0_Test.py`:
```python
import streamlit as st
st.write("Test page works!")
```

Then:
```powershell
git add pages/0_Test.py
git commit -m "Add test page"
git push origin main
```

If the Test page shows but Benchmark Report doesn't, there's an error in the Benchmark Report code. Check the logs.

## Common Issues:

1. **Page not in sidebar**: File must be named `pages/X_Name.py` where X is a number
2. **Syntax error**: Check Streamlit Cloud logs
3. **Import error**: All imports must be in requirements.txt
4. **Caching**: Hard refresh browser (Ctrl+Shift+R)

## Still Not Working?

Share:
1. What you see in Streamlit Cloud logs
2. Output of `git ls-files pages/`
3. Whether the Test page (if created) shows up

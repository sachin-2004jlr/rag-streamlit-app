# End-to-End Setup Guide: Benchmark Report Page

## Step 1: Test Locally First (Verify It Works)

Open PowerShell in your project folder:

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
streamlit run app.py
```

**What to check:**
- Browser opens at `http://localhost:8501`
- In the **left sidebar**, you should see:
  - **Multi Model RAG** (main page)
  - **Benchmark Report** (new page)
- Click **Benchmark Report** - it should show "No benchmark results yet" (this is normal)

If you DON'T see "Benchmark Report" in the sidebar:
- Stop Streamlit (Ctrl+C)
- Check that `pages/1_Benchmark_Report.py` exists
- Restart: `streamlit run app.py`

---

## Step 2: Push to GitHub

Once you see the page locally, push to GitHub:

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
git add .
git status
git commit -m "Add Benchmark Report page"
git push origin main
```

**Wait 2-3 minutes** for Streamlit Cloud to redeploy.

---

## Step 3: Check Streamlit Cloud

1. Go to your Streamlit Cloud URL (the one you already have)
2. Look at the **left sidebar** - you should see:
   - **Multi Model RAG** (or just the app name)
   - **Benchmark Report**
3. Click **Benchmark Report**

**If you still don't see it:**

### Option A: Check Streamlit Cloud Logs
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Click your app
3. Click **Manage app** → **Logs**
4. Look for errors mentioning `1_Benchmark_Report.py`

### Option B: Force Redeploy
1. In Streamlit Cloud dashboard
2. Click **⋮** (three dots) → **Reboot app**
3. Wait 1 minute, refresh your app URL

### Option C: Verify Files Were Pushed
```powershell
git log --oneline -5
git ls-files | findstr pages
git ls-files | findstr benchmark
```

You should see `pages/1_Benchmark_Report.py` and all benchmark files listed.

---

## Step 4: Add Benchmark Data (Optional - To See Real Results)

To see actual benchmark results instead of "No benchmark results yet":

**On your local PC:**

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
python benchmark/run_benchmark.py "c:\path\to\your\AKSHITHA_YC_Major_Project_report.pdf"
```

This creates `benchmark/final_benchmark_results.json`.

**Then push it:**

```powershell
git add benchmark/final_benchmark_results.json
git commit -m "Add benchmark results"
git push origin main
```

After redeploy (2-3 min), refresh the **Benchmark Report** page - you'll see the full report with questions, answers, and metrics.

---

## Troubleshooting

### Page doesn't appear in sidebar

**Check:**
- File is named exactly: `pages/1_Benchmark_Report.py` (not `Benchmark_Report.py` or `benchmark_report.py`)
- File is in `pages/` folder (not `benchmark/pages/`)
- No syntax errors in the file

**Fix:**
```powershell
# Verify structure
dir pages
# Should show: 1_Benchmark_Report.py
```

### "Module not found" or import errors

**Check:** All files are committed:
```powershell
git status
# Should show nothing (all committed)
```

### Page shows but is blank/error

**Check Streamlit Cloud logs** (see Step 3, Option A)

**Common fixes:**
- Make sure `benchmark/final_benchmark_results.json` exists (or the page will show the "no results" message)
- Check file permissions

---

## Quick Verification Checklist

- [ ] `pages/1_Benchmark_Report.py` exists
- [ ] `benchmark/` folder exists with all files
- [ ] Tested locally - page shows in sidebar
- [ ] Pushed to GitHub (`git push origin main`)
- [ ] Streamlit Cloud redeployed (wait 2-3 min)
- [ ] Page appears in sidebar on Streamlit Cloud
- [ ] (Optional) Added `final_benchmark_results.json` and pushed

---

## Still Not Working?

Run this diagnostic:

```powershell
cd "c:\Users\sachi\Desktop\RAG System"
python -c "import os; print('Pages folder:', os.path.exists('pages')); print('Benchmark page:', os.path.exists('pages/1_Benchmark_Report.py')); print('Benchmark JSON:', os.path.exists('benchmark/final_benchmark_results.json'))"
```

Share the output if you need more help.

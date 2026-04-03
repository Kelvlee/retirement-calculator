# Retirement Projections Calculator - Web Version

Interactive retirement calculator for bambootrading.com.au

## Features

- **Real-time Interactive Charts**: Drag sliders, chart updates instantly
- **Plotly Visualizations**: Zoom, pan, hover for exact values
- **Two-Phase Projection**: Growth (contributions) + Drawdown (withdrawals)
- **CSV Export**: Download year-by-year breakdown
- **Mobile Responsive**: Works on phone, tablet, desktop

## Local Testing

```bash
cd "C:\Users\kelvi\Python Code\Financial Planning\Web"
streamlit run retirement_calculator.py
```

Opens in browser at: http://localhost:8501

## Deployment to Streamlit Cloud

### Step 1: Create GitHub Repository

1. Go to https://github.com
2. Click "New repository"
3. Name: `retirement-calculator`
4. Visibility: Private (or Public, your choice)
5. Click "Create repository"

### Step 2: Upload Files

**Option A: Via GitHub Web Interface**
1. Click "uploading an existing file"
2. Drag these files:
   - `retirement_calculator.py`
   - `requirements.txt`
   - `README.md`
3. Commit changes

**Option B: Via Git Command Line** (if you have Git installed)
```bash
cd "C:\Users\kelvi\Python Code\Financial Planning\Web"
git init
git add .
git commit -m "Initial commit - Retirement Calculator"
git remote add origin https://github.com/YOUR_USERNAME/retirement-calculator.git
git push -u origin main
```

### Step 3: Deploy to Streamlit Cloud

1. Go to https://share.streamlit.io
2. Sign in with GitHub
3. Click "New app"
4. Repository: `YOUR_USERNAME/retirement-calculator`
5. Branch: `main`
6. Main file path: `retirement_calculator.py`
7. Click "Deploy!"

Wait 2-3 minutes for deployment.

You'll get a URL like: `https://yourapp.streamlit.app`

### Step 4: Configure Custom Domain (Optional)

**In GoDaddy DNS Settings:**

1. Login to GoDaddy
2. My Products → Domains → bambootrading.com.au → DNS
3. Add new record:
   - Type: **CNAME**
   - Host: **calculator**
   - Points to: **yourapp.streamlit.app**
   - TTL: **600** (10 minutes)
4. Save

**Wait 10-60 minutes for DNS propagation.**

Result: `https://calculator.bambootrading.com.au` → your calculator

## WordPress Integration

### Create New Page in WordPress

1. Login to WordPress Dashboard
2. Pages → Add New
3. Title: **Retirement Calculator**
4. Use Custom HTML block or Elementor HTML widget
5. Paste this code:

```html
<iframe
    src="https://yourapp.streamlit.app"
    width="100%"
    height="1400px"
    frameborder="0"
    style="border: none; overflow: hidden;">
</iframe>
```

6. Publish page

### Add to Navigation Menu

1. Appearance → Menus
2. Select your main menu (usually "Primary Menu")
3. Add "Retirement Calculator" page
4. Save menu

### Add Button to Homepage (Optional)

Using Elementor:
1. Edit homepage
2. Add Button widget
3. Button text: "Try Our Retirement Calculator"
4. Link: `/retirement-calculator`
5. Style: Green (#32CD32) background, white text
6. Update page

Or using Custom HTML:
```html
<a href="/retirement-calculator"
   style="display: inline-block;
          background: #32CD32;
          color: white;
          padding: 20px 40px;
          text-align: center;
          border-radius: 10px;
          font-size: 18px;
          text-decoration: none;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
   🎯 Try Our Retirement Calculator
</a>
```

## File Structure

```
Web/
├── retirement_calculator.py    # Main Streamlit app
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── wordpress_integration.html  # Copy/paste code for WordPress
```

## Troubleshooting

### "Module not found" error
Install dependencies:
```bash
pip install -r requirements.txt
```

### Chart not displaying
Clear browser cache or try different browser

### Streamlit app not deploying
- Check requirements.txt has all dependencies
- Ensure repository is public or Streamlit has access
- Check Streamlit Cloud logs for errors

## Support

Contact: kelvin@bambootrading.com.au
Website: https://www.bambootrading.com.au

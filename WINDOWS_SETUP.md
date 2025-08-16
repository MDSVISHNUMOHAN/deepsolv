# 🚀 Shopify Insights Extractor - Windows Setup

## Quick Start for Windows

### Method 1: Automatic Setup (Recommended)

1. **Download all files** to a folder on your Windows computer
2. **Double-click** `setup_windows.bat` 
3. Wait for installation to complete
4. **Run** `python local_app.py` in command prompt
5. **Open browser** to `http://localhost:5000`

### Method 2: Manual Setup

#### Prerequisites
- Python 3.8 or higher installed
- Command prompt access

#### Step-by-step Installation

1. **Open Command Prompt** (cmd)
2. **Navigate to project folder**:
   ```cmd
   cd path\to\shopify-insights-extractor
   ```

3. **Run setup script**:
   ```cmd
   python local_setup.py
   ```

4. **Start the application**:
   ```cmd
   python local_app.py
   ```

5. **Open your browser** and go to:
   ```
   http://localhost:5000
   ```

## 🎯 How to Use

1. Enter a Shopify store URL (e.g., `memy.co.in`, `hairoriginals.com`)
2. Choose analysis type:
   - **Single Analysis**: Basic store insights
   - **Competitive Analysis**: Store + competitor comparison
3. Click "Extract Insights"
4. View comprehensive results including:
   - Product catalog
   - Contact information
   - Social media handles
   - Store policies
   - FAQ analysis

## 📁 Files Created

- `.env` - Local configuration
- `local_shopify_insights.db` - SQLite database for storing results
- `local_config.py` - Configuration overrides

## 🔧 Features Available

✅ **Single Store Analysis**
- Product catalog extraction
- Contact details mining
- Social media discovery
- Policy document analysis

✅ **Competitive Analysis**
- Competitor identification
- Comparative insights
- Market positioning analysis

✅ **Bulk Processing**
- Multiple URL analysis
- Job tracking
- Progress monitoring

✅ **Data Persistence**
- Analysis history
- Export capabilities
- Search and filter results

## 🐛 Troubleshooting

### Common Issues

**Error: "Error occurred during data extraction"**
- This has been fixed in the latest version
- Some Shopify stores may have different data formats
- The application now handles both string and list tag formats

**Database Error**
- Delete `local_shopify_insights.db` and restart
- Run `python local_app.py` again to recreate database

**Port Already in Use**
- Close other applications using port 5000
- Or edit `local_app.py` to use a different port

**Python Not Found**
- Install Python from python.org
- Make sure Python is added to your PATH

## 💡 Tips

- **Test URLs**: Try `allbirds.com`, `bombas.com`, or `mvmt.com`
- **Performance**: Wait for analysis to complete (can take 30-60 seconds)
- **Data Storage**: All results are saved locally in SQLite database
- **Privacy**: No data is sent to external servers except to fetch store data

## 🔄 Updates

**Latest Fix**: Resolved the "'list' object has no attribute 'split'" error for sites like memy.co.in and hairoriginals.com

---

**Need Help?** 
- Check if Python is properly installed: `python --version`
- Ensure all files are in the same folder
- Try rerunning the setup script if installation fails
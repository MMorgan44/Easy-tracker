# Easy Tracking Pro - Streamlit Edition 🦷

A modern, professional dental auditing application with AI-powered analysis, rebuilt from Tkinter to Streamlit with a sleek, responsive UI.

![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

## ✨ Features

### 📊 Dashboard
- Real-time statistics and metrics
- Severity distribution charts
- Branch performance tracking
- Top doctors by discrepancy count
- Interactive data visualization with Plotly

### 🔍 Analysis
- Manual input for charged services, clinical notes, and approvals
- AI-powered discrepancy detection
- Severity classification (SEVERE, MODERATE, MILD)
- Actionable fix recommendations

### 💬 AI Chat
- Interactive dental audit assistant
- Context-aware responses
- Integration with last analysis results
- Professional terminology support

### 🤖 AI Discrepancy Check
- Load records from Supabase
- Filter by discrepancy status
- Individual record analysis
- Detailed discrepancy reports

### 👨‍⚕️ Doctor Search
- Performance metrics per doctor
- Discrepancy breakdown
- Recent cases overview
- Visual analytics

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip package manager

### Setup

1. **Clone or download the project**
   ```bash
   cd easy_tracking_streamlit
   ```

2. **Create a virtual environment (recommended)**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open in browser**
   The app will automatically open at `http://localhost:8501`

## ⚙️ Configuration

### AI Models

The app supports two AI backends:

#### ☁️ Cerebras Cloud (Default)
- `gpt-oss-120b` (recommended)
- `llama-3.3-70b`
- `llama3.1-8b`
- `qwen-3-235b-a22b-instruct-2507`
- `qwen-3-32b`
- `zai-glm-4.6`

#### 🖥️ Local Ollama
- `deepseek-r1:1.5b` through `deepseek-r1:70b`
- `llama3.2:latest`
- `llama3.1:latest`
- `qwen2.5:latest`
- `mistral:latest`
- `phi3:latest`

### Database

The app connects to Supabase for record storage. Update the credentials in `app.py` if needed:

```python
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-key"
```

## 🎨 UI Features

- **Modern Design**: Clean, professional interface with custom CSS
- **Responsive Layout**: Works on desktop and tablet screens
- **Dark/Light Theme**: Sidebar with dark theme for contrast
- **Interactive Charts**: Plotly-powered visualizations
- **Real-time Updates**: Instant feedback on all operations
- **Custom Typography**: Plus Jakarta Sans for readability

## 📁 Project Structure

```
easy_tracking_streamlit/
├── app.py              # Main Streamlit application
├── requirements.txt    # Python dependencies
└── README.md          # This file
```

## 🔧 Customization

### Adding New AI Models

Edit the model lists in `app.py`:

```python
CEREBRAS_CLOUD_MODELS = [
    "your-new-model",
    ...
]
```

### Modifying Severity Rules

Update the `DISCREPANCY_SEVERITY_RULES` dictionary:

```python
DISCREPANCY_SEVERITY_RULES = {
    "your-new-rule": "SEVERE",
    ...
}
```

### Custom Styling

Modify the CSS in the `st.markdown()` block at the top of `app.py` to customize colors, fonts, and layouts.

## 🔐 Security Notes

- API keys are embedded in the code for demonstration purposes
- For production use, move credentials to environment variables or Streamlit secrets
- Use `.streamlit/secrets.toml` for secure credential storage

## 📝 License

MIT License - feel free to use and modify for your needs.

## 🤝 Support

For issues or feature requests, please contact the development team.

---

Built with ❤️ using Streamlit and Python

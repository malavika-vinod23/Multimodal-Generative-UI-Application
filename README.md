# Generative UI Demo

A Streamlit web application that accepts multimodal inputs (text, files, and images) and dynamically generates a custom user interface using an LLM. The app sends file content to GPT, which returns structured JSON describing the UI layout — widgets, charts, cards, and more — rendered in real time.

## Demo

Input & Configure → Generated Dashboard  
Upload file → describe UI → click Generate → Dashboard appears with charts, metrics, and cards

---

## Features

- Multimodal Input — Upload CSV, TXT, PY, PDF, or JSON files plus an optional image
- Generative UI — LLM outputs structured JSON that drives the entire frontend layout
- Streaming Responses — Live token-by-token display as the LLM generates the UI
- Dynamic Components — Metrics, cards, bar charts, pie charts, line charts, scatter plots, tables, code blocks, sliders, selectboxes, and alerts
- Smart Layout — Components rendered side by side using columns layout
- Image Guidance — Upload a dashboard screenshot or wireframe to influence the generated layout style
- Auto Session Reset — Uploading a new file automatically clears the previous dashboard
- Robust Error Handling — Non-numeric column fallbacks, duplicate column deduplication, BOM stripping, quoted CSV repair

---

## Project Structure

```bash
generative_ui_app/
│
├── app.py              # Main Streamlit application
├── .env                # API key (not committed to GitHub)
├── requirements.txt    # Python dependencies
└── README.md           # This file
```

---

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/generative-ui-demo.git
cd generative-ui-demo
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Set Up API Key

Create a `.env` file in the root directory:

```env
OPENAI_API_KEY=your_openai_api_key_here
```

Never commit your `.env` file to GitHub. It should be included in `.gitignore`.

### 4. Run the App

```bash
streamlit run app.py
```

The app will open at:

```bash
http://localhost:8501
```

---

## Requirements

```txt
streamlit
openai
pandas
matplotlib
python-dotenv
PyPDF2
```

---

## Supported File Types

| File Type | What the LLM Generates |
|---|---|
| `.csv` | Metrics, bar charts, pie charts, line charts, scatter plots, data tables |
| `.txt` | Summary cards, markdown overview, key insight alerts |
| `.py` | Code blocks with syntax highlighting, cards explaining each section |
| `.pdf` | Document summary, key points as cards, markdown overview |
| `.json` | Structured summary, markdown, cards |
| Image (optional) | Guides the layout style — replicates screenshots and follows wireframes |

---

## UI Components

The LLM can generate any combination of these components:

| Component | Description |
|---|---|
| `markdown` | Rich text paragraphs and headings |
| `metric` | KPI number display |
| `card` | Coloured info box |
| `alert` | Info, warning, success, or error message box |
| `divider` | Horizontal section separator |
| `table` | Full interactive data table |
| `bar_chart` | Vertical bar chart |
| `count_bar_chart` | Bar chart counting occurrences of a column |
| `line_chart` | Line chart for trends |
| `scatter_plot` | Scatter plot for correlations |
| `pie_chart` | Pie chart (auto-limited to top 10 slices) |
| `code` | Syntax-highlighted code block |
| `selectbox` | Dropdown widget |
| `slider` | Range slider widget |
| `columns` | Side-by-side layout container |

---

## Example Prompts

### For a CSV file

```text
Create a comprehensive dashboard with a row of 4 metrics,
a bar chart, a pie chart, insight cards, and a full data table
```

### For a Python file

```text
Analyse this Python file and create a code review dashboard
with cards explaining each section and a code block showing
the most important function
```

### For a text file

```text
Summarize this document into a dashboard with key points
as coloured cards, a markdown overview, and a success alert
with the main conclusion
```

### With an image

```text
Create a dashboard in the style of the uploaded image
using my CSV data
```

---

## How It Works

```text
User uploads file + optional image
            ↓
File content extracted (CSV parsed, PDF text extracted, etc.)
            ↓
System prompt built with file content + column info + image context
            ↓
GPT-5.4-mini called with streaming enabled
            ↓
Response streamed live to the screen
            ↓
JSON parsed and validated
            ↓
Components rendered dynamically in Tab 2
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Your OpenAI API key from platform.openai.com |

---

## .gitignore

Make sure your `.gitignore` includes:

```gitignore
.env
__pycache__/
*.pyc
.streamlit/
```

---

## Built With

- Streamlit — Web app framework
- OpenAI API — GPT-5.4-mini for UI generation
- Pandas — Data processing
- Matplotlib — Pie chart rendering
- PyPDF2 — PDF text extraction
- python-dotenv — Environment variable management

---

## Author

Developed as an internship project demonstrating multimodal LLM-powered generative UI.

---

## License

This project is for educational and demonstration purposes.

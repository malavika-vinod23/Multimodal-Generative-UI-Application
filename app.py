import streamlit as st
import pandas as pd
import json
import os
import re
import base64
import matplotlib.pyplot as plt
from io import StringIO
from dotenv import load_dotenv
from openai import OpenAI

# -----------------------------
# Load API Key
# -----------------------------
load_dotenv(override=True)

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

# -----------------------------
# Helper: Case-insensitive column finder
# -----------------------------
def find_column(name, columns):
    if name in columns:
        return name
    for col in columns:
        if col.lower().strip() == name.lower().strip():
            return col
    return None

# -----------------------------
# Helper: Extract file content
# -----------------------------
def extract_file_content(uploaded_file):
    filename = uploaded_file.name
    extension = filename.split(".")[-1].lower()

    if extension == "csv":
        raw = uploaded_file.read().decode("utf-8")
        uploaded_file.seek(0)
        return "csv", raw

    elif extension in ["txt", "py", "json", "md"]:
        content = uploaded_file.read().decode("utf-8")
        return extension, content

    elif extension == "pdf":
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            content = "\n".join(
                page.extract_text() for page in reader.pages
            )
            return "pdf", content
        except Exception as e:
            return "error", str(e)

    else:
        return "unknown", None

# -----------------------------
# Helper: Render a single component
# -----------------------------
def render_component(component, data, columns):
    component_type = component.get("type")

    # ---------- MARKDOWN ----------
    if component_type == "markdown":
        st.markdown(
            f"""
            <div style="
                font-size: 0.95rem;
                line-height: 1.6;
            ">
                {component.get("content", "")}
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------- DIVIDER ----------
    elif component_type == "divider":
        st.divider()

    # ---------- ALERT ----------
    elif component_type == "alert":
        level   = component.get("level", "info")
        message = component.get("message", "")
        if level == "info":
            st.info(message)
        elif level == "warning":
            st.warning(message)
        elif level == "success":
            st.success(message)
        elif level == "error":
            st.error(message)

    # ---------- CARD ----------
    elif component_type == "card":
        color_map = {
            "blue":   {"bg": "#1E3A5F", "border": "#2E5A8F"},
            "green":  {"bg": "#1E4D2B", "border": "#2E7D3E"},
            "red":    {"bg": "#4D1E1E", "border": "#8F2E2E"},
            "purple": {"bg": "#2D1E4D", "border": "#4D2E8F"},
            "orange": {"bg": "#4D2E1E", "border": "#8F5A2E"},
        }
        colors = color_map.get(
            component.get("color", "blue"), color_map["blue"]
        )
        st.markdown(
            f"""
            <div style="
                background: {colors['bg']};
                border-left: 4px solid {colors['border']};
                padding: 20px 24px;
                border-radius: 10px;
                margin: 8px 0;
            ">
                <h4 style="
                    color: #FFFFFF;
                    margin: 0 0 8px 0;
                    font-size: 1rem;
                    font-weight: 600;
                    letter-spacing: 0.3px;
                ">{component.get("title", "")}</h4>
                <p style="
                    color: #E8E8E8;
                    margin: 0;
                    font-size: 0.9rem;
                    line-height: 1.5;
                ">{component.get("content", "")}</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    # ---------- METRIC ----------
    elif component_type == "metric":
        st.metric(component.get("label", ""), component.get("value", ""))

    # ---------- TABLE ----------
    elif component_type == "table":
        if data is not None and len(data) > 0:
            st.dataframe(data, use_container_width=True)
        else:
            st.info(
                "No tabular data available for this file type. "
                "Table is only shown for CSV files."
            )

    # ---------- CODE ----------
    elif component_type == "code":
        st.code(
            component.get("content", ""),
            language=component.get("language", "python")
        )

    # ---------- SELECTBOX ----------
    elif component_type == "selectbox":
        st.selectbox(
            component.get("label", "Select"),
            options=component.get("options", [])
        )

    # ---------- SLIDER ----------
    elif component_type == "slider":
        st.slider(
            component.get("label", "Slider"),
            min_value=int(component.get("min", 0)),
            max_value=int(component.get("max", 100)),
            value=int(component.get("default", 50))
        )

    # ---------- BAR CHART ----------
    elif component_type == "bar_chart":
        if data is not None:
            x_col = find_column(component.get("x", ""), columns)
            y_col = find_column(component.get("y", ""), columns)
            if not x_col:
                st.error(f"Invalid X column: {component.get('x')}")
            elif not y_col:
                st.error(f"Invalid Y column: {component.get('y')}")
            elif not pd.api.types.is_numeric_dtype(data[y_col]):
                st.warning(
                    f"'{y_col}' is not numeric. "
                    f"Showing count of {x_col} instead."
                )
                chart_data = (
                    data[x_col].value_counts()
                    .head(10).reset_index()
                )
                chart_data.columns = [x_col, "Count"]
                st.bar_chart(data=chart_data, x=x_col, y="Count",
                             use_container_width=True)
            else:
                if data[x_col].nunique() > 15:
                    chart_data = (
                        data.groupby(x_col)[y_col]
                        .sum().nlargest(10).reset_index()
                    )
                    st.markdown(
                        "<small style='color:#888;'>"
                        f"Top 10 by {y_col}</small>",
                        unsafe_allow_html=True
                    )
                else:
                    chart_data = data
                st.bar_chart(data=chart_data, x=x_col, y=y_col,
                             use_container_width=True)

    # ---------- COUNT BAR CHART ----------
    elif component_type == "count_bar_chart":
        if data is not None:
            x_col = find_column(component.get("x", ""), columns)
            if not x_col:
                st.error(f"Invalid column: {component.get('x')}")
            else:
                chart_data = (
                    data[x_col].value_counts()
                    .head(10).reset_index()
                )
                chart_data.columns = [x_col, "Count"]
                st.bar_chart(data=chart_data, x=x_col, y="Count",
                             use_container_width=True)
                label = (
                    "Cities"    if x_col.lower() == "city"    else
                    "Countries" if x_col.lower() == "country" else
                    f"{x_col}s"
                )
                st.markdown(
                    f"<small style='color:#888;'>"
                    f"Top 10 {label} by count</small>",
                    unsafe_allow_html=True
                )

    # ---------- LINE CHART ----------
    elif component_type == "line_chart":
        if data is not None:
            x_col = find_column(component.get("x", ""), columns)
            y_col = find_column(component.get("y", ""), columns)
            if not x_col:
                st.error(f"Invalid X column: {component.get('x')}")
            elif not y_col:
                st.error(f"Invalid Y column: {component.get('y')}")
            elif not pd.api.types.is_numeric_dtype(data[y_col]):
                st.error(
                    f"'{y_col}' is not numeric. Cannot draw line chart.")
            else:
                st.line_chart(data=data, x=x_col, y=y_col,
                              use_container_width=True)

    # ---------- SCATTER PLOT ----------
    elif component_type == "scatter_plot":
        if data is not None:
            x_col = find_column(component.get("x", ""), columns)
            y_col = find_column(component.get("y", ""), columns)
            if not x_col:
                st.error(f"Invalid X column: {component.get('x')}")
            elif not y_col:
                st.error(f"Invalid Y column: {component.get('y')}")
            elif not pd.api.types.is_numeric_dtype(data[x_col]):
                st.error(
                    f"'{x_col}' is not numeric. Cannot draw scatter plot.")
            elif not pd.api.types.is_numeric_dtype(data[y_col]):
                st.error(
                    f"'{y_col}' is not numeric. Cannot draw scatter plot.")
            else:
                st.scatter_chart(data=data, x=x_col, y=y_col,
                                 use_container_width=True)

    # ---------- PIE CHART ----------
    elif component_type == "pie_chart":
        if data is not None:
            names_col  = find_column(component.get("names",  ""), columns)
            values_col = find_column(component.get("values", ""), columns)
            if not names_col:
                st.error(
                    f"Invalid names column: {component.get('names')}")
            elif not values_col:
                st.error(
                    f"Invalid values column: {component.get('values')}")
            else:
                if not pd.api.types.is_numeric_dtype(data[values_col]):
                    pie_data = data[names_col].value_counts()
                else:
                    pie_data = data.groupby(names_col)[values_col].sum()

                if len(pie_data) > 10:
                    top      = pie_data.head(10)
                    others   = pd.Series(
                        {"Others": pie_data.iloc[10:].sum()})
                    pie_data = pd.concat([top, others])

                fig, ax = plt.subplots(figsize=(7, 7))
                pie_data.plot.pie(autopct='%1.1f%%', ylabel='', ax=ax)
                st.pyplot(fig)
                plt.close(fig)

    # ---------- COLUMNS LAYOUT ----------
    elif component_type == "columns":
        items = component.get("items", [])
        if items:
            cols = st.columns(len(items))
            for i, item in enumerate(items):
                with cols[i]:
                    render_component(item, data, columns)

    # ---------- UNKNOWN ----------
    else:
        st.warning(f"Unknown component type: {component_type}")


# -----------------------------
# Helper: Build System Prompt
# -----------------------------
def build_system_prompt(file_type, file_content, columns=None,
                         numeric_columns=None, summary_metrics=None,
                         data=None, image_b64=None):

    csv_context = ""
    if file_type == "csv" and columns:
        unique_counts = "\n".join(
            [f"{col}: {data[col].nunique()} unique values"
             for col in columns]
        ) if data is not None else ""

        csv_context = f"""
Available dataframe columns:
{", ".join(columns)}

Numeric columns:
{", ".join(numeric_columns) if numeric_columns else "None"}

Dataset summary:
{chr(10).join(summary_metrics) if summary_metrics else "None"}

Column unique value counts:
{unique_counts}
"""

    image_context = ""
    if image_b64:
        image_context = """
The user has also uploaded an image. Analyse it and use it as follows:
- If it looks like a dashboard or UI screenshot: replicate that layout style and structure in your JSON
- If it looks like a wireframe or hand-drawn sketch: use it as the exact layout blueprint
- If it looks like a chart or graph: recreate a similar visualization using the file data
- If it looks like a logo or branding material: reference the brand name in the title and cards
- If it is not clearly any of the above: describe what you see in a markdown component and incorporate it meaningfully
Always acknowledge the image in at least one markdown or card component.
"""

    return f"""
You are a UI architect for Streamlit applications.

Return ONLY valid JSON. No markdown. No explanations.

The user has uploaded a {file_type} file. Here is its content:

{file_content[:3000]}

{csv_context}
{image_context}

Generate a rich, well-structured Streamlit UI layout using the schema below.

Valid JSON schema:
{{
  "title": "string",
  "components": [
    {{"type": "markdown",       "content": "string"}},
    {{"type": "divider"}},
    {{"type": "alert",          "message": "string", "level": "info|warning|success|error"}},
    {{"type": "card",           "title": "string", "content": "string", "color": "blue|green|red|purple|orange"}},
    {{"type": "metric",         "label": "string", "value": "string"}},
    {{"type": "table"}},
    {{"type": "code",           "content": "string", "language": "string"}},
    {{"type": "selectbox",      "label": "string", "options": ["A","B","C"]}},
    {{"type": "slider",         "label": "string", "min": 0, "max": 100, "default": 50}},
    {{"type": "bar_chart",      "x": "string", "y": "string"}},
    {{"type": "line_chart",     "x": "string", "y": "string"}},
    {{"type": "scatter_plot",   "x": "string", "y": "string"}},
    {{"type": "pie_chart",      "names": "string", "values": "string"}},
    {{"type": "count_bar_chart","x": "string"}},
    {{"type": "columns", "items": [
        {{"type": "metric", "label": "string", "value": "string"}},
        {{"type": "card",   "title": "string", "content": "string", "color": "blue"}}
    ]}}
  ]
}}

Layout Rules:
- Always start with a markdown component introducing the dashboard
- Group related metrics inside a columns component (2-4 per row)
- Use cards for key insights or summaries
- Use dividers to separate sections
- Use alerts for important notes or warnings
- For .py files : show code blocks, explain with markdown, summarize with cards
- For CSV files : use charts, metrics in columns, and tables
- For text/PDF  : use cards for key points, markdown for summary
- For images    : follow the image_context instructions above
- NEVER use bar_chart, line_chart, or scatter_plot with a non-numeric y column
- For non-numeric columns always use count_bar_chart instead
- Never use pie_chart if a column has more than 10 unique values — use count_bar_chart instead
- Use columns layout as much as possible to avoid everything stacking vertically
- Always end with a table component for CSV files
- Make the layout feel like a real designed dashboard
- Never invent column names — use ONLY the exact column names listed above
"""


# ================================
# STREAMLIT APP
# ================================
st.set_page_config(
    page_title="Generative UI Demo",
    layout="wide"
)

# -----------------------------
# Session State Init
# -----------------------------
if "ui_json"       not in st.session_state:
    st.session_state.ui_json = None
if "data"          not in st.session_state:
    st.session_state.data = None
if "columns"       not in st.session_state:
    st.session_state.columns = []
if "response_text" not in st.session_state:
    st.session_state.response_text = ""
if "last_file"     not in st.session_state:
    st.session_state.last_file = None  
# ==============================
# SIDEBAR
# ==============================
with st.sidebar:
    st.markdown("##  Generative UI")
    st.caption("Upload a file, describe your UI, and let AI build it.")
    st.divider()

    st.markdown("### 📁 Upload File")
    uploaded_file = st.file_uploader(
        "CSV, TXT, PY, PDF, JSON",
        type=["csv", "txt", "py", "pdf", "json"],
        label_visibility="collapsed"
    )

    # Reset session state when file changes
    if uploaded_file is not None:
        current_file = uploaded_file.name
    else:
        current_file = None

    

    if current_file != st.session_state.last_file:
        # File changed — clear everything
        st.session_state.last_file     = current_file
        st.session_state.ui_json       = None
        st.session_state.response_text = ""
        st.session_state.data          = None
        st.session_state.columns       = []

    st.markdown("### 🖼️ Upload Image *(optional)*")
    st.caption(
        "Upload a dashboard screenshot, wireframe, or "
        "branding image to guide the UI style."
    )
    uploaded_image = st.file_uploader(
        "PNG, JPG, JPEG, WEBP",
        type=["png", "jpg", "jpeg", "webp"],
        label_visibility="collapsed"
    )

    image_b64 = None
    if uploaded_image is not None:
        image_bytes = uploaded_image.read()
        image_b64   = base64.b64encode(image_bytes).decode("utf-8")
        st.image(uploaded_image, caption="Uploaded Image",
                 use_container_width=True)
        st.info(
            "💡 GPT will analyse this image and use it to "
            "guide the layout, style, or content of your dashboard."
        )

    st.divider()

    if st.session_state.ui_json is not None:
        st.success("✅ Dashboard ready")
        if st.button("🔄 Reset", use_container_width=True):
            st.session_state.ui_json       = None
            st.session_state.response_text = ""
            st.session_state.data          = None
            st.session_state.columns       = []
            st.rerun()
    elif uploaded_file is not None:
        st.info("📝 File loaded — describe your UI below")
    else:
        st.warning("⬆️ Upload a file to get started")


# ==============================
# MAIN AREA
# ==============================
st.title(" Generative UI Demo")
st.divider()

tab1, tab2 = st.tabs(["📁  Input & Configure", "✨  Generated Dashboard"])

# ==============================
# TAB 1 — INPUT
# ==============================
with tab1:

    if uploaded_file is None:
        st.markdown(
            """
            <div style="text-align:center; padding:80px;
                        color:#888; border:2px dashed #ddd;
                        border-radius:12px; margin-top:20px;">
                <h2>👈 Start by uploading a file in the sidebar</h2>
                <p>Supports CSV, TXT, PY, PDF, JSON</p>
                <p>Optionally upload an image to guide the UI style</p>
            </div>
            """,
            unsafe_allow_html=True
        )

    else:
        data            = None
        columns         = []
        numeric_columns = []
        summary_metrics = []

        file_type, file_content = extract_file_content(uploaded_file)

        if file_type == "unknown" or file_content is None:
            st.error("Unsupported file type.")
            st.stop()

        if file_type == "error":
            st.error(f"Error reading file: {file_content}")
            st.stop()

        if file_type == "csv":
            try:
                lines       = file_content.strip().split("\n")
                fixed_lines = []

                for line in lines:
                    line = line.strip()
                    line = line.lstrip("\ufeff").lstrip("\xef\xbb\xbf")

                    if line.startswith(','):
                        line = line[1:]

                    if line.startswith('"'):
                        try:
                            end_quote = line.index('",')
                            inner     = line[1:end_quote]
                            rest      = line[end_quote+2:]
                            line      = inner + "," + rest
                        except ValueError:
                            pass

                    fixed_lines.append(line)

                fixed_csv = "\n".join(fixed_lines)
                data      = pd.read_csv(StringIO(fixed_csv))

                seen        = {}
                new_columns = []
                for col in data.columns:
                    col = col.strip()
                    if col in seen:
                        seen[col] += 1
                        new_columns.append(f"{col}_{seen[col]}")
                    else:
                        seen[col] = 0
                        new_columns.append(col)
                data.columns = new_columns

                data = data.dropna(how="all")
                data = data.dropna(axis=1, how="all")
                data = data.loc[
                    :,
                    ~data.columns.astype(str).str.contains("^Unnamed")
                ]
                data.columns = data.columns.str.strip()
                data.columns = data.columns.str.strip('"')

                columns         = data.columns.tolist()
                numeric_columns = data.select_dtypes(
                    include="number").columns.tolist()

                for col in numeric_columns:
                    summary_metrics.append(
                        f"{col}: sum={round(data[col].sum(),2)}, "
                        f"mean={round(data[col].mean(),2)}, "
                        f"max={round(data[col].max(),2)}, "
                        f"min={round(data[col].min(),2)}"
                    )

                st.session_state.data    = data
                st.session_state.columns = columns

                st.subheader("📊 Dataset Preview")
                st.dataframe(data.head(), use_container_width=True)
                st.markdown(
                    f"<small style='color:#888;'>"
                    f"{len(data)} rows × {len(columns)} columns"
                    f"</small>",
                    unsafe_allow_html=True
                )

                st.divider()

                col_a, col_b = st.columns(2)
                with col_a:
                    st.markdown("**All Columns**")
                    st.write(columns)
                with col_b:
                    st.markdown("**Numeric Columns**")
                    st.write(
                        numeric_columns if numeric_columns
                        else "None detected"
                    )

            except Exception as e:
                st.error(f"CSV Error: {e}")
                st.stop()

        else:
            st.subheader("📄 File Preview")
            st.code(
                file_content[:1000],
                language=file_type if file_type == "py" else "text"
            )

        st.divider()

        if image_b64:
            st.info(
                "🖼️ Image uploaded — GPT will use it to guide "
                "the layout and style of your dashboard."
            )
            st.divider()

        if image_b64:
            placeholder = (
                "Example: Create a dashboard in the style of "
                "the uploaded image using my file data"
            )
        elif file_type == "csv":
            placeholder = (
                "Example: Create a dashboard with key metrics, "
                "charts, insight cards, and a full table"
            )
        elif file_type == "py":
            placeholder = (
                "Example: Analyse this Python file and create a "
                "code review dashboard with cards and explanations"
            )
        else:
            placeholder = (
                "Example: Summarize this document into a dashboard "
                "with key points as cards and a markdown overview"
            )

        st.subheader(" Describe the UI you want")
        user_prompt = st.text_area(
            "Prompt",
            placeholder=placeholder,
            height=120,
            label_visibility="collapsed"
        )

        if st.button("✨ Generate UI",
                     disabled=not user_prompt,
                     type="primary",
                     use_container_width=True):

            with st.spinner("Generating your dashboard..."):

                SYSTEM_PROMPT = build_system_prompt(
                    file_type=file_type,
                    file_content=file_content,
                    columns=columns,
                    numeric_columns=numeric_columns,
                    summary_metrics=summary_metrics,
                    data=data,
                    image_b64=image_b64
                )

                if image_b64:
                    user_message = [
                        {"type": "text", "text": user_prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_b64}"
                            }
                        }
                    ]
                else:
                    user_message = user_prompt

                stream = client.chat.completions.create(
                    model="gpt-5.4-mini",
                    stream=True,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user",   "content": user_message}
                    ]
                )

                response_text      = ""
                stream_placeholder = st.empty()

                for chunk in stream:
                    delta          = chunk.choices[0].delta.content or ""
                    response_text += delta
                    stream_placeholder.text(response_text)

                stream_placeholder.empty()

            try:
                clean_text = re.sub(
                    r"```(?:json)?", "", response_text
                ).strip("`").strip()
                ui_json = json.loads(clean_text)

                st.session_state.ui_json       = ui_json
                st.session_state.response_text = response_text

                st.success(
                    "✅ Dashboard generated! "
                    "Click the **✨ Generated Dashboard** tab to view it."
                )

            except Exception as e:
                st.error("Invalid JSON generated")
                st.text(str(e))
                st.code(response_text, language="json")

# ==============================
# TAB 2 — GENERATED DASHBOARD
# ==============================
with tab2:

    if st.session_state.ui_json is None:
        st.markdown(
            """
            <div style="text-align:center; padding:80px;
                        color:#888; border:2px dashed #ddd;
                        border-radius:12px; margin-top:20px;">
                <h2>✨ Your dashboard will appear here</h2>
                <p>Go to <b>Input & Configure</b>, upload a file
                   and click <b>Generate UI</b></p>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        ui_json = st.session_state.ui_json
        data    = st.session_state.data
        columns = st.session_state.columns

        with st.expander("🔍 Raw GPT Response"):
            st.code(st.session_state.response_text, language="json")

        st.divider()

        st.markdown(
            f"""
            <div style="
                background: linear-gradient(90deg, #1E3A5F, #2D1E4D);
                padding: 20px 28px;
                border-radius: 12px;
                margin-bottom: 24px;
            ">
                <h1 style="
                    color: #FFFFFF;
                    margin: 0;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                ">
                    {ui_json.get("title", "Dashboard")}
                </h1>
            </div>
            """,
            unsafe_allow_html=True
        )

        for component in ui_json.get("components", []):
            render_component(component, data, columns)

        st.divider()

        if st.button("🔄 Generate Another Dashboard",
                     use_container_width=True):
            st.session_state.ui_json       = None
            st.session_state.response_text = ""
            st.rerun()
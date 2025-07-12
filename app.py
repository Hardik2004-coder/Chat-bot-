import os
import urllib.parse
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import dotenv
import re
import base64
import io
import matplotlib.pyplot as plt
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_community.agent_toolkits import create_sql_agent
from langchain.agents.agent_types import AgentType
# Load environment variables
dotenv.load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found.")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD")
if not DB_PASSWORD:
    raise ValueError("DB_PASSWORD not found.")
DB_HOST = os.getenv("DB_HOST", "127.0.0.1")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "hdfc")
encoded_db_password = urllib.parse.quote_plus(DB_PASSWORD)
DATABASE_URI = f"postgresql+psycopg2://{DB_USER}:{encoded_db_password}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
app = Flask(__name__)
CORS(app)
db = SQLDatabase.from_uri(DATABASE_URI)
llm = ChatGoogleGenerativeAI(
    model="models/gemini-2.0-flash",
    temperature=0,
    google_api_key=GOOGLE_API_KEY
)
# Updated prefix with instruction about graph generation
prefix = """
You are an expert data analyst.

Instructions:
- When the user refers to "vendor", "seller", or "supplier", use data from the `extraction_header_details_seller_company_name` table.
- Use `seller_company_name` or `seller_gstin` from `extraction_header_details`.
- Do NOT use the `builder_details` table for any vendor-related information.

Builder/Project-based Join Logic:
- Use `extraction_stagging_details`,`project_details`,`builder_details` for `builder_name`, `project_name`, and `unique_number`.
- Join `extraction_stagging_details` with:
  - `extraction_header_details` for header-level queries
  - `extraction_line_item_details` for line-item queries
  ON `unique_number`.
- Join `builder_details` with:
  -`project_details` for loan amount queries ON builder_id.
  - Use `builder_detalis` for loan amount sanctioned queries.
  - Use `project_details` if loan used on project queries.
- Apply WHERE filters on builder/project name accordingly.
Sample_Sales Table Instructions:
- Use the `Sample_Sales` table to answer real estate sales-related queries.
- Column mappings:
  - "S. No.": Serial number of the record
  - "PROJECT NAME": Name of the real estate project
  - "CONFIGURATION": Flat configuration (e.g., 2BHK, 3BHK)
  - "UNIT NO": Unit number of the flat
  - "FLOOR": Floor number
  - "CUSTOMER": Name of the customer
  - "CARPET AREA (SQ FT)": Carpet area in square feet
  - "Saleable Area": Saleable area in square feet
  - "Sale price": Total sale price
  - "Sale Price (As per Saleable Area)": Sale price calculated using saleable area
  - "Price p.sq.ft - carpet": Price per square foot based on carpet area
  - "Price p.sq.ft - Saleable": Price per square foot based on saleable area
  - "ALLOTMENT DATE": Date of property allotment
  - "Self funded/ Bank Loan": Indicates whether the purchase was self-funded or bank financed
- For price or area comparisons, map user terms like "cost", "rate", or "area" to appropriate fields.
- Always filter or group by "PROJECT NAME", "CONFIGURATION", or "ALLOTMENT DATE" if specified in the query.
- Use price-per-square-foot fields for pricing insights, and total area fields for volume-based insights.

Graph Generation Instructions:
- Generate a graph only if the user explicitly requests it by mentioning words like "graph", "chart", "bar chart", "pie chart", "histogram", or "line chart".
- Supported graph types: bar chart, histogram, pie chart, line chart.
- If generating a graph, produce the visualization from the SQL query results.
- Otherwise, do not generate any graph.
"""
sql_agent = create_sql_agent(
    llm=llm,
    db=db,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True,
    handle_parsing_errors=True,
    prefix=prefix
)
response_prompt = PromptTemplate(
    template="""
You are a data expert. Based on the user query: "{user_query}", and the following SQL result:

{sql_data}

Explain this result in a clear and concise way that a business user can understand.
""",
    input_variables=["user_query", "sql_data"]
)
response_chain = LLMChain(llm=llm, prompt=response_prompt)
def clean_sql(query: str) -> str:
    if not isinstance(query, str):
        return ""
    match = re.search(r"```sql(.*?)```", query, re.DOTALL)
    if match:
        return match.group(1).strip()
    match = re.search(r"```(.*?)```", query, re.DOTALL)
    if match:
        return match.group(1).strip()
    return query.strip()
def mask_sensitive_data(sql_result):
    """Mask sensitive fields in SQL result to protect privacy."""
    masked_result = []
    sensitive_fields = {'account_number', 'name', 'email', 'phone', 'seller_gstin', 'seller_company_name'}
    for row in sql_result:
        masked_row = {}
        for key, value in row.items():
            if key.lower() in sensitive_fields:
                masked_row[key] = "***"
            else:
                masked_row[key] = value
        masked_result.append(masked_row)
    return masked_result
def generate_pie_chart(data_dict):
    labels = list(data_dict.keys())
    sizes = list(data_dict.values())
    plt.figure(figsize=(6,6))
    plt.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=140)
    plt.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle.
    # Save to a BytesIO object
    img_io = io.BytesIO()
    plt.savefig(img_io, format='png', bbox_inches='tight')
    img_io.seek(0)
    # Encode image as base64 string
    base64_img = base64.b64encode(img_io.read()).decode('utf-8')
    plt.close()
    return base64_img
def generate_graph(data, chart_type):
    """
    Generate a graph image (base64 PNG) from SQL result data.

    data: list of dicts (query result)
    chart_type: one of 'bar', 'histogram', 'pie', 'line'
    """
    if not data or not isinstance(data, list):
        return None
    plt.switch_backend('Agg')  # Use non-GUI backend for servers
    # Convert list of dicts into separate lists for keys and values
    # Assume keys are consistent across rows
    keys = list(data[0].keys())
    if len(keys) < 2:
        return None  # Need at least two columns: x and y for plotting
    x_key = keys[0]
    y_key = keys[1]
    x = [row[x_key] for row in data]
    y = [row[y_key] for row in data]
    fig, ax = plt.subplots(figsize=(8, 6))
    try:
        if chart_type == 'bar':
            ax.bar(x, y)
            ax.set_xlabel(x_key)
            ax.set_ylabel(y_key)
            ax.set_title('Bar Chart')
        elif chart_type == 'histogram':
            # Histogram only needs y values (numerical)
            ax.hist(y, bins=10)
            ax.set_xlabel(y_key)
            ax.set_title('Histogram')
        elif chart_type == 'pie':
            # Pie chart slices correspond to y, labels to x
            ax.pie(y, labels=x, autopct='%1.1f%%', startangle=90)
            ax.set_title('Pie Chart')
        elif chart_type == 'line':
            ax.plot(x, y, marker='o')
            ax.set_xlabel(x_key)
            ax.set_ylabel(y_key)
            ax.set_title('Line Chart')
        else:
            return None
        buf = io.BytesIO()
        plt.tight_layout()
        fig.savefig(buf, format='png')
        plt.close(fig)
        buf.seek(0)
        img_bytes = buf.read()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        return img_base64
    except Exception as e:
        print("Error generating graph:", e)
        return None
@app.route("/get-answer", methods=["POST"])
def get_answer():
    timestamp = datetime.now().timestamp()
    print({'time stamp': timestamp})
    data = request.get_json()
    user_msg = data.get("query", "").strip()
    acc_no = data.get("acc_no", "").strip()
    if not user_msg:
        return jsonify({"answer": "Please enter a valid question."})
    try:
        final_user_msg = f"{user_msg}. Restrict to account number {acc_no}." if acc_no else user_msg
        sql_generation_result = sql_agent.invoke({"input": final_user_msg})
        print("Raw SQL Agent Result:", sql_generation_result)
        intermediate_steps = sql_generation_result.get("intermediate_steps", [])
        original_query = intermediate_steps[-1][1] if intermediate_steps and len(intermediate_steps[-1]) > 1 else None
        cleaned_query = clean_sql(original_query) if original_query else None
        final_output = sql_generation_result.get("output", "").strip()
        # Enhanced chart keyword detection
        graph_keywords = ["graph", "chart", "bar chart", "bargraph", "bar", "pie", "pie chart", "line", "line chart", "histogram", "plot", "visualize"]
        wants_graph = any(word in user_msg.lower() for word in graph_keywords)
        chart_type = None
        for ctype in ['bar', 'histogram', 'pie', 'line']:
            if ctype in user_msg.lower():
                chart_type = ctype
                break
        print("Wants Graph:", wants_graph)
        print("Chart Type Detected:", chart_type)
        if final_output:
            final_output_list = final_output.split(",")
            print("Final Output from Agent as list:", final_output_list)
            table_html = "<table border='1'><tr><th>Index</th><th>Item</th></tr>"
            for idx, item in enumerate(final_output_list, start=1):
                table_html += f"<tr><td>{idx}</td><td>{item}</td></tr>"
            table_html += "</table>"
            return jsonify({
                "answer": table_html,
                "sql_query": cleaned_query,
                "raw_data": "",
                "graph": None
            })
        if cleaned_query:
            print("Executing cleaned SQL:", cleaned_query)
            raw_result = db.run(cleaned_query)
            print("SQL Output:", raw_result)
            if not raw_result:
                return jsonify({
                    "answer": "No data found for this query.",
                    "sql_query": cleaned_query,
                    "raw_data": [],
                    "graph": None
                })
            masked_data = mask_sensitive_data(raw_result)
            explanation = response_chain.run({
                "user_query": user_msg,
                "sql_data": masked_data
            })
            graph_base64 = None
            if wants_graph and chart_type:
                try:
                    print("Attempting to generate graph...")
                    graph_base64 = generate_graph(raw_result, chart_type)
                    if not graph_base64:
                        print("Graph generation failed or returned None.")
                except Exception as e:
                    print("Graph generation error:", e)
                    graph_base64 = None
            return jsonify({
                "answer": explanation,
                "sql_query": cleaned_query,
                "raw_data": raw_result,
                "graph": graph_base64
            })
        return jsonify({"answer": "I couldn't generate a valid SQL query. Please try rephrasing your question."})
    except Exception as e:
        print("Error during /get-answer:", e)
        return jsonify({"answer": f"Something went wrong. Please try again.\n\nDebug: {str(e)}"})
@app.route("/", methods=["GET"])
def home():
    return "Bank Assistant backend (with data privacy masking) is running!"
if __name__ == "__main__":
    app.run(debug=True, port=3000)
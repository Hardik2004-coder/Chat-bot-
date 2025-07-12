# Chat-bot-
Project mainly focus on backend code 

This project, **Bank Assistant**, is a web-based application designed to provide an interactive chat interface for both bank users and administrators. The primary focus of this upload is on the backend functionality, which leverages AI to process natural language queries and interact with a PostgreSQL database. The frontend is a sample implementation to demonstrate the backend's capabilities.

**Key Features:**

* **User and Admin Portals:** Separate login interfaces for general users and bank administrators.
* **AI-Powered Chatbot:** The core of the application, allowing users and admins to query bank-related information using natural language.
* **Database Integration (PostgreSQL):** The backend connects to a PostgreSQL database (`hdfc` in this case) to retrieve and manage banking data.
* **LangChain Integration:** Utilizes LangChain for building the AI agent that understands and responds to queries, specifically `SQLDatabase` and `create_sql_agent` for interacting with the SQL database.
* **Google Generative AI (Gemini-2.0-Flash):** Employs Google's Gemini-2.0-Flash model for generating responses.
* **Data Privacy Masking:** Sensitive data fields (e.g., account number, name, email, phone, GSTIN) are masked in SQL query results before being sent to the frontend.
* **Graph Generation:** The backend can generate various types of graphs (bar, histogram, pie, line) from SQL query results if explicitly requested by the user. These graphs are sent as base64 encoded images to the frontend for display.
* **Session Management:** Uses `sessionStorage` for user and admin authentication and `localStorage` for "remember me" functionality.
* **Frontend (Sample):** Basic HTML, CSS, and JavaScript provide a chat interface and demonstrate interaction with the backend.

**Backend Technologies:**

* **Flask:** Python web framework for building the API.
* **Flask-CORS:** Enables Cross-Origin Resource Sharing.
* **SQLAlchemy / Psycopg2:** For connecting to and interacting with the PostgreSQL database.
* **LangChain:** Framework for developing applications powered by language models.
* **Google Generative AI SDK:** For integrating with Gemini models.
* **Matplotlib:** For generating data visualizations (graphs).

**Frontend Technologies (Sample):**

* **HTML5:** Structure of the web pages.
* **CSS3:** Styling of the application.
* **JavaScript:** Client-side logic for user interaction, form handling, and API calls.

This project serves as a robust foundation for building an intelligent banking assistant, highlighting the power of AI in streamlining data retrieval and analysis from relational databases.

# Developer Assistant Chatbot

A Streamlit-based chatbot that helps developers perform Git and code operations through natural language commands.

## Features

- **Create and modify files** in your repository
- **Commit and push changes** to GitHub
- **Create and manage branches**
- **Generate pull requests**
- **Search through your codebase**
- **Run tests** in your repository
- **Install dependencies** as needed

## Setup

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/developer-assistant.git
   cd developer-assistant
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   GITHUB_TOKEN=your_personal_access_token
   GITHUB_REPO=yourusername/your-repo
   GITHUB_USER=yourusername
   OPENAI_API_KEY=your_openai_api_key
   LOCAL_REPO_PATH=/path/to/local/repository
   ```

4. Run the application:
   ```
   streamlit run app.py
   ```

## Usage

Once the application is running, you can interact with the chatbot by typing natural language commands:

- "Create a new file called app.py with a function that calculates Fibonacci numbers"
- "List all branches in the repository"
- "Create a new branch called feature/user-authentication"
- "Commit the changes to README.md with a message about documentation updates"
- "Search for all instances of 'TODO' in the codebase"
- "Run the tests in the tests/unit directory"

## Project Structure

- `app.py`: Main Streamlit application
- `git_functions.py`: Extended Git functionality
- `requirements.txt`: Required Python packages

## How It Works

The Developer Assistant uses LangChain to connect an LLM (OpenAI) with various tools that perform Git and code operations. The LLM interprets your natural language requests and determines which tools to use and how to use them to accomplish your tasks.
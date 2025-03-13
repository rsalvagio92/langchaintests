from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI
from git_functions import *
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Get the repository path from environment or use default
repo_local_path = os.getenv("LOCAL_REPO_PATH", "local_repo")
print(f"Using repository path: {repo_local_path}")

# Ensure the repository is cloned before running operations
clone_status = clone_repo(repo_local_path)
print(f"Repository status: {clone_status}")

# Define tools for the agent
tools = [
    Tool(
        name="ModifyCode",
        func=lambda x: modify_code_wrapper(x, repo_local_path),
        description="Modifies a file in the repository. Inputs: file_path (str), new_content (str).",
    ),
    Tool(
        name="CommitAndPush",
        func=lambda x: commit_and_push_wrapper(x, repo_local_path),
        description="Commits and pushes changes to GitHub. Inputs: file_path (str), commit_message (str).",
    ),
    Tool(
        name="ListBranches",
        func=lambda x: list_branches(repo_local_path),
        description="Lists all branches in the local repository.",
    ),
    Tool(
        name="CreatePullRequest",
        func=create_pull_request_wrapper,
        description="Creates a pull request. Inputs: branch_name (str, optional), title (str, optional), body (str, optional).",
    )
]

# Initialize LangChain LLM
llm = OpenAI(model="gpt-3.5-turbo-instruct", temperature=0)

# Create an agent
agent = initialize_agent(
    tools=tools,
    llm=llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Run the agent
response = agent.run("Create the file 'app.py' to print 'Hello AI', then commit and push.")
print(response)
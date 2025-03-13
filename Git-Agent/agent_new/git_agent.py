from langchain.agents import initialize_agent, AgentType, Tool
from langchain_openai import OpenAI
#from git_functions import clone_repo,list_branches,modify_code,commit_and_push,create_pull_request
from git_functions import *
from dotenv import load_dotenv

# Load .env file
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Define tools for the agent
tools = [
    Tool(
        name="ModifyCode",
        func=modify_code_wrapper,
        description="Modifies a file in the repository. Inputs: file_path (str), new_content (str), local_path (optional).",
    ),
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
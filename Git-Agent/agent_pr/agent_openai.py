from typing import TypedDict
from langgraph.graph import StateGraph, END, START
from langchain_core.prompts import ChatPromptTemplate
#from langchain_anthropic import ChatAnthropic
from langchain_openai import OpenAI
from pydantic import BaseModel, Field
from git import Repo
from github import Github
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO_NAME = "rsalvagio92/Wild-Nomad"

class CodeSolution(BaseModel):
    """Schema for code solutions."""
    description: str = Field(description="Description of the solution approach")
    code: str = Field(description="Complete code including imports and docstring")

class GraphState(TypedDict):
    """State for the task processing workflow."""
    status: str # Using status instead of error to track state
    task_content: str
    repo_dir: str
    generation: CodeSolution | None
    iterations: int


def clone_repository(github_token: str, repo_name: str) -> tuple[str, str]:
    """Clone the repository and return the local directory."""
    try:
        script_dir = os.path.dirname(os.path.abspath(_file_))
        repo_dir = os.path.join(script_dir, 'agent-task')

        if os.path.exists(repo_dir):
            os.system(f'rm -rf {repo_dir}')

        g = Github(github_token)
        repo = g.get_repo(repo_name)
        Repo.clone_from(repo.clone_url, repo_dir)
        return repo_dir, ""
    except Exception as e:
        return "", f"Repository setup failed: {str(e)}"


def read_task_file(repo_dir: str) -> tuple[str, str]:
    """Read the task markdown file."""
    try:
        task_path = os.path. join(repo_dir, 'tasks', 'task.md')
        with open(task_path, 'r') as f:
            return f.read(), ""
    except Exception as e:
        return "", f"Failed to read task: {str(e)}"

def initialize_state(github_token: str, repo_name: str) -> dict:
    """Initialize the workflow state."""
    repo_dir, error = clone_repository(github_token, repo_name)
    if error:
        return {
            "status": "failed",
            "task_content": "",
            "repo_dir": "",
            "generation": None,
            "iterations": 0
        }       

    task_content, error = read_task_file(repo_dir)
    if error:
        return {
            "status": "failed",
            "task_content": "",
            "repo_dir": repo_dir,
            "generation": None,
            "iterations": 0
        }
    return {
        "status": "ready",
        "task_content": task_content,
        "repo_dir": repo_dir,
        "generation": None,
        "iterations": 0
    }


def generate_solution(state: GraphState):
    """Generate code solution based on task description."""
    if state["status"] == "failed":
         return state

    task_content = state["task_content"]
    iterations = state["iterations"]

    prompt = ChatPromptTemplate. from_messages( [
        ("system", """You are a Python developer. Generate a solution based on the task requirements.
        Include complete code with imports, type hints, docstring, and examples."""),
        ("human", "Task description:\n{task}"),

    ])  

    try:
        llm = OpenAI(openai_api_key=openai_api_key, model="gpt-3.5-turbo", temperature=0)
        chain = prompt | llm.with_structured_output(CodeSolution)

        print(f"Generating solution - Attempt #{iterations + 1}")
        solution = chain. invoke({"task": task_content})

        return {
            "status": "generated",
            "task_content": task_content,
            "repo_dir": statę["repo_dir"],
            "generation": solution,
            "iterations": iterations + 1
        }
    except Exception:
        return { ** state, "status": "failed"}
    

def test_solution(state: GraphState):
    """Test the generated code solution."""
    if state["status"] != "generated" or not state["generation"]:
        return { ** state, "status": "failed"}

    try:
        namespace = {}
        exec(state["generation"]. code, namespace)

        result = namespace['calculate_products'] ( [1, 2, 3, 4])
        if result != [24, 12, 8, 6]:
            return { ** state, "status": "failed"}

        return { ** state, "status": "tested"}

    except Exception:
        return { ** state, "status": "failed"}


def create_pr(state: GraphState):
    """Create a pull request with the solution."""
    if state["status"] != "tested" or not state["generation"]:
        return { ** state, "status": "failed"}

    try:
        solution = state["generation"]
        repo = Repo(state["repo_dir"])

        # Local git operations
        branch_name = f"solution/array-products"
        current = repo.create_head(branch_name)
        current. checkout()

        solution_path = os.path.join(state["repo_dir"], "array_products. py")
        with open(solution_path, "w") as f:
          f.write(solution.code)

        repo. index.add(["array_products.py"])
        repo. index. commit ("feat: add array products calculator")
        origin = repo.remote("origin")
        origin.push(branch_name)

        # Create PR using GitHub API
        g = Github(os.getenv("GITHUB_TOKEN"))
        repo_name = repo. remotes.origin.url.split('.git') [0].split('/') [-2:]
        repo_name = '/'.join(repo_name)

        gh_repo = g.get_repo(repo_name)

        pr = gh_repo. create_pull(
            title="Add Array Products Calculator",
            body=f"Implements array products calculator with the following approach: \n\n{solution.description}",
            base="main",
            head=branch_name

        )

        print(f"Created PR: {pr.html_url}")
        return { ** state, "status": "completed", "pr_url": pr.html_url}

    except Exception as e:
        print(f"Failed to create PR: {str(e)}")
        return { ** state, "status": "failed"}

def should_continue(state: GraphState) -> str:
    """Determine next step based on status."""
    if state["status"] == "failed":
        if state["iterations"] < 3:
            return "generate"
        return "end"
    return "continue"

def create_agent(github_token: str, repo_name: str):
    workflow = StateGraph(GraphState)
    workflow.add_node("generate", generate_solution)
    workflow.add_node("test", test_solution)
    workflow.add_node("create_pr", create_pr)

    # Define core workflow
    workflow.add_edge(START, "generate")
    workflow.add_edge("generate", "test")
    workflow.add_edge("create_pr", END)

    # Define conditional transitions from test node
    workflow.add_conditional_edges(
    "test", should_continue,
    {"generate": "generate", "continue": "create_pr", "end": END}

    )
    return workflow. compile()

def run_agent(github_token: str, repo_name: str):
    """Run the agent to generate and submit a solution."""
    try:
        agent = create_agent(github_token, repo_name)
        initial_state = initialize_state(github_token, repo_name)


        if initial_state["status"] == "failed":
            print("Failed to initialize agent")
            return {"status": "failed"}

        result = agent.invoke(initial_state)

        if result["status"] == "completed":
            print("Successfully created PR with solution!")
        else:
            print("Failed to create solution")

        return {
        "status": result["status"],
        "generation": result ["generation"]. code if result ["generation"] else None,
        "pr_url": result.get("pr_url")
        }
    except Exception as e:
        print("Agent execution failed")
        return {"status": "failed"}

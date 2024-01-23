from flask import Flask, request, render_template_string, jsonify,redirect, url_for,send_file,flash
from crewai import Agent, Task, Crew, Process
import secrets
import os
api_key_set = False  # Initialize as not set
# Generate a random secret key


app = Flask(__name__)

app.secret_key = secrets.token_hex(16)  
def get_agents():
    agents = []
    try:
        with open('agents.txt', 'r') as file:
            for line in file:
                if line.startswith("Agent:"):
                    agent_role = line.split(',')[0].split(': ')[1]
                    agents.append(agent_role)
    except FileNotFoundError:
        pass
    return agents

@app.route('/set_api_key', methods=['POST'])
def set_api_key():
    try:
        openai_api_key = request.form['openai_api_key']
        with open('agents.txt', 'a') as file:
            file.write(f"API_KEY: {openai_api_key}\n")
        flash('API Key set successfully!', 'success')
    except Exception as e:
        flash(f'Error setting API Key: {str(e)}', 'error')
    return redirect(url_for('index'))


def is_api_key_set():
    try:
        with open('agents.txt', 'r') as file:
            for line in file:
                if line.startswith("API_KEY:"):
                    return True
    except FileNotFoundError:
        pass
    return False


@app.route('/')
def index():
    agents = get_agents()
    api_key_set = is_api_key_set()

    # Check file existence and pass to template
    agents_file_exists = 'agents.txt' in os.listdir()
    output_file_exists = 'final_code_output.txt' in os.listdir()
    consolidated_code_exists = 'consolidated_code.py' in os.listdir()

    with open('index.html', 'r') as file:
        html_content = file.read()

    return render_template_string(html_content, agents=agents, api_key_set=api_key_set,
                           agents_file_exists=agents_file_exists,
                           output_file_exists=output_file_exists,
                           consolidated_code_exists=consolidated_code_exists)




@app.route('/get_agent_details')
def get_agent_details():
    selected_agent = request.args.get('agent_role')
    agent_details = {}
    try:
        with open('agents.txt', 'r') as file:
            for line in file:
                if line.startswith(f"Agent: {selected_agent}"):
                    details = line.strip().split(',')
                    for detail in details:
                        if ': ' in detail:
                            key, value = detail.split(': ', 1)  # Split only on the first occurrence
                            agent_details[key] = value
                    break
    except FileNotFoundError:
        pass
    return jsonify(agent_details)


@app.route('/create_agent', methods=['POST'])
def create_agent():
   try:
    role = request.form['role']
    goal = request.form['goal']
    verbose = request.form['verbose'].lower() == 'true'
    backstory = request.form['backstory']
    allow_delegation = request.form['allow_delegation'].lower() == 'true'

    with open('agents.txt', 'a') as file:
        file.write(f"Agent: {role}, Goal: {goal}, Verbose: {verbose}, Backstory: {backstory}, Allow Delegation: {allow_delegation}\n")
    flash('Agent created successfully!', 'success')
   except Exception as e:
        flash(f'Error creating agent: {str(e)}', 'error')
   return redirect(url_for('index'))

@app.route('/create_task', methods=['POST'])
def create_task():
    selected_agent = request.form['selected_agent']
    task_name = request.form['task_name']
    task_description = request.form['task_description']

    with open('agents.txt', 'a') as file:
        file.write(f"Task for Agent {selected_agent}: {task_name}, Description: {task_description}\n")

    return redirect(url_for('index'))


# ... [previous Flask app code] ...

def get_tasks():
    tasks = []
    try:
        with open('agents.txt', 'r') as file:
            for line in file:
                if line.startswith("Task for Agent"):
                    tasks.append(line.strip())
    except FileNotFoundError:
        pass
    return tasks

@app.route('/get_tasks')
def fetch_tasks():
    tasks = get_tasks()
    return jsonify(tasks)

@app.route('/delete_task', methods=['POST'])
def delete_task():
    task_to_delete = request.form['task']
    tasks = get_tasks()
    try:
        with open('agents.txt', 'w') as file:
            for task in tasks:
                if task != task_to_delete:
                    file.write(task + "\n")
    except FileNotFoundError:
        pass
    return redirect(url_for('index'))


# ... [previous Flask app code] ...

@app.route('/reassign_task', methods=['POST'])
def reassign_task():
    task_details = request.form['task']
    with open('agents.txt', 'a') as file:
        file.write(task_details + "\n")
    return redirect(url_for('index'))



# ... [previous Flask app code] ...

def find_agent_for_task(task_description):
    # This function should find and return the agent responsible for the task
    # For simplicity, let's assume each task description starts with "Task for Agent <Agent Role>:"
    agent_role = task_description.split(':')[0].replace("Task for Agent ", "")

    # Read the agents from the 'agents.txt' file
    agents = []
    try:
        with open('agents.txt', 'r') as file:
            for line in file:
                if line.startswith(f"Agent: {agent_role}"):
                    details = line.strip().split(', ')
                    agent_details = {}
                    for detail in details:
                        if ': ' in detail:
                            key, value = detail.split(': ', 1)
                            agent_details[key] = value

                    # Extract relevant information
                    agent_role = agent_role
                    agent_goal = agent_details.get('Goal')
                    agent_verbose = agent_details.get('Verbose') == 'True'  # Convert to bool
                    agent_backstory = agent_details.get('Backstory', 'Default Backstory')  # Provide a default value if not present
                    allow_delegation = agent_details.get('Allow Delegation', 'False')  # Provide a default value if not present

                    # # Print or use the extracted information as needed
                    # print(f"Agent Role: {agent_role}")
                    # print(f"Agent Goal: {agent_goal}")
                    # print(f"Agent Verbose: {agent_verbose}")
                    # print(f"Agent Backstory: {agent_backstory}")
                    # print(f"Allow Delegation: {allow_delegation}")

                    if agent_goal is not None and agent_verbose is not None:
                        created_agent = Agent(role=agent_role, goal=agent_goal, verbose=agent_verbose, backstory=agent_backstory)
                        # print(f"Found Agent: {created_agent}")
                        return created_agent
                    else:
                        # Handle the case where goal or verbose information is missing
                        # You may want to log an error or handle it based on your application's needs
                        # print(f"Agent details are incomplete for {agent_role}. Skipping.")
                        pass

    except FileNotFoundError:
        pass

    # Handle the case where the agent is not found
    # You may want to log an error or handle it based on your application's needs
    # print(f"Agent with role {agent_role} not found in agents.txt.")
    return None

# ... [remaining Flask app code] ...


def consolidate_code():
    # Consolidate the code from this script
    with open(__file__, 'r') as file:
        code_content = file.read()
    return code_content



@app.route('/execute_tasks', methods=['POST'])
def execute_tasks():
    data = request.json
    selected_tasks = data['tasks']
    # print(selected_tasks,"selected_tasks")

    # Instantiate Crew and Tasks
    agents = []
    tasks = []
    for task_description in selected_tasks:
        agent = find_agent_for_task(task_description)
        agents.append(agent)
        tasks.append(Task(description=task_description, agent=agent))

    # Create a Crew and execute tasks sequentially
    app_dev_crew = Crew(agents=agents, tasks=tasks, process=Process.sequential)
    # Start the process
    result = app_dev_crew.kickoff()

    output_file = 'output.txt'

    with open('final_code_output.txt', 'w') as file:
        print(result)  # Print to the terminal
        file.write(str(result))  # Write to the file

    complete_code = consolidate_code()
    with open('consolidated_code.py', 'w') as code_file:
        code_file.write(complete_code)


    # print(f'Results have been written to {output_file}')
    # print('All code has been consolidated and saved in final_code_output.txt')
    
    return jsonify({"result": result})
        

@app.route('/download_file')
def download_file():
    filename = request.args.get('file')
    return send_file(filename, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)

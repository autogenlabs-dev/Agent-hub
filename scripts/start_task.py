import requests
import time
import sys

BACKEND_URL = "http://localhost:8000"

def wait_for_backend():
    print("Waiting for backend to be ready...")
    for _ in range(30):
        try:
            response = requests.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("Backend is ready.")
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    print("Backend failed to start.")
    return False

def send_message(agent_id, content, sender_id="system"):
    print(f"Sending message to {agent_id}...")
    try:
        response = requests.post(f"{BACKEND_URL}/api/messages", json={
            "sender_id": sender_id,
            "recipient_id": agent_id,
            "content": content,
            "message_type": "text"
        })
        response.raise_for_status()
        print(f"Message sent to {agent_id}: {content[:50]}...")
    except Exception as e:
        print(f"Failed to send message to {agent_id}: {e}")

def main():
    if not wait_for_backend():
        sys.exit(1)

    # Allow some time for agents to connect via WebSocket
    print("Waiting for agents to connect...")
    time.sleep(5)

    # Configure Task Manager (Clawdbot 1)
    manager_prompt = (
        "You are the **Task Manager**. Your role is to coordinate work.\n"
        "Your goal is to verify that the 'Worker' agent is available and assign it a task.\n"
        "1. First, say hello to the Worker (agent_id: clawdbot-2).\n"
        "2. Then, use the task management tools or simply ask the Worker to calculate the 10th Fibonacci number.\n"
        "3. Wait for the result and report it back to me."
    )
    send_message("clawdbot-1", manager_prompt)

    # Configure Worker (Clawdbot 2)
    worker_prompt = (
        "You are the **Worker**. Your role is to execute tasks assigned by the Task Manager.\n"
        "Wait for instructions from 'clawdbot-1'. When you receive a task, do it and reply with the result."
    )
    send_message("clawdbot-2", worker_prompt)

    # Trigger the Manager to start
    send_message("clawdbot-1", "Please start the workflow now.", sender_id="user")

if __name__ == "__main__":
    main()

import os
import json
import logging
import msal
import requests
import random
import time
from urllib.parse import quote

# Configure logging for this module
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Configuration ---
# You obtained this from your Azure App Registration (Step 1)
CLIENT_ID = "eb71fb44-f2dd-4e1b-9d36-0422e092058b" 
# For personal Microsoft accounts, use "common"
AUTHORITY = "https://login.microsoftonline.com/common" 
# Define the permissions your app needs
# User.Read is generally good to have, Tasks.ReadWrite is for tasks
SCOPES = ["User.Read", "Tasks.ReadWrite"] 

def make_request_with_retry(method, url, headers, json_data=None, max_retries=3):
    """Make HTTP request with retry logic"""
    
    for attempt in range(max_retries):
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_data, timeout=30)
            elif method.upper() == "PATCH":
                response = requests.patch(url, headers=headers, json=json_data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            
            # Handle empty responses for DELETE requests
            if method.upper() == "DELETE":
                return {"success": True}
            else:
                return response.json()
                
        except (requests.exceptions.ConnectionError, ConnectionResetError, requests.exceptions.Timeout) as e:
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) + random.uniform(0, 1)
                logger.warning(f"Connection error on attempt {attempt + 1}, retrying in {wait_time:.2f}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"Failed after {max_retries} attempts")
                raise e
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise e

# --- Function to get an authentication token (Device Code Flow) ---
def get_auth_token():
    # Create a PublicClientApplication instance
    # This is suitable for desktop/mobile apps, not web apps
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority=AUTHORITY
    )

    # Initiate the device code flow
    # This will give you a code and a URL to visit
    flow = app.initiate_device_flow(scopes=SCOPES)

    if "user_code" not in flow:
        raise ValueError("Failed to initiate device flow. Check your CLIENT_ID and network.")

    print(flow["message"]) # This message tells the user what to do

    # Wait for the user to authenticate and then acquire the token
    result = app.acquire_token_by_device_flow(flow)

    if "access_token" in result:
        print("\nAuthentication successful!")
        return result["access_token"]
    else:
        print(f"\nAuthentication failed: {result.get('error_description')}")
        raise Exception("Could not acquire access token.")

# --- Function to create a task in Outlook ---
def create_outlook_task(access_token, task_title, due_date_iso=None): # Add due_date_iso parameter
    logger.info(f"Attempting to create task: '{task_title}' with due date: {due_date_iso}")
    graph_api_url = "https://graph.microsoft.com/v1.0"
    
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    # First, let's get the ID of the default "Tasks" todo list.
    # Microsoft Graph uses "todoTaskLists" for task lists.
    try:
        todo_lists_data = make_request_with_retry(
            "GET", 
            f"{graph_api_url}/me/todo/lists", 
            headers
        )
    except Exception as e:
        print(f"Failed to get todo lists: {e}")
        raise

    default_task_list_id = None
    for todo_list in todo_lists_data["value"]:
        # The default list often has a display name like "Tasks" or "To Do"
        # We can also check if it's the 'default' list based on other properties
        if todo_list.get("wellknownListName") == "defaultList":
             default_task_list_id = todo_list["id"]
             break
        elif todo_list["displayName"].lower() == "tasks": # Fallback for display name
            default_task_list_id = todo_list["id"]
            break
            
    if not default_task_list_id:
        print("Could not find a default To Do list. Creating task in the first list found.")
        if todo_lists_data["value"]:
            default_task_list_id = todo_lists_data["value"][0]["id"] # Use the first one if no default found
        else:
            raise Exception("No To Do lists found in your Outlook account.")

    # Now, create the task in the identified list
    task_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks"
    
    task_payload = {
        "title": task_title,
        "status": "notStarted", # or "completed", "inProgress", "waitingOnOthers", "deferred"
        # You can add more properties like "body", "dueDateTime", "importance" etc.
        # "body": {
        #     "content": "This is a detailed description of the task.",
        #     "contentType": "html" # or "text"
        # },
        # "dueDateTime": {
        #     "dateTime": "2025-09-25T17:00:00.0000000",
        #     "timeZone": "Asia/Kuala_Lumpur" # Malaysia timezone
        # }
    }

    if due_date_iso:
        # Microsoft Graph API expects dueDateTime as an object with dateTime and timeZone
        task_payload["dueDateTime"] = {
            "dateTime": due_date_iso,
            "timeZone": "Asia/Kuala_Lumpur" # Malaysia timezone (UTC+8)
        }

    print(f"Attempting to create task: '{task_title}' in list ID: {default_task_list_id}")
    try:
        task_data = make_request_with_retry(
            "POST",
            task_endpoint,
            headers,
            json_data=task_payload
        )
    except Exception as e:
        print(f"Failed to create task: {e}")
        raise

    print("\nTask created successfully!")
    print(f"Task ID: {task_data['id']}")
    print(f"Task Title: {task_data['title']}")
    # print(json.dumps(task_data, indent=4)) # Uncomment to see full task details
    
    return task_data  # Return the task data for tracking

def get_all_tasks(access_token):
    """Retrieve all tasks from the default Outlook task list"""
    logger.info("Attempting to retrieve all tasks from the default list.")
    graph_api_url = "https://graph.microsoft.com/v1.0"
    
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    # First, get the ID of the default "Tasks" todo list
    try:
        get_lists_response = make_request_with_retry("GET", f"{graph_api_url}/me/todo/lists", headers)
        todo_lists_data = get_lists_response

        default_task_list_id = None
        for todo_list in todo_lists_data["value"]:
            if todo_list.get("wellknownListName") == "defaultList" or \
            todo_list["displayName"].lower() == "tasks":
                default_task_list_id = todo_list["id"]
                break
                
        if not default_task_list_id:
            if todo_lists_data["value"]:
                default_task_list_id = todo_lists_data["value"][0]["id"]
                logger.warning("Could not find default To Do list, using the first available list for fetching tasks.")
            else:
                raise Exception("No To Do lists found in your Outlook account to retrieve tasks from.")

        # Now, fetch all tasks from this identified list
        tasks_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks"
        tasks_response = make_request_with_retry("GET", tasks_endpoint, headers)
        
        logger.info(f"Successfully retrieved {len(tasks_response['value'])} tasks.")
        return tasks_response["value"]  # This will be a list of task dictionaries

    except Exception as e:
        logger.error(f"Error retrieving tasks: {e}")
        raise

def get_uncompleted_tasks(access_token, max_tasks=10):
    """
    Retrieve uncompleted tasks from the default Outlook task list
    
    Args:
        access_token (str): Microsoft Graph API access token
        max_tasks (int): Maximum number of tasks to return (default: 10)
    
    Returns:
        list: List of uncompleted task dictionaries with task info
    """
    logger.info(f"Attempting to retrieve up to {max_tasks} uncompleted tasks from the default list.")
    graph_api_url = "https://graph.microsoft.com/v1.0"
    
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    try:
        # First, get the ID of the default "Tasks" todo list
        get_lists_response = make_request_with_retry("GET", f"{graph_api_url}/me/todo/lists", headers)
        todo_lists_data = get_lists_response

        default_task_list_id = None
        for todo_list in todo_lists_data["value"]:
            if todo_list.get("wellknownListName") == "defaultList" or \
            todo_list["displayName"].lower() == "tasks":
                default_task_list_id = todo_list["id"]
                break
                
        if not default_task_list_id:
            if todo_lists_data["value"]:
                default_task_list_id = todo_lists_data["value"][0]["id"]
                logger.warning("Could not find default To Do list, using the first available list for fetching uncompleted tasks.")
            else:
                raise Exception("No To Do lists found in your Outlook account to retrieve tasks from.")

        # Fetch tasks from the identified list with filter for uncompleted tasks
        # Use $filter parameter to get only non-completed tasks
        tasks_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks"
        filter_param = "$filter=status ne 'completed'"
        top_param = f"$top={max_tasks}"
        orderby_param = "$orderby=dueDateTime/dateTime asc"  # Order by due date, with null values last
        
        # Combine parameters
        full_endpoint = f"{tasks_endpoint}?{filter_param}&{top_param}&{orderby_param}"
        
        tasks_response = make_request_with_retry("GET", full_endpoint, headers)
        
        uncompleted_tasks = tasks_response["value"]
        logger.info(f"Successfully retrieved {len(uncompleted_tasks)} uncompleted tasks.")
        
        return uncompleted_tasks

    except Exception as e:
        logger.error(f"Error retrieving uncompleted tasks: {e}")
        raise

def update_task_due_date(access_token, task_id, new_due_date_iso):
    """Update the due date of an existing task"""
    logger.info(f"Attempting to update task {task_id} with new due date: {new_due_date_iso}")
    graph_api_url = "https://graph.microsoft.com/v1.0"
    
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    # First, find the task list containing this task
    try:
        get_lists_response = make_request_with_retry("GET", f"{graph_api_url}/me/todo/lists", headers)
        todo_lists_data = get_lists_response
        
        logger.info(f"Found {len(todo_lists_data.get('value', []))} todo lists")

        # Try to update from the default list first
        default_task_list_id = None
        for todo_list in todo_lists_data["value"]:
            logger.info(f"Checking list: {todo_list.get('displayName')} (wellknown: {todo_list.get('wellknownListName')})")
            if todo_list.get("wellknownListName") == "defaultList" or \
            todo_list["displayName"].lower() == "tasks":
                default_task_list_id = todo_list["id"]
                logger.info(f"Selected default list: {todo_list['displayName']} (ID: {default_task_list_id})")
                break
                
        if not default_task_list_id and todo_lists_data["value"]:
            default_task_list_id = todo_lists_data["value"][0]["id"]
            logger.warning(f"No default list found, using first available: {todo_lists_data['value'][0]['displayName']}")

        if not default_task_list_id:
            raise Exception("No todo lists found in account")

        # URL encode the task ID to handle special characters
        encoded_task_id = quote(task_id, safe='')
        logger.info(f"Original task ID: {task_id}")
        logger.info(f"Encoded task ID: {encoded_task_id}")

        # Verify the task exists before attempting to update
        try:
            verify_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks/{encoded_task_id}"
            verify_response = make_request_with_retry("GET", verify_endpoint, headers)
            logger.info(f"Task exists: {verify_response.get('title', 'Unknown')} (ID: {task_id})")
        except requests.exceptions.HTTPError as verify_error:
            if hasattr(verify_error, 'response') and verify_error.response.status_code == 404:
                logger.error(f"Task {task_id} not found in list {default_task_list_id}")
                raise Exception(f"Task not found: {task_id}. It may have been deleted or moved to a different list.")
            else:
                logger.warning(f"Could not verify task existence: {verify_error}")

        # Validate the datetime format
        try:
            from datetime import datetime
            # Try to parse the Microsoft Graph datetime format (YYYY-MM-DDTHH:MM:SS.0000000)
            if new_due_date_iso.endswith('.0000000'):
                # Remove the microseconds part for parsing
                dt_for_parsing = new_due_date_iso[:-8]  # Remove .0000000
                datetime.fromisoformat(dt_for_parsing)
            else:
                # Handle other ISO formats
                datetime.fromisoformat(new_due_date_iso.replace('Z', '+00:00'))
            logger.info(f"Valid datetime format: {new_due_date_iso}")
        except ValueError as date_error:
            logger.error(f"Invalid datetime format: {new_due_date_iso} - {date_error}")
            raise ValueError(f"Invalid datetime format: {new_due_date_iso}")

        # Update the task's due date using the correct Microsoft Graph API format
        update_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks/{encoded_task_id}"
        logger.info(f"Update endpoint: {update_endpoint}")
        
        # Use the simplified format that Microsoft Graph expects
        update_payload = {
            "dueDateTime": {
                "dateTime": new_due_date_iso,
                "timeZone": "Asia/Kuala_Lumpur"
            }
        }
        
        logger.info(f"Update payload: {update_payload}")

        # Try the update with explicit error handling
        try:
            response = requests.patch(update_endpoint, headers=headers, json=update_payload, timeout=30)
            logger.info(f"Raw response status: {response.status_code}")
            logger.info(f"Raw response headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                response_data = response.json()
                logger.info(f"Successfully updated task {task_id} with new due date")
                return response_data
            else:
                # Log the error details
                logger.error(f"Update failed with status {response.status_code}")
                try:
                    error_json = response.json()
                    logger.error(f"Error response: {error_json}")
                    error_message = error_json.get('error', {}).get('message', 'Unknown error')
                    raise Exception(f"Microsoft Graph API Error: {error_message}")
                except (ValueError, KeyError):
                    logger.error(f"Raw error response: {response.text}")
                    raise Exception(f"HTTP {response.status_code}: {response.text}")
                    
        except requests.exceptions.RequestException as req_error:
            logger.error(f"Request error: {req_error}")
            raise Exception(f"Network error while updating task: {req_error}")

    except Exception as e:
        logger.error(f"Error updating task {task_id}: {e}")
        raise

def delete_task(access_token, task_id):
    """Delete a specific task by its ID"""
    logger.info(f"Attempting to delete task with ID: {task_id}")
    graph_api_url = "https://graph.microsoft.com/v1.0"
    
    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json"
    }

    # First, we need to find which list contains this task
    # Get all lists first
    try:
        get_lists_response = make_request_with_retry("GET", f"{graph_api_url}/me/todo/lists", headers)
        todo_lists_data = get_lists_response

        # Try to delete from the default list first
        default_task_list_id = None
        for todo_list in todo_lists_data["value"]:
            if todo_list.get("wellknownListName") == "defaultList" or \
            todo_list["displayName"].lower() == "tasks":
                default_task_list_id = todo_list["id"]
                break
                
        if not default_task_list_id and todo_lists_data["value"]:
            default_task_list_id = todo_lists_data["value"][0]["id"]

        # Delete the task
        delete_endpoint = f"{graph_api_url}/me/todo/lists/{default_task_list_id}/tasks/{task_id}"
        delete_response = make_request_with_retry("DELETE", delete_endpoint, headers)
        
        logger.info(f"Successfully deleted task with ID: {task_id}")
        return True

    except Exception as e:
        logger.error(f"Error deleting task {task_id}: {e}")
        raise

# Duplicate function removed - using the comprehensive version above that handles list IDs correctly


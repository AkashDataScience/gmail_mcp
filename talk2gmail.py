import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_safety_iterations = 20  # Safety limit to prevent infinite loops
last_response = None
iteration = 0
iteration_response = []
consecutive_errors = 0
max_consecutive_errors = 3

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response, consecutive_errors
    last_response = None
    iteration = 0
    iteration_response = []
    consecutive_errors = 0

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to Gmail MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["gmail/server.py", 
                  "--creds-file-path", "client_creds.json", 
                  "--token-path", "token.json"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")
                

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""You are a Gmail Automation Agent that can manage emails using Gmail MCP tools. You handle email operations autonomously based on natural language queries.

Available Gmail tools:
{tools_description}

You must respond with EXACTLY ONE line in one of these formats (no additional text):
1. For function calls:
   FUNCTION_CALL: function_name|param1|param2|...
   
2. For final answers:
   FINAL_ANSWER: [Done]

Gmail Workflow:
1. Use get-unread-emails to retrieve unread emails
2. Use read-email with email_id to get email content
3. Use send-email with recipient_id, subject, message to send emails
4. Use trash-email with email_id to delete emails
5. Use mark-email-as-read with email_id to mark as read
6. Use open-email with email_id to open in browser
7. Continue making FUNCTION_CALL until ALL requested tasks are complete
8. Only return FINAL_ANSWER: [Done] when the ENTIRE workflow is finished

Examples:

Check unread emails:
- FUNCTION_CALL: get-unread-emails
- FINAL_ANSWER: [Done]

Read specific email:
- FUNCTION_CALL: read-email|email_id_123
- FINAL_ANSWER: [Done]

Send email:
- FUNCTION_CALL: send-email|user@example.com|Hello|This is a test message
- FINAL_ANSWER: [Done]

DO NOT include any explanations or additional text.
Your entire response should be a single line starting with either FUNCTION_CALL: or FINAL_ANSWER:"""

                # Get user query for Gmail automation
                query = input("\n📧 Enter your Gmail request: ").strip()
                if not query:
                    query = "Get my unread emails and show me the first one"
                    print(f"Using default query: {query}")
                
                print(f"\n🚀 Processing query: {query}")
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response, consecutive_errors
                
                # Continue until agent provides FINAL_ANSWER (no iteration limit)
                while True:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    
                    # Safety checks to prevent infinite loops
                    if iteration >= max_safety_iterations:
                        print(f"\n⚠️ Safety limit reached ({max_safety_iterations} iterations)")
                        print("Stopping execution to prevent infinite loop")
                        break
                    
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"\n⚠️ Too many consecutive errors ({consecutive_errors})")
                        print("Stopping execution due to repeated failures")
                        break
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        for line in response_text.split('\n'):
                            line = line.strip()
                            if line.startswith("FUNCTION_CALL:"):
                                response_text = line
                                break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        consecutive_errors += 1
                        print(f"⚠️ Consecutive errors: {consecutive_errors}/{max_consecutive_errors}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            print("Breaking due to too many consecutive LLM failures")
                        break


                    if response_text.startswith("FUNCTION_CALL:"):
                        _, function_info = response_text.split(":", 1)
                        parts = [p.strip() for p in function_info.split("|")]
                        func_name, params = parts[0], parts[1:]
                        
                        print(f"\nDEBUG: Raw function info: {function_info}")
                        print(f"DEBUG: Split parts: {parts}")
                        print(f"DEBUG: Function name: {func_name}")
                        print(f"DEBUG: Raw parameters: {params}")
                        
                        try:
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} with {arguments} parameters, "
                                f"and the function returned {result_str}."
                            )
                            last_response = iteration_result
                            
                            # Reset consecutive errors on successful function call
                            consecutive_errors = 0

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            
                            # Track consecutive errors
                            consecutive_errors += 1
                            print(f"⚠️ Consecutive errors: {consecutive_errors}/{max_consecutive_errors}")
                            
                            if consecutive_errors >= max_consecutive_errors:
                                print("Breaking due to too many consecutive errors")
                                break

                    elif response_text.startswith("FINAL_ANSWER:"):
                        print("\n=== 📧 Gmail Automation Complete ===")
                        final_answer = response_text.split(":", 1)[1].strip()
                        print(f"✅ Final Result: {final_answer}")
                        
                        # Display completion summary
                        print("\n📋 Execution Summary:")
                        for i, step in enumerate(iteration_response, 1):
                            print(f"  {i}. {step}")
                        
                        break
                    
                    else:
                        # Handle invalid response format
                        print(f"⚠️ Invalid response format: {response_text}")
                        print("Expected FUNCTION_CALL: or FINAL_ANSWER:")
                        
                        consecutive_errors += 1
                        print(f"⚠️ Consecutive errors: {consecutive_errors}/{max_consecutive_errors}")
                        
                        if consecutive_errors >= max_consecutive_errors:
                            print("Breaking due to too many invalid responses")
                            break
                        
                        # Add to iteration log
                        iteration_response.append(f"Iteration {iteration + 1}: Invalid response format - {response_text[:100]}...")

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())
    
    

import openai
import json

#TODO: Add your OpenAI key here.
openai.api_key = ""

"""
The new OpenAI's new parallel function calling API launched at Dev Day in Nov 2023
can coordinate multiple function calls and feed the results back to the model.
OpenAI's example is here:
https://platform.openai.com/docs/guides/function-calling
IMHO the below is a better example than the one in the docs because it illustrates:
- the model's ability to select from different provided functions
- the model's ability to understand that a multi-day trip requires a flight and multiple hotel nights
EXAMPLE INPUT:
  How much would a 3 day trip to New York, Paris, and Tokyo cost?
  + functions get_flight_price(), get_nightly_hotel_price()
EXAMPLE OUTPUT FROM gpt-3.5-turbo-1106:
  The estimated cost for a 3-day trip to New York, Paris, and Tokyo, including flights and hotel accommodations, would be:
  New York:
  Flight: $450
  Hotel (3 nights): $900 (assuming $300 per night)
  Paris:
  Flight: $750
  Hotel (3 nights): $600 (assuming $200 per night)
 
  Tokyo:
  Flight: $1200
  Hotel (3 nights): $900 (assuming $300 per night)
  Total estimated cost: $4800
  Please note that this is just an estimate and actual prices may vary based on factors such as travel dates, availability, and accommodation preferences.
"""

def get_flight_price(city):
    """Get flight price for a given city"""
    # Dummy data for example purposes
    prices = {
        "New York": 450,
        "Paris": 750,
        "Tokyo": 1200
    }
    return json.dumps({"city": city, "flight_price": prices.get(city, float("nan"))})

def get_nightly_hotel_price(city):
    """Get nightly hotel room price for a given city"""
    # Dummy data for example purposes
    prices = {
        "New York": 300,
        "Paris": 200,
        "Tokyo": 300
    }
    
    return json.dumps({"city": city, "hotel_price": prices.get(city, float("nan"))})

def run_conversation():
    messages = [
        {"role": "user", "content": "What is the Capital of India"}
    ]
    tools = [
        {
            "type": "function",
            "function": {
                "name": "get_flight_price",
                "description": "Get flight price for a given city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city to get flight prices for",
                        }
                    },
                    "required": ["city"],
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_nightly_hotel_price",
                "description": "Get hotel room price for a given city",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "city": {
                            "type": "string",
                            "description": "The city to get hotel prices for",
                        }
                    },
                    "required": ["city"],
                },
            },
        }
    ]
    response = openai.chat.completions.create(
        model="gpt-3.5-turbo-1106",
        messages=messages,
        tools=tools,
        tool_choice="auto",  # auto is default, but we'll be explicit
    )
    
    
    print(response)
    response_message = response.choices[0].message
    tool_calls = response_message.tool_calls
    # Step 2: check if the model wanted to call a function
    if tool_calls:
        # Step 3: call the function
        # Note: the JSON response may not always be valid; be sure to handle errors
        available_functions = {
            "get_flight_price": get_flight_price,
            "get_nightly_hotel_price": get_nightly_hotel_price,
        }  # only one function in this example, but you can have multiple
        messages.append(response_message)  # extend conversation with assistant's reply
        # Step 4: send the info for each function call and function response to the model
        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_to_call = available_functions[function_name]
            function_args = json.loads(tool_call.function.arguments)
            function_response = function_to_call(
                city=function_args.get("city")
            )

            message_to_append = {
                    "tool_call_id": tool_call.id,
                    "role": "tool",
                    "name": function_name,
                    "content": function_response,
                }
            messages.append(message_to_append)  # extend conversation with function response


        print(messages);
        # CRUDE FIX FOR: 'content' is a required property - 'messages.1'.
        # OpenAI API is not parsing the ChatCompletionMessage correctly - it requires a content that's not None
        # Turns out, we can just set it to an empty string
        messages[1].content = "" # clear the first message (parsing bug)

        second_response = openai.chat.completions.create(
            model="gpt-3.5-turbo-1106",
            messages=messages,
        )  # get a new response from the model where it can see the function response
        return second_response

print(run_conversation())

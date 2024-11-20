from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import db_helper  # Importing the db_helper module
import generic_helper

app = FastAPI()

inprogress_orders = {}

# Adding a GET route for testing
@app.get("/")
async def root():
    return {"message": "FastAPI server is running"}

@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()
    
    # Extract the necessary information from the payload
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    outputContexts = payload['queryResult']['outputContexts']
    
    session_id = generic_helper.extract_session_id(outputContexts[0]["name"])
    
    # Check if the intent is for tracking the order
    if intent == "track_order-content:ongoing_tracking":
        # Call the track_order function from db_helper
        response = db_helper.track_order(parameters)
        # Return the response as JSON
        return JSONResponse(content=response)
    
    # Define intent handler dictionary for other intents
    intent_handler_dict = {
        'add_order-Context:ongoing_order': add_to_order,  # Update the intent name to match the one in your request
        # You can add more handlers for other intents here, for example:
        'order_remove-context:ongoing_order': remove_from_order,
        'Order_Complete-content:ongoing-order': complete_order,
        'track_order-content:ongoing_tracking': track_order,
        'Store_hours': store_hours,
    }
    
    # Check if the intent exists in the dictionary, and if so, call the corresponding function
    if intent in intent_handler_dict:
        return intent_handler_dict[intent](parameters, session_id)
    
    # Default response if the intent does not match
    return JSONResponse(content={"fulfillmentText": "Unable to process your request."})

# inprogress_order = {
#     'session_id1': {"yomari":2, "bara":1}, # 2 pieces of yomari and 1 bara
#     'session_id2': {"yomari":2, "bara":1,"dhau":2}, # add two dhau also
# }

# session_id_1 : "So far, You have 2 yomari, 1 bara and 2 dhau."

# Function to add a new order in previous one
def add_to_order(parameters: dict, session_id : str):
    food_items = parameters.get("Food_Items", [])
    quantities = parameters.get("number", [])
    
    # Check if the number of food items matches the number of quantities
    if len(food_items) != len(quantities):
        fulfillment_text = "Sorry! Did not understand. Could you please specify the food items and quantities clearly?"
    else:
        new_food_dict = dict(zip(food_items, quantities))
        
        if session_id in inprogress_orders:
            
           current_food_dict =  inprogress_orders[session_id]
           current_food_dict.update(new_food_dict)
           inprogress_orders[session_id] = current_food_dict
            
        else:
            inprogress_orders[session_id] = new_food_dict
            
        # cheking inprogress_orders
        # print("*"*50)
        # print(inprogress_orders)
        
        order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        
        # Handle the received food items and quantities
        fulfillment_text = f"Your current order is: {order_str}. Is there anything else you would like to add?"
        
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
    
# def add_to_order(parameters: dict, session_id: str):
#     """
#     Add food items and quantities to the current order. If the user asks to place a new order, clear previous orders and start fresh.
    
#     Args:
#         parameters (dict): Contains food items and their quantities.
#         session_id (str): Unique session ID for the user.
#     """
#     food_items = parameters.get("Food_Items", [])
#     quantities = parameters.get("number", [])

#     # Check if the number of food items matches the number of quantities
#     if len(food_items) != len(quantities):
#         fulfillment_text = "Sorry! Did not understand. Could you please specify the food items and quantities clearly?"
#     else:
#         # Create a dictionary from food items and quantities
#         new_food_dict = dict(zip(food_items, quantities))
        
#         # If the user wants a fresh order, reset the current order for this session
#         inprogress_orders[session_id] = new_food_dict

#         # Generate a string representation of the new order
#         order_str = generic_helper.get_str_from_food_dict(inprogress_orders[session_id])
        
#         # Response to the user with the new order
#         fulfillment_text = f"Your current order is: {order_str}. Is there anything else you would like to add?"

#     return JSONResponse(content={
#         "fulfillmentText": fulfillment_text
#     })



    
# Function to handle once the user completes their order
def complete_order(parameters: dict, session_id : str):
    
    if session_id not in inprogress_orders:
        fullfillment_txt = "Sorry! I'm having a trouble finding your order. Can you place a new order please?"

    else:
        orders = inprogress_orders[session_id]
        order_id = save_to_db(orders)
        
        if order_id == -1:
            fulfillment_text = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db_helper.get_total_order_price(order_id)

            fulfillment_text = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"
        
        del inprogress_orders[session_id]
                           
    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
        
def  save_to_db(orders:dict):
    
    # order = {"Aila":2, "Chana":4}
    next_order_id = db_helper.get_next_order_id()
    
    for food_item, quantity in orders.items():
       rcode =  db_helper.insert_order_item(food_item, quantity, next_order_id)
    
       if rcode == -1:
           return -1
       
    db_helper.insert_order_tracking(next_order_id, "in progress")  
      
       
    return next_order_id


# FUNCTION TO REMOVE THE FOOD ITEMS FROM THE ORDER LIST
# step1: locate the session id record
# step2: get the value from dict
# step3: remove the food items. requests["choila", 'baji']


def remove_from_order(parameters: dict, session_id: str):
    fulfillment_text = ""
    
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            "fulfillmentText": "I'm having trouble finding your order. Sorry! Can you place a new order, please?"
        })
    
    # Extract food items and quantities to remove
    food_items = parameters.get("food_items", [])
    quantities = parameters.get("number", [])

    print("*" * 50)
    print(inprogress_orders)
    print("Parameters received:", parameters)
    print("Food_Items extracted:", food_items)
    print("Quantities extracted:", quantities)

    if not food_items or not quantities or len(food_items) != len(quantities):
        return JSONResponse(content={
            "fulfillmentText": "Please specify the items and quantities you want to remove from your order."
        })

    current_order = inprogress_orders[session_id]
    removed_items = []
    no_such_items = []
    partial_removals = []

    for item, qty in zip(food_items, quantities):
        qty = float(qty)  # Ensure quantity is a number
        if item in current_order:
            if current_order[item] > qty:  # Reduce quantity
                current_order[item] -= qty
                partial_removals.append(f"{qty} {item}(s)")
            elif current_order[item] == qty:  # Remove item completely
                removed_items.append(item)
                del current_order[item]
            else:  # Quantity to remove is more than available
                partial_removals.append(f"only {current_order[item]} {item}(s)")
                del current_order[item]
        else:
            no_such_items.append(item)

    if removed_items:
        fulfillment_text += f"Removed {', '.join(removed_items)} from your order!"
    if partial_removals:
        fulfillment_text += f" Adjusted quantities: {', '.join(partial_removals)}."
    if no_such_items:
        fulfillment_text += f" Your order does not contain {', '.join(no_such_items)}."

    if not current_order:
        fulfillment_text += " Your order is now empty!"
    else:
        order_str = generic_helper.get_str_from_food_dict(current_order)
        fulfillment_text += f" Here is what is left in your order: {order_str}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })



# Track user order from the order id
def track_order(parameters: dict, session_id: str):
    order_id = int(parameters['order_id'])
    order_status = db_helper.get_order_status(order_id)
    if order_status:
        fulfillment_text = f"The order status for order id: {order_id} is: {order_status}"
    else:
        fulfillment_text = f"No order found with order id: {order_id}"

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })
    
    
# handle the store hours
def store_hours(parameters: dict, session_id: str):
    """
    Provides store information, including opening hours, days of operation,
    and home delivery facilities. Optionally logs session ID if provided.
    """
    store_name = "Newari Pasa"
    opening_time = "10:00 AM"
    closing_time = "12:00 AM"
    delivery_facility = "home delivery"
    days_open = "all days of the week"
    peak_hours = "1pm:4pm"

    fulfillment_text = (
        f"Our {store_name} is open from {opening_time} in the morning to {closing_time} at midnight. "
        f"We are open {days_open}, so feel free to visit or place your orders anytime during these hours. "
        f"We also offer {delivery_facility} for your convenience! "
        f"There is special discount offer from {peak_hours} on Monday and Thursday"
    )

    # Optional: Log session ID for debugging or analytics
    if session_id:
        print(f"Store Hours intent invoked by session ID: {session_id}")

    return JSONResponse(content={
        "fulfillmentText": fulfillment_text
    })

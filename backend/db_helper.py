import mysql.connector

# Establish a global MySQL connection
global cnx

cnx = mysql.connector.connect(
    host="localhost",
    user="root",
    password="root",
    database="newar_foodi"
)

# Function to get the order status from the database
def get_order_status(order_id: int):
    try:
        # Create a cursor object
        cursor = cnx.cursor()

        # Define the query
        query = "SELECT status FROM order_tracking WHERE order_id = %s"

        # Execute the query
        cursor.execute(query, (order_id,))

        # Fetch the result
        result = cursor.fetchone()

        # Close the cursor
        cursor.close()

        # Return the order status if found
        if result:
            return result[0]
        else:
            return None
    except mysql.connector.Error as err:
        print(f"Error: {err}")
        return None

# Function to handle the order tracking request
def track_order(parameters):
    # Safely access 'number'
    order_id_list = parameters.get('number', [])
    
    if not order_id_list:
        return {"fulfillmentText": "Order ID is missing in the request."}

    try:
        # Extract the order ID
        order_id = int(order_id_list[0])
    except (ValueError, IndexError):
        return {"fulfillmentText": "Invalid Order ID format. Please provide a numeric order ID."}

    # Get the order status from the database
    status = get_order_status(order_id)

    # Check if the status is found
    if status:
        return {"fulfillmentText": f"The status of your order ID {order_id} is: {status}"}
    else:
        return {"fulfillmentText": f"Order ID {order_id} not found in our records."}

# Function to get the next available order_id
def get_next_order_id():
    cursor = cnx.cursor()

    # Executing the SQL query to get the next available order_id
    query = "SELECT MAX(order_id) FROM orders"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    # Returning the next available order_id
    if result is None:
        return 1
    else:
        return result + 1
    
# Function to add order items into db   
def insert_order_item(food_item, quantity,order_id):
    try:
        cursor = cnx.cursor()

        # Calling the stored procedure
        cursor.callproc('insert_order_item', (food_item, quantity, order_id))

        # Committing the changes
        cnx.commit()

        # Closing the cursor
        cursor.close()

        print("Order item inserted successfully!")

        return 1

    except mysql.connector.Error as err:
        print(f"Error inserting order item: {err}")

        # Rollback changes if necessary
        cnx.rollback()

        return -1

    except Exception as e:
        print(f"An error occurred: {e}")
        # Rollback changes if necessary
        cnx.rollback()

        return -1


# Calling the function of the MYSQL db directly 
def get_total_order_price(order_id):
    cursor = cnx.cursor()

    # Executing the SQL query to get the total order price
    query = f"SELECT get_total_order_price({order_id})"
    cursor.execute(query)

    # Fetching the result
    result = cursor.fetchone()[0]

    # Closing the cursor
    cursor.close()

    return result

# Function to insert a record into the order_tracking table
def insert_order_tracking(order_id, status):
    cursor = cnx.cursor()

    # Inserting the record into the order_tracking table
    insert_query = "INSERT INTO order_tracking (order_id, status) VALUES (%s, %s)"
    cursor.execute(insert_query, (order_id, status))

    # Committing the changes
    cnx.commit()

    # Closing the cursor
    cursor.close()
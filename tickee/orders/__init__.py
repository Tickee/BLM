"""
Order Session Management
========================

    An order can be in 3 different states depending on the phase 
    of the sale process.
    
      - STARTED
        The user initiated a request for purchasing an amount of tickets of 
        a particular ticket type. The amount of tickets will be reserved for
        a set time. During this time they cannot be sold by other people.
         
      - PURCHASED
        The organizer confirms the payment of the order. The user is now sure
        of a ticket for the event.
       
      - TIMEOUT
        The set time that the tickets were reserved has timed out and the 
        tickets are once again available for purchase by other users.
      
      - CANCELLED
        The organizer sets a ticket order to cancelled.
    
Timing out an order session
---------------------------

    By successfully initiating an order session, we can guarantee the 
    visitor the possibility to purchase available tickets at the beginning 
    of the session by reserving the amount for the duration of the session.
    
    If the order session takes too long, the order will time out and the 
    reserved tickets will once again become available to the public.
    
    In the rare case an order session receives a payment confirmation
    of a timed out session, we will still set the order to "Purchased" and
    send the user his purchase confirmation. This might cause an overbooking
    of the event if done during a CLAIMED phase of the specific ticket type.

State Flow
----------

                               +-----------+       +-------------+
                         +---->| Purchased +------>|  Cancelled  |
                     (1) |     +-----------+  (4)  +-------------+
                         |           ^
           +---------+   |           |
           | Started +---+           | (3)
           +---------+   |           |
                         |           |
                     (2) |     +-----+-----+
                         +---->|  Timeout  |
                               +-----------+
    
    (1) A purchase confirmation with the correct order_key has been sent.
    (2) It took too long for the order to be completed
    (3) In the rare case a timed out order receives a confirmed payment code. 
    (4) The purchased order was cancelled by the organizer

Using the ``OrderManager``
--------------------------

    Starting an Order
    ^^^^^^^^^^^^^^^^^
    
    When the user requests his first ticket an ``Order`` is started using the
    ``start_order`` method. This will create an order session where the user
    can request tickets.
    
    Reserving Tickets
    ^^^^^^^^^^^^^^^^^
    
    The requesting of tickets can be done using the ``add_tickets`` method, 
    reserving a specific amount of a particular ``TicketType``. Upon a 
    successful reservation of the tickets, the order key of the ``Order`` 
    session will be returned. These tickets will not be available for other 
    users.
    
    Finalizing the Order
    ^^^^^^^^^^^^^^^^^^^^
    
    At any point the order can be finalized by calling one of the following 
    methods:
    
        -  ``confirm_purchase``: Confirms the ``Order`` as being purchased.
        -  ``timeout_sessions``: Times out the ``Order`` and releases the
                                 reserved tickets.

"""
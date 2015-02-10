import sqlahelper

Session = sqlahelper.get_session()

def delete_ticket(ticket):
    """ Removes a ticket from the database """
    Session.delete(ticket)


def code_to_id(code):
    return int(code, 16)
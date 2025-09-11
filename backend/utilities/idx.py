import uuid


def generate_checkout_id():
    '''Generate a unique checkout ID'''
    return "chk_" + uuid.uuid4().hex

def generate_payment_id():
    '''Generate a unique payment ID'''
    return "pay_" + uuid.uuid4().hex

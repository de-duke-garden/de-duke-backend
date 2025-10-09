import uuid


def generate_checkout_id():
    '''Generate a unique checkout ID'''
    return "chk_" + uuid.uuid4().hex

def generate_payment_id():
    '''Generate a unique payment ID'''
    return "pay_" + uuid.uuid4().hex

def generate_user_id():
    '''Generate a unique user ID'''
    return "usr_" + uuid.uuid4().hex

def generate_otp_id():
    '''Generate a unique OTP ID'''
    return "otp_" + uuid.uuid4().hex

def generate_phone_number_id():
    '''Generate a unique Phone Number ID'''
    return "phn_" + uuid.uuid4().hex

def generate_host_id():
    '''Generate a unique Host ID'''
    return "hst_" + uuid.uuid4().hex

def generate_property_id():
    '''Generate a unique Property ID'''
    return "prp_" + uuid.uuid4().hex

def generate_property_image_id():
    '''Generate a unique Property Image ID'''
    return "pim_" + uuid.uuid4().hex

def generate_property_room_id():
    '''Generate a unique Property Room ID'''
    return "pro_" + uuid.uuid4().hex

def generate_banned_property_id():
    '''Generate a unique Banned Property ID'''
    return "bpr_" + uuid.uuid4().hex

def generate_verified_property_id():
    '''Generate a unique Verified Property ID'''
    return "vpr_" + uuid.uuid4().hex

def generate_bookmarked_property_id():
    '''Generate a unique Bookmarked Property ID'''
    return "bkp_" + uuid.uuid4().hex

def generate_interested_property_id():
    '''Generate a unique Interested Property ID'''
    return "ipr_" + uuid.uuid4().hex

def generate_interested_property_dialogue_id():
    '''Generate a unique Interested Property Dialogue ID'''
    return "ipd_" + uuid.uuid4().hex
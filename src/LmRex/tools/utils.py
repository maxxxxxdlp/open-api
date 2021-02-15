
# ......................................................
def is_uuid(uuidstr):
    """Identify whether the string follows a UUID pattern
    
    Args:
        uuidstr: string to test for possible UUID
        
    Returns:
        True if possible UUID string, False if not
    """
    if len(uuidstr) <= 30:
        return False
    
    cleanstr = uuidstr.replace('-', '')
    try:
        int(cleanstr, 16)
    except:
        return False
return True


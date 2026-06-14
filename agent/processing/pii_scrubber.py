import re

def scrub_pii(text: str) -> str:
    """Removes emails, phone numbers, and potential Aadhaar/PAN patterns from text."""
    if not text:
        return text
        
    # Email pattern
    text = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+').sub('[EMAIL]', text)
    
    # Phone number pattern (matches basic Indian mobile formats like +919876543210, 9876543210, 98765 43210)
    text = re.compile(r'(?:\+91[\-\s]?)?[6789]\d{9}').sub('[PHONE]', text)
    text = re.compile(r'(?:\+91[\-\s]?)?[6789]\d{4}[\-\s]?\d{5}').sub('[PHONE]', text)
    
    # Potential Aadhaar pattern (12 digits with spaces)
    text = re.compile(r'\b\d{4}\s\d{4}\s\d{4}\b').sub('[AADHAAR]', text)
    text = re.compile(r'\b\d{12}\b').sub('[AADHAAR]', text)
    
    # Potential PAN pattern (5 letters, 4 numbers, 1 letter)
    text = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b', re.IGNORECASE).sub('[PAN]', text)
    
    # URL pattern
    text = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+').sub('[URL]', text)
    
    return text

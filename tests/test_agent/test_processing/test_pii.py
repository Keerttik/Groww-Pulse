from agent.processing.pii_scrubber import scrub_pii

def test_scrub_email():
    text = "Contact me at user@example.com for info."
    assert scrub_pii(text) == "Contact me at [EMAIL] for info."

def test_scrub_phone():
    text = "Call +919876543210 immediately."
    assert scrub_pii(text) == "Call [PHONE] immediately."
    
    text = "Number is 98765 43210"
    assert scrub_pii(text) == "Number is [PHONE]"

def test_scrub_aadhaar():
    text = "My aadhaar is 1234 5678 9012"
    assert scrub_pii(text) == "My aadhaar is [AADHAAR]"

def test_scrub_pan():
    text = "PAN card ABCDE1234F is mine"
    assert scrub_pii(text) == "PAN card [PAN] is mine"

def test_no_pii():
    text = "Great app, highly recommended!"
    assert scrub_pii(text) == text

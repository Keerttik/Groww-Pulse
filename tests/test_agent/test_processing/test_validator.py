from agent.models.types import Quote, Review
from agent.processing.validator import validate_quotes

def test_validate_quotes():
    reviews = [
        Review(rating=5, text="I love the new UI design. It is super fast.", thumbs_up=0, app_version="1.0"),
        Review(rating=1, text="App keeps crashing on login.", thumbs_up=0, app_version="1.0")
    ]
    
    quotes = [
        Quote(text="I love the new UI design.", rating=1, validated=False),  # Wrong rating, exists
        Quote(text="App keeps crashing", rating=1, validated=False),  # Substring match
        Quote(text="This app is terrible.", rating=1, validated=False) # Doesn't exist
    ]
    
    valid_quotes = validate_quotes(quotes, reviews)
    
    assert len(valid_quotes) == 3
    assert valid_quotes[0].validated == True
    assert valid_quotes[0].rating == 5  # Should be corrected to actual rating
    
    assert valid_quotes[1].validated == True
    
    assert valid_quotes[2].validated == False

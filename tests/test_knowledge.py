from app.knowledge import split_text

def test_empty(): assert split_text("") == []
def test_short(): assert split_text("short text") == ["short text"]
def test_long(): assert len(split_text("x"*3000,size=1000,overlap=100)) >= 3

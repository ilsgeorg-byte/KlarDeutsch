import requests

def test_search():
    try:
        # Search for German word
        r = requests.get("http://localhost:5000/api/words/search?q=Tisch")
        print("Search for 'Tisch':")
        print(r.json())
        
        # Search for Russian word
        r = requests.get("http://localhost:5000/api/words/search?q=понимать")
        print("\nSearch for 'понимать':")
        print(r.json())
        
    except Exception as e:
        print(f"Error testing search: {e}")

if __name__ == "__main__":
    test_search()

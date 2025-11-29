import requests
import json
import time

def test_system():
    url = "http://localhost:5000/api/process-rfp"
    
    # Test with a URL that likely contains relevant keywords
    # Using a Wikipedia page as a stable "real" URL that contains the word "Laptop"
    test_input = "https://en.wikipedia.org/wiki/Laptop"
    
    print(f"Testing System with URL: {test_input}")
    print("-" * 50)
    
    try:
        start_time = time.time()
        response = requests.post(url, json={"input": test_input})
        response.raise_for_status()
        data = response.json()
        duration = time.time() - start_time
        
        print(f"Request completed in {duration:.2f} seconds\n")
        
        # Verify Sales Agent
        print("1. Sales Agent:")
        if "workflow" in data and "sales" in data["workflow"]:
            sales = data["workflow"]["sales"]
            print(f"   - Title: {sales['rfp_metadata'].get('title')}")
            print(f"   - Items Found: {len(sales.get('items', []))}")
            for item in sales.get('items', []):
                print(f"     * {item['name']} (Qty: {item['quantity']})")
        else:
            print("   [FAIL] No Sales Data")

        # Verify Technical Agent
        print("\n2. Technical Agent:")
        if "workflow" in data and "technical" in data["workflow"]:
            tech = data["workflow"]["technical"]
            print(f"   - Overall Match: {tech['tech_match'].get('overall_match_percent')}")
            print(f"   - Matched SKUs: {len(tech['tech_match'].get('matched_skus', []))}")
        else:
            print("   [FAIL] No Technical Data")

        # Verify Pricing Agent
        print("\n3. Pricing Agent:")
        if "workflow" in data and "pricing" in data["workflow"]:
            pricing = data["workflow"]["pricing"]
            print(f"   - Total Cost: ${pricing['pricing'].get('total_cost')}")
            print(f"   - Breakdown Items: {len(pricing['pricing'].get('breakdown', []))}")
        else:
            print("   [FAIL] No Pricing Data")

        # Verify Master Agent
        print("\n4. Master Agent:")
        if "workflow" in data and "master" in data["workflow"]:
            master = data["workflow"]["master"]
            print("   - Final Document Generated: Yes")
            print(f"   - Document Length: {len(master['final_response'].get('final_document_text', ''))} chars")
        else:
            print("   [FAIL] No Master Data")
            
        print("-" * 50)
        print("OVERALL STATUS: SUCCESS" if "workflow" in data else "OVERALL STATUS: FAILED")

    except Exception as e:
        print(f"Test Failed: {e}")

if __name__ == "__main__":
    test_system()

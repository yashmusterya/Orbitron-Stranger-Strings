import json
import os
import datetime
import requests
from bs4 import BeautifulSoup
import re

# --- Configuration ---
DATA_DIR = "data"
OUTPUT_DIR = "outputs/test_run"
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
PRICING_FILE = os.path.join(DATA_DIR, "pricing_rules.json")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Helper Functions ---
def save_json(filename, data):
    path = os.path.join(OUTPUT_DIR, filename)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Saved: {path}")

def load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

# --- Agents ---

class SalesAgent:
    def process(self, url):
        print(f"[Sales Agent] Fetching URL: {url}")
        
        data = {
            "rfp_metadata": {
                "contract_id": "Not available",
                "title": "Not available",
                "authority": "Not available",
                "category": "Not available",
                "bid_dates": {
                    "start": "Not available",
                    "end": "Not available"
                }
            },
            "items": [],
            "financials": {},
            "delivery_terms": "Not available",
            "documents": []
        }

        try:
            # Real Scraping Logic
            if url.startswith("http"):
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(url, headers=headers, timeout=10, verify=False)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extract Title
                title_tag = soup.find('title') or soup.find('h1')
                if title_tag:
                    data["rfp_metadata"]["title"] = title_tag.get_text(strip=True)
                
                # Extract Text for analysis
                text_content = soup.get_text(separator=' ', strip=True)
                
                # Heuristics for Contract ID
                id_match = re.search(r'(Tender No|Contract ID|Ref No)[:\s]+([A-Za-z0-9\-/]+)', text_content, re.IGNORECASE)
                if id_match:
                    data["rfp_metadata"]["contract_id"] = id_match.group(2)
                
                # Heuristics for Dates
                date_matches = re.findall(r'\d{4}-\d{2}-\d{2}', text_content)
                if date_matches:
                    data["rfp_metadata"]["bid_dates"]["start"] = date_matches[0]
                    if len(date_matches) > 1:
                        data["rfp_metadata"]["bid_dates"]["end"] = date_matches[-1]
                
                # Heuristics for Authority
                auth_match = re.search(r'(Authority|Organization|Department)[:\s]+([^.\n]+)', text_content, re.IGNORECASE)
                if auth_match:
                    data["rfp_metadata"]["authority"] = auth_match.group(2).strip()

            else:
                # Fallback for text input (testing)
                data["rfp_metadata"]["title"] = "Manual Text Input"
                data["rfp_metadata"]["description"] = url
                text_content = url # Treat the input as the text content

            # Common Keyword Extraction (Applied to both Scraped Text and Manual Input)
            known_keywords = ["Laptop", "Server", "Cable", "Software", "Office 365", "Switch", "Router"]
            
            for keyword in known_keywords:
                if keyword.lower() in text_content.lower():
                    # Try to find a quantity near the keyword
                    # Regex: keyword ... number OR number ... keyword
                    qty = 1 # Default
                    qty_match = re.search(rf'{keyword}.{{0,20}}?(\d+)', text_content, re.IGNORECASE)
                    if not qty_match:
                            qty_match = re.search(rf'(\d+).{{0,20}}?{keyword}', text_content, re.IGNORECASE)
                    
                    if qty_match:
                        qty = int(qty_match.group(1))
                    
                    data["items"].append({
                        "name": keyword,
                        "quantity": qty,
                        "description": f"Detected {keyword} in text"
                    })

        except Exception as e:
            print(f"[Sales Agent] Error: {e}")
            data["error"] = str(e)

        return data

class TechnicalAgent:
    def process(self, sales_data):
        print("[Technical Agent] Matching SKUs...")
        inventory = load_json(INVENTORY_FILE)
        
        matched_skus = []
        total_items = len(sales_data.get("items", []))
        matched_count = 0
        
        for item in sales_data.get("items", []):
            best_match = None
            highest_score = 0
            
            for sku in inventory:
                score = 0
                # Simple keyword matching
                item_name = item["name"].lower()
                sku_name = sku["name"].lower()
                sku_cat = sku["category"].lower()
                
                if sku_name in item_name or item_name in sku_name:
                    score += 50
                if sku_cat in item_name:
                    score += 30
                
                if score > highest_score:
                    highest_score = score
                    best_match = sku
            
            if best_match and highest_score > 0:
                matched_count += 1
                matched_skus.append({
                    "item": item["name"],
                    "matched_sku": best_match["sku"],
                    "sku_name": best_match["name"],
                    "match_percent": f"{min(highest_score + 40, 100)}%", # Simulation
                    "quantity": item["quantity"]
                })
            else:
                matched_skus.append({
                    "item": item["name"],
                    "matched_sku": "Not available",
                    "match_percent": "0%"
                })

        overall_match = int((matched_count / total_items * 100)) if total_items > 0 else 0

        return {
            "tech_match": {
                "overall_match_percent": f"{overall_match}%",
                "matched_skus": matched_skus
            }
        }

class PricingAgent:
    def process(self, tech_data):
        print("[Pricing Agent] Calculating pricing...")
        rules = load_json(PRICING_FILE)
        inventory = {item['sku']: item for item in load_json(INVENTORY_FILE)}
        
        breakdown = []
        total_cost = 0.0
        
        for match in tech_data["tech_match"]["matched_skus"]:
            if match["matched_sku"] == "Not available":
                continue
                
            sku_info = inventory.get(match["matched_sku"])
            base_cost = sku_info["base_cost"]
            qty = match["quantity"]
            
            # Margin logic
            margin_percent = rules["standard_margin_percent"]
            if sku_info["category"] == "Software":
                margin_percent = rules["software_margin_percent"]
            
            unit_cost = base_cost
            profit_margin = base_cost * (margin_percent / 100)
            final_unit_price = unit_cost + profit_margin
            
            # Add tax
            tax = final_unit_price * (rules["tax_rate_percent"] / 100)
            final_price_inc_tax = final_unit_price + tax
            
            line_total = final_price_inc_tax * qty
            total_cost += line_total
            
            breakdown.append({
                "sku": match["matched_sku"],
                "unit_cost": f"{unit_cost:.2f}",
                "profit_margin": f"{profit_margin:.2f}",
                "tax": f"{tax:.2f}",
                "final_unit_price": f"{final_price_inc_tax:.2f}",
                "quantity": qty,
                "line_total": f"{line_total:.2f}"
            })
            
        return {
            "pricing": {
                "total_cost": f"{total_cost:.2f}",
                "currency": "INR",
                "breakdown": breakdown
            }
        }

class MasterAgent:
    def process(self, sales_data, tech_data, pricing_data):
        
        # Construct the final document text
        doc_lines = []
        doc_lines.append(f"# RFP Response: {sales_data['rfp_metadata']['title']}")
        doc_lines.append(f"**Contract ID:** {sales_data['rfp_metadata']['contract_id']}")
        doc_lines.append(f"**Authority:** {sales_data['rfp_metadata']['authority']}")
        doc_lines.append(f"**Date:** {datetime.date.today()}")
        doc_lines.append("\n## Executive Summary")
        doc_lines.append(f"We are pleased to submit our proposal. We have achieved a {tech_data['tech_match']['overall_match_percent']} technical match for your requirements.")
        
        doc_lines.append("\n## Technical & Commercial Breakdown")
        doc_lines.append("| Item | SKU | Qty | Unit Price | Total |")
        doc_lines.append("|---|---|---|---|---|")
        
        for item in pricing_data["pricing"]["breakdown"]:
            # Find item name from tech data
            item_name = next((t['item'] for t in tech_data['tech_match']['matched_skus'] if t['matched_sku'] == item['sku']), item['sku'])
            doc_lines.append(f"| {item_name} | {item['sku']} | {item['quantity']} | ₹{item['final_unit_price']} | ₹{item['line_total']} |")
            
        doc_lines.append(f"\n**Grand Total:** ₹{pricing_data['pricing']['total_cost']}")
        
        final_doc_text = "\n".join(doc_lines)
        
        return {
            "final_response": {
                "rfp_summary": sales_data["rfp_metadata"],
                "technical_summary": tech_data["tech_match"],
                "pricing_summary": pricing_data["pricing"],
                "final_document_text": final_doc_text
            }
        }

class Orchestrator:
    def __init__(self):
        self.sales = SalesAgent()
        self.technical = TechnicalAgent()
        self.pricing = PricingAgent()
        self.master = MasterAgent()
    
    def run(self, url):
        print("=== Starting Strict RFP Workflow ===")
        
        # Step 1: Sales
        step1 = self.sales.process(url)
        save_json("step1_sales.json", step1)
        
        # Step 2: Technical
        step2 = self.technical.process(step1)
        save_json("step2_technical.json", step2)
        
        # Step 3: Pricing
        step3 = self.pricing.process(step2)
        save_json("step3_pricing.json", step3)
        
        # Step 4: Master (Final Response)
        step4 = self.master.process(step1, step2, step3)
        save_json("step4_master.json", step4)
        
        # Save Markdown for easy reading
        with open(os.path.join(OUTPUT_DIR, "final_proposal.md"), 'w', encoding='utf-8') as f:
            f.write(step4["final_response"]["final_document_text"])

        print("=== Workflow Complete ===")
        
        # Final Main Agent Output
        return {
            "status": "complete",
            "workflow": {
                "sales": step1,
                "technical": step2,
                "pricing": step3,
                "master": step4
            },
            "final_document": step4["final_response"]["final_document_text"]
        }

if __name__ == "__main__":
    # Test with a dummy URL or text if run directly
    orch = Orchestrator()
    orch.run("https://example.com/tender/office-supplies") # Will likely fail scraping but test flow

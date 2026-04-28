# agent.py - Fixed version with date extraction

from airlabs_tools import AirLabsTools
# from email_sender import EmailSender
import re
from datetime import datetime

class TravelAgent:
    def __init__(self):
        self.flight_tools = AirLabsTools()
        # self.email_sender = EmailSender()
    
    def parse_query(self, query: str) -> dict:
        """Extract origin, destination, date, and email from user query"""
        query_lower = query.lower()
        
        # Extract date (various formats)
        date = None
        
        # Format 1: DD Month YYYY (e.g., 19 June 2026)
        date_match = re.search(r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', query_lower)
        if date_match:
            day = date_match.group(1)
            month = date_match.group(2)
            year = date_match.group(3)
            date = f"{year}-{self.month_to_number(month)}-{day.zfill(2)}"
        
        # Format 2: YYYY-MM-DD
        if not date:
            date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', query)
            if date_match:
                date = date_match.group(0)
        
        # Format 3: DD/MM/YYYY or DD-MM-YYYY
        if not date:
            date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', query)
            if date_match:
                day = date_match.group(1)
                month = date_match.group(2)
                year = date_match.group(3)
                date = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        
        # Extended city list with common spellings
        cities = {
            "moscow": ["moscow", "moskva", "moscv", "msk"],
            "dubai": ["dubai", "dubay", "dxb"],
            "cairo": ["cairo", "cario", "qahira", "cai"],
            "istanbul": ["istanbul", "istambul", "stambul", "ist"],
            "antalya": ["antalya", "antalia", "ant"],
            "london": ["london", "lond", "lon"],
            "paris": ["paris", "par", "cdg"],
            "bangkok": ["bangkok", "bkk"],
            "tashkent": ["tashkent", "tas"],
            "baku": ["baku", "bki", "gyd"],
            "ufa": ["ufa"],
            "casablanca": ["casablanca", "casa", "cmn"],
        }
        
        # Find which cities are mentioned
        found = []
        for city, variants in cities.items():
            for variant in variants:
                if variant in query_lower:
                    found.append(city)
                    break
        
        origin = found[0] if len(found) >= 1 else None
        destination = found[1] if len(found) >= 2 else None
        
        # Find email
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', query)
        email = email_match.group(0) if email_match else None
        
        # Fix city names (capitalize properly)
        if origin:
            origin = origin.title()
        if destination:
            destination = destination.title()
        
        return {
            'origin': origin,
            'destination': destination,
            'date': date,
            'email': email
        }
    
    def month_to_number(self, month: str) -> str:
        """Convert month name to number"""
        months = {
            'january': '01', 'february': '02', 'march': '03', 'april': '04',
            'may': '05', 'june': '06', 'july': '07', 'august': '08',
            'september': '09', 'october': '10', 'november': '11', 'december': '12'
        }
        return months.get(month, '01')
    
    def run(self):
        print("\n" + "=" * 70)
        print("🤖 SMART TRAVEL AGENT - Flight Search Assistant")
        print("=" * 70)
        print("\nI can help you find flights from anywhere!")
        print("\n📝 Examples:")
        print("   • Moscow to Dubai")
        print("   • Moscow to Cairo on 19 June 2026")
        print("   • Moscow to Istanbul 2026-07-15")
        print("   • Ufa to Casablanca")
        print("\n" + "─" * 70)
        
        while True:
            print("\n" + "─" * 70)
            user_input = input("💬 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Safe travels!")
                break
            
            if not user_input:
                continue
            
            # Parse the query
            info = self.parse_query(user_input)
            
            # If cities missing, ask for them
            if not info['origin']:
                info['origin'] = input("📍 Departure city: ").strip().title()
            
            if not info['destination']:
                info['destination'] = input("🎯 Destination city: ").strip().title()
            
            # If date missing, ask if they want to specify
            if not info['date']:
                add_date = input("📅 Add travel date? (y/n): ").lower()
                if add_date == 'y':
                    date_input = input("   Enter date (YYYY-MM-DD or DD Month YYYY): ").strip()
                    # Try to parse the date
                    if '-' in date_input and len(date_input) == 10:
                        info['date'] = date_input
                    else:
                        # Try to parse "19 June 2026" format
                        date_match = re.search(r'(\d{1,2})\s+(\w+)\s+(\d{4})', date_input.lower())
                        if date_match:
                            day = date_match.group(1)
                            month = self.month_to_number(date_match.group(2))
                            year = date_match.group(3)
                            info['date'] = f"{year}-{month}-{day.zfill(2)}"
                        else:
                            info['date'] = date_input
            
            # Search for flights
            print(f"\n🔍 Searching flights from {info['origin']} to {info['destination']}...")
            if info['date']:
                print(f"   Travel date: {info['date']}")
            
            results = self.flight_tools.search_flights(info['origin'], info['destination'], info['date'])
            print(self.flight_tools.format_results(results))
            
            # Ask about email if results found
            if results and (results.get('direct') or results.get('connecting')):
                send = input("\n📧 Send results to email? (y/n): ").lower()
                if send == 'y':
                    email = input("📧 Your email: ").strip()
                    if email:
                        # Format results for email
                        email_body = self.format_results_for_email(results, info)
                        self.email_sender.send_email(email, f"Flight Deals: {info['origin']} to {info['destination']}", email_body)
            else:
                print("\n💡 No flights found for this route.")
                print("   Try: Moscow to Istanbul, Moscow to Tashkent, or Moscow to Dubai")


class QuickTravelAgent:
    """Simpler version that just passes raw query"""
    
    def __init__(self):
        self.flight_tools = AirLabsTools()
        # self.email_sender = EmailSender()
    
    def run(self):
        print("\n" + "=" * 70)
        print("🤖 QUICK TRAVEL AGENT")
        print("=" * 70)
        print("\nJust type: 'Moscow to Istanbul on 19 June 2026'")
        print("Or: 'Moscow to Dubai'")
        print("\n" + "─" * 70)
        
        while True:
            print("\n" + "─" * 70)
            user_input = input("💬 You: ").strip()
            
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if not user_input:
                continue
            
            # Parse the query
            info = self.parse_query_simple(user_input)
            
            if not info['origin'] or not info['destination']:
                print("\n❌ Please use format: 'City to City'")
                print("   Example: 'Moscow to Istanbul'")
                continue
            
            print(f"\n🔍 Searching: {info['origin']} → {info['destination']}")
            if info['date']:
                print(f"   Date: {info['date']}")
            
            results = self.flight_tools.search_flights(info['origin'], info['destination'], info['date'])
            print(self.flight_tools.format_results(results))
    
    def parse_query_simple(self, query: str) -> dict:
        """Simple query parsing"""
        query_lower = query.lower()
        
        # Extract date
        date = None
        date_match = re.search(r'(\d{1,2})\s+(january|february|march|april|may|june|july|august|september|october|november|december)\s+(\d{4})', query_lower)
        if date_match:
            months = {'january':'01','february':'02','march':'03','april':'04','may':'05','june':'06',
                     'july':'07','august':'08','september':'09','october':'10','november':'11','december':'12'}
            date = f"{date_match.group(3)}-{months[date_match.group(2)]}-{date_match.group(1).zfill(2)}"
        
        # Extract cities using "to" pattern
        origin = None
        destination = None
        
        if ' to ' in query_lower:
            parts = query_lower.split(' to ')
            if len(parts) >= 2:
                origin_part = parts[0].strip()
                dest_part = parts[1].split()[0].strip() if parts[1] else None
                
                # Clean up origin (remove words like 'from')
                origin_part = origin_part.replace('from ', '').replace('fly from ', '').strip()
                
                origin = origin_part.title()
                destination = dest_part.title() if dest_part else None
        
        return {'origin': origin, 'destination': destination, 'date': date}


def main():
    print("\n" + "=" * 70)
    print("✈️  WELCOME TO YOUR PERSONAL TRAVEL AGENT  ✈️")
    print("=" * 70)
    
    print("\nChoose mode:")
    print("   1. 🧠 Smart Mode (asks questions if needed)")
    print("   2. ⚡ Quick Mode (type everything at once)")
    
    choice = input("\n👉 Enter 1 or 2: ").strip()
    
    if choice == '2':
        agent = QuickTravelAgent()
    else:
        agent = TravelAgent()
    
    agent.run()


if __name__ == "__main__":
    main()
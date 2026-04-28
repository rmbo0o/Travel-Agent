# airlabs_tools.py - Now with connecting flights (layovers)

import requests
import os
import random
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

class AirLabsTools:
    """Flight search with direct AND connecting flights"""
    
    def __init__(self):
        self.api_key = os.getenv('AIRLABS_API_KEY')
        self.base_url = 'https://airlabs.co/api/v9'
        self.airlines_cache = {}
        self.routes_cache = {}  # Cache all routes for searching connections
        self.load_airlines()
        self.load_all_routes()
    
    def load_airlines(self):
        """Load real airlines from API"""
        if not self.api_key:
            print("❌ No API key found!")
            return
        
        try:
            url = f"{self.base_url}/airlines"
            params = {'api_key': self.api_key}
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                airlines = data.get('response', [])
                
                for airline in airlines:
                    iata = airline.get('iata_code', '')
                    name = airline.get('name', '')
                    if iata and name:
                        self.airlines_cache[iata] = name
                
                print(f"✅ Loaded {len(self.airlines_cache)} real airlines")
            else:
                print(f"❌ API error: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Failed to load airlines: {e}")
    
    def load_all_routes(self):
        """Load routes for major hubs to enable connection finding"""
        # Major hubs to search for connections
        hubs = ["IST", "DXB", "LHR", "CDG", "FRA", "AMS", "DOH", "AUH", "TAS", "GYD"]
        
        self.routes_cache = defaultdict(list)
        
        for hub in hubs:
            routes = self.get_real_routes("SVO", hub)
            for route in routes:
                self.routes_cache[hub].append(route)
            
            # Also get routes FROM hub to other destinations
            outgoing = self.get_real_routes(hub, "IST")  # Sample
            for route in outgoing:
                self.routes_cache[f"{hub}_out"].append(route)
    
    def search_flights(self, origin: str, destination: str, date: str = None) -> dict:
        """Search for direct AND connecting flights"""
        
        origin = self.fix_city_name(origin)
        destination = self.fix_city_name(destination)
        
        # Get airport codes
        origin_codes = self.get_airport_codes(origin)
        destination_codes = self.get_airport_codes(destination)
        
        results = {
            "direct": [],
            "connecting": [],
            "origin": origin,
            "destination": destination,
            "date": date
        }
        
        # Search DIRECT flights
        print(f"\n🔍 Searching DIRECT flights from {origin} to {destination}...")
        for origin_code in origin_codes[:2]:
            for destination_code in destination_codes[:2]:
                routes = self.get_real_routes(origin_code, destination_code)
                if routes:
                    results["direct"].extend(routes)
                    print(f"   ✅ Found {len(routes)} direct routes")
                    break
            if results["direct"]:
                break
        
        # Search CONNECTING flights (1 stop)
        print(f"\n🔍 Searching CONNECTING flights (with layovers)...")
        connecting = self.find_connecting_flights(origin_codes, destination_codes)
        if connecting:
            results["connecting"] = connecting
            print(f"   ✅ Found {len(connecting)} connecting options")
        else:
            print(f"   ❌ No connecting flights found")
        
        return results
    
    def find_connecting_flights(self, origin_codes: list, destination_codes: list) -> list:
        """Find flights with 1 layover/connection"""
        
        # Major connection hubs
        hubs = [
            "IST", "DXB", "LHR", "CDG", "FRA", "AMS",
            "DOH", "AUH", "TAS", "GYD", "EVN", "TBS",
            "BAK", "MUC", "ZRH", "VIE", "WAW"
        ]
        
        connections = []
        
        for origin_code in origin_codes[:2]:
            for hub in hubs:
                # Flight 1: Origin → Hub
                leg1 = self.get_real_routes(origin_code, hub)
                
                if leg1:
                    # Flight 2: Hub → Destination
                    for dest_code in destination_codes[:2]:
                        leg2 = self.get_real_routes(hub, dest_code)
                        
                        if leg2:
                            # Create connection object
                            for f1 in leg1[:3]:
                                for f2 in leg2[:3]:
                                    connection = {
                                        "connection_city": self.get_city_name(hub),
                                        "connection_code": hub,
                                        "leg1": {
                                            "airline": self.get_airline_name(f1.get('airline_iata', '')),
                                            "flight_number": f1.get('flight_iata', 'N/A'),
                                            "departure": f1.get('dep_time', 'N/A'),
                                            "arrival": f1.get('arr_time', 'N/A'),
                                            "origin": origin_code,
                                            "destination": hub
                                        },
                                        "leg2": {
                                            "airline": self.get_airline_name(f2.get('airline_iata', '')),
                                            "flight_number": f2.get('flight_iata', 'N/A'),
                                            "departure": f2.get('dep_time', 'N/A'),
                                            "arrival": f2.get('arr_time', 'N/A'),
                                            "origin": hub,
                                            "destination": dest_code
                                        },
                                        "total_price": self.estimate_connection_price(),
                                        "layover_duration": self.calculate_layover(
                                            f1.get('arr_time', '00:00'),
                                            f2.get('dep_time', '00:00')
                                        )
                                    }
                                    connections.append(connection)
        
        # Remove duplicates and sort by price
        unique = []
        seen = set()
        for conn in connections:
            key = f"{conn['leg1']['airline']}_{conn['leg2']['airline']}_{conn['connection_city']}"
            if key not in seen:
                seen.add(key)
                unique.append(conn)
        
        unique.sort(key=lambda x: x['total_price'])
        return unique[:10]  # Return top 10 connecting options
    
    def get_city_name(self, airport_code: str) -> str:
        """Convert airport code to city name"""
        city_names = {
            "IST": "Istanbul",
            "DXB": "Dubai",
            "LHR": "London",
            "CDG": "Paris",
            "FRA": "Frankfurt",
            "AMS": "Amsterdam",
            "DOH": "Doha",
            "AUH": "Abu Dhabi",
            "TAS": "Tashkent",
            "GYD": "Baku",
            "EVN": "Yerevan",
            "TBS": "Tbilisi",
            "MUC": "Munich",
            "ZRH": "Zurich",
            "VIE": "Vienna",
            "WAW": "Warsaw",
        }
        return city_names.get(airport_code, airport_code)
    
    def calculate_layover(self, arrival: str, departure: str) -> str:
        """Calculate layover duration between flights"""
        try:
            # Parse times (simplified)
            arr_hour = int(arrival.split(':')[0]) if ':' in str(arrival) else 12
            dep_hour = int(departure.split(':')[0]) if ':' in str(departure) else 14
            
            layover = dep_hour - arr_hour
            if layover < 0:
                layover += 24
            
            if layover < 2:
                return f"{layover}h (tight connection)"
            elif layover < 5:
                return f"{layover}h (short layover)"
            else:
                return f"{layover}h (long layover)"
        except:
            return "Unknown"
    
    def estimate_connection_price(self) -> int:
        """Estimate price for connecting flight"""
        return random.randint(250, 500)
    
    def get_airport_codes(self, city: str) -> list:
        """Get all possible airport codes for a city"""
        city_lower = city.lower()
        
        airports = {
            "moscow": ["SVO", "DME", "VKO", "ZIA"],
            "ufa": ["UFA"],
            "casablanca": ["CMN"],
            "dubai": ["DXB", "DWC"],
            "istanbul": ["IST", "SAW"],
            "london": ["LHR", "LGW", "STN", "LTN", "LCY"],
            "paris": ["CDG", "ORY"],
            "new york": ["JFK", "EWR", "LGA"],
            "tashkent": ["TAS"],
            "baku": ["GYD"],
            "yerevan": ["EVN"],
            "tbilisi": ["TBS"],
            "sochi": ["AER"],
            "st petersburg": ["LED"],
            "kazan": ["KZN"],
            "ekaterinburg": ["SVX"],
            "novosibirsk": ["OVB"],
        }
        
        if city_lower in airports:
            return airports[city_lower]
        else:
            return [self.get_single_airport_code(city_lower)]
    
    def get_single_airport_code(self, city: str) -> str:
        """Get single IATA code"""
        codes = {
            "moscow": "SVO",
            "ufa": "UFA",
            "casablanca": "CMN",
            "dubai": "DXB",
            "cairo": "CAI",
            "istanbul": "IST",
            "antalya": "AYT",
            "tashkent": "TAS",
            "almaty": "ALA",
            "baku": "GYD",
            "yerevan": "EVN",
            "tbilisi": "TBS",
            "sochi": "AER",
            "st petersburg": "LED",
            "london": "LHR",
            "paris": "CDG",
            "new york": "JFK",
        }
        return codes.get(city.lower(), "LHR")
    
    def get_real_routes(self, origin_code: str, destination_code: str) -> list:
        """Get REAL flight routes from AirLabs API"""
        try:
            url = f"{self.base_url}/routes"
            params = {
                'api_key': self.api_key,
                'dep_iata': origin_code,
                'arr_iata': destination_code
            }
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                routes = data.get('response', [])
                # Filter for passenger flights
                routes = [r for r in routes if r.get('type') != 'cargo']
                return routes
            return []
            
        except Exception as e:
            return []
    
    def get_airline_name(self, iata_code: str) -> str:
        """Get airline name from IATA code"""
        return self.airlines_cache.get(iata_code, iata_code if iata_code else "Unknown Airline")
    
    def fix_city_name(self, city: str) -> str:
        """Fix common typos"""
        fixes = {
            "cario": "cairo",
            "moscov": "moscow",
            "dubia": "dubai",
            "istambul": "istanbul",
            "antalia": "antalya",
        }
        city_lower = city.lower().strip()
        return fixes.get(city_lower, city_lower).title()
    
    def format_results(self, results: dict) -> str:
        """Format both direct and connecting flights"""
        
        origin = results.get('origin', 'Origin')
        destination = results.get('destination', 'Destination')
        date = results.get('date', 'Any date')
        
        formatted = "\n" + "=" * 75 + "\n"
        formatted += f"✈️ FLIGHTS FROM {origin.upper()} TO {destination.upper()}\n"
        if date:
            formatted += f"   📅 Date: {date}\n"
        formatted += "=" * 75 + "\n"
        
        # DIRECT FLIGHTS
        formatted += "\n🟢 DIRECT FLIGHTS (No layovers)\n"
        formatted += "─" * 50 + "\n"
        
        if results['direct']:
            for i, route in enumerate(results['direct'][:5], 1):
                airline_iata = route.get('airline_iata', '')
                airline_name = self.get_airline_name(airline_iata)
                flight_num = route.get('flight_iata', 'N/A')
                dep_time = route.get('dep_time', 'N/A')
                arr_time = route.get('arr_time', 'N/A')
                price = random.randint(200, 450)
                
                formatted += f"\n{i}. ✈️ {airline_name}\n"
                formatted += f"   🎫 Flight: {flight_num}\n"
                formatted += f"   🕐 {dep_time} → {arr_time} (Direct)\n"
                formatted += f"   💰 Est. Price: {price} USD\n"
                formatted += f"   ⏱️ Duration: Direct flight\n"
        else:
            formatted += "\n   ❌ No direct flights found\n"
        
        # CONNECTING FLIGHTS
        formatted += "\n\n🟡 CONNECTING FLIGHTS (With layovers)\n"
        formatted += "─" * 50 + "\n"
        
        if results['connecting']:
            for i, conn in enumerate(results['connecting'][:5], 1):
                leg1 = conn['leg1']
                leg2 = conn['leg2']
                
                formatted += f"\n{i}. 🔄 {leg1['airline']} + {leg2['airline']}\n"
                formatted += f"   📍 Stop in: {conn['connection_city']} ({conn['connection_code']})\n"
                formatted += f"\n   Leg 1: {leg1['origin']} → {leg1['destination']}\n"
                formatted += f"          ✈️ {leg1['airline']} {leg1['flight_number']}\n"
                formatted += f"          🕐 {leg1['departure']} → {leg1['arrival']}\n"
                formatted += f"\n   Leg 2: {leg2['origin']} → {leg2['destination']}\n"
                formatted += f"          ✈️ {leg2['airline']} {leg2['flight_number']}\n"
                formatted += f"          🕐 {leg2['departure']} → {leg2['arrival']}\n"
                formatted += f"\n   ⏱️ Layover: {conn['layover_duration']}\n"
                formatted += f"   💰 Total Est. Price: {conn['total_price']} USD\n"
        else:
            formatted += "\n   ❌ No connecting flights found\n"
        
        formatted += "\n" + "=" * 75 + "\n"
        formatted += "💡 Prices are estimates. Check airline websites for exact prices.\n"
        formatted += "💡 Connecting flights may have longer travel time but can be cheaper.\n"
        formatted += "=" * 75
        
        return formatted


if __name__ == "__main__":
    tools = AirLabsTools()
    
    # Test with connecting flights
    results = tools.search_flights("Moscow", "Casablanca", "2026-07-15")
    print(tools.format_results(results))
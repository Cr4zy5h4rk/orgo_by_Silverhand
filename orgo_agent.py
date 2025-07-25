import os
import json
import time
import requests
from orgo import Computer
from datetime import datetime
from dotenv import load_dotenv

class SolarCalcOrgo:
    def __init__(self, project_id, orgo_api_key, claude_api_key):
        self.computer = Computer(
            project_id=project_id,
            api_key=orgo_api_key
        )
        self.claude_api_key = claude_api_key
        self.results_folder = "solar_reports"
        self.electricity_costs = self.load_electricity_costs()
        self.create_results_folder()
    
    def create_results_folder(self):
        """Create folder to save reports"""
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
    
    def load_electricity_costs(self):
        """Load electricity costs database"""
        try:
            with open('./database/cost-of-electricity-by-country-2025.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"✅ Loaded electricity costs for {len(data)} countries")
                return data
        except FileNotFoundError:
            print("⚠️ Electricity costs database not found.")
            return []
        except Exception as e:
            print(f"❌ Error loading electricity costs: {e}")
            return []
    
    def get_country_from_coordinates(self, lat, lon):
        """Get country from coordinates using reverse geocoding"""
        try:
            # Using OpenStreetMap Nominatim for reverse geocoding (free)
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 3  # Country level
            }
            headers = {'User-Agent': 'SolarCalc-Orgo/1.0'}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                country = data.get('address', {}).get('country', '')
                print(f"🌍 Country detected from coordinates ({lat}, {lon}): {country}")
                return country
            else:
                print(f"⚠️ Geocoding API error: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ Error in reverse geocoding: {e}")
            return None
    
    def get_electricity_cost(self, country_name):
        """Get electricity cost for a specific country"""
        if not self.electricity_costs:
            return None
        
        # Search for the country in the database
        for entry in self.electricity_costs:
            if entry['country'].lower() == country_name.lower():
                # Use the most recent cost (2024 March if available, otherwise 2022 Sept)
                cost_2024 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2024March')
                cost_2022 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2022Sept')
                
                cost = cost_2024 if cost_2024 is not None else cost_2022
                if cost is not None:
                    print(f"💰 Electricity cost for {country_name}: ${cost:.3f}/kWh")
                    return cost
        
        # If country not found, try partial matching
        country_lower = country_name.lower()
        for entry in self.electricity_costs:
            if country_lower in entry['country'].lower() or entry['country'].lower() in country_lower:
                cost_2024 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2024March')
                cost_2022 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2022Sept')
                
                cost = cost_2024 if cost_2024 is not None else cost_2022
                if cost is not None:
                    print(f"💰 Electricity cost for {entry['country']} (matched with {country_name}): ${cost:.3f}/kWh")
                    return cost
        
        print(f"⚠️ No electricity cost found for {country_name}")
        return None
    
    def calculate_solar_potential(self, address, save_report=True):
        """
        Calculate solar potential for a given address and get electricity costs
        Args:
            address (str): Building address
            save_report (bool): Save the report
        """
        print(f"🌞 Solar analysis for: {address}")
        
        # Enhanced instructions to extract coordinates and solar data
        instruction = f"""
You are a Solar Energy Data Extraction Specialist. Your role is to navigate the PVGIS website, configure solar calculations, and extract precise data with coordinates.

TASK: Extract solar potential data for "{address}" using PVGIS calculator

REASONING APPROACH: Think step by step, observe results after each action, and adapt if needed.

STEP-BY-STEP PROCESS:
1. NAVIGATE TO PVGIS
   - Open Firefox browser
   - Go to https://re.jrc.ec.europa.eu/pvg_tools/en/
   - Wait for page to fully load (look for address input field)

2. LOCATE ADDRESS
   - Type "{address}" in the Address field
   - Click "Go!" button
   - Observe: Wait for map to center on location (zoom animation will occur)
   - Verify: Check that the map shows the correct location

3. EXTRACT COORDINATES
   - Look at the right panel for "Selected:" coordinates
   - Record the exact latitude and longitude values shown
   - Reasoning: These coordinates are crucial for country identification

4. CONFIGURE SOLAR SYSTEM
   - In the orange "PERFORMANCE OF GRID-CONNECTED PV" panel:
     * PV technology: Verify "Crystalline silicon" is selected
     * Installed peak PV power: Change from 1 to 5 kWp
     * System loss: Keep default 14%
     * Mounting position: Keep "Free-standing"
     * Slope: Keep default 35°
     * Azimuth: Keep default 0°
   - Reasoning: 5kWp represents a typical residential system size

5. GENERATE RESULTS
   - Click "Visualize results" (blue button)
   - Observe: Wait for results page with orange background to load
   - Verify: Look for "Simulation outputs:" section

6. EXTRACT SOLAR DATA
   - Find these exact values in "Simulation outputs:":
     * "Yearly PV energy production [kWh]:" → Record the number
     * "Yearly in-plane irradiation [kWh/m²]:" → Record the number
   - Reasoning: These are the key metrics for solar potential assessment

EXAMPLE OF SUCCESSFUL EXTRACTION:
For "Eiffel Tower, Paris":
- Navigate to PVGIS → Success
- Enter address → Map centers on Paris
- Coordinates shown: 48.8584, 2.2945
- Configure 5kWp system → Settings applied
- Generate results → Page loads with data
- Extract: Production = 4,847 kWh, Irradiation = 1,367 kWh/m²

CRITICAL SUCCESS FACTORS:
- Always wait for pages/maps to fully load before proceeding
- Double-check coordinate extraction from "Selected:" field
- Ensure 5kWp is properly set before generating results
- Look specifically for the "Simulation outputs:" section

IF PROBLEMS OCCUR:
- Page won't load → Wait longer, then refresh if needed
- Address not found → Try broader location (city, country)
- Results don't appear → Check if all settings are configured correctly

MANDATORY OUTPUT FORMAT:
End your response with exactly this format:

"EXTRACTED DATA:
Coordinates: [exact latitude], [exact longitude]
Production: [exact value] kWh
Irradiation: [exact value] kWh/m²"

Replace bracketed values with the exact numbers from the PVGIS interface.
"""
        
        try:
            print("🤖 Launching Orgo agent...")
            messages = self.computer.prompt(
                instruction=instruction,
                model="claude-sonnet-4-20250514",
                api_key=self.claude_api_key,
                max_iterations=20,
                max_tokens=1024
            )
            
            # Extract solar data and coordinates
            result = self.extract_solar_and_geo_data(messages)
            
            # Get country and electricity cost if coordinates were found
            if result and result.get('latitude') and result.get('longitude'):
                country = self.get_country_from_coordinates(
                    result['latitude'], 
                    result['longitude']
                )
                if country:
                    result['country'] = country
                    result['electricity_cost_usd_kwh'] = self.get_electricity_cost(country)
                else:
                    result['country'] = None
                    result['electricity_cost_usd_kwh'] = None
            else:
                result['country'] = None
                result['electricity_cost_usd_kwh'] = None
            
            # Save results
            if save_report:
                self.save_results(address, messages, result)
            
            return result
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def extract_solar_and_geo_data(self, messages):
        """Extract solar data and coordinates from messages - ONLY real data, no defaults"""
        import re
        
        solar_data = {
            "timestamp": datetime.now().isoformat(),
            "latitude": None,
            "longitude": None,
            "annual_production_kwh": None,
            "irradiation_kwh_m2": None,
            "country": None,
            "electricity_cost_usd_kwh": None,
            "status": "extraction_attempted"
        }
        
        # Convert messages to string for analysis
        messages_text = str(messages).lower()
        
        print("🔍 Analyzing results...")
        print(f"📝 Complete messages:")
        print("=" * 60)
        print(str(messages)[:1500])
        print("=" * 60)
        
        # First search for the specifically requested format
        formatted_match = re.search(
            r'extracted\s+data:.*?coordinates:\s*([0-9.-]+),\s*([0-9.-]+).*?production:\s*([0-9]+\.?[0-9]*)\s*kwh.*?irradiation:\s*([0-9]+\.?[0-9]*)\s*kwh/m²', 
            messages_text, 
            re.DOTALL
        )
        
        if formatted_match:
            try:
                lat = float(formatted_match.group(1))
                lon = float(formatted_match.group(2))
                prod_value = float(formatted_match.group(3))
                irrad_value = float(formatted_match.group(4))
                
                # Validate coordinates (basic range check)
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    solar_data['latitude'] = lat
                    solar_data['longitude'] = lon
                    print(f"✅ Coordinates extracted: {lat}, {lon}")
                
                # Validate production (for 5kWp system: reasonable range)
                if prod_value > 0:
                    solar_data['annual_production_kwh'] = prod_value
                    print(f"✅ Production extracted: {prod_value} kWh/year (5kWp)")
                
                # Validate irradiation (positive value)
                if irrad_value > 0:
                    solar_data['irradiation_kwh_m2'] = irrad_value
                    print(f"✅ Irradiation extracted: {irrad_value} kWh/m²/year")
                
                if all([solar_data['latitude'], solar_data['longitude'], 
                       solar_data['annual_production_kwh'], solar_data['irradiation_kwh_m2']]):
                    solar_data['status'] = "completed"
                    return solar_data
                    
            except (ValueError, IndexError) as e:
                print(f"⚠️ Error parsing formatted data: {e}")
        
        # Fallback: search for coordinates separately
        coord_patterns = [
            r'selected:\s*([0-9.-]+),\s*([0-9.-]+)',
            r'coordinates:\s*([0-9.-]+),\s*([0-9.-]+)',
            r'lat:\s*([0-9.-]+).*?lon:\s*([0-9.-]+)',
            r'([0-9]{1,2}\.[0-9]+),\s*([0-9.-]+\.[0-9]+)'
        ]
        
        for pattern in coord_patterns:
            matches = re.findall(pattern, messages_text)
            for match in matches:
                try:
                    lat, lon = float(match[0]), float(match[1])
                    if -90 <= lat <= 90 and -180 <= lon <= 180:
                        solar_data['latitude'] = lat
                        solar_data['longitude'] = lon
                        print(f"✅ Coordinates found: {lat}, {lon}")
                        break
                except ValueError:
                    continue
            if solar_data['latitude']:
                break
        
        # Search for production values (only realistic values)
        production_patterns = [
            r'yearly\s+pv\s+energy\s+production\s*\[kwh\]:\s*([0-9]+\.?[0-9]*)',
            r'production\s*\[kwh\]:\s*([0-9]+\.?[0-9]*)',
            r'energy\s+production\s*:\s*([0-9]+\.?[0-9]*)',
            r'production:\s*([0-9]+\.?[0-9]*)',
            r'([0-9]+\.?[0-9]*)\s*kwh(?:/year|/an)?'
        ]
        
        for pattern in production_patterns:
            matches = re.findall(pattern, messages_text)
            for match in matches:
                try:
                    value = float(match)
                    # Only accept positive values
                    if value > 0:
                        solar_data['annual_production_kwh'] = value
                        print(f"✅ Production found: {value} kWh/year (5kWp)")
                        break
                except ValueError:
                    continue
            if solar_data['annual_production_kwh']:
                break
        
        # Search for irradiation
        irradiation_patterns = [
            r'yearly\s+in-plane\s+irradiation\s*\[kwh/m²\]:\s*([0-9]+\.?[0-9]*)',
            r'irradiation\s*\[kwh/m²\]:\s*([0-9]+\.?[0-9]*)',
            r'in-plane\s+irradiation\s*:\s*([0-9]+\.?[0-9]*)',
            r'([0-9]+\.?[0-9]*)\s*kwh/m²',
            r'irradiation:\s*([0-9]+\.?[0-9]*)'
        ]
        
        for pattern in irradiation_patterns:
            matches = re.findall(pattern, messages_text)
            for match in matches:
                try:
                    value = float(match)
                    # Only accept positive values
                    if value > 0:
                        solar_data['irradiation_kwh_m2'] = value
                        print(f"✅ Irradiation found: {value} kWh/m²/year")
                        break
                except ValueError:
                    continue
            if solar_data['irradiation_kwh_m2']:
                break
        
        # Set status based on what was found
        found_items = sum([
            1 if solar_data['latitude'] else 0,
            1 if solar_data['longitude'] else 0,
            1 if solar_data['annual_production_kwh'] else 0,
            1 if solar_data['irradiation_kwh_m2'] else 0
        ])
        
        if found_items == 4:
            solar_data['status'] = "completed"
        elif found_items > 0:
            solar_data['status'] = "partial"
        else:
            solar_data['status'] = "failed"
            print("❌ No valid data could be extracted from agent response")
        
        return solar_data
    
    def save_results(self, address, messages, extracted_data):
        """Save results to a JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_folder}/solar_calc_{timestamp}.json"
        
        data = {
            "address": address,
            "timestamp": timestamp,
            "extracted_data": extracted_data,
            "messages": str(messages)[:2000],  # Limit size
            "status": extracted_data.get('status', 'unknown')
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Report saved: {filename}")
    
    def batch_calculate(self, addresses_list):
        """Calculate for multiple addresses (with pause to save API costs)"""
        results = []
        
        for i, address in enumerate(addresses_list):
            print(f"\n📍 Calculation {i+1}/{len(addresses_list)}")
            result = self.calculate_solar_potential(address)
            results.append({"address": address, "data": result})
            
            # Pause between calculations to avoid overload
            if i < len(addresses_list) - 1:
                print("⏸️ 30s pause to save API costs...")
                time.sleep(30)
        
        return results
    
    def debug_last_results(self):
        """Display content of the last results file for debugging"""
        import glob
        
        files = glob.glob(f"{self.results_folder}/solar_calc_*.json")
        if not files:
            print("❌ No results files found")
            return
        
        latest_file = max(files, key=os.path.getctime)
        print(f"🔍 Debugging file: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📍 Address: {data.get('address', 'N/A')}")
            print(f"📅 Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"🌍 Extracted data: {data.get('extracted_data', {})}")
            print(f"📝 Messages (excerpt):")
            print("-" * 50)
            print(data.get('messages', 'N/A')[:800])
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Error reading file: {e}")
    
    def generate_enhanced_report(self, address, solar_data):
        """Generate an enhanced report - only with real data"""
        if not solar_data:
            return f"❌ Unable to calculate solar potential for {address}"
        
        if solar_data.get('status') == 'failed':
            return f"❌ No data could be extracted for {address}"
        
        production = solar_data.get('annual_production_kwh')
        irradiation = solar_data.get('irradiation_kwh_m2')
        country = solar_data.get('country')
        electricity_cost = solar_data.get('electricity_cost_usd_kwh')
        coordinates = f"{solar_data.get('latitude', 'N/A')}, {solar_data.get('longitude', 'N/A')}"
        
        report = f"""
🌞 SOLAR REPORT - {address}
{'='*60}
📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}
📊 Status: {solar_data.get('status', 'Unknown')}

🌍 LOCATION DATA:
• Coordinates: {coordinates}
• Country: {country if country else 'Not found'}
• Electricity cost: ${electricity_cost:.3f}/kWh" if electricity_cost else "Not available"

📊 SOLAR POTENTIAL:
• Annual production: {f"{production:,} kWh/year" if production else "Not extracted"}
• Solar irradiation: {f"{irradiation:,} kWh/m²/year" if irradiation else "Not extracted"}

🔧 SYSTEM CONFIGURATION:
• Capacity: 5 kWp
• Technology: Crystalline silicon
• Mounting: Free-standing, 35° slope, South-facing
        """
        
        # Only add economic analysis if we have both production and electricity cost
        if production and electricity_cost:
            savings_per_year_usd = int(production * electricity_cost)
            co2_avoided = int(production * 0.4)  # 0.4kg CO2/kWh
            system_cost_usd = 5000 * 3  # 5kWp × $3/Watt = $15,000
            payback_years = int(system_cost_usd / savings_per_year_usd) if savings_per_year_usd > 0 else 'N/A'
            
            report += f"""
💰 ECONOMIC ANALYSIS:
• Annual savings: ${savings_per_year_usd:,}/year
• System cost estimate: ${system_cost_usd:,}
• Payback period: {payback_years} years
• 25-year savings: ${savings_per_year_usd * 25:,}

🌱 ENVIRONMENTAL IMPACT:
• CO2 avoided: {co2_avoided:,} kg/year
• 25-year CO2 reduction: {co2_avoided * 25:,} kg
            """
        else:
            missing_data = []
            if not production:
                missing_data.append("production data")
            if not electricity_cost:
                missing_data.append("electricity cost")
            
            report += f"""
💰 ECONOMIC ANALYSIS:
• Cannot calculate: Missing {', '.join(missing_data)}
            """
        
        return report

# MAIN USAGE
def main():
    # Load environment variables
    load_dotenv()
    
    # Configuration
    PROJECT_ID = os.getenv("PROJECT_ID")
    ORGO_API_KEY = os.getenv("ORGO_API_KEY") 
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    
    # Initialize agent
    solar_agent = SolarCalcOrgo(
        project_id=PROJECT_ID,
        orgo_api_key=ORGO_API_KEY,
        claude_api_key=CLAUDE_API_KEY
    )
    
    print("🌞 SolarCalc Orgo - Only Real Data Extraction")
    print("=" * 80)
    
    # Test with multiple addresses
    test_addresses = [
        "San francisco, Larkin Street",
        # "Eiffel Tower, Paris, France",
        # "Times Square, New York, USA"
    ]
    
    for i, test_address in enumerate(test_addresses):
        print(f"\n🏠 Testing {i+1}/{len(test_addresses)}: {test_address}")
        solar_data = solar_agent.calculate_solar_potential(test_address)
        
        # Generate and display report
        report = solar_agent.generate_enhanced_report(test_address, solar_data)
        print(report)
        
        # Add delay between tests
        if i < len(test_addresses) - 1:
            print("\n⏸️ Waiting 30 seconds before next calculation...")
            time.sleep(30)
    
    # Debug: see what the agent actually retrieved
    print("\n🔍 DEBUG - Last calculation details:")
    solar_agent.debug_last_results()

if __name__ == "__main__":
    main()
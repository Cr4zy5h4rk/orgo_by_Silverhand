import os
import json
import time
import requests
import subprocess
import sys
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
            url = f"https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 3
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
        
        for entry in self.electricity_costs:
            if entry['country'].lower() == country_name.lower():
                cost_2024 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2024March')
                cost_2022 = entry.get('CostOfElectricity_ElectricityCost_USDPerkWh_2022Sept')
                
                cost = cost_2024 if cost_2024 is not None else cost_2022
                if cost is not None:
                    print(f"💰 Electricity cost for {country_name}: ${cost:.3f}/kWh")
                    return cost
        
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
        """Calculate solar potential for a given address and get electricity costs"""
        print(f"🌞 Solar analysis for: {address}")
        
        instruction = f"""
        You are a Solar Energy Data Extraction Specialist. Your role is to navigate the PVGIS website, configure solar calculations, extract precise data with coordinates, and then share results on social media.

        TASK: Extract solar potential data for "{address}" using PVGIS calculator, then post on Twitter and redirect to solar store

        REASONING APPROACH: Think step by step, observe results after each action, and adapt if needed.

        STEP-BY-STEP PROCESS:
        1. NAVIGATE TO PVGIS
        - Open Firefox browser
        - Go to https://re.jrc.ec.europa.eu/pvg_tools/en/
        - Wait 5 sec for page to fully load (look for address input field)

        2. LOCATE ADDRESS
        - Type "{address}" in the Address field
        - Click "Go!" button

        3. EXTRACT COORDINATES
        - Look at the right section for "Selected:" coordinates
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

        6. EXTRACT SOLAR DATA - CRITICAL STEP
        **IMPORTANT: You must locate the "Simulation outputs:" section in the left panel of the results page.**

        This section appears as a blue-headed table with specific rows. Look for these EXACT labels:

        **For Production Value:**
        - Find the row labeled EXACTLY: "Yearly PV energy production [kWh]:"
        - This will be followed by a numerical value 
        - DO NOT confuse with "Monthly energy output" or any other production metric
        - The value represents annual electricity generation in kWh for the configured system

        **For Irradiation Value:**
        - Find the row labeled EXACTLY: "Yearly in-plane irradiation [kWh/m²]:"
        - This will be followed by a numerical value
        - DO NOT confuse with "Global horizontal irradiation" or other irradiation metrics
        - This represents the solar energy hitting the tilted PV panels per square meter per year

        **Visual Reference:** 
        - The "Simulation outputs:" section is located in the left panel
        - It has a blue header and contains multiple rows of data
        - These values are typically displayed as decimal numbers

        **Extraction Strategy:**
        1. Scroll through the "Simulation outputs:" section carefully
        2. Read each row label completely before recording values
        3. Copy the exact numerical value (including decimals)
        4. Double-check you have the correct labels before proceeding

        **Common Mistakes to Avoid:**
        - Don't take values from the monthly chart
        - Don't use "Global horizontal irradiation" instead of "in-plane irradiation"
        - Don't use summary values from other sections
        - Don't round the numbers - use exact values shown

        7. REDIRECT TO SOLAR STORE - FINAL STEP
        - Open another new tab (Ctrl+T)
        - Navigate to: https://a1solarstore.com/
        - Wait for the page to fully load
        - Reasoning: Direct the user to a solar equipment store where they can take action on their solar potential
        
        8. POST ON TWITTER - NEW STEP
        - Open Twitter in a new tab (Ctrl+T then go to https://twitter.com)
        - Wait for Twitter to fully load
        - Click on "Post" or "What's happening?" field
        - Type exactly this tweet:

        "🌞 Just discovered my rooftop could produce [PRODUCTION_VALUE] kWh/year of solar energy! That's enough to power my home and save $900/year on electricity ⚡
        Calculated instantly with my agent on @OrgoAI using real solar data ☀️
        #SolarScope #AI #ClimateTech #CleanEnergy #OrgoHackathon"

        - Replace [PRODUCTION_VALUE] with the exact production value from step 6 (rounded to nearest 100)
        - Click "Post" button
        - Observe: Wait for tweet to be published successfully
        - Reasoning: Showcases the practical value and promotes the OrgoAI platform

        MANDATORY OUTPUT FORMAT:
        End your response with exactly this format:

        "EXTRACTED DATA:
        Coordinates: [exact latitude], [exact longitude]
        Production: [exact value] kWh
        Irradiation: [exact value] kWh/m²

        SOCIAL MEDIA: Tweet posted successfully on Twitter
        NEXT STEP: User redirected to A1 Solar Store for solar equipment options"

        Replace bracketed values with the exact numbers from the PVGIS interface.

        VERIFICATION CHECKLIST:
        - [ ] Coordinates are from the "Selected:" field
        - [ ] Production value is from "Yearly PV energy production [kWh]:" row
        - [ ] Irradiation value is from "Yearly in-plane irradiation [kWh/m²]:" row
        - [ ] All values are exact numbers from the interface (with decimals)
        - [ ] Twitter tab opened and tweet posted
        - [ ] A1 Solar Store tab opened for user
        """
        
        try:
            print("🤖 Launching Orgo agent...")
            messages = self.computer.prompt(
                instruction=instruction,
                model="claude-sonnet-4-20250514",
                api_key=self.claude_api_key,
                max_iterations=35,
                max_tokens=4096
            )
            
            result = self.extract_solar_and_geo_data(messages)
            
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
                
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    solar_data['latitude'] = lat
                    solar_data['longitude'] = lon
                    print(f"✅ Coordinates extracted: {lat}, {lon}")
                
                if prod_value > 0:
                    solar_data['annual_production_kwh'] = prod_value
                    print(f"✅ Production extracted: {prod_value} kWh/year (5kWp)")
                
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
            "messages": str(messages)[:2000],
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
• Electricity cost: {f'${electricity_cost:.3f}/kWh' if electricity_cost else 'Not available'}

📊 SOLAR POTENTIAL:
• Annual production: {f"{production:,} kWh/year" if production else "Not extracted"}
• Solar irradiation: {f"{irradiation:,} kWh/m²/year" if irradiation else "Not extracted"}

🔧 SYSTEM CONFIGURATION:
• Capacity: 5 kWp
• Technology: Crystalline silicon
• Mounting: Free-standing, 35° slope, South-facing
        """
        
        if production and electricity_cost:
            savings_per_year_usd = int(production * electricity_cost)
            co2_avoided = int(production * 0.4)
            system_cost_usd = 5000 * 3
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
    
    def launch_streamlit_dashboard(self):
        """Launch the Streamlit dashboard automatically"""
        print("\n🚀 Launching Streamlit Dashboard...")
        
        # Create the dashboard script if it doesn't exist
        dashboard_script = "solar_dashboard.py"
        
        try:
            # Launch Streamlit in a separate process
            print("🌐 Opening dashboard in browser...")
            
            # Check if streamlit is installed
            try:
                import streamlit
                print("✅ Streamlit is available")
            except ImportError:
                print("❌ Streamlit not installed. Installing...")
                subprocess.check_call([sys.executable, "-m", "pip", "install", "streamlit", "folium", "streamlit-folium", "plotly"])
                print("✅ Streamlit installed successfully")
            
            # Launch the dashboard
            subprocess.Popen([
                sys.executable, "-m", "streamlit", "run", dashboard_script,
                "--server.headless", "false",
                "--server.port", "8501",
                "--browser.gatherUsageStats", "false"
            ])
            
            print("🎉 Dashboard launched successfully!")
            print("🌐 Access your dashboard at: http://localhost:8501")
            print("📱 The dashboard will open automatically in your browser")
            
        except Exception as e:
            print(f"❌ Error launching dashboard: {e}")
            print(f"💡 You can manually run: streamlit run {dashboard_script}")

# MAIN USAGE
def get_user_addresses():
    """
    Get addresses from user input with interactive menu
    """
    addresses = []
    
    print("\n🏠 ADDRESS INPUT")
    print("=" * 50)
    print("Enter addresses for solar potential analysis.")
    print("You can add multiple addresses or just one.")
    print("Type 'done' when finished, or 'quit' to exit.\n")
    
    while True:
        try:
            # Show current addresses
            if addresses:
                print(f"\n📍 Current addresses ({len(addresses)}):")
                for i, addr in enumerate(addresses, 1):
                    print(f"   {i}. {addr}")
            
            # Get user input
            user_input = input(f"\n🔍 Enter address #{len(addresses) + 1} (or 'done'/'quit'): ").strip()
            
            # Handle special commands
            if user_input.lower() in ['done', 'd']:
                if addresses:
                    break
                else:
                    print("⚠️  Please enter at least one address before finishing.")
                    continue
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                return None
            
            # Validate address input
            if not user_input:
                print("⚠️  Please enter a valid address.")
                continue
            
            if len(user_input) < 3:
                print("⚠️  Address seems too short. Please enter a more complete address.")
                continue
            
            # Add address to list
            addresses.append(user_input)
            print(f"✅ Added: {user_input}")
            
            # Ask if user wants to continue
            if len(addresses) >= 1:
                continue_input = input("➕ Add another address? (y/n): ").lower()
                if continue_input in ['n', 'no']:
                    break
        
        except KeyboardInterrupt:
            print("\n\n👋 Process interrupted by user.")
            return None
        except Exception as e:
            print(f"❌ Error: {e}")
            continue
    
    return addresses

def confirm_addresses(addresses):
    """
    Show final confirmation of addresses
    """
    print("\n📋 CONFIRMATION")
    print("=" * 50)
    print("You have entered the following addresses:")
    
    for i, addr in enumerate(addresses, 1):
        print(f"   {i}. {addr}")
    
    while True:
        confirm = input(f"\n✅ Proceed with analysis of {len(addresses)} address(es)? (y/n): ").lower()
        
        if confirm in ['y', 'yes']:
            return True
        elif confirm in ['n', 'no']:
            return False
        else:
            print("⚠️  Please enter 'y' for yes or 'n' for no.")

def display_progress_bar(current, total, address):
    """
    Display a simple progress bar
    """
    progress = int(50 * current / total)
    bar = "█" * progress + "-" * (50 - progress)
    percent = int(100 * current / total)
    
    print(f"\n🌞 Progress: [{bar}] {percent}% ({current}/{total})")
    print(f"📍 Current: {address}")

def main():
    load_dotenv()
    
    PROJECT_ID = os.getenv("PROJECT_ID")
    ORGO_API_KEY = os.getenv("ORGO_API_KEY") 
    CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
    
    # Check for required environment variables
    missing_vars = []
    if not PROJECT_ID:
        missing_vars.append("PROJECT_ID")
    if not ORGO_API_KEY:
        missing_vars.append("ORGO_API_KEY")
    if not CLAUDE_API_KEY:
        missing_vars.append("CLAUDE_API_KEY")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print("\n💡 Please set these variables in your .env file")
        return
    
    # Initialize solar agent
    try:
        solar_agent = SolarCalcOrgo(
            project_id=PROJECT_ID,
            orgo_api_key=ORGO_API_KEY,
            claude_api_key=CLAUDE_API_KEY
        )
    except Exception as e:
        print(f"❌ Failed to initialize SolarCalcOrgo: {e}")
        return
    
    print("🌞 SolarCalc Orgo - Interactive Solar Analysis")
    print("=" * 80)
    print("Welcome to the interactive solar potential calculator!")
    print("This tool will analyze solar potential for addresses you provide.")
    
    # Get addresses from user
    addresses = get_user_addresses()
    
    if not addresses:
        print("🚫 No addresses provided. Exiting...")
        return
    
    # Confirm addresses
    if not confirm_addresses(addresses):
        print("🚫 Analysis cancelled by user.")
        return
    
    print(f"\n🚀 Starting analysis of {len(addresses)} address(es)...")
    print("=" * 80)
    
    # Execute solar calculations
    successful_calculations = 0
    failed_calculations = 0
    
    for i, address in enumerate(addresses):
        try:
            display_progress_bar(i, len(addresses), address)
            
            print(f"\n🔍 Analyzing: {address}")
            print("-" * 60)
            
            # Calculate solar potential
            solar_data = solar_agent.calculate_solar_potential(address)
            
            if solar_data:
                # Generate and display report
                report = solar_agent.generate_enhanced_report(address, solar_data)
                print(report)
                successful_calculations += 1
                print(f"✅ Analysis completed for: {address}")
            else:
                print(f"❌ Failed to get solar data for: {address}")
                failed_calculations += 1
            
            # Wait between calculations
            if i < len(addresses) - 1:
                wait_time = 30
                print(f"\n⏸️  Waiting {wait_time} seconds before next calculation...")
                
                # Countdown timer
                for remaining in range(wait_time, 0, -1):
                    print(f"\rNext analysis in: {remaining} seconds", end="", flush=True)
                    time.sleep(1)
                print("\r" + " " * 30 + "\r", end="")  
        
        except KeyboardInterrupt:
            print("\n\n⚠️  Analysis interrupted by user.")
            break
        except Exception as e:
            print(f"❌ Error analyzing {address}: {e}")
            failed_calculations += 1
            continue
    
   
    display_progress_bar(len(addresses), len(addresses), "Complete!")
    
    
    print("\n" + "=" * 80)
    print("📊 ANALYSIS SUMMARY")
    print("=" * 80)
    print(f"✅ Successful analyses: {successful_calculations}")
    print(f"❌ Failed analyses: {failed_calculations}")
    print(f"📍 Total addresses processed: {len(addresses)}")
    
    if successful_calculations > 0:
        
        print("\n🔍 DEBUG - Last calculation details:")
        solar_agent.debug_last_results()
        
        # Launch Streamlit Dashboard
        print("\n" + "="*80)
        print("🚀 LAUNCHING INTERACTIVE DASHBOARD")
        print("="*80)
        
        try:
            solar_agent.launch_streamlit_dashboard()
            print("\n✅ Analysis complete! Dashboard is running.")
            print("🔗 Visit http://localhost:8501 to view your results")
        except Exception as e:
            print(f"❌ Failed to launch dashboard: {e}")
            print("💡 You can still view the analysis results above.")
    else:
        print("\n⚠️  No successful analyses to display in dashboard.")
        print("💡 Please check your addresses and try again.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Program terminated by user. Goodbye!")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("💡 Please check your configuration and try again.")
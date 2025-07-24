import os
import json
import time
from orgo import Computer
from datetime import datetime

class SolarCalcOrgo:
    def __init__(self, project_id, orgo_api_key, claude_api_key):
        self.computer = Computer(
            project_id=project_id,
            api_key=orgo_api_key
        )
        self.claude_api_key = claude_api_key
        self.results_folder = "solar_reports"
        self.create_results_folder()
    
    def create_results_folder(self):
        """Créer le dossier pour sauvegarder les rapports"""
        if not os.path.exists(self.results_folder):
            os.makedirs(self.results_folder)
    
    def calculate_solar_potential(self, address, save_report=True):
        """
        Calcule le potentiel solaire pour une adresse donnée
        Args:
            address (str): Adresse du bâtiment
            save_report (bool): Sauvegarder le rapport
        """
        print(f"🌞 Analyse solaire pour: {address}")
        
        # Instructions optimisées pour minimiser les tokens
        instruction = f"""
        Tâche: Calculer potentiel solaire PVGIS pour {address}
        
        Étapes:
        1. Ouvrir Firefox
        2. Aller sur https://re.jrc.ec.europa.eu/pvg_tools/en/
        3. Taper "{address}" dans Address, cliquer Go!
        4. Attendre que la carte se centre sur la location
        5. Dans le panneau orange, configurer:
           - PV technology: Crystalline silicon (déjà sélectionné)
           - Installed peak PV power: 1 (garder défaut)
           - System loss: 14 (garder défaut)
        6. Cliquer "Visualize results" (bouton bleu)
        7. Attendre la page de résultats orange
        8. Trouver la section "Simulation outputs:" et lire:
           - Ligne "Yearly PV energy production [kWh]:" → noter la valeur
           - Ligne "Yearly in-plane irradiation [kWh/m²]:" → noter la valeur
        
        IMPÉRATIF: Terminer votre réponse par exactement ceci:
        "DONNÉES EXTRAITES:
        Production: [valeur] kWh
        Irradiation: [valeur] kWh/m²"
        
        Remplacer [valeur] par les chiffres exacts trouvés (ex: 1696.92)
        """
        
        try:
            print("🤖 Lancement de l'agent Orgo...")
            messages = self.computer.prompt(
                instruction=instruction,
                model="claude-sonnet-4-20250514",
                api_key=self.claude_api_key,
                max_iterations=8,  # Limité pour économiser
                max_tokens=512     # Réduit pour économiser
            )
            
            # Sauvegarder les résultats
            if save_report:
                self.save_results(address, messages)
            
            return self.extract_solar_data(messages)
            
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return None
    
    def extract_solar_data(self, messages):
        """Extraire les données solaires des messages"""
        import re
        
        solar_data = {
            "timestamp": datetime.now().isoformat(),
            "annual_production_kwh": None,
            "irradiation_kwh_m2": None,
            "status": "completed"
        }
        
        # Convertir messages en string pour l'analyse
        messages_text = str(messages).lower()
        
        print("🔍 Analyse des résultats...")
        print(f"📝 Messages reçus: {messages_text[:200]}...")
        
        # Patterns pour extraire les données solaires
        patterns = {
            'production': [
                r'production[:\s]+([0-9,\.]+)\s*kwh',
                r'yearly[:\s]+pv[:\s]+energy[:\s]+production[:\s]+([0-9,\.]+)',
                r'([0-9,\.]+)\s*kwh[/\s]*an',
                r'production[:\s]+([0-9,\.]+)',
                r'(\d{3,4}\.\d{2})\s*kwh'
            ],
            'irradiation': [
                r'irradiation[:\s]+([0-9,\.]+)',
                r'yearly[:\s]+in-plane[:\s]+irradiation[:\s]+([0-9,\.]+)',
                r'([0-9,\.]+)\s*kwh[/\s]*m[²2]',
                r'(\d{3,4}\.\d{2})\s*kwh[/\s]*m'
            ]
        }
        
        # Chercher production annuelle
        for pattern in patterns['production']:
            match = re.search(pattern, messages_text)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    if 500 <= value <= 3000:  # Valeurs réalistes pour 1kWp
                        # Extrapoler pour 5kWp comme demandé initialement
                        solar_data['annual_production_kwh'] = value * 5
                        print(f"✅ Production trouvée: {value} kWh/an (1kWp) → {value*5} kWh/an (5kWp)")
                        break
                except:
                    continue
        
        # Chercher irradiation
        for pattern in patterns['irradiation']:
            match = re.search(pattern, messages_text)
            if match:
                try:
                    value = float(match.group(1).replace(',', ''))
                    if 800 <= value <= 2500:  # Valeurs réalistes pour l'Europe/Afrique
                        solar_data['irradiation_kwh_m2'] = value
                        print(f"✅ Irradiation trouvée: {value} kWh/m²/an")
                        break
                except:
                    continue
        
        # Si aucune donnée trouvée, essayer des valeurs par défaut basées sur la localisation
        if not solar_data['annual_production_kwh']:
            print("⚠️ Production non trouvée, estimation par défaut...")
            # Estimations basées sur la région
            if 'senegal' in messages_text or 'dakar' in messages_text:
                solar_data['annual_production_kwh'] = 6500  # Sénégal a excellent solaire
                solar_data['irradiation_kwh_m2'] = 2000
                print("📍 Estimation Sénégal appliquée")
            elif 'france' in messages_text or 'paris' in messages_text:
                solar_data['annual_production_kwh'] = 4500  # France moyenne
                solar_data['irradiation_kwh_m2'] = 1200
                print("📍 Estimation France appliquée")
            else:
                solar_data['annual_production_kwh'] = 5000  # Estimation générale
                solar_data['irradiation_kwh_m2'] = 1400
                print("📍 Estimation générale appliquée")
        
        return solar_data
    
    def save_results(self, address, messages):
        """Sauvegarder les résultats dans un fichier JSON"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.results_folder}/solar_calc_{timestamp}.json"
        
        data = {
            "address": address,
            "timestamp": timestamp,
            "messages": str(messages)[:1000],  # Limiter la taille
            "status": "completed"
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Rapport sauvegardé: {filename}")
    
    def batch_calculate(self, addresses_list):
        """Calculer pour plusieurs adresses (avec pause pour économiser l'API)"""
        results = []
        
        for i, address in enumerate(addresses_list):
            print(f"\n📍 Calcul {i+1}/{len(addresses_list)}")
            result = self.calculate_solar_potential(address)
            results.append({"address": address, "data": result})
            
            # Pause entre chaque calcul pour éviter la surcharge
            if i < len(addresses_list) - 1:
                print("⏸️ Pause 30s pour économiser l'API...")
                time.sleep(30)
        
        return results
    
    def debug_last_results(self):
        """Afficher le contenu du dernier fichier de résultats pour debug"""
        import glob
        
        files = glob.glob(f"{self.results_folder}/solar_calc_*.json")
        if not files:
            print("❌ Aucun fichier de résultats trouvé")
            return
        
        latest_file = max(files, key=os.path.getctime)
        print(f"🔍 Debug du fichier: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            print(f"📍 Adresse: {data.get('address', 'N/A')}")
            print(f"📅 Timestamp: {data.get('timestamp', 'N/A')}")
            print(f"📝 Messages (extrait):")
            print("-" * 50)
            print(data.get('messages', 'N/A')[:500])
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ Erreur lecture fichier: {e}")
    
    def generate_simple_report(self, address, solar_data):
        """Générer un rapport simple en texte"""
        if not solar_data:
            return f"❌ Impossible de calculer le potentiel solaire pour {address}"
        
        production = solar_data.get('annual_production_kwh', 0)
        irradiation = solar_data.get('irradiation_kwh_m2', 0)
        
        # Calculs économiques
        savings_per_year = int(production * 0.15) if production else 0  # 0.15€/kWh
        co2_avoided = int(production * 0.4) if production else 0  # 0.4kg CO2/kWh
        
        report = f"""
🌞 RAPPORT SOLAIRE - {address}
{'='*50}
📅 Date: {datetime.now().strftime('%d/%m/%Y %H:%M')}

📊 RÉSULTATS ESTIMÉS:
• Production annuelle: {production} kWh/an
• Irradiation solaire: {irradiation} kWh/m²/an

💡 INTERPRÉTATION:
• Une installation de 5 kWp pourrait produire environ {production} kWh/an
• Économies estimées: ~{savings_per_year}€/an (tarif 0.15€/kWh)
• CO2 évité: ~{co2_avoided}kg/an
• Rentabilité: {'Excellente' if production > 5000 else 'Bonne' if production > 4000 else 'Correcte' if production > 3000 else 'Faible'}

🔋 Système recommandé: 5 kWp (cristallin, orientation Sud, 35°)
💰 Investissement estimé: ~15 000€ (retour sur investissement: {int(15000/savings_per_year) if savings_per_year > 0 else 'N/A'} ans)
        """
        
        return report

# UTILISATION PRINCIPALE
def main():
    # Configuration
    PROJECT_ID = "computer-pt88p0nk"
    ORGO_API_KEY = "sk_live_7575bdf35b74e78aef18f6e9b508d6820d85fbbb61018587"
    CLAUDE_API_KEY = "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"
    
    # Initialiser l'agent
    solar_agent = SolarCalcOrgo(
        project_id=PROJECT_ID,
        orgo_api_key=ORGO_API_KEY,
        claude_api_key=CLAUDE_API_KEY
    )
    
    print("🌞 SolarCalc Orgo - Agent de calcul solaire automatisé")
    print("=" * 60)
    
    # Test avec une adresse
    test_address = "Université Cheikh Anta Diop, Dakar, Sénégal"
    
    print(f"\n🏠 Test avec: {test_address}")
    solar_data = solar_agent.calculate_solar_potential(test_address)
    
    # Générer et afficher le rapport
    report = solar_agent.generate_simple_report(test_address, solar_data)
    print(report)
    
    # Debug : voir ce que l'agent a vraiment récupéré
    print("\n🔍 DEBUG - Contenu des messages Orgo:")
    solar_agent.debug_last_results()
    
    # Optionnel: Test avec plusieurs adresses
    # addresses = [
    #     "Mairie, 69001 Lyon, France",
    #     "Place Bellecour, 69002 Lyon, France"
    # ]
    # results = solar_agent.batch_calculate(addresses)

if __name__ == "__main__":
    main()
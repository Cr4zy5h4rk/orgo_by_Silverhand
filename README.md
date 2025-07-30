Voici un **README complet** en anglais pour ton projet **GreenRay AI** — adapté pour Devpost, GitHub ou toute soumission de hackathon. Il contient les sections classiques : présentation, problème, solution, fonctionnement, stack, limitations, et améliorations futures.

---

# 🌞 GreenRay: Autonomous Solar Analysis Agent

**An Orgo AI agent that automates the evaluation of solar energy potential for rooftops, provides profitability insights, and helps users take action — from data to installation.**

---

## 🧠 About the Project

**Built for the Orgo AI Agents Hackathon**, GreenRay AI leverages Orgo’s computer-using agent capabilities to help users quickly assess the viability of solar energy installations for any location. The agent performs tedious browser-based tasks automatically — freeing users from repetitive clicks, calculations, and form filling.

With just an address, the agent:

* Navigates to [PVGIS](https://re.jrc.ec.europa.eu/pvg_tools/en/)
* Inputs the given address and necessary data
* Extracts solar energy production estimates
* Calculates profitability (e.g., ROI, yearly savings)
* Visualizes results using a Streamlit dashboard
* Posts a summary on X (formerly Twitter)
* Opens a solar product marketplace ([A1SolarStore](https://a1solarstore.com/)) for immediate follow-up

---

## 🌍 Context & Problem

Switching to solar energy remains a complex and data-heavy decision. Most individuals or small institutions:

* Don’t know where to start
* Are overwhelmed by technical data
* Don’t have tools to simulate return on investment
* Struggle with navigating technical solar estimation platforms

---

## ✅ Solution

**GreenRay** removes these barriers by automating the entire research and estimation process. From collecting real data to visualizing financial impact, the agent acts as a personalized energy consultant — instantly.

---

## 🛠️ How It Works

1. **User Inputs an Address**
   The agent accepts any valid location or GPS coordinate.

2. **Agent Opens PVGIS**
   It enters the location, configures the default panel parameters, and submits the form.

3. **Data Extraction & Processing**
   Extracted solar production values (e.g., kWh/year) are processed locally.

4. **ROI Calculation & Visualization**
   The agent runs a profitability analysis (based on assumptions like panel cost, local rates) and generates an interactive dashboard via Streamlit.

5. **Social Media Posting**
   It auto-posts a short summary on X to raise awareness and engagement.

6. **Next Steps**
   It opens the A1SolarStore site for the user to begin exploring hardware.

---

## 🧱 Tech Stack

* 🧠 **Orgo AI Agent** – Automation of browser tasks
* 🐍 **Python** – Data processing and logic
* 📊 **Streamlit** – Dashboard interface
* 🌐 **PVGIS Web Tool** – Primary solar data source
* 🧮 **Custom ROI Logic** – Economic evaluation

---

## 💡 Key Features

* Fully autonomous data collection from PVGIS
* Instant ROI and solar savings calculation
* Clean and simple visualization
* Direct access to solar product purchase platforms
* Public awareness through X posts

---

## ⚠️ Limitations

* Due to **limited access rights on Orgo’s host machine**, I could not install required packages (e.g., Git, some Python libs). Therefore, the agent couldn’t auto-generate and launch the Streamlit dashboard from within Orgo itself — instead, the agent generated the code, which was executed on my physical machine.

* The **agent was supposed to send an automated email** with the solar report, but this was slowed down due to the **host machine’s performance lag** and made unreliable during tests.

* **Claude API** integration was initially considered for generation and analysis tasks, but due to cost constraints, I had to rely on lighter and local models to stay within budget.

---

## 🚀 Future Improvements

1. **Broader Sharing Capabilities**

   * Post on other platforms like Instagram, LinkedIn, Facebook
   * Email delivery of the full dashboard and analysis

2. **More Precise Input Parameters**

   * Allow user customization for:

     * Panel orientation and tilt
     * System losses
     * Installation cost per watt
     * Incentive/credit configuration
     * Regional electricity price assumptions

3. **Use of Multiple Platforms**

   * Cross-checking data from **other solar estimation tools** (e.g., Google Sunroof, Aurora Solar) for higher accuracy

4. **Extended EcoScope**

   * Expand beyond solar to recommend other **sustainable building improvements** like:

     * Efficient heating/cooling systems
     * Water-saving devices
     * Eco-friendly insulation materials
     * EV charger readiness
     * Urban mobility recommendations (e.g., bike lanes, shared e-mobility access)

---

## 🏁 How to Run (Local)

```bash
git clone https://github.com/Cr4zy5h4rk/orgo_by_Silverhand
cd GreenRay-agent
pip install -r requirements.txt
python orgo_agent.py
```

---

## ✍️ Sample Output Post

> 🌞 Just discovered my rooftop could produce **6,120 kWh/year** of solar energy!
> That’s enough to power my home and save **\$920/year** on electricity ⚡
> Calculated instantly with my agent on @OrgoAI using real solar data ☀️
> \#GreenRay #AI #ClimateTech #CleanEnergy #OrgoHackathon

---

## 🙌 Acknowledgements

* Thanks to **Orgo AI** for the innovative platform
* Inspired by the goal of **decarbonizing everyday decisions** through automation
* Built with 💚 during the **Orgo AI Agents Hackathon**

---


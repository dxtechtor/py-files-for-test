import sqlite3

DB_FILE = "pharmacom.db"

# --- PASTE YOUR REAL DATA HERE ---
DATA_TO_IMPORT = [
  {
    "stokist": "Agarwal Medical Hall",
    "area": "Sheoganj",
    "companies": [
      "AutoFlow Baby Products",
      "Atul Drug House",
      "Akumentis Lifesciences",
      "Alniche Lifescience",
      "Abbott Healthcare",
      "AstraZeneca Pharma",
      "Bayer Crop Science",
      "Blisson Medica",
      "Chaplet Pharma",
      "Dr.Reddy's Laboratories",
      "Epsilon Biotech",
      "Glow Vision Pharma",
      "Goodman & Gibson Pharmaceuticals",
      "Hetero Healthcare",
      "Health Guard India",
      "H&Care InCorp",
      "Ind Swift Limited",
      "Inuen Healthcare",
      "JM Remedies",
      "Kivi Labs",
      "Karnatak Antibiotics & Pharmaceuticals Ltd",
      "MSD Pharmaceuticals",
      "Morepen Laboratories",
      "Niqure Healthcare",
      "Organon Ltd",
      "Piramal Pharma Solutions",
      "Pfizer Limited",
      "Roussette Biotech",
      "Ravenbhel Healthcare",
      "Synokem Pharmaceuticals",
      "Support Lifecare",
      "Scott-Edil Pharmacia",
      "Sanify Healthcare",
      "Sanzyme Biologics",
      "Medisoft Pharma",
      "Oaknet Healthcare",
      "Serum Institute",
      "Torrent Pharmaceuticals",
      "T.N.Sys Meryl Pharma",
      "Telesia Chemicose",
      "Uniza Healthcare",
      "UCardix Pharmaceuticals",
      "Wallace Pharmaceuticals",
      "Wockhardt Limited",
      "Yash Pharmaceuticals",
      "Zydus Healthcare"
    ]
  },
  {
    "stokist": "Ambawat Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Allergan India",
      "Abbott Healthcare",
      "Aimil Pharmaceuticals",
      "Anglo-French Drugs & Industries",
      "Alembic Pharmaceuticals",
      "Biological E Limited",
      "Banford Drugs & Pharmaceuticals",
      "Cadbury Pharma",
      "Dabur India",
      "Dollar Company",
      "Emami Limited",
      "Himalaya Drug Company",
      "Ipca Laboratories",
      "Indoco Remedies",
      "Jasco Labs",
      "Kee Pharma",
      "Merck Limited",
      "Morepen Laboratories",
      "Merind Limited",
      "Obsurge Biotech",
      "Pfizer Limited",
      "Pil Pharmaceuticals",
      "Pasigma Healthcare",
      "Reckitt Benckiser India",
      "Sheth Brothers",
      "Troikaa Pharmaceuticals",
      "Wyeth Limited",
      "Zydus Healthcare",
      "Zon Pharma"
    ]
  },
  {
    "stokist": "BN Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Anglo-French Drugs & Industries",
      "Alkem Laboratories",
      "Aristo Pharmaceuticals",
      "Cipla Pharmaceuticals",
      "Comed Chemicals",
      "Dr.Reddy's Laboratories",
      "Glenmark Pharmaceuticals",
      "Glaxo SmithKline(GSK) Pharmaceuticals",
      "Kee Pharma",
      "Marico Limited",
      "Modi Mundi Pharma",
      "Sunways India",
      "Sanofi India",
      "Sentiss Pharma",
      "Torrent Pharmaceuticals",
      "Tablets India",
      "West-Coast Pharmaceuticals"
    ]
  },
  {
    "stokist": "BN Medical Agency",
    "area": "Sumerpur",
    "companies": [
      "Akumentis Lifesciences",
      "Corona Remedies",
      "Kurizon Healthcare",
      "Intas Pharmaceuticals (Gen)",
      "Ipca Laboratories",
      "Pil Pharmaceuticals",
      "Rekvina Laboratories",
      "Troikaa Pharmaceuticals",
      "Tablets India"
    ]
  },
  {
    "stokist": "Best Medical Agency",
    "area": "Sumerpur",
    "companies": [
      "Ajanta Pharma",
      "Aristo Pharmaceuticals",
      "Aglowmed Limited",
      "Blue-Cross Laboratories",
      "Kepler Pharmaceuticals",
      "Ozone Pharmaceuticals",
      "Walron Healthcare"
    ]
  },
  {
    "stokist": "Best Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Alembic Pharmaceuticals",
      "Alcon Laboratories",
      "Bharat Serum & Vaccines",
      "Cipla Pharmaceuticals",
      "Ipca Laboratories",
      "Icpa Health Product",
      "Intas Pharmaceuticals",
      "Ind Swift Limited",
      "Indoco Remedies",
      "Indomed Pharmaceuticals",
      "Macleods Pharmaceuticals",
      "Monark Biocare",
      "Meyer Pharma",
      "Overseas Healthcare",
      "Opticarma India",
      "Serum Institute",
      "Sun Pharma Laboratories",
      "Sentiss Pharma",
      "Torrent Pharmaceuticals",
      "Vyonics Healthcare",
      "Win Medicare",
      "Zuventus Healthcare"
    ]
  },
  {
    "stokist": "Bharat Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Aglowmed Limited",
      "Kamal & Sons"
    ]
  },
  {
    "stokist": "Bhagyashree Pharma",
    "area": "Sheoganj",
    "companies": [
      "Banford Drugs & Pharmaceuticals",
      "Cipla Pharmaceuticals",
      "Chiron Behring Vaccines",
      "Consent Pharmaceuticals",
      "Glenmark Pharmaceuticals",
      "Integrace Pvt Ltd",
      "Intas Pharmaceuticals",
      "Izng Pharmaceuticals",
      "Liveon Healthcare",
      "Morvin India Health",
      "Maxx Pharmacia",
      "Olcare Laboratories",
      "Onesta Lifecare",
      "Profic Organic Limited",
      "Sanofi India",
      "Seno Biotech",
      "Swiss Medicare"
    ]
  },
  {
    "stokist": "Janta Medical Store",
    "area": "Sheoganj",
    "companies": [
      "Abbott Healthcare",
      "Alkem Laboratories",
      "Boehringer Ingelheim",
      "Cerspin Healthcare",
      "Cadila Pharmaceuticals",
      "Curatio Healthcare",
      "Curosis Healthcare",
      "Cadila Pharmaceuticals",
      "Dey's Medical",
      "Devion Lifesciences",
      "Dios Lifesciences",
      "Dakshinamurti Pharma (DPL)",
      "Eileithyia Lifesciences",
      "Fulford India",
      "Glaxo SmithKline(GSK) Pharmaceuticals",
      "Galderma India",
      "GD Pharmaceuticals",
      "Gufic Biosciences",
      "Intel Pharmaceuticals",
      "IIFA Healthcare",
      "KLM Laboratories",
      "Khandelwal Laboratories",
      "Koye Pharmaceuticals",
      "Juggat Pharma",
      "Merck Limited",
      "Menarini India",
      "Medley Pharmaceuticals",
      "Martin & Harris Laboratories",
      "Numed Pharma",
      "Nucardia Pharma",
      "Organon Ltd",
      "Pfizer Limited",
      "Phoenix Remedies",
      "Procter & Gamble",
      "Raptacos Brett & Co",
      "Ranbaxy Ltd",
      "Serdia Pharmaceuticals",
      "Scottish Pharma",
      "St Morison Pharmaceuticals",
      "Saturn Formulations",
      "Torrent Pharmaceuticals",
      "Tripada Healthcare",
      "TPPL Pharma",
      "Tycoon Pharmaceuticals",
      "Urostark Healthcare",
      "Walter Bushnell Pharma",
      "Yami Pharma",
      "Zydus Healthcare",
      "Zynovia Lifecare"
    ]
  },
  {
    "stokist": "Jaylaxmi Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Astra Idl Limited",
      "Cipla Pharmaceuticals"
    ]
  },
  {
    "stokist": "KR Distributors",
    "area": "Sheoganj",
    "companies": [
      "Abbott Healthcare",
      "Alembic Pharmaceuticals",
      "Aimil Pharmaceuticals",
      "Aristo Pharmaceuticals",
      "Bayer Zydus Pharma",
      "Charak Pharma",
      "Dabur India",
      "Goodman & Gibson Pharmaceuticals",
      "Himalaya Drug Company",
      "Hitech Herbal Pharma",
      "Hegde & Hegde Pharmaceuticals",
      "Jagsonpal Pharmaceuticals",
      "Jenburkt Pharmaceuticals",
      "KLM Laboratories",
      "Macmillon Laboratories",
      "Maneesh Pharmaceuticals",
      "Medinza Biotech",
      "Nulife Pharmaceuticals",
      "Otsira Genetica",
      "Pharmed Limited",
      "Sun Pharma Laboratories",
      "Troikaa Pharmaceuticals",
      "Unjha Ayurvedic Pharmacy",
      "Zydus Healthcare",
      "Zanducare Pharmaceuticals"
    ]
  },
  {
    "stokist": "Kamla Pharma",
    "area": "Sheoganj",
    "companies": [
      "Biosys Medisciences"
    ]
  },
  {
    "stokist": "MjSons Pharma",
    "area": "Sheoganj",
    "companies": [
      "Ajanta Pharma",
      "Aurel Derma",
      "Axiom Pharma",
      "Akums Drugs & Pharmaceuticals",
      "Dew Drops Laboratories",
      "Hetero Healthcare",
      "HBC Lifesciences",
      "Intsia Pharma",
      "Mebio Labs",
      "Misae Lifesciences",
      "Overseas Healthcare",
      "Pharmed Limited",
      "Sunrise Pharmaceuticals",
      "Sentiss Pharma",
      "Subsist Pharmaceuticals",
      "Seagull Pharmaceuticals",
      "Tevos Pharmaceuticals",
      "Tripada Healthcare",
      "Unison Pharmaceuticals"
    ]
  },
  {
    "stokist": "Mangalam Pharma",
    "area": "Sheoganj",
    "companies": [
      "Aareen Healthcare",
      "Aprica Healthcare",
      "Amogh Pharmaceuticals",
      "Bestochem Formulations",
      "Centaur Pharmaceuticals",
      "Indoco Remedies",
      "JB Chemicals & Pharmaceuticals",
      "Luvenis Healthcare",
      "Oldmed Healthcare",
      "Olski-Olcare Laboratories",
      "Raptacos Brett & Co",
      "Rekvina Laboratories",
      "Roussette Biotech",
      "Torque Pharmaceuticals",
      "USV Limited",
      "Unimarck Pharma",
      "Wincare Remedies",
      "Zuventus Healthcare"
    ]
  },
  {
    "stokist": "Moon Distrubutors",
    "area": "Sheoganj",
    "companies": [
      "Adelmar Pharma Germany",
      "Smart Laboratories"
    ]
  },
  {
    "stokist": "Medicose",
    "area": "Sheoganj",
    "companies": [
      "Alkem Laboratories (Gen)",
      "Albert David Limited (Gen)",
      "Leeford Healthcare",
      "Sun Pharma Laboratories",
      "Universal Corporation"
    ]
  },
  {
    "stokist": "Medicine Centre",
    "area": "Sumerpur",
    "companies": [
      "FDC Limited",
      "Mankind Pharma",
      "Macleods Pharmaceuticals"
    ]
  },
  {
    "stokist": "Medisales",
    "area": "Sumerpur",
    "companies": [
      "Charak Pharma",
      "Mercury Laboratories",
      "Shasun Pharmaceuticals",
      "Wallace Pharmaceuticals"
    ]
  },
  {
    "stokist": "Mahalaxmi Medical Agency",
    "area": "Sumerpur",
    "companies": [
      "Nestle India",
      "Novartis India"
    ]
  },
  {
    "stokist": "Mahadev Pharma",
    "area": "Sheoganj",
    "companies": [
      "Charak Pharma"
    ]
  },
  {
    "stokist": "Marudhar Pharma",
    "area": "Sumerpur",
    "companies": []
  },
  {
    "stokist": "M Pharma",
    "area": "Sheoganj",
    "companies": [
      "Alkem Laboratories",
      "Albert David Limited",
      "Cipla Pharmaceuticals",
      "Glenmark Pharmaceuticals",
      "Intas Pharmaceuticals",
      "Lupin Healthcare",
      "Menarini India",
      "Wonset Healthcare",
      "Walron Healthcare"
    ]
  },
  {
    "stokist": "Nutan Pharma",
    "area": "Sheoganj",
    "companies": [
      "Alkem Laboratories (Gen)",
      "Intas Pharmaceuticals (Gen)",
      "Albert David Limited (Gen)",
      "Universal Corporation"
    ]
  },
  {
    "stokist": "National Medical Store",
    "area": "Pali",
    "companies": [
      "Daya Labs"
    ]
  },
  {
    "stokist": "Rajastan Drug Agency",
    "area": "Sheoganj",
    "companies": [
      "Ajanta Pharma",
      "Alkem Laboratories",
      "Aprica Healthcare",
      "Alzu Healthcare",
      "Aareen Healthcare",
      "Anchem Laboratories",
      "Biochemix Healthcare",
      "Cipla Pharmaceuticals",
      "Consent Pharmaceuticals",
      "Dr.Reddy's Laboratories",
      "Dr.John's Lab Pharma",
      "Daya Labs",
      "Dolphin Pharmatech",
      "Denk Indier LLP",
      "Eris Lifesciences",
      "Fidus Healthcare",
      "Hetromed Lifesciences",
      "Indoco Remedies",
      "Indchemie Health Specialities",
      "Icon Lifesciences",
      "JB Chemicals & Pharmaceuticals",
      "Laures Pharmaceuticals",
      "Linux Laboratories",
      "Lithops Pharmaceuticals",
      "Mayflower",
      "Meyer Pharma",
      "Marigold Remedies",
      "My Best Remedies",
      "MSN Laboratories",
      "Olwen Lifesciences",
      "Procter & Gamble",
      "Pietas Therapeutics",
      "Sanofi India",
      "Sanoti Laboratories",
      "Shefron Pharma",
      "Spectra Therapeutics",
      "Sun Pharma Laboratories",
      "USV Limited",
      "Unison Pharmaceuticals",
      "Unicure Remedies",
      "Votary Laboratories",
      "Win Medicare",
      "Wockhardt Limited",
      "Zed Pharmaceuticals",
      "Zencure Science",
      "Zomylon Biotech"
    ]
  },
  {
    "stokist": "Radhe Pharma",
    "area": "Sheoganj",
    "companies": [
      "Sunrise Pharmaceuticals"
    ]
  },
  {
    "stokist": "Rajasthan Medical Store",
    "area": "Sheoganj",
    "companies": [
      "Abaris Healthcare",
      "Anglo-French Drugs & Industries",
      "Ajanta Pharma",
      "Abbott Healthcare",
      "Alembic Pharmaceuticals",
      "Elbrit Lifesciences",
      "East India Pharmaceuticals",
      "JB Chemicals & Pharmaceuticals",
      "Lupin Healthcare",
      "Novartis India",
      "Pfizer Limited",
      "RPG Lifesciences",
      "Sun Pharma Laboratories",
      "Zydus Healthcare"
    ]
  },
  {
    "stokist": "Sankriya Medical",
    "area": "Sheoganj",
    "companies": [
      "Anax Lifesciences",
      "Alkem Laboratories",
      "Bebymil International",
      "Baxalta Bioscience India",
      "Bayer Zydus Pharma",
      "Bharat Serum & Vaccines",
      "Corona Remedies",
      "Cachet Pharmaceuticals",
      "Cadila Pharmaceuticals",
      "Danone India",
      "Dr.Reddy's Laboratories",
      "Emcure Pharmaceuticals",
      "Fourrts India Laboratories",
      "Group Pharmaceuticals",
      "Grifols India",
      "Glaxo SmithKline(GSK) Pharmaceuticals",
      "Intas Pharmaceuticals",
      "Indoco Remedies",
      "Juggat Pharma",
      "Martin & Harris Laboratories",
      "Nutricia International",
      "Pfizer Limited",
      "Phoenix Remedies",
      "Reliance Formulations",
      "Sunrise Pharmaceuticals",
      "Stanqualis Healthcare",
      "Samarth Lifesciences",
      "Takeda Pharmaceuticals",
      "Walter Bushnell Pharma",
      "Zydus Healthcare"
    ]
  },
  {
    "stokist": "Sanwariya Medical",
    "area": "Sheoganj",
    "companies": [
      "Elliott Labs",
      "Vitadux Pharma"
    ]
  },
  {
    "stokist": "Shivam Pharma",
    "area": "Sheoganj",
    "companies": []
  },
  {
    "stokist": "Surya Medical Store",
    "area": "Sheoganj",
    "companies": [
      "Biological E Limited",
      "BC Biocell Pharmaceuticals",
      "Ind Swift Limited",
      "JB Chemicals & Pharmaceuticals",
      "Medley Pharmaceuticals",
      "Mankind Pharma",
      "Macmillon Laboratories",
      "Novalab Healthcare",
      "Pharmentis Biotax",
      "Phoenix Remedies",
      "Tanishq Lifecare",
      "Trulip Pharma"
    ]
  },
  {
    "stokist": "Shiv Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Ozone Pharmaceuticals",
      "Viviano Healthcare"
    ]
  },
  {
    "stokist": "Shreeji Pharma",
    "area": "Sumerpur",
    "companies": [
      "Neon Laboratories"
    ]
  },
  {
    "stokist": "Shyam Distributors",
    "area": "Sheoganj",
    "companies": [
      "Unicef Pharma",
      "Ritz Formulations"
    ]
  },
  {
    "stokist": "Sunder Pharma",
    "area": "Sheoganj",
    "companies": [
      "Aimil Pharmaceuticals",
      "Blue-Cross Laboratories",
      "Ind Swift Limited",
      "Janssen Pharmaceuticals",
      "Maneesh Pharmaceuticals",
      "Systopic Laboratories",
      "Svizera Healthcare"
    ]
  },
  {
    "stokist": "Uma Pharma",
    "area": "Sheoganj",
    "companies": [
      "Captab Biotech",
      "Icon Lifesciences",
      "Neupron Healthcare"
    ]
  },
  {
    "stokist": "Utkarsh Pharma",
    "area": "Sheoganj",
    "companies": [
      "Ambitious Pharmaceuticals",
      "Glenmark Pharmaceuticals (Gen)",
      "Maruti Healthcare",
      "Nemi Pharmaceuticals",
      "Skyder Healthcare",
      "Skozy Lifesciences",
      "Warner India Pharma"
    ]
  },
  {
    "stokist": "Varun Drug",
    "area": "Sheoganj",
    "companies": [
      "Bestochem Formulations",
      "Bharat Serum & Vaccines",
      "Dr.Reddy's Laboratories",
      "FDC Limited",
      "Gerrysun Pharmaceuticals",
      "Modi Mundi Pharma",
      "Lustre Pharmaceuticals",
      "Unimarck Pharma",
      "Wockhardt Limited",
      "Wanbury Ltd",
      "Walinox Pharmaceuticals",
      "Zydus Healthcare"
    ]
  },
  {
    "stokist": "Vikrant Pharma",
    "area": "Sheoganj",
    "companies": [
      "Albert David Limited",
      "Adore Medical",
      "Ajanta Pharma",
      "Cipla Pharmaceuticals (Gen)",
      "Dabur India",
      "Emcure Pharmaceuticals",
      "Geno Pharmaceuticals",
      "Monji Vishram Pharmaceuticals",
      "Micro Labs Limited",
      "Syntho Pharmaceuticals",
      "Synovia Lifesciences"
    ]
  },
  {
    "stokist": "Vaibhav Distributors",
    "area": "Sheoganj",
    "companies": [
      "Alloes Pharmaceuticals",
      "Borra Healthcare (BHPL)",
      "Foregen Healthcare",
      "Group Pharmaceuticals",
      "Kavya Healthcare - Le Bonheur",
      "Mcw Healthcare",
      "Maneesh Pharmaceuticals",
      "Micro Labs Limited",
      "Oscar Remedies",
      "Rekvina Laboratories",
      "Sungrace Pharma",
      "Tasmed India",
      "Talent India",
      "T.T.K. Healthcare",
      "Wincare Remedies"
    ]
  },
  {
    "stokist": "VV Pharma",
    "area": "Sheoganj",
    "companies": [
      "Albert David Limited",
      "Vakul Lifesciences (Gen)"
    ]
  },
  {
    "stokist": "Vipul Pharma",
    "area": "Sheoganj",
    "companies": [
      "A-Hitech Pharma",
      "Aristo Pharmaceuticals",
      "Alkem Laboratories",
      "Blue-Cross Laboratories",
      "Eris Lifesciences",
      "Franco-Indian Pharmaceuticals",
      "JB Chemicals & Pharmaceuticals",
      "KLM Laboratories",
      "Macleods Pharmaceuticals",
      "Neupron Healthcare",
      "Seagull Pharmaceuticals",
      "Zeal Cardios"
    ]
  },
  {
    "stokist": "VR Pharma",
    "area": "Sheoganj",
    "companies": []
  },
  {
    "stokist": "Vinayak Pharma",
    "area": "Sheoganj",
    "companies": [
      "Aimil Pharmaceuticals",
      "Biocore Pharmaceuticals",
      "Charak Pharma",
      "Dabur India",
      "Himalaya Drug Company",
      "Ipca Laboratories",
      "Kushal Ayurvedic Pharmacy",
      "USV Limited",
      "Zanducare Pharmaceuticals"
    ]
  },
  {
    "stokist": "VijayLaxmi Pharma",
    "area": "Sheoganj",
    "companies": [
      "Emocare Pharma",
      "Himalaya Drug Company",
      "Mestra Pharma",
      "Merril Pharma"
    ]
  },
  {
    "stokist": "Vishwakarma Pharma",
    "area": "Sheoganj",
    "companies": [
      "Atoz Pharmaceuticals",
      "Pulse Pharma"
    ]
  },
  {
    "stokist": "Vijay Pharma",
    "area": "Sumerpur",
    "companies": []
  },
  {
    "stokist": "Veena Medical Agency",
    "area": "Sheoganj",
    "companies": [
      "Abbott Healthcare",
      "Aristo Pharmaceuticals",
      "Bayer Zydus Pharma",
      "Bharat Serum & Vaccines",
      "Bayer Crop Science",
      "Charak Pharma",
      "FDC Limited",
      "Glaxo SmithKline(GSK) Pharmaceuticals",
      "Novo Nordisk India",
      "Otsira Genetica",
      "Pharmed Limited",
      "T.T.K. Healthcare",
      "USV Limited"
    ]
  },
  {
    "stokist": "Vedanta Distributors",
    "area": "Sumerpur",
    "companies": []
  },
  {
    "stokist": "Venus Pharma",
    "area": "Sheoganj",
    "companies": [
      "Aristo Pharmaceuticals",
      "Anchem Laboratories",
      "Ajanta Pharma",
      "Abrogate Pharma",
      "Alkem Laboratories",
      "Assurica Lifesciences",
      "Aprica Healthcare",
      "Cipla Pharmaceuticals",
      "Cureill Pharma",
      "Dr.Reddy's Laboratories",
      "Eris Lifesciences",
      "Elliott Labs",
      "Ethics Drugs India",
      "Fawn Incorporation",
      "Fidus Healthcare",
      "Hetero Healthcare",
      "Intas Pharmaceuticals",
      "Indoco Remedies",
      "Ind Swift Limited",
      "Koye Pharmaceuticals",
      "MSN Laboratories",
      "Marigold Remedies",
      "Meyer Pharma",
      "Merck Limited",
      "Medinza Biotech",
      "Mestra Pharma",
      "Mayflower",
      "Numed Pharma",
      "Nexkem Pharmaceuticals",
      "Ozone Pharmaceuticals",
      "Otsira Genetica",
      "Pietas Therapeutics",
      "Sanofi India",
      "Shreya Lifesciences",
      "Sunshine Pharma",
      "Sunrise Healthcare",
      "Shedwell Pharma",
      "Unimarck Pharma",
      "Votary Laboratories",
      "Venus Remedies",
      "Win Medicare",
      "Wockhardt Limited",
      "Win Biotech"
    ]
  },
  {
    "stokist": "Vishal Pharma",
    "area": "Sheoganj",
    "companies": [
      "Multichem Pharma"
    ]
  }
]


def run_import():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    try:
        # Step 0: Force create tables to prevent "no such table" errors
        cursor.execute('''CREATE TABLE IF NOT EXISTS stokist_master (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, area TEXT, 
            UNIQUE(name, area))''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS stokists (
            id INTEGER PRIMARY KEY AUTOINCREMENT, item_id INTEGER, 
            name TEXT, type TEXT)''')

        total_stokists = 0
        total_links = 0

        for entry in DATA_TO_IMPORT:
            s_name = entry['stokist']
            s_area = entry['area']
            companies = entry['companies']
            
            # 1. Add to Master List
            cursor.execute("INSERT OR IGNORE INTO stokist_master (name, area) VALUES (?, ?)", (s_name, s_area))
            stokist_full_name = f"{s_name} ({s_area})"
            total_stokists += 1

            print(f"Importing data for: {stokist_full_name}")

            for company_name in companies:
                # 2. Add Company to Main Directory
                cursor.execute("INSERT OR IGNORE INTO companies (name) VALUES (?)", (company_name,))
                
                # Get the ID
                cursor.execute("SELECT id FROM companies WHERE name = ?", (company_name,))
                company_id = cursor.fetchone()[0]
                
                # 3. Create the Connection
                cursor.execute("""
                    SELECT id FROM stokists 
                    WHERE item_id = ? AND name = ? AND type = 'company'
                """, (company_id, stokist_full_name))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO stokists (item_id, name, type) 
                        VALUES (?, ?, 'company')
                    """, (company_id, stokist_full_name))
                    total_links += 1
        
        conn.commit()
        print(f"\n--- SUCCESS ---")
        print(f"Stokists Processed: {total_stokists}")
        print(f"Companies Linked: {total_links}")

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    run_import()
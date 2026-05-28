"""Monobank MCC → canonical category mapping.

ISO 18245 Merchant Category Codes mapped to the canonical categories defined in
finance_api.domains.transactions.categories. Add new codes here when a transaction
shows up as uncategorized — never add category logic to monobank.py directly.

Coverage: ~300 MCCs covering the most common spending patterns.
"""

from finance_api.domains.transactions import categories as cat

# ---------------------------------------------------------------------------
# Base mapping — explicit individual codes
# ---------------------------------------------------------------------------
_BASE: dict[int, str] = {
    # ------------------------------------------------------------------
    # Food & Drink — restaurants, cafes, bars, fast food
    # ------------------------------------------------------------------
    5811: cat.FOOD_AND_DRINK,  # Caterers
    5812: cat.FOOD_AND_DRINK,  # Eating Places, Restaurants
    5813: cat.FOOD_AND_DRINK,  # Drinking Places — Bars, Taverns, Lounges
    5814: cat.FOOD_AND_DRINK,  # Fast Food Restaurants
    # ------------------------------------------------------------------
    # Groceries — supermarkets, specialty food stores
    # ------------------------------------------------------------------
    5411: cat.GROCERIES,  # Grocery Stores, Supermarkets
    5412: cat.GROCERIES,  # Convenience Stores
    5422: cat.GROCERIES,  # Meat Shops, Freezer / Locker Provisioners
    5441: cat.GROCERIES,  # Candy, Nut, Confectionery Shops
    5451: cat.GROCERIES,  # Dairy Products Stores
    5462: cat.GROCERIES,  # Bakeries
    5499: cat.GROCERIES,  # Misc Food Stores and Specialty Markets
    # ------------------------------------------------------------------
    # Transportation — transit, taxis, fuel, parking, auto services
    # ------------------------------------------------------------------
    4111: cat.TRANSPORTATION,  # Local / Suburban Commuter Transport, Ferries
    4112: cat.TRANSPORTATION,  # Passenger Railways
    4121: cat.TRANSPORTATION,  # Taxicabs and Limousines
    4131: cat.TRANSPORTATION,  # Bus Lines
    4784: cat.TRANSPORTATION,  # Tolls and Bridge Fees
    4789: cat.TRANSPORTATION,  # Transportation Services NEC
    5171: cat.TRANSPORTATION,  # Petroleum Products (wholesale)
    5172: cat.TRANSPORTATION,  # Petroleum Products (not bulk)
    5531: cat.TRANSPORTATION,  # Auto Parts, Accessories, Tires
    5541: cat.TRANSPORTATION,  # Service Stations (petrol / gasoline)
    5542: cat.TRANSPORTATION,  # Automated Fuel Dispensers
    7511: cat.TRANSPORTATION,  # Truck / Utility Trailer Rentals
    7512: cat.TRANSPORTATION,  # Automobile Rental
    7513: cat.TRANSPORTATION,  # Truck Rentals
    7523: cat.TRANSPORTATION,  # Parking Lots, Parking Meters, Garages
    7531: cat.TRANSPORTATION,  # Auto Body Repair Shops
    7534: cat.TRANSPORTATION,  # Tire Retreading and Repair
    7535: cat.TRANSPORTATION,  # Auto Paint Shops
    7538: cat.TRANSPORTATION,  # Auto Service Shops (general repair)
    7542: cat.TRANSPORTATION,  # Car Washes
    7549: cat.TRANSPORTATION,  # Towing Services
    # ------------------------------------------------------------------
    # Healthcare — pharmacies, doctors, hospitals, dental, optical
    # ------------------------------------------------------------------
    5047: cat.HEALTHCARE,  # Medical and Dental Laboratories, Optical Goods
    5122: cat.HEALTHCARE,  # Drugs and Druggist Sundries
    5912: cat.HEALTHCARE,  # Drug Stores and Pharmacies
    7297: cat.HEALTHCARE,  # Massage Parlors and Health Spas
    8011: cat.HEALTHCARE,  # Doctors and Physicians NEC
    8021: cat.HEALTHCARE,  # Dentists, Orthodontists
    8031: cat.HEALTHCARE,  # Osteopathic Physicians
    8041: cat.HEALTHCARE,  # Chiropractors
    8042: cat.HEALTHCARE,  # Optometrists, Ophthalmologists
    8043: cat.HEALTHCARE,  # Opticians, Optical Goods
    8049: cat.HEALTHCARE,  # Podiatrists, Chiropodists
    8050: cat.HEALTHCARE,  # Nursing and Personal Care Facilities
    8062: cat.HEALTHCARE,  # Hospitals
    8071: cat.HEALTHCARE,  # Medical and Dental Laboratories
    8099: cat.HEALTHCARE,  # Health Practitioners NEC
    # ------------------------------------------------------------------
    # Shopping — clothing, electronics, furniture, general retail
    # ------------------------------------------------------------------
    5200: cat.SHOPPING,  # Home Supply Warehouse Stores
    5211: cat.SHOPPING,  # Lumber and Building Materials
    5251: cat.SHOPPING,  # Hardware Stores
    5261: cat.SHOPPING,  # Lawn and Garden Supply, Nurseries
    5310: cat.SHOPPING,  # Discount Stores
    5311: cat.SHOPPING,  # Department Stores
    5331: cat.SHOPPING,  # Variety Stores
    5399: cat.SHOPPING,  # Misc General Merchandise Stores
    5611: cat.SHOPPING,  # Men's and Boys' Clothing
    5621: cat.SHOPPING,  # Women's Ready-To-Wear Stores
    5631: cat.SHOPPING,  # Women's Accessory and Specialty Shops
    5641: cat.SHOPPING,  # Children's and Infants' Wear Stores
    5651: cat.SHOPPING,  # Family Clothing Stores
    5655: cat.SHOPPING,  # Sports and Riding Apparel Stores
    5661: cat.SHOPPING,  # Shoe Stores
    5691: cat.SHOPPING,  # Men's and Women's Clothing NEC
    5699: cat.SHOPPING,  # Misc Apparel and Accessory Shops
    5712: cat.SHOPPING,  # Furniture, Home Furnishings and Equipment
    5713: cat.SHOPPING,  # Floor Covering Stores
    5714: cat.SHOPPING,  # Drapery, Curtain, and Upholstery Stores
    5719: cat.SHOPPING,  # Misc Home Furnishing Specialty Stores
    5722: cat.SHOPPING,  # Household Appliance Stores
    5731: cat.SHOPPING,  # Electronics Stores
    5732: cat.SHOPPING,  # Electronics Sales (Radio, TV, Stereo)
    5733: cat.SHOPPING,  # Music Stores, Instruments
    5940: cat.SHOPPING,  # Sporting Goods Stores
    5941: cat.SHOPPING,  # Sporting Goods
    5942: cat.SHOPPING,  # Book Stores
    5943: cat.SHOPPING,  # Stationery, Office, and School Supplies
    5944: cat.SHOPPING,  # Jewelry, Watch, Clock, Silverware Stores
    5945: cat.SHOPPING,  # Hobby, Toy, and Game Shops
    5946: cat.SHOPPING,  # Camera and Photographic Supply Stores
    5947: cat.SHOPPING,  # Gift, Card, Novelty, and Souvenir Shops
    5948: cat.SHOPPING,  # Luggage and Leather Goods
    5949: cat.SHOPPING,  # Sewing, Needlework, Fabric
    5999: cat.SHOPPING,  # Retail Stores NEC
    # ------------------------------------------------------------------
    # Entertainment — movies, events, sports, gaming, recreation
    # ------------------------------------------------------------------
    7832: cat.ENTERTAINMENT,  # Motion Picture Theaters
    7841: cat.ENTERTAINMENT,  # DVD / Video Tape Rental Stores
    7922: cat.ENTERTAINMENT,  # Theatrical Ticket Agencies
    7929: cat.ENTERTAINMENT,  # Bands, Orchestras, Misc Entertainers
    7932: cat.ENTERTAINMENT,  # Billiard and Pool Establishments
    7933: cat.ENTERTAINMENT,  # Bowling Alleys
    7941: cat.ENTERTAINMENT,  # Commercial Sports, Arenas
    7991: cat.ENTERTAINMENT,  # Tourist Attractions and Exhibits
    7992: cat.ENTERTAINMENT,  # Golf Courses
    7993: cat.ENTERTAINMENT,  # Video Amusement Game Supplies
    7994: cat.ENTERTAINMENT,  # Video Game Arcades
    7995: cat.ENTERTAINMENT,  # Betting, Casino, Gambling
    7996: cat.ENTERTAINMENT,  # Amusement Parks, Circuses, Fairs
    7997: cat.ENTERTAINMENT,  # Country and Athletic Clubs
    7998: cat.ENTERTAINMENT,  # Aquariums, Seaquariums, Zoos
    7999: cat.ENTERTAINMENT,  # Amusement and Recreation NEC
    # ------------------------------------------------------------------
    # Travel — hotels, airlines, travel agencies, cruises
    # ------------------------------------------------------------------
    4411: cat.TRAVEL,  # Cruise Lines
    4511: cat.TRAVEL,  # Airlines and Air Carriers
    4722: cat.TRAVEL,  # Travel Agencies and Tour Operators
    7011: cat.TRAVEL,  # Hotels and Motels
    7012: cat.TRAVEL,  # Timeshares
    7032: cat.TRAVEL,  # Sporting and Recreational Camps
    7033: cat.TRAVEL,  # Trailer Parks and Campgrounds
    # ------------------------------------------------------------------
    # Subscriptions — software, streaming, digital services
    # ------------------------------------------------------------------
    4816: cat.SUBSCRIPTIONS,  # Computer Network Services (internet/SaaS)
    5734: cat.SUBSCRIPTIONS,  # Computer Software Stores
    5735: cat.SUBSCRIPTIONS,  # Record Stores (music)
    7372: cat.SUBSCRIPTIONS,  # Computer Programming and Data Processing
    7374: cat.SUBSCRIPTIONS,  # Computer Processing and Data Prep
    7375: cat.SUBSCRIPTIONS,  # Information Retrieval Services
    7379: cat.SUBSCRIPTIONS,  # Computer Maintenance and Repair NEC
    # ------------------------------------------------------------------
    # Utilities — electricity, gas, water, heating, telecom
    # ------------------------------------------------------------------
    4814: cat.UTILITIES,  # Telephone Services (mobile, landline)
    4899: cat.UTILITIES,  # Cable, Satellite, and Pay TV
    4900: cat.UTILITIES,  # Utilities — General
    4911: cat.UTILITIES,  # Electric Companies, Power Utilities
    4924: cat.UTILITIES,  # Gas Distribution
    4931: cat.UTILITIES,  # Combined Electric and Gas Utilities
    4941: cat.UTILITIES,  # Water Supply
    4961: cat.UTILITIES,  # Heating Oil, Propane
    4991: cat.UTILITIES,  # Utilities NEC
    # ------------------------------------------------------------------
    # ATM & Cash — withdrawals, cash advances
    # ------------------------------------------------------------------
    6010: cat.ATM_CASH,  # Financial Institutions — Manual Cash Disbursements
    6011: cat.ATM_CASH,  # Financial Institutions — Automated Cash (ATM)
    6051: cat.ATM_CASH,  # Non-Financial Institutions — Money Transfer, Crypto
    # ------------------------------------------------------------------
    # Finance — banking fees, insurance, financial services
    # ------------------------------------------------------------------
    6012: cat.FINANCE,  # Financial Institutions — Merchandise and Services
    6099: cat.FINANCE,  # Financial Services NEC
    6300: cat.FINANCE,  # Insurance Sales
    6381: cat.FINANCE,  # Insurance Premium Payments
    6399: cat.FINANCE,  # Insurance NEC
    # ------------------------------------------------------------------
    # Education — schools, universities, courses
    # ------------------------------------------------------------------
    8220: cat.EDUCATION,  # Colleges, Universities, Professional Schools
    8241: cat.EDUCATION,  # Correspondence Schools
    8244: cat.EDUCATION,  # Business and Secretarial Schools
    8249: cat.EDUCATION,  # Trade and Vocational Schools
    8299: cat.EDUCATION,  # Schools and Educational Services NEC
    # ------------------------------------------------------------------
    # Pets — vets, pet shops
    # ------------------------------------------------------------------
    742: cat.PETS,  # Veterinary Services for Livestock
    5995: cat.PETS,  # Pet Shops, Pet Food, and Pet Supplies
}

# ---------------------------------------------------------------------------
# Range additions - large uniform blocks (airlines, car rentals, hotels)
# ---------------------------------------------------------------------------
# MCC 3000-3299: individual airline company codes (United, Delta, KLM, etc.)
# MCC 3300-3499: car rental company codes (Hertz, Avis, Budget, etc.)
# MCC 3500-3826: lodging/hotel chain codes (Hilton, Marriott, etc.)

MCC_LOOKUP: dict[int, str] = {
    **_BASE,
    **{mcc: cat.TRAVEL for mcc in range(3000, 3300)},
    **{mcc: cat.TRANSPORTATION for mcc in range(3300, 3500)},
    **{mcc: cat.TRAVEL for mcc in range(3500, 3827)},
}

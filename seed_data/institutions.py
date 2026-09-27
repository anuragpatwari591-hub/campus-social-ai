"""
Seed list for the global college directory.

Each tuple is:
    (name, short_name, institution_type, country, region, city, [aliases])

This is not an exhaustive list of every college in the world -- the schema
(Country -> Region -> City -> Institution -> Campus, plus InstitutionAlias)
is designed so more institutions can be imported later from an official
dataset (e.g. AISHE for India, IPEDS for the US) without any schema change.
"""

INSTITUTIONS = [
    # --- India: IITs ---
    ("Indian Institute of Technology Kharagpur", "IIT Kharagpur", "IIT", "India", "West Bengal", "Kharagpur", ["IIT KGP", "IITKGP"]),
    ("Indian Institute of Technology Bombay", "IIT Bombay", "IIT", "India", "Maharashtra", "Mumbai", ["IITB", "IIT Powai"]),
    ("Indian Institute of Technology Delhi", "IIT Delhi", "IIT", "India", "Delhi", "New Delhi", ["IITD"]),
    ("Indian Institute of Technology Madras", "IIT Madras", "IIT", "India", "Tamil Nadu", "Chennai", ["IITM"]),
    ("Indian Institute of Technology Kanpur", "IIT Kanpur", "IIT", "India", "Uttar Pradesh", "Kanpur", ["IITK"]),
    ("Indian Institute of Technology Roorkee", "IIT Roorkee", "IIT", "India", "Uttarakhand", "Roorkee", ["IITR"]),
    ("Indian Institute of Technology Guwahati", "IIT Guwahati", "IIT", "India", "Assam", "Guwahati", ["IITG"]),

    # --- Kolkata / West Bengal cluster (from spec) ---
    ("Institute of Engineering and Management", "IEM Kolkata", "private", "India", "West Bengal", "Kolkata", ["IEM"]),
    ("Jadavpur University", "JU", "state", "India", "West Bengal", "Kolkata", []),
    ("University of Calcutta", "CU", "state", "India", "West Bengal", "Kolkata", ["Calcutta University"]),
    ("Indian Institute of Management Calcutta", "IIM Calcutta", "IIM", "India", "West Bengal", "Kolkata", ["IIM-C", "IIMC"]),
    ("Indian Statistical Institute", "ISI Kolkata", "central", "India", "West Bengal", "Kolkata", ["ISI"]),
    ("Heritage Institute of Technology", "HIT Kolkata", "private", "India", "West Bengal", "Kolkata", ["Heritage"]),
    ("Techno India University", "Techno India", "private", "India", "West Bengal", "Kolkata", []),
    ("Maulana Abul Kalam Azad University of Technology", "MAKAUT", "state", "India", "West Bengal", "Haringhata", ["WBUT"]),
    ("Presidency University Kolkata", "Presidency University", "state", "India", "West Bengal", "Kolkata", []),
    ("St. Xavier's College Kolkata", "St. Xavier's Kolkata", "private", "India", "West Bengal", "Kolkata", []),

    # --- Other major Indian institutions ---
    ("Indian Institute of Science", "IISc Bangalore", "central", "India", "Karnataka", "Bengaluru", ["IISc"]),
    ("National Institute of Technology Tiruchirappalli", "NIT Trichy", "NIT", "India", "Tamil Nadu", "Tiruchirappalli", ["NITT"]),
    ("National Institute of Technology Karnataka", "NIT Surathkal", "NIT", "India", "Karnataka", "Mangalore", ["NITK"]),
    ("International Institute of Information Technology Hyderabad", "IIIT Hyderabad", "IIIT", "India", "Telangana", "Hyderabad", ["IIIT-H"]),
    ("Indian Institute of Management Ahmedabad", "IIM Ahmedabad", "IIM", "India", "Gujarat", "Ahmedabad", ["IIM-A"]),
    ("University of Delhi", "Delhi University", "central", "India", "Delhi", "New Delhi", ["DU"]),
    ("Birla Institute of Technology and Science Pilani", "BITS Pilani", "private", "India", "Rajasthan", "Pilani", ["BITS"]),
    ("Vellore Institute of Technology", "VIT Vellore", "private", "India", "Tamil Nadu", "Vellore", ["VIT"]),
    ("Anna University", "Anna University", "state", "India", "Tamil Nadu", "Chennai", []),
    ("Manipal Academy of Higher Education", "MAHE", "private", "India", "Karnataka", "Manipal", ["Manipal University"]),

    # --- International ---
    ("Massachusetts Institute of Technology", "MIT", "private", "United States", "Massachusetts", "Cambridge", []),
    ("Stanford University", "Stanford", "private", "United States", "California", "Stanford", []),
    ("Harvard University", "Harvard", "private", "United States", "Massachusetts", "Cambridge", []),
    ("Yale University", "Yale", "private", "United States", "Connecticut", "New Haven", []),
    ("Princeton University", "Princeton", "private", "United States", "New Jersey", "Princeton", []),
    ("Columbia University", "Columbia", "private", "United States", "New York", "New York City", []),
    ("Cornell University", "Cornell", "private", "United States", "New York", "Ithaca", []),
    ("California Institute of Technology", "Caltech", "private", "United States", "California", "Pasadena", []),
    ("University of California, Berkeley", "UC Berkeley", "state", "United States", "California", "Berkeley", ["Berkeley"]),
    ("University of California, Los Angeles", "UCLA", "state", "United States", "California", "Los Angeles", []),
    ("University of Chicago", "UChicago", "private", "United States", "Illinois", "Chicago", []),
    ("Carnegie Mellon University", "CMU", "private", "United States", "Pennsylvania", "Pittsburgh", []),
    ("University of Oxford", "Oxford", "public", "United Kingdom", "England", "Oxford", []),
    ("University of Cambridge", "Cambridge", "public", "United Kingdom", "England", "Cambridge", []),
    ("Imperial College London", "Imperial", "public", "United Kingdom", "England", "London", []),
    ("University College London", "UCL", "public", "United Kingdom", "England", "London", []),
    ("University of Edinburgh", "Edinburgh", "public", "United Kingdom", "Scotland", "Edinburgh", []),
    ("University of Toronto", "U of T", "public", "Canada", "Ontario", "Toronto", ["UofT"]),
    ("University of British Columbia", "UBC", "public", "Canada", "British Columbia", "Vancouver", []),
    ("McGill University", "McGill", "public", "Canada", "Quebec", "Montreal", []),
    ("University of Melbourne", "Melbourne", "public", "Australia", "Victoria", "Melbourne", []),
    ("University of Sydney", "Sydney", "public", "Australia", "New South Wales", "Sydney", []),
    ("Australian National University", "ANU", "public", "Australia", "Australian Capital Territory", "Canberra", []),
    ("National University of Singapore", "NUS", "public", "Singapore", "Central Region", "Singapore", []),
    ("Nanyang Technological University", "NTU", "public", "Singapore", "West Region", "Singapore", []),
    ("University of Tokyo", "UTokyo", "public", "Japan", "Kanto", "Tokyo", []),
    ("Kyoto University", "Kyoto U", "public", "Japan", "Kansai", "Kyoto", []),
    ("Korea Advanced Institute of Science and Technology", "KAIST", "public", "South Korea", "Daejeon", "Daejeon", []),
    ("Seoul National University", "SNU", "public", "South Korea", "Seoul", "Seoul", []),
    ("Tsinghua University", "Tsinghua", "public", "China", "Beijing", "Beijing", []),
    ("Peking University", "PKU", "public", "China", "Beijing", "Beijing", []),
    ("ETH Zurich", "ETH Zurich", "public", "Switzerland", "Zurich", "Zurich", []),
    ("EPFL", "EPFL", "public", "Switzerland", "Vaud", "Lausanne", ["Ecole Polytechnique Federale de Lausanne"]),
    ("Technical University of Munich", "TUM", "public", "Germany", "Bavaria", "Munich", []),
    ("University of Amsterdam", "UvA", "public", "Netherlands", "North Holland", "Amsterdam", []),
    ("Delft University of Technology", "TU Delft", "public", "Netherlands", "South Holland", "Delft", []),
]

COUNTRY_CODES = {
    "India": "IND", "United States": "USA", "United Kingdom": "GBR", "Canada": "CAN",
    "Australia": "AUS", "Singapore": "SGP", "Japan": "JPN", "South Korea": "KOR",
    "China": "CHN", "Switzerland": "CHE", "Germany": "DEU", "Netherlands": "NLD",
}

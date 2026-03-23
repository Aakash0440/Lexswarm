# intake/classifier.py
# Multilingual case intake — detects language, jurisdiction, case type, urgency
# Supports 80+ countries with native script city detection
# No API key required for core classification

import re
import uuid
from datetime import datetime, timezone
from intake.base import LegalCase, CaseType, UrgencyLevel, CaseStatus


NATIVE_SCRIPT_CITIES = {
    "اسلام آباد": "PK", "کراچی": "PK", "لاہور": "PK", "پشاور": "PK",
    "کوئٹہ": "PK", "فیصل آباد": "PK", "راولپنڈی": "PK", "ملتان": "PK",
    "حیدرآباد": "PK", "گوجرانوالہ": "PK", "سیالکوٹ": "PK", "بہاولپور": "PK",
    "پاکستان": "PK",
    "ঢাকা": "BD", "চট্টগ্রাম": "BD", "সিলেট": "BD", "রাজশাহী": "BD",
    "খুলনা": "BD", "বরিশাল": "BD", "কক্সবাজার": "BD", "ময়মনসিংহ": "BD",
    "নারায়ণগঞ্জ": "BD", "গাজীপুর": "BD", "বাংলাদেশ": "BD",
    "কলকাতা": "IN", "দার্জিলিং": "IN",
    "दिल्ली": "IN", "नई दिल्ली": "IN", "मुंबई": "IN", "बेंगलुरु": "IN",
    "कोलकाता": "IN", "चेन्नई": "IN", "हैदराबाद": "IN", "पुणे": "IN",
    "अहमदाबाद": "IN", "जयपुर": "IN", "सूरत": "IN", "लखनऊ": "IN",
    "कानपुर": "IN", "नागपुर": "IN", "पटना": "IN", "इंदौर": "IN",
    "भोपाल": "IN", "विशाखापट्टनम": "IN", "भारत": "IN",
    "الرياض": "SA", "جدة": "SA", "مكة": "SA", "المدينة": "SA",
    "الدمام": "SA", "الخبر": "SA", "تبوك": "SA", "أبها": "SA",
    "المملكة العربية السعودية": "SA",
    "دبي": "AE", "أبوظبي": "AE", "الشارقة": "AE", "عجمان": "AE",
    "رأس الخيمة": "AE", "الفجيرة": "AE", "الإمارات": "AE",
    "القاهرة": "EG", "الإسكندرية": "EG", "الجيزة": "EG",
    "الإسماعيلية": "EG", "بورسعيد": "EG", "مصر": "EG",
    "بغداد": "IQ", "البصرة": "IQ", "الموصل": "IQ",
    "أربيل": "IQ", "النجف": "IQ", "كربلاء": "IQ",
    "عمّان": "JO", "الزرقاء": "JO", "إربد": "JO",
    "بيروت": "LB", "طرابلس": "LB", "صيدا": "LB",
    "الرباط": "MA", "الدار البيضاء": "MA", "مراكش": "MA",
    "فاس": "MA", "أكادير": "MA", "المغرب": "MA",
    "الجزائر": "DZ", "وهران": "DZ", "قسنطينة": "DZ",
    "تونس": "TN", "صفاقس": "TN", "سوسة": "TN",
    "طرابلس": "LY", "بنغازي": "LY",
    "الخرطوم": "SD", "أم درمان": "SD", "بورتسودان": "SD",
    "دمشق": "SY", "حلب": "SY", "حمص": "SY", "اللاذقية": "SY",
    "صنعاء": "YE", "عدن": "YE", "تعز": "YE",
    "الكويت": "KW", "الدوحة": "QA", "المنامة": "BH",
    "مسقط": "OM", "صلالة": "OM",
    "غزة": "PS", "رام الله": "PS", "الضفة الغربية": "PS",
    "تهران": "IR", "مشهد": "IR", "اصفهان": "IR",
    "تبریز": "IR", "شیراز": "IR", "اهواز": "IR", "ایران": "IR",
    "کابل": "AF", "قندهار": "AF", "هرات": "AF",
    "مزار شریف": "AF", "افغانستان": "AF",
    "İstanbul": "TR", "Ankara": "TR", "İzmir": "TR", "Bursa": "TR",
    "Adana": "TR", "Antalya": "TR", "Gaziantep": "TR", "Konya": "TR",
    "Türkiye": "TR",
    "Москва": "RU", "Санкт-Петербург": "RU", "Новосибирск": "RU",
    "Екатеринбург": "RU", "Казань": "RU", "Нижний Новгород": "RU",
    "Красноярск": "RU", "Россия": "RU",
    "Київ": "UA", "Харків": "UA", "Одеса": "UA", "Дніпро": "UA",
    "Запоріжжя": "UA", "Львів": "UA", "Україна": "UA",
    "Мінск": "BY", "Гомель": "BY",
    "Алматы": "KZ", "Астана": "KZ", "Шымкент": "KZ",
    "Ташкент": "UZ", "Самарқанд": "UZ", "Наманган": "UZ",
    "北京": "CN", "上海": "CN", "广州": "CN", "深圳": "CN", "成都": "CN",
    "武汉": "CN", "西安": "CN", "重庆": "CN", "杭州": "CN", "南京": "CN",
    "天津": "CN", "中国": "CN", "香港": "HK", "台北": "TW", "高雄": "TW",
    "澳門": "MO",
    "東京": "JP", "大阪": "JP", "名古屋": "JP", "札幌": "JP", "福岡": "JP",
    "神戸": "JP", "京都": "JP", "横浜": "JP", "日本": "JP",
    "서울": "KR", "부산": "KR", "인천": "KR", "대구": "KR",
    "대전": "KR", "광주": "KR", "한국": "KR",
    "กรุงเทพ": "TH", "เชียงใหม่": "TH", "พัทยา": "TH", "ภูเก็ต": "TH",
    "ไทย": "TH",
    "Hà Nội": "VN", "Hồ Chí Minh": "VN", "Đà Nẵng": "VN",
    "Cần Thơ": "VN", "Việt Nam": "VN",
    "Jakarta": "ID", "Surabaya": "ID", "Bandung": "ID", "Medan": "ID",
    "Semarang": "ID", "Makassar": "ID", "Palembang": "ID", "Tangerang": "ID",
    "Depok": "ID", "Bekasi": "ID", "Indonesia": "ID",
    "Maynila": "PH", "Cebu": "PH", "Davao": "PH", "Quezon City": "PH",
    "Zamboanga": "PH", "Antipolo": "PH", "Pilipinas": "PH",
    "Nairobi": "KE", "Mombasa": "KE", "Kisumu": "KE",
    "Nakuru": "KE", "Eldoret": "KE",
    "Dar es Salaam": "TZ", "Dodoma": "TZ", "Zanzibar": "TZ",
    "Mwanza": "TZ", "Arusha": "TZ",
    "Kampala": "UG", "Gulu": "UG", "Mbarara": "UG",
    "አዲስ አበባ": "ET", "ድሬዳዋ": "ET", "ጎንደር": "ET", "ሐዋሳ": "ET",
    "ኢትዮጵያ": "ET",
    "ኣስመራ": "ER",
    "Muqdisho": "SO", "Hargeysa": "SO", "Berbera": "SO",
    "eThekwini": "ZA", "iGoli": "ZA", "eGoli": "ZA", "iKapa": "ZA",
    "eKapa": "ZA", "iNingizimu Afrika": "ZA", "eNingizimu Afrika": "ZA",
    "uMgungundlovu": "ZA", "eMalahleni": "ZA", "Tshwane": "ZA",
    "Johannesburg": "ZA", "Cape Town": "ZA", "Durban": "ZA",
    "Pretoria": "ZA", "Port Elizabeth": "ZA", "Bloemfontein": "ZA",
    "Èkó": "NG", "Abuja": "NG", "Lagos": "NG", "Kano": "NG",
    "Ibadan": "NG", "Port Harcourt": "NG", "Benin City": "NG",
    "Enugu": "NG", "Kaduna": "NG", "Aba": "NG",
    "Accra": "GH", "Kumasi": "GH", "Tamale": "GH", "Sekondi": "GH",
    "Kigali": "RW", "Butare": "RW",
    "Bujumbura": "BI", "Gitega": "BI",
    "Paris": "FR", "Lyon": "FR", "Marseille": "FR", "Toulouse": "FR",
    "Nice": "FR", "Bordeaux": "FR", "Lille": "FR", "Strasbourg": "FR",
    "Montréal": "CA", "Québec": "CA",
    "Dakar": "SN", "Abidjan": "CI", "Bamako": "ML", "Ouagadougou": "BF",
    "Lomé": "TG", "Cotonou": "BJ", "Niamey": "NE", "N'Djamena": "TD",
    "Kinshasa": "CD", "Lubumbashi": "CD", "Brazzaville": "CG",
    "Libreville": "GA", "Yaoundé": "CM", "Douala": "CM", "Bangui": "CF",
    "Conakry": "GN", "Bissau": "GW", "Nouakchott": "MR",
    "Antananarivo": "MG",
    "São Paulo": "BR", "Rio de Janeiro": "BR", "Brasília": "BR",
    "Salvador": "BR", "Fortaleza": "BR", "Belo Horizonte": "BR",
    "Manaus": "BR", "Curitiba": "BR", "Recife": "BR", "Porto Alegre": "BR",
    "Brasil": "BR",
    "Lisboa": "PT", "Porto": "PT", "Coimbra": "PT",
    "Maputo": "MZ", "Beira": "MZ", "Luanda": "AO", "Huambo": "AO",
    "Praia": "CV",
    "Madrid": "ES", "Barcelona": "ES", "Valencia": "ES", "Sevilla": "ES",
    "Zaragoza": "ES", "Bilbao": "ES",
    "Ciudad de México": "MX", "Guadalajara": "MX", "Monterrey": "MX",
    "Puebla": "MX", "Tijuana": "MX", "Ciudad Juárez": "MX",
    "Bogotá": "CO", "Medellín": "CO", "Cali": "CO",
    "Barranquilla": "CO", "Cartagena": "CO",
    "Buenos Aires": "AR", "Córdoba": "AR", "Rosario": "AR", "Mendoza": "AR",
    "Lima": "PE", "Arequipa": "PE", "Trujillo": "PE",
    "Caracas": "VE", "Maracaibo": "VE",
    "Santiago": "CL", "Valparaíso": "CL",
    "Quito": "EC", "Guayaquil": "EC", "La Paz": "BO", "Santa Cruz": "BO",
    "Asunción": "PY", "Montevideo": "UY",
    "San José": "CR", "Ciudad de Guatemala": "GT", "Tegucigalpa": "HN",
    "San Pedro Sula": "HN", "Managua": "NI", "San Salvador": "SV",
    "Panamá": "PA", "Santo Domingo": "DO", "La Habana": "CU",
    "San Juan": "PR",
    "Αθήνα": "GR", "Θεσσαλονίκη": "GR", "Πειραιάς": "GR", "Ελλάδα": "GR",
    "תל אביב": "IL", "ירושלים": "IL", "חיפה": "IL", "באר שבע": "IL",
    "ישראל": "IL",
    "කොළඹ": "LK", "ගම්පහ": "LK", "ශ්‍රී ලංකා": "LK",
    "கொழும்பு": "LK", "சென்னை": "IN", "கோயம்புத்தூர்": "IN",
    "ရန်ကုန်": "MM", "နေပြည်တော်": "MM", "မန္တလေး": "MM",
    "မြန်မာ": "MM", "Rakhine": "MM",
    "ភ្នំពេញ": "KH", "សៀមរាប": "KH", "កម្ពុជា": "KH",
    "ວຽງຈັນ": "LA", "ລາວ": "LA",
    "काठमाडौं": "NP", "पोखरा": "NP", "ललितपुर": "NP", "नेपाल": "NP",
    "މާލެ": "MV",
    "Cox's Bazar": "BD", "Teknaf": "BD", "Ukhiya": "BD",
    "Bakı": "AZ", "Gəncə": "AZ",
    "Երևան": "AM",
    "თბილისი": "GE", "ბათუმი": "GE",
    "București": "RO", "Cluj-Napoca": "RO",
    "Warszawa": "PL", "Kraków": "PL", "Gdańsk": "PL",
    "Praha": "CZ", "Brno": "CZ",
    "Budapest": "HU", "Debrecen": "HU",
    "Beograd": "RS", "Novi Sad": "RS", "Zagreb": "HR", "Split": "HR",
    "София": "BG", "Пловдив": "BG",
    "Amsterdam": "NL", "Rotterdam": "NL", "Den Haag": "NL",
    "Utrecht": "NL", "Eindhoven": "NL", "Groningen": "NL",
    "Stockholm": "SE", "Göteborg": "SE",
    "Oslo": "NO", "Bergen": "NO",
    "København": "DK", "Aarhus": "DK",
    "Helsinki": "FI", "Tampere": "FI",
    "Berlin": "DE", "München": "DE", "Hamburg": "DE", "Frankfurt": "DE",
    "Köln": "DE", "Stuttgart": "DE", "Düsseldorf": "DE", "Leipzig": "DE",
    "Roma": "IT", "Milano": "IT", "Napoli": "IT", "Torino": "IT",
    "Palermo": "IT",
    "Harare": "ZW", "Bulawayo": "ZW",
    "Lusaka": "ZM", "Ndola": "ZM",
    "Lilongwe": "MW", "Blantyre": "MW",
    "Gaborone": "BW",
    "Windhoek": "NA",
}


JURISDICTION_HINTS = {
    "PK": ["pakistan", "lahore", "karachi", "islamabad", "peshawar", "quetta",
           "faisalabad", "rawalpindi", "multan", "sialkot", "gujranwala",
           "pakistani", "rupees", "pkr"],
    "IN": ["india", "delhi", "mumbai", "bangalore", "kolkata", "chennai",
           "hyderabad", "pune", "ahmedabad", "jaipur", "surat", "lucknow",
           "indian court", "rupees", "inr", "high court", "district court"],
    "ID": ["indonesia", "jakarta", "surabaya", "bandung", "medan", "semarang",
           "makassar", "tangerang", "bekasi", "pengadilan", "indonesian", "rupiah"],
    "US": ["united states", "america", "new york", "los angeles", "chicago",
           "houston", "atlanta", "california", "texas", "florida", "illinois",
           "federal court", "section 1983", "usd", "dollars"],
    "GB": ["england", "wales", "scotland", "uk", "united kingdom", "british",
           "london", "manchester", "birmingham", "leeds", "glasgow", "edinburgh",
           "crown court", "pounds", "gbp", "housing benefit"],
    "NG": ["nigeria", "lagos", "abuja", "port harcourt", "kano", "ibadan",
           "enugu", "benin city", "kaduna", "aba", "nigerian", "naira"],
    "BD": ["bangladesh", "dhaka", "chittagong", "sylhet", "rajshahi", "khulna",
           "bangladeshi", "cox's bazar", "teknaf", "taka", "garment"],
    "ZA": ["south africa", "cape town", "johannesburg", "durban", "pretoria",
           "south african", "rand", "zar", "ekapa", "ethekwini", "igoli",
           "egoli", "ikapa", "ningizimu afrika", "mzansi",
           "umnikazi", "indlu", "abantwana"],
    "KE": ["kenya", "nairobi", "mombasa", "kisumu", "nakuru", "eldoret",
           "kenyan", "shilling", "kes"],
    "CA": ["canada", "toronto", "montreal", "vancouver", "ottawa", "calgary",
           "edmonton", "winnipeg", "canadian", "ontario", "british columbia",
           "quebec", "alberta"],
    "PH": ["philippines", "manila", "cebu", "davao", "quezon", "philippine",
           "filipino", "peso", "php", "ofw", "poea"],
    "SA": ["saudi arabia", "riyadh", "jeddah", "mecca", "medina", "saudi",
           "kafala", "sar"],
    "AE": ["uae", "dubai", "abu dhabi", "sharjah", "emirates",
           "united arab emirates", "aed", "dirhams"],
    "EG": ["egypt", "cairo", "alexandria", "egyptian", "egp"],
    "MM": ["myanmar", "burma", "yangon", "rangoon", "mandalay", "rakhine",
           "burmese", "rohingya"],
    "ET": ["ethiopia", "addis ababa", "ethiopian", "birr"],
    "CN": ["china", "beijing", "shanghai", "guangzhou", "shenzhen", "chinese",
           "yuan", "rmb", "cny"],
    "JP": ["japan", "tokyo", "osaka", "nagoya", "sapporo", "japanese", "yen"],
    "KR": ["south korea", "korea", "seoul", "busan", "incheon", "korean", "won"],
    "TH": ["thailand", "bangkok", "chiang mai", "thai", "baht"],
    "VN": ["vietnam", "hanoi", "ho chi minh", "saigon", "vietnamese", "dong"],
    "BR": ["brazil", "brasil", "sao paulo", "rio de janeiro", "brasilia",
           "brazilian", "real", "brl"],
    "MX": ["mexico", "ciudad de mexico", "guadalajara", "monterrey", "mexican",
           "peso", "mxn"],
    "AR": ["argentina", "buenos aires", "cordoba", "rosario", "argentinian",
           "peso", "ars"],
    "CO": ["colombia", "bogota", "medellin", "cali", "colombian", "peso"],
    "PE": ["peru", "lima", "arequipa", "peruvian", "sol"],
    "VE": ["venezuela", "caracas", "maracaibo", "venezuelan", "bolivar"],
    "CL": ["chile", "santiago", "valparaiso", "chilean", "peso"],
    "TR": ["turkey", "istanbul", "ankara", "izmir", "turkish", "lira", "try"],
    "IR": ["iran", "tehran", "mashhad", "isfahan", "iranian", "farsi", "rial"],
    "IQ": ["iraq", "baghdad", "basra", "mosul", "iraqi", "dinar"],
    "SY": ["syria", "damascus", "aleppo", "syrian", "pound"],
    "AF": ["afghanistan", "kabul", "kandahar", "herat", "afghan", "afghani",
           "taliban"],
    "LK": ["sri lanka", "colombo", "sinhala", "tamil", "rupee"],
    "NP": ["nepal", "kathmandu", "nepali", "rupee"],
    "KH": ["cambodia", "phnom penh", "khmer", "riel"],
    "GH": ["ghana", "accra", "kumasi", "ghanaian", "cedi"],
    "SN": ["senegal", "dakar", "senegalese", "franc"],
    "CI": ["ivory coast", "cote d'ivoire", "abidjan", "franc"],
    "CD": ["congo", "kinshasa", "democratic republic", "drc", "franc"],
    "MZ": ["mozambique", "maputo", "metical"],
    "AO": ["angola", "luanda", "kwanza"],
    "ZW": ["zimbabwe", "harare", "bulawayo", "zimbabwean"],
    "ZM": ["zambia", "lusaka", "zambian", "kwacha"],
    "UG": ["uganda", "kampala", "ugandan", "shilling"],
    "TZ": ["tanzania", "dar es salaam", "tanzanian", "shilling"],
    "RW": ["rwanda", "kigali", "rwandan", "franc"],
    "SO": ["somalia", "mogadishu", "somali", "shilling"],
    "PT": ["portugal", "lisboa", "lisbon", "porto", "portuguese"],
    "ES": ["spain", "madrid", "barcelona", "spanish"],
    "FR": ["france", "paris", "lyon", "marseille", "french"],
    "DE": ["germany", "berlin", "munich", "hamburg", "frankfurt", "german",
           "deutschland", "arbeitgeber", "miete", "münchen", "köln"],
    "IT": ["italy", "rome", "milan", "naples", "italian"],
    "RU": ["russia", "moscow", "saint petersburg", "russian", "ruble"],
    "UA": ["ukraine", "kyiv", "kharkiv", "odessa", "ukrainian"],
    "IL": ["israel", "tel aviv", "jerusalem", "haifa", "israeli", "shekel"],
    "GR": ["greece", "athens", "thessaloniki", "greek", "euro"],
    "MA": ["morocco", "rabat", "casablanca", "marrakech", "moroccan", "dirham"],
    "KZ": ["kazakhstan", "almaty", "astana", "kazakh", "tenge"],
    "UZ": ["uzbekistan", "tashkent", "uzbek", "sum"],
    "NL": ["netherlands", "amsterdam", "rotterdam", "den haag", "utrecht",
           "eindhoven", "dutch", "holland", "nederland", "nederlanden",
           "werkgever", "huurder", "verhuurder", "politie", "groningen"],
    "BE": ["belgium", "brussels", "bruxelles", "belgian", "antwerp", "gent"],
    "SE": ["sweden", "stockholm", "gothenburg", "swedish", "krona", "malmö"],
    "NO": ["norway", "oslo", "norwegian", "krone", "bergen"],
    "DK": ["denmark", "copenhagen", "danish", "krone", "aarhus"],
    "FI": ["finland", "helsinki", "finnish", "euro", "tampere"],
    "PL": ["poland", "warsaw", "krakow", "polish", "zloty", "gdansk"],
    "RO": ["romania", "bucharest", "romanian", "leu", "cluj"],
    "HU": ["hungary", "budapest", "hungarian", "forint"],
    "RS": ["serbia", "belgrade", "serbian", "dinar"],
    "HR": ["croatia", "zagreb", "croatian"],
    "BG": ["bulgaria", "sofia", "bulgarian", "lev"],
    "JO": ["jordan", "amman", "jordanian", "dinar"],
    "LB": ["lebanon", "beirut", "lebanese", "pound"],
    "KW": ["kuwait", "kuwaiti", "dinar"],
    "QA": ["qatar", "doha", "qatari", "riyal"],
    "BH": ["bahrain", "manama", "bahraini", "dinar"],
    "OM": ["oman", "muscat", "omani", "rial"],
    "PS": ["palestine", "gaza", "west bank", "ramallah", "palestinian"],
    "AZ": ["azerbaijan", "baku", "azerbaijani", "manat"],
    "AM": ["armenia", "yerevan", "armenian", "dram"],
    "GE": ["georgia", "tbilisi", "georgian", "lari"],
    "BW": ["botswana", "gaborone", "batswana", "pula"],
    "NA": ["namibia", "windhoek", "namibian", "dollar"],
    "MW": ["malawi", "lilongwe", "blantyre", "malawian", "kwacha"],
}


CASE_TYPE_KEYWORDS = {
    CaseType.HOUSING: [
        "evict", "eviction", "landlord", "tenant", "rent", "lease", "lockout",
        "lock changed", "locks changed", "threw my belongings", "nowhere to sleep",
        "nowhere to live", "habitability", "deposit", "notice to quit",
        "mortgage", "foreclosure", "illegal entry", "forced out", "kicked out",
        "no running water", "no electricity", "mold", "uninhabitable",
        "section 8", "housing benefit", "council flat", "public housing",
        # Dutch
        "verhuurder", "huurder", "huur", "uitzetting", "buitengezet",
        "huurcontract", "borg", "huurwoning", "woning", "huurprijs",
        # German
        "vermieter", "mieter", "miete", "kündigung", "räumung", "wohnung",
        # Urdu
        "مالک مکان", "کرایہ", "بے دخلی", "تالہ", "گھر سے نکال",
        # Bengali
        "বাড়িওয়ালা", "ভাড়া", "উচ্ছেদ", "তালা", "বাড়ি থেকে বের",
        # Hindi
        "मकान मालिक", "किराया", "बेदखल", "घर से निकाल",
        # Arabic
        "مالك العقار", "إيجار", "إخلاء", "طرد من المنزل",
        # Indonesian
        "sewa", "penggusuran", "pemilik rumah", "dikosongkan", "diusir",
        # Swahili
        "mwenye nyumba", "kodi", "kufukuzwa nyumba", "kupigwa nje",
        # French
        "propriétaire", "loyer", "expulsion", "logement", "locataire",
        # Spanish
        "arrendador", "alquiler", "desalojo", "inquilino", "propietario",
        # Portuguese
        "senhorio", "aluguel", "despejo", "inquilino",
        # Russian
        "арендодатель", "аренда", "выселение", "квартира",
        # Zulu/Xhosa
        "umnikazi wendlu", "ikhaya", "ukukhishwa",
        # Yoruba
        "onile", "iyalo",
        # Turkish
        "ev sahibi", "kira", "tahliye",
    ],
    CaseType.CRIMINAL: [
        "arrest", "arrested", "police", "charge", "criminal", "prison", "jail",
        "bail", "accused", "sentence", "detention", "detained", "custody",
        "interrogation", "absconding", "warrant", "handcuffed", "locked up",
        "police brutality", "false arrest", "wrongful conviction",
        # Dutch
        "arrestatie", "gearresteerd", "politie", "gevangenis", "aangehouden",
        "hechtenis", "borg", "beschuldigd", "celstraf",
        # German
        "verhaftet", "polizei", "gefängnis", "festgenommen", "haft",
        # Urdu
        "گرفتار", "پولیس", "حراست", "ضمانت", "جیل", "قید",
        # Bengali
        "গ্রেফতার", "পুলিশ", "আটক", "জেল", "কারাগার",
        # Hindi
        "गिरफ्तार", "पुलिस", "हिरासत", "जेल", "कारागार",
        # Arabic
        "اعتقال", "شرطة", "احتجاز", "سجن", "كفالة",
        # Indonesian
        "ditahan", "polisi", "ditangkap", "penjara", "penahanan",
        # Swahili
        "kukamatwa", "polisi", "kizuizini", "gerezani", "dhamana",
        # French
        "arrestation", "police", "détention", "prison", "garde à vue",
        # Spanish
        "arresto", "policía", "detención", "prisión", "fianza",
        # Portuguese
        "prisão", "detido", "polícia", "fiança",
        # Russian
        "арест", "полиция", "задержание", "тюрьма", "залог",
        # Turkish
        "tutuklandım", "polis", "gözaltı", "hapis", "kefalet",
        # Zulu
        "ukubopha", "amaphoyisa",
        # Hausa
        "daurin", "sanda",
    ],
    CaseType.LABOR: [
        "employer", "fired", "wrongful termination", "wage", "salary", "unpaid",
        "workplace", "discrimination", "harassment", "union", "overtime",
        "not paid", "haven't paid", "hasn't paid", "placement fee",
        "recruitment agency", "domestic worker", "work permit", "work visa",
        "constructive dismissal", "redundancy", "unfair dismissal",
        "minimum wage", "payslip", "employment contract",
        # Dutch — critical
        "werkgever", "werknemer", "loon", "salaris", "ontslagen", "ontslag",
        "arbeidscontract", "betaalt niet", "geen loon", "geen salaris",
        "zwart werk", "uitbetaling", "arbeidsrecht", "dienstverband",
        "cao", "minimumloon", "overwerk", "vakantiegeld", "uitgebuit",
        # German
        "arbeitgeber", "arbeitnehmer", "gehalt", "lohn", "entlassen",
        "kündigung", "arbeitsvertrag", "mindestlohn", "überstunden",
        # Urdu
        "ملازمت", "تنخواہ", "ملازم", "نوکری", "برطرف", "اجرت",
        # Bengali
        "নিয়োগকর্তা", "বেতন", "চাকরি", "মজুরি", "বরখাস্ত", "ছাঁটাই",
        # Hindi
        "नियोक्ता", "वेतन", "नौकरी", "मजदूरी", "बर्खास्त",
        # Arabic
        "صاحب العمل", "راتب", "أجر", "فصل من العمل", "عمالة",
        # Indonesian
        "pemecatan", "upah", "majikan", "gaji", "PHK", "pesangon", "buruh",
        # Swahili
        "mwajiri", "mshahara", "kufukuzwa kazi", "mkataba wa kazi",
        # French
        "employeur", "salaire", "licenciement", "travailleur", "contrat",
        # Spanish
        "empleador", "salario", "despido", "trabajador", "contrato laboral",
        # Portuguese
        "empregador", "salário", "demissão", "trabalhador",
        # Russian
        "работодатель", "зарплата", "увольнение", "трудовой договор",
        # Turkish
        "işveren", "maaş", "işten çıkarma", "ücret",
        # Zulu
        "umqashi", "iholo", "ukuxoshwa",
        # Tagalog
        "employer", "sahod", "tinanggal",
    ],
    CaseType.FAMILY: [
        "divorce", "custody", "child", "domestic violence", "abuse", "alimony",
        "marriage", "husband", "wife", "children taken", "took my children",
        "took the children", "talaq", "mehr", "maintenance", "restraining order",
        "child support", "paternity", "adoption", "forced marriage",
        # Dutch
        "echtscheiding", "voogdij", "huiselijk geweld", "alimentatie",
        "kinderen meegenomen", "mishandeling", "man", "vrouw", "kinderen",
        # German
        "scheidung", "sorgerecht", "häusliche gewalt", "unterhalt",
        # Urdu
        "طلاق", "بچہ", "گھریلو تشدد", "بچے", "شوہر", "بیوی", "نان نفقہ",
        "خلع", "حضانت",
        # Bengali
        "তালাক", "সন্তান", "গৃহহিংসা", "স্বামী", "স্ত্রী", "বাচ্চা",
        # Hindi
        "तलाक", "बच्चे", "घरेलू हिंसा", "पति", "पत्नी", "गुजारा भत्ता",
        # Arabic
        "طلاق", "حضانة", "عنف أسري", "زوج", "زوجة", "نفقة", "خلع",
        # Indonesian
        "perceraian", "hak asuh", "kekerasan rumah tangga", "suami", "istri",
        "cerai", "nafkah",
        # Swahili
        "talaka", "mtoto", "ukatili wa nyumbani", "mke", "mume", "matunzo",
        # French
        "divorce", "garde", "violence conjugale", "pension alimentaire",
        # Spanish
        "divorcio", "custodia", "violencia doméstica", "pensión alimenticia",
        # Portuguese
        "divórcio", "guarda", "violência doméstica", "pensão alimentícia",
        # Russian
        "развод", "опека", "домашнее насилие", "алименты",
        # Turkish
        "boşanma", "velayet", "aile içi şiddet", "nafaka",
        # Zulu
        "ukushaywa", "abantwana", "umzali",
        # Hausa
        "saki", "yara",
    ],
    CaseType.IMMIGRATION: [
        "visa", "deportation", "deport", "asylum", "refugee", "immigration",
        "undocumented", "citizenship", "border", "stateless", "no documents",
        "passport confiscated", "kafala", "absconding charge", "work permit",
        "residence permit", "green card", "naturalization", "illegal entry",
        "overstay", "smuggled", "human trafficking",
        # Dutch
        "verblijfsvergunning", "uitzetting", "asiel", "vluchteling",
        "illegaal verblijf", "paspoort ingenomen", "paspoort afgenomen",
        "geen verblijfsvergunning", "uitgezet",
        # German
        "aufenthaltserlaubnis", "abschiebung", "asyl", "flüchtling",
        "illegaler aufenthalt", "pass beschlagnahmt",
        # Urdu
        "ویزا", "پناہ گزین", "بے وطن", "ملک بدری", "شہریت",
        # Bengali
        "ভিসা", "শরণার্থী", "নির্বাসন", "রোহিঙ্গা", "নাগরিকত্ব",
        # Hindi
        "वीजा", "शरणार्थी", "निर्वासन", "नागरिकता",
        # Arabic
        "لاجئ", "ترحيل", "تأشيرة", "لجوء", "جنسية", "إقامة",
        # Indonesian
        "deportasi", "suaka", "pengungsi", "visa", "izin tinggal",
        # Swahili
        "uhamiaji", "kimbizi", "visa", "deportesheni",
        # French
        "expulsion", "asile", "réfugié", "visa", "titre de séjour",
        # Spanish
        "deportación", "asilo", "refugiado", "visa", "permiso de residencia",
        # Portuguese
        "deportação", "asilo", "refugiado", "visto",
        # Russian
        "депортация", "убежище", "беженец", "виза", "вид на жительство",
        # Turkish
        "sınır dışı etme", "sığınmacı", "mülteci", "vize", "oturma izni",
        # Tagalog
        "deportasyon", "visa", "refugee",
    ],
    CaseType.CONSUMER: [
        "fraud", "scam", "refund", "consumer", "product", "defective",
        "warranty", "debt collector", "overcharged", "false advertising",
        "pyramid scheme", "credit card", "loan shark", "interest rate",
        "banking", "insurance claim",
        # Dutch
        "oplichting", "terugbetaling", "consument", "defect product",
        "garantie", "schuldinvordering", "bank", "verzekering",
        # German
        "betrug", "rückerstattung", "verbraucher", "garantie", "schulden",
        # Urdu
        "دھوکہ", "واپسی", "صارف", "قرض",
        # Bengali
        "জালিয়াতি", "ফেরত", "ভোক্তা", "ঋণ",
        # Arabic
        "احتيال", "استرداد", "مستهلك", "قرض", "غش",
        # Indonesian
        "penipuan", "konsumen", "produk cacat", "hutang", "kartu kredit",
        # Swahili
        "udanganyifu", "mdai", "mkopo", "benki",
        # French
        "fraude", "remboursement", "consommateur", "arnaque", "prêt",
        # Spanish
        "fraude", "reembolso", "consumidor", "estafa", "préstamo",
        # Portuguese
        "fraude", "reembolso", "consumidor", "empréstimo",
        # Russian
        "мошенничество", "возврат", "потребитель", "кредит",
        # Turkish
        "dolandırıcılık", "iade", "tüketici", "kredi",
    ],
    CaseType.CIVIL: [
        "lawsuit", "sue", "contract", "breach", "damages", "compensation",
        "negligence", "property dispute", "inheritance", "will", "estate",
        "trespassing", "defamation", "slander", "libel",
        # Dutch
        "rechtszaak", "schadevergoeding", "contract", "nalatenschap",
        # German
        "klage", "schadensersatz", "vertrag", "erbschaft",
        # Urdu
        "مقدمہ", "معاوضہ", "عدالت", "وراثت",
        # Bengali
        "মামলা", "ক্ষতিপূরণ", "চুক্তি", "উত্তরাধিকার",
        # Arabic
        "دعوى", "تعويض", "عقد", "ميراث", "وصية",
        # Indonesian
        "gugatan", "ganti rugi", "kontrak", "warisan",
        # French
        "procès", "indemnisation", "contrat", "succession",
        # Spanish
        "demanda", "indemnización", "contrato", "herencia",
        # Portuguese
        "processo", "indemnização", "contrato", "herança",
        # Russian
        "иск", "компенсация", "договор", "наследство",
    ],
    CaseType.HUMAN_RIGHTS: [
        "torture", "discrimination", "rights violation", "freedom", "arbitrary",
        "persecution", "execution", "killed", "murdered", "disappeared",
        "extrajudicial", "enforced disappearance", "political prisoner",
        "freedom of speech", "freedom of assembly", "protest",
        "ethnic cleansing", "genocide", "war crime",
        # Dutch
        "marteling", "discriminatie", "mensenrechten", "vervolging",
        "verdwijning", "politieke gevangene",
        # German
        "folter", "diskriminierung", "menschenrechte", "verfolgung",
        # Urdu
        "تعذیب", "امتیازی سلوک", "ظلم", "جبری گمشدگی",
        # Bengali
        "নির্যাতন", "বৈষম্য", "গুম", "রাজনৈতিক বন্দী",
        # Hindi
        "यातना", "भेदभाव", "अत्याचार",
        # Arabic
        "تعذيب", "اضطهاد", "انتهاك حقوق", "اختفاء قسري",
        # Indonesian
        "penyiksaan", "diskriminasi", "penghilangan paksa",
        # Swahili
        "mateso", "ubaguzi", "ukiukwaji wa haki",
        # French
        "torture", "discrimination", "persécution", "disparition forcée",
        # Spanish
        "tortura", "discriminación", "persecución", "desaparición forzada",
        # Portuguese
        "tortura", "discriminação", "perseguição",
        # Russian
        "пытки", "дискриминация", "преследование", "насильственное исчезновение",
        # Turkish
        "işkence", "ayrımcılık", "zulüm",
        # Zulu
        "ukuhlukunyezwa", "ukucwaswa",
    ],
}

URGENCY_CRITICAL_KEYWORDS = [
    "tonight", "today", "right now", "immediately", "emergency", "arrested",
    "being evicted", "locked out", "deported", "deportation tonight",
    "nowhere to sleep", "nowhere to go", "cannot contact", "don't know where",
    "being killed", "will be killed", "threatening to deport", "on the street",
    "no food", "children starving", "my life is in danger", "death threat",
    "in custody right now", "they took my child", "missing person",
    # Dutch
    "vannacht", "nu meteen", "noodgeval", "gearresteerd", "op straat",
    "leven in gevaar", "mijn kind meegenomen",
    # German
    "heute nacht", "sofort", "notfall", "verhaftet", "auf der straße",
    # Urdu
    "آج رات", "ابھی", "فوری", "گرفتار", "جان کو خطرہ", "بچہ لے گئے",
    # Bengali
    "আজ রাতে", "এখনই", "জরুরি", "গ্রেফতার", "জীবন বিপন্ন",
    # Hindi
    "आज रात", "अभी", "आपातकाल", "जान को खतरा",
    # Arabic
    "الليلة", "الآن", "طوارئ", "اعتقل", "حياتي في خطر",
    # Indonesian
    "malam ini", "segera", "darurat", "ditangkap", "nyawa terancam",
    # Swahili
    "usiku huu", "haraka", "dharura", "maisha yangu hatarini",
    # French
    "ce soir", "maintenant", "urgence", "arrêté", "ma vie est en danger",
    # Spanish
    "esta noche", "ahora", "urgente", "arrestado", "mi vida está en peligro",
    # Portuguese
    "esta noite", "agora", "urgente", "preso", "minha vida está em perigo",
    # Russian
    "сегодня ночью", "сейчас", "срочно", "арестован", "жизнь под угрозой",
    # Turkish
    "bu gece", "şimdi", "acil", "tutuklandım", "hayatım tehlikede",
    # Zulu
    "usuku", "manje", "isimo esiphuthumayo",
    # Tagalog
    "ngayon", "emergency", "dinakip",
    # Hausa
    "yanzu", "gaggawa",
]

URGENCY_HIGH_KEYWORDS = [
    "tomorrow", "this week", "court date", "hearing", "deadline",
    "24 hours", "48 hours", "months unpaid", "haven't paid", "eviction notice",
    "court order", "summons", "judgment", "appeal deadline",
    # Dutch
    "morgen", "rechtszitting", "termijn", "maanden niet betaald",
    "aanmaning", "dagvaarding",
    # German
    "morgen", "gerichtstermin", "frist", "monate nicht bezahlt",
    # Urdu
    "کل", "عدالت", "مہینوں سے", "نوٹس",
    # Bengali
    "কাল", "আদালত", "মাস ধরে", "নোটিশ",
    # Hindi
    "कल", "अदालत", "महीनों से", "नोटिस",
    # Arabic
    "غداً", "المحكمة", "أشهر", "إشعار",
    # Indonesian
    "besok", "sidang", "tenggat", "berbulan-bulan", "surat peringatan",
    # Swahili
    "kesho", "mahakama", "miezi", "notisi",
    # French
    "demain", "audience", "échéance", "convocation",
    # Spanish
    "mañana", "audiencia", "plazo", "citación",
    # Portuguese
    "amanhã", "audiência", "prazo", "citação",
    # Russian
    "завтра", "суд", "слушание", "срок", "уведомление",
    # Turkish
    "yarın", "mahkeme", "süre", "ihbar",
    # Tagalog
    "bukas", "korte", "deadline",
]

STATELESS_KEYWORDS = [
    "no documents", "no passport", "no id", "no papers", "undocumented",
    "stateless", "rohingya", "no nationality", "no legal status",
    "no citizenship", "without papers", "no identity", "unregistered",
    # Dutch
    "geen papieren", "geen documenten", "illegaal", "geen identiteitsbewijs",
    # German
    "keine papiere", "keine dokumente", "staatenlos",
    # Arabic
    "لا وثائق", "عديم الجنسية", "بلا هوية",
    # Urdu
    "بلا دستاویز", "کوئی کاغذات نہیں",
    # Bengali
    "কোনো কাগজ নেই", "কোনো পাসপোর্ট নেই", "রোহিঙ্গা",
    # French
    "sans papiers", "apatride", "sans documents",
    # Spanish
    "sin documentos", "apátrida", "indocumentado",
    # Russian
    "без документов", "лицо без гражданства",
    # Indonesian
    "tanpa dokumen", "tidak berkewarganegaraan",
    # Swahili
    "bila hati", "mkimbizi asiye na nyaraka",
]

MINOR_KEYWORDS = [
    "year-old", "years old", "years-old",
    "my son", "my daughter", "my child", "my kid", "my baby",
    "14-year", "15-year", "16-year", "17-year", "13-year",
    "12-year", "11-year", "10-year", "minor", "juvenile", "underage",
    "teenager", "toddler", "infant",
    # Dutch
    "mijn kind", "mijn kinderen", "mijn zoon", "mijn dochter",
    "minderjarig", "kind", "kinderen",
    # German
    "mein kind", "meine kinder", "mein sohn", "meine tochter", "minderjährig",
    # Urdu
    "میرا بیٹا", "میری بیٹی", "بچہ", "بچی", "بچے",
    # Bengali
    "আমার ছেলে", "আমার মেয়ে", "শিশু", "বাচ্চা",
    # Hindi
    "मेरा बेटा", "मेरी बेटी", "बच्चा", "बच्चे",
    # Arabic
    "ابني", "ابنتي", "طفل", "قاصر", "أطفالي",
    # Indonesian
    "anak saya", "putra saya", "putri saya", "anak-anak", "anakku",
    # Swahili
    "mtoto wangu", "mwanangu", "watoto wangu",
    # French
    "mon fils", "ma fille", "mon enfant", "mineur", "mes enfants",
    # Spanish
    "mi hijo", "mi hija", "mi hijo menor", "menor", "mis hijos",
    # Portuguese
    "meu filho", "minha filha", "menor", "meus filhos",
    # Russian
    "мой сын", "моя дочь", "мой ребёнок", "несовершеннолетний",
    # Turkish
    "oğlum", "kızım", "çocuğum", "reşit olmayan",
    # Zulu
    "abantwana", "ingane yami",
    # Tagalog
    "anak ko", "bata",
    # Hausa
    "ɗana", "yarana",
]

DEPORTATION_KEYWORDS = [
    "deport", "deportation", "threatening to deport", "remove", "removal order",
    "illegal entry", "send back", "will be sent", "return to",
    "forced return", "expulsion order", "removal proceedings",
    # Dutch
    "uitzetting", "uitwijzing", "dreigt uit te zetten", "teruggestuurd",
    "uitgezet worden", "illegaal verblijf",
    # German
    "abschiebung", "abschieben", "ausweisung", "zurückschicken",
    # Urdu
    "ملک بدر", "ملک بدری", "بے دخل", "واپس بھیجنا",
    # Bengali
    "নির্বাসন", "ফেরত পাঠানো", "বহিষ্কার",
    # Hindi
    "निर्वासन", "वापस भेजना", "देश निकाला",
    # Arabic
    "ترحيل", "يرحّلني", "إعادة قسرية",
    # Indonesian
    "deportasi", "akan dideportasi", "diusir dari negara",
    # Swahili
    "deportesheni", "kurudishwa", "kufukuzwa nchini",
    # French
    "expulsion", "expulsé", "reconduite à la frontière",
    # Spanish
    "deportación", "deportar", "expulsión",
    # Portuguese
    "deportação", "deportar", "expulsão",
    # Russian
    "депортация", "депортировать", "выдворение",
    # Turkish
    "sınır dışı etme", "deport edilmek",
    # Tagalog
    "deportasyon", "papalayasin",
]

TRAFFICKING_KEYWORDS = [
    "passport confiscated", "took my passport", "holding my passport",
    "confiscated my passport", "not allowed to leave", "cannot leave",
    "locked in", "cannot go out", "trafficking", "forced labour",
    "forced labor", "bonded labour", "debt bondage", "placement fee",
    "recruitment debt", "kafala", "domestic worker", "no freedom",
    "employer controls", "cannot contact family", "phone taken",
    "watched all the time", "threatened if i leave",
    # Dutch — critical
    "paspoort ingenomen", "paspoort afgenomen", "mag niet weg",
    "mag het huis niet verlaten", "geen bewegingsvrijheid",
    "opgesloten", "kan niet vertrekken", "mensenhandel",
    "schuld aan werkgever", "vluchtticket schuld",
    # German
    "pass beschlagnahmt", "darf nicht gehen", "eingesperrt",
    "menschenhandel", "zwangsarbeit",
    # Arabic
    "مصادرة جواز سفري", "لا يسمح لي بالمغادرة", "اتجار بالبشر",
    # Bengali
    "পাসপোর্ট নিয়ে নিয়েছে", "যেতে দেওয়া হচ্ছে না", "পাচার",
    # Tagalog
    "kinuha ang passport", "hindi makaalis", "trafficking",
    # Indonesian
    "paspor disita", "tidak boleh keluar", "perdagangan orang",
    # French
    "confiscation du passeport", "traite des êtres humains",
    # Spanish
    "confiscación del pasaporte", "trata de personas",
]

CHILD_ABDUCTION_KEYWORDS = [
    "took my children", "took the children", "took my kids", "took my son",
    "took my daughter", "children taken", "abducted", "kidnapped my child",
    "won't let me see", "denied access to my child", "parental abduction",
    "child taken across border",
    # Dutch
    "kinderen meegenomen", "kind ontvoerd", "toegang tot kinderen geweigerd",
    # German
    "kinder mitgenommen", "kind entführt", "kindesentführung",
    # Urdu
    "بچوں کو لے گئے", "بچے لے گئے", "بچہ اغوا",
    # Bengali
    "সন্তান নিয়ে গেছে", "বাচ্চা নিয়ে গেছে", "শিশু অপহরণ",
    # Hindi
    "बच्चों को ले गया", "बच्चे ले गए", "बच्चे का अपहरण",
    # Arabic
    "اختطف أطفالي", "أخذ أطفالي", "اختطاف الأطفال",
    # French
    "a pris mes enfants", "enlèvement parental", "rapt d'enfant",
    # Spanish
    "se llevó a mis hijos", "secuestro parental", "sustracción de menores",
    # Portuguese
    "levou meus filhos", "rapto parental",
    # Russian
    "забрал моих детей", "похищение ребёнка",
    # Swahili
    "watoto wangu wamechukuliwa", "utekaji nyara wa mtoto",
    # Zulu
    "bathatha abantwana bami",
    # Tagalog
    "kinuha ang aking mga anak",
]


def _check_keywords(text: str, keywords: list) -> bool:
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _extract_age(text: str) -> int | None:
    match = re.search(r'\b(\d{1,2})[- ]?year[s]?[- ]?old\b', text, re.IGNORECASE)
    if match:
        return int(match.group(1))
    return None


class CaseClassifier:
    """
    Multilingual case intake classifier.
    Supports 80+ countries with native script detection.
    Sets all specialist flags consumed by the retriever.
    """

    def __init__(self):
        self._lang_detector = None

    def _get_lang_detector(self):
        if self._lang_detector is None:
            try:
                from langdetect import detect
                self._lang_detector = detect
            except ImportError:
                print("[Classifier] langdetect not installed — defaulting to 'en'")
                self._lang_detector = lambda x: "en"
        return self._lang_detector

    def detect_language(self, text: str) -> str:
        text_lower = text.lower()
        if any(kw in text for kw in ["umnikazi", "indlu", "abantwana", "ngiyacela",
                                      "ukushaywa", "ethekwini", "ekapa", "mzansi"]):
            return "zu"
        if any(kw in text_lower for kw in ["mwajiri", "mwenye nyumba", "alikamatwa",
                                            "mashtaka", "kizuizini", "sheria"]):
            return "sw"
        if any(kw in text_lower for kw in ["majikan", "gaji", "pengadilan",
                                            "ditangkap", "phk"]):
            return "id"
        if any(kw in text_lower for kw in ["werkgever", "huurder", "verhuurder",
                                            "loon", "salaris", "ontslagen",
                                            "paspoort ingenomen", "mag niet weg",
                                            "geen loon", "betaalt niet"]):
            return "nl"
        if any(kw in text_lower for kw in ["arbeitgeber", "mieter", "vermieter",
                                            "gehalt", "entlassen", "abschiebung"]):
            return "de"
        if any(kw in text_lower for kw in ["employeur", "salaire", "loyer",
                                            "propriétaire", "arrestation"]):
            return "fr"
        if any(kw in text_lower for kw in ["empleador", "salario", "arrendador",
                                            "arrestado", "desalojo"]):
            return "es"
        if any(kw in text_lower for kw in ["empregador", "salário", "senhorio",
                                            "despejo"]):
            return "pt"
        if any(kw in text_lower for kw in ["işveren", "maaş", "ev sahibi",
                                            "tutuklandım"]):
            return "tr"
        if any(kw in text for kw in ["sahod", "tinanggal", "deportasyon",
                                      "pilipinas", "kinuha ang passport"]):
            return "tl"
        try:
            return self._get_lang_detector()(text)
        except Exception:
            return "en"

    def detect_jurisdiction(self, text: str) -> tuple[str, str]:
        for city, code in NATIVE_SCRIPT_CITIES.items():
            if city in text:
                print(f"[Classifier] Native script match: '{city}' → {code}")
                return code, code
        text_lower = text.lower()
        for country, hints in JURISDICTION_HINTS.items():
            if any(hint in text_lower for hint in hints):
                return country, country
        return "XX", "UNKNOWN"

    def classify_case_type(self, text: str) -> CaseType:
        text_lower = text.lower()
        scores = {}
        for case_type, keywords in CASE_TYPE_KEYWORDS.items():
            score = sum(1 for kw in keywords if kw.lower() in text_lower)
            if score > 0:
                scores[case_type] = score
        if not scores:
            return CaseType.UNKNOWN
        return max(scores, key=scores.get)

    def assess_urgency(self, text: str) -> UrgencyLevel:
        if _check_keywords(text, URGENCY_CRITICAL_KEYWORDS):
            return UrgencyLevel.CRITICAL
        if _check_keywords(text, URGENCY_HIGH_KEYWORDS):
            return UrgencyLevel.HIGH
        if _check_keywords(text, [
            "arrest", "jail", "prison", "گرفتار", "গ্রেফতার",
            "ditangkap", "arrêté", "arrestado", "арестован",
            "tutuklandım", "ukubopha", "gearresteerd", "verhaftet",
        ]):
            return UrgencyLevel.HIGH
        return UrgencyLevel.MEDIUM

    def detect_flags(self, text: str) -> dict:
        flags = {
            "is_stateless":           _check_keywords(text, STATELESS_KEYWORDS),
            "involves_minor":         False,
            "deportation_risk":       _check_keywords(text, DEPORTATION_KEYWORDS),
            "trafficking_indicators": False,
            "child_abduction":        _check_keywords(text, CHILD_ABDUCTION_KEYWORDS),
        }

        if _check_keywords(text, MINOR_KEYWORDS):
            flags["involves_minor"] = True
        age = _extract_age(text)
        if age is not None and age < 18:
            flags["involves_minor"] = True

        has_passport = _check_keywords(text, [
            "passport confiscated", "took my passport",
            "holding my passport", "confiscated my passport",
            "paspoort ingenomen", "paspoort afgenomen",
            "pass beschlagnahmt",
            "مصادرة جواز", "পাসপোর্ট নিয়ে", "paspor disita",
        ])
        has_unpaid = _check_keywords(text, [
            "not paid", "unpaid", "haven't paid", "hasn't paid",
            "no salary", "no wages", "7 months", "6 months", "5 months",
            "8 months", "9 months", "10 months", "4 months",
            "geen loon", "niet betaald", "geen salaris",
            "nicht bezahlt", "kein gehalt",
        ])
        has_no_movement = _check_keywords(text, [
            "not allowed to leave", "cannot leave", "locked in",
            "cannot go out", "not permitted to leave", "no freedom to leave",
            "mag niet weg", "mag het huis niet verlaten",
            "darf nicht gehen", "eingesperrt",
        ])
        if has_passport and (has_unpaid or has_no_movement):
            flags["trafficking_indicators"] = True
        if _check_keywords(text, [
            "trafficking", "forced labour", "forced labor",
            "debt bondage", "kafala", "bonded labour",
            "mensenhandel", "zwangsarbeit", "menschenhandel",
        ]):
            flags["trafficking_indicators"] = True

        return flags

    def extract_key_facts(self, text: str) -> list[str]:
        facts = []
        for sent in re.split(r'[.!?।۔]\s+', text)[:10]:
            sent = sent.strip()
            if len(sent) > 15:
                facts.append(sent)
        return facts[:6]

    def intake(self, description: str) -> LegalCase:
        case_id   = str(uuid.uuid4())[:8].upper()
        language  = self.detect_language(description)
        country, jurisdiction = self.detect_jurisdiction(description)
        case_type = self.classify_case_type(description)
        urgency   = self.assess_urgency(description)
        key_facts = self.extract_key_facts(description)
        flags     = self.detect_flags(description)

        if flags["child_abduction"] or flags["deportation_risk"]:
            urgency = UrgencyLevel.CRITICAL
        if flags["trafficking_indicators"]:
            urgency = UrgencyLevel.CRITICAL

        mandate_human = (
            flags["is_stateless"]
            or flags["trafficking_indicators"]
            or flags["child_abduction"]
            or (flags["involves_minor"] and flags["deportation_risk"])
        )

        print(
            f"[Classifier] {case_id}: {case_type.value} | {urgency.name} | "
            f"{country} | lang={language} | "
            f"flags={[k for k, v in flags.items() if v]}"
        )

        return LegalCase(
            case_id=case_id,
            raw_description=description,
            language=language,
            jurisdiction=jurisdiction,
            country=country,
            case_type=case_type,
            urgency=urgency,
            status=CaseStatus.INTAKE,
            key_facts=key_facts,
            mandate_human_lawyer=mandate_human,
            metadata={"intake_timestamp": datetime.now(timezone.utc).isoformat()},
            **flags,
        )
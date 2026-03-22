# intake/classifier.py
# Multilingual case intake — detects language, jurisdiction, case type, urgency
# Supports 50+ countries with native script city detection
# No API key required for core classification

import re
import uuid
from datetime import datetime, timezone
from intake.base import LegalCase, CaseType, UrgencyLevel, CaseStatus


# ── Native script city → ISO country code ─────────────────────────────────────
# Covers 50+ countries. Checked against city names in their own scripts.
# Add new entries here only — no other code changes needed.

NATIVE_SCRIPT_CITIES = {

    # ── URDU — Pakistan ──────────────────────────────────────────────────────
    "اسلام آباد": "PK",   # Islamabad
    "کراچی":       "PK",   # Karachi
    "لاہور":       "PK",   # Lahore
    "پشاور":       "PK",   # Peshawar
    "کوئٹہ":       "PK",   # Quetta
    "فیصل آباد":   "PK",   # Faisalabad
    "راولپنڈی":    "PK",   # Rawalpindi
    "ملتان":       "PK",   # Multan
    "حیدرآباد":    "PK",   # Hyderabad (PK)
    "پاکستان":     "PK",   # Pakistan

    # ── BENGALI — Bangladesh ─────────────────────────────────────────────────
    "ঢাকা":        "BD",   # Dhaka
    "চট্টগ্রাম":   "BD",   # Chittagong
    "সিলেট":       "BD",   # Sylhet
    "রাজশাহী":     "BD",   # Rajshahi
    "খুলনা":       "BD",   # Khulna
    "বরিশাল":      "BD",   # Barisal
    "কক্সবাজার":   "BD",   # Cox's Bazar
    "বাংলাদেশ":    "BD",   # Bangladesh

    # ── HINDI — India ────────────────────────────────────────────────────────
    "दिल्ली":      "IN",   # Delhi
    "मुंबई":       "IN",   # Mumbai
    "बेंगलुरु":    "IN",   # Bangalore
    "कोलकाता":     "IN",   # Kolkata
    "चेन्नई":      "IN",   # Chennai
    "हैदराबाद":    "IN",   # Hyderabad (IN)
    "पुणे":        "IN",   # Pune
    "अहमदाबाद":    "IN",   # Ahmedabad
    "जयपुर":       "IN",   # Jaipur
    "भारत":        "IN",   # India

    # ── ARABIC — Multiple countries ───────────────────────────────────────────
    # Saudi Arabia
    "الرياض":      "SA",   # Riyadh
    "جدة":         "SA",   # Jeddah
    "مكة":         "SA",   # Mecca
    "المدينة":     "SA",   # Medina
    "الدمام":      "SA",   # Dammam
    # UAE
    "دبي":         "AE",   # Dubai
    "أبوظبي":      "AE",   # Abu Dhabi
    "الشارقة":     "AE",   # Sharjah
    # Egypt
    "القاهرة":     "EG",   # Cairo
    "الإسكندرية":  "EG",   # Alexandria
    "مصر":         "EG",   # Egypt
    # Iraq
    "بغداد":       "IQ",   # Baghdad
    "البصرة":      "IQ",   # Basra
    # Jordan
    "عمّان":       "JO",   # Amman
    # Lebanon
    "بيروت":       "LB",   # Beirut
    # Morocco
    "الرباط":      "MA",   # Rabat
    "الدار البيضاء": "MA", # Casablanca
    "مراكش":       "MA",   # Marrakech
    # Algeria
    "الجزائر":     "DZ",   # Algiers
    # Tunisia
    "تونس":        "TN",   # Tunis
    # Libya
    "طرابلس":      "LY",   # Tripoli
    # Sudan
    "الخرطوم":     "SD",   # Khartoum
    # Syria
    "دمشق":        "SY",   # Damascus
    "حلب":         "SY",   # Aleppo
    # Yemen
    "صنعاء":       "YE",   # Sanaa
    # Kuwait
    "الكويت":      "KW",   # Kuwait City
    # Qatar
    "الدوحة":      "QA",   # Doha
    # Bahrain
    "المنامة":     "BH",   # Manama
    # Oman
    "مسقط":        "OM",   # Muscat

    # ── PERSIAN/FARSI — Iran ─────────────────────────────────────────────────
    "تهران":       "IR",   # Tehran
    "مشهد":        "IR",   # Mashhad
    "اصفهان":      "IR",   # Isfahan
    "ایران":       "IR",   # Iran

    # ── TURKISH — Turkey ─────────────────────────────────────────────────────
    "İstanbul":    "TR",   # Istanbul
    "Ankara":      "TR",   # Ankara
    "İzmir":       "TR",   # Izmir
    "Türkiye":     "TR",   # Turkey

    # ── RUSSIAN — Russia & CIS ───────────────────────────────────────────────
    "Москва":      "RU",   # Moscow
    "Санкт-Петербург": "RU", # Saint Petersburg
    "Новосибирск": "RU",   # Novosibirsk
    "Россия":      "RU",   # Russia
    "Київ":        "UA",   # Kyiv
    "Харків":      "UA",   # Kharkiv
    "Одеса":       "UA",   # Odessa
    "Україна":     "UA",   # Ukraine
    "Мінск":       "BY",   # Minsk
    "Алматы":      "KZ",   # Almaty
    "Астана":      "KZ",   # Astana
    "Ташкент":     "UZ",   # Tashkent

    # ── CHINESE — China ───────────────────────────────────────────────────────
    "北京":        "CN",   # Beijing
    "上海":        "CN",   # Shanghai
    "广州":        "CN",   # Guangzhou
    "深圳":        "CN",   # Shenzhen
    "成都":        "CN",   # Chengdu
    "武汉":        "CN",   # Wuhan
    "西安":        "CN",   # Xi'an
    "中国":        "CN",   # China
    "香港":        "HK",   # Hong Kong
    "台北":        "TW",   # Taipei
    "澳門":        "MO",   # Macau

    # ── JAPANESE — Japan ─────────────────────────────────────────────────────
    "東京":        "JP",   # Tokyo
    "大阪":        "JP",   # Osaka
    "名古屋":      "JP",   # Nagoya
    "札幌":        "JP",   # Sapporo
    "日本":        "JP",   # Japan

    # ── KOREAN — South Korea ─────────────────────────────────────────────────
    "서울":        "KR",   # Seoul
    "부산":        "KR",   # Busan
    "인천":        "KR",   # Incheon
    "한국":        "KR",   # South Korea

    # ── THAI — Thailand ──────────────────────────────────────────────────────
    "กรุงเทพ":     "TH",   # Bangkok
    "เชียงใหม่":   "TH",   # Chiang Mai
    "ไทย":         "TH",   # Thailand

    # ── VIETNAMESE — Vietnam ─────────────────────────────────────────────────
    "Hà Nội":      "VN",   # Hanoi
    "Hồ Chí Minh": "VN",  # Ho Chi Minh City
    "Đà Nẵng":     "VN",   # Da Nang
    "Việt Nam":    "VN",   # Vietnam

    # ── INDONESIAN — Indonesia ───────────────────────────────────────────────
    "Jakarta":     "ID",
    "Surabaya":    "ID",
    "Bandung":     "ID",
    "Medan":       "ID",
    "Semarang":    "ID",
    "Makassar":    "ID",
    "Palembang":   "ID",
    "Indonesia":   "ID",

    # ── TAGALOG — Philippines ────────────────────────────────────────────────
    "Maynila":     "PH",   # Manila in Tagalog
    "Cebu":        "PH",
    "Davao":       "PH",
    "Quezon City": "PH",
    "Pilipinas":   "PH",   # Philippines in Tagalog

    # ── SWAHILI — Kenya / Tanzania ───────────────────────────────────────────
    "Nairobi":     "KE",
    "Mombasa":     "KE",
    "Kisumu":      "KE",
    "Nakuru":      "KE",
    "Dar es Salaam": "TZ",
    "Dodoma":      "TZ",
    "Zanzibar":    "TZ",

    # ── AMHARIC — Ethiopia ───────────────────────────────────────────────────
    "አዲስ አበባ":    "ET",   # Addis Ababa
    "ድሬዳዋ":       "ET",   # Dire Dawa
    "ኢትዮጵያ":      "ET",   # Ethiopia

    # ── ZULU / XHOSA / AFRIKAANS — South Africa ─────────────────────────────
    "eThekwini":   "ZA",   # Durban in Zulu
    "iGoli":       "ZA",   # Johannesburg in Zulu
    "iKapa":       "ZA",   # Cape Town in Xhosa
    "Tshwane":     "ZA",   # Pretoria
    "Johannesburg":"ZA",
    "Cape Town":   "ZA",
    "Durban":      "ZA",
    "Pretoria":    "ZA",

    # ── HAUSA / YORUBA / IGBO — Nigeria ──────────────────────────────────────
    "Èkó":         "NG",   # Lagos in Yoruba
    "Abuja":       "NG",
    "Lagos":       "NG",
    "Kano":        "NG",
    "Ibadan":      "NG",
    "Port Harcourt": "NG",

    # ── FRENCH — France / Canada / West Africa ───────────────────────────────
    "Paris":       "FR",
    "Lyon":        "FR",
    "Marseille":   "FR",
    "Montréal":    "CA",
    "Québec":      "CA",
    "Dakar":       "SN",   # Senegal
    "Abidjan":     "CI",   # Côte d'Ivoire
    "Bamako":      "ML",   # Mali
    "Ouagadougou": "BF",   # Burkina Faso
    "Lomé":        "TG",   # Togo
    "Cotonou":     "BJ",   # Benin
    "Niamey":      "NE",   # Niger
    "N'Djamena":   "TD",   # Chad
    "Kinshasa":    "CD",   # DR Congo
    "Brazzaville": "CG",   # Republic of Congo

    # ── PORTUGUESE — Brazil / Portugal / Mozambique / Angola ─────────────────
    "São Paulo":   "BR",
    "Rio de Janeiro": "BR",
    "Brasília":    "BR",
    "Salvador":    "BR",
    "Fortaleza":   "BR",
    "Brasil":      "BR",
    "Lisboa":      "PT",   # Lisbon
    "Porto":       "PT",
    "Maputo":      "MZ",   # Mozambique
    "Luanda":      "AO",   # Angola

    # ── SPANISH — Latin America / Spain ──────────────────────────────────────
    "Madrid":      "ES",
    "Barcelona":   "ES",
    "Ciudad de México": "MX",  # Mexico City
    "Guadalajara": "MX",
    "Monterrey":   "MX",
    "Buenos Aires":"AR",
    "Córdoba":     "AR",
    "Bogotá":      "CO",
    "Medellín":    "CO",
    "Lima":        "PE",
    "Santiago":    "CL",
    "Caracas":     "VE",
    "La Paz":      "BO",
    "Quito":       "EC",
    "Asunción":    "PY",
    "Montevideo":  "UY",
    "San José":    "CR",
    "Ciudad de Guatemala": "GT",
    "Tegucigalpa": "HN",
    "Managua":     "NI",
    "San Salvador":"SV",
    "Santo Domingo": "DO",
    "La Habana":   "CU",   # Havana

    # ── GREEK — Greece ───────────────────────────────────────────────────────
    "Αθήνα":       "GR",   # Athens
    "Θεσσαλονίκη": "GR",   # Thessaloniki
    "Ελλάδα":      "GR",   # Greece

    # ── HEBREW — Israel ──────────────────────────────────────────────────────
    "תל אביב":     "IL",   # Tel Aviv
    "ירושלים":     "IL",   # Jerusalem
    "חיפה":        "IL",   # Haifa
    "ישראל":       "IL",   # Israel

    # ── SINHALA — Sri Lanka ──────────────────────────────────────────────────
    "කොළඹ":        "LK",   # Colombo
    "ශ්‍රී ලංකා":  "LK",   # Sri Lanka

    # ── MYANMAR / BURMESE ────────────────────────────────────────────────────
    "ရန်ကုန်":     "MM",   # Yangon
    "နေပြည်တော်":  "MM",   # Naypyidaw
    "မန္တလေး":     "MM",   # Mandalay
    "မြန်မာ":      "MM",   # Myanmar
    "Rakhine":     "MM",   # Rakhine State (Rohingya context)

    # ── KHMER — Cambodia ─────────────────────────────────────────────────────
    "ភ្នំពេញ":     "KH",   # Phnom Penh
    "កម្ពុជា":     "KH",   # Cambodia

    # ── NEPALI ───────────────────────────────────────────────────────────────
    "काठमाडौं":    "NP",   # Kathmandu
    "नेपाल":       "NP",   # Nepal

    # ── ROHINGYA-SPECIFIC ────────────────────────────────────────────────────
    "Cox's Bazar": "BD",
    "Teknaf":      "BD",
    "Ukhiya":      "BD",
}


# ── JURISDICTION_HINTS — Latin script fallback ────────────────────────────────

JURISDICTION_HINTS = {
    "PK": [
        "pakistan", "lahore", "karachi", "islamabad", "peshawar", "quetta",
        "faisalabad", "rawalpindi", "multan", "pakistani",
    ],
    "IN": [
        "india", "delhi", "mumbai", "bangalore", "kolkata", "chennai",
        "hyderabad", "pune", "ahmedabad", "jaipur", "indian court",
        "rupees", "inr",
    ],
    "ID": [
        "indonesia", "jakarta", "surabaya", "bandung", "medan", "semarang",
        "pengadilan", "indonesian", "rupiah",
    ],
    "US": [
        "united states", "america", "new york", "los angeles", "chicago",
        "houston", "atlanta", "california", "texas", "florida",
        "federal court", "section 1983",
    ],
    "GB": [
        "england", "wales", "scotland", "uk", "united kingdom", "british",
        "london", "manchester", "birmingham", "crown court", "pounds", "gbp",
    ],
    "NG": [
        "nigeria", "lagos", "abuja", "port harcourt", "kano", "ibadan",
        "nigerian", "naira",
    ],
    "BD": [
        "bangladesh", "dhaka", "chittagong", "sylhet", "rajshahi",
        "bangladeshi", "cox's bazar", "teknaf", "taka",
    ],
    "ZA": [
        "south africa", "cape town", "johannesburg", "durban", "pretoria",
        "south african", "rand",
    ],
    "KE": [
        "kenya", "nairobi", "mombasa", "kisumu", "nakuru", "kenyan", "shilling",
    ],
    "CA": [
        "canada", "toronto", "montreal", "vancouver", "ottawa", "calgary",
        "canadian", "ontario", "british columbia",
    ],
    "PH": [
        "philippines", "manila", "cebu", "davao", "quezon", "philippine",
        "filipino", "peso",
    ],
    "SA": [
        "saudi arabia", "riyadh", "jeddah", "mecca", "medina", "saudi",
        "kafala",
    ],
    "AE": [
        "uae", "dubai", "abu dhabi", "sharjah", "emirates",
    ],
    "EG": [
        "egypt", "cairo", "alexandria", "egyptian",
    ],
    "MM": [
        "myanmar", "burma", "yangon", "rangoon", "mandalay", "rakhine", "burmese",
    ],
    "ET": [
        "ethiopia", "addis ababa", "ethiopian",
    ],
    "CN": [
        "china", "beijing", "shanghai", "guangzhou", "shenzhen", "chinese",
        "yuan", "rmb",
    ],
    "JP": [
        "japan", "tokyo", "osaka", "nagoya", "sapporo", "japanese", "yen",
    ],
    "KR": [
        "south korea", "korea", "seoul", "busan", "incheon", "korean", "won",
    ],
    "TH": [
        "thailand", "bangkok", "chiang mai", "thai", "baht",
    ],
    "VN": [
        "vietnam", "hanoi", "ho chi minh", "saigon", "vietnamese", "dong",
    ],
    "BR": [
        "brazil", "brasil", "sao paulo", "rio de janeiro", "brasilia",
        "brazilian", "real",
    ],
    "MX": [
        "mexico", "ciudad de mexico", "guadalajara", "monterrey", "mexican", "peso",
    ],
    "AR": [
        "argentina", "buenos aires", "cordoba", "argentinian",
    ],
    "CO": [
        "colombia", "bogota", "medellin", "colombian",
    ],
    "TR": [
        "turkey", "istanbul", "ankara", "izmir", "turkish", "lira",
    ],
    "IR": [
        "iran", "tehran", "mashhad", "isfahan", "iranian", "farsi",
    ],
    "IQ": [
        "iraq", "baghdad", "basra", "iraqi",
    ],
    "SY": [
        "syria", "damascus", "aleppo", "syrian",
    ],
    "LK": [
        "sri lanka", "colombo", "sinhala",
    ],
    "NP": [
        "nepal", "kathmandu", "nepali",
    ],
    "KH": [
        "cambodia", "phnom penh", "khmer",
    ],
    "GH": [
        "ghana", "accra", "ghanaian", "cedi",
    ],
    "SN": [
        "senegal", "dakar", "senegalese",
    ],
    "CI": [
        "ivory coast", "cote d'ivoire", "abidjan",
    ],
    "CD": [
        "congo", "kinshasa", "democratic republic",
    ],
    "MZ": [
        "mozambique", "maputo",
    ],
    "AO": [
        "angola", "luanda",
    ],
    "PT": [
        "portugal", "lisboa", "lisbon", "porto", "portuguese",
    ],
    "ES": [
        "spain", "madrid", "barcelona", "spanish",
    ],
    "FR": [
        "france", "paris", "lyon", "marseille", "french",
    ],
    "DE": [
        "germany", "berlin", "munich", "hamburg", "frankfurt", "german",
    ],
    "IT": [
        "italy", "rome", "milan", "naples", "italian",
    ],
    "RU": [
        "russia", "moscow", "saint petersburg", "russian", "ruble",
    ],
    "UA": [
        "ukraine", "kyiv", "kharkiv", "odessa", "ukrainian",
    ],
    "IL": [
        "israel", "tel aviv", "jerusalem", "haifa", "israeli",
    ],
    "GR": [
        "greece", "athens", "thessaloniki", "greek",
    ],
    "MA": [
        "morocco", "rabat", "casablanca", "marrakech", "moroccan",
    ],
    "KZ": [
        "kazakhstan", "almaty", "astana", "kazakh",
    ],
}


# ── Case type keywords — multilingual ─────────────────────────────────────────

CASE_TYPE_KEYWORDS = {
    CaseType.HOUSING: [
        "evict", "eviction", "landlord", "tenant", "rent", "lease", "lockout",
        "lock changed", "locks changed", "threw my belongings", "nowhere to sleep",
        "nowhere to live", "illegal entry", "habitability", "deposit",
        "notice to quit", "mortgage", "foreclosure",
        # Urdu
        "مالک مکان", "کرایہ", "بے دخلی", "تالہ",
        # Bengali
        "বাড়িওয়ালা", "ভাড়া", "উচ্ছেদ", "তালা",
        # Hindi
        "मकान मालिक", "किराया", "बेदखल",
        # Arabic
        "مالك", "إيجار", "إخلاء",
        # Indonesian
        "sewa", "penggusuran", "pemilik rumah",
        # Swahili
        "mwenye nyumba", "kodi", "kufukuzwa",
        # French
        "propriétaire", "loyer", "expulsion",
        # Spanish
        "arrendador", "alquiler", "desalojo",
        # Portuguese
        "senhorio", "aluguel", "despejo",
        # Russian
        "арендодатель", "аренда", "выселение",
    ],
    CaseType.CRIMINAL: [
        "arrest", "arrested", "police", "charge", "criminal", "prison", "jail",
        "bail", "accused", "sentence", "detention", "detained", "custody",
        "interrogation", "absconding",
        # Urdu
        "گرفتار", "پولیس", "حراست", "ضمانت",
        # Bengali
        "গ্রেফতার", "পুলিশ", "আটক",
        # Hindi
        "गिरफ्तार", "पुलिस", "हिरासत",
        # Arabic
        "اعتقال", "شرطة", "احتجاز",
        # Indonesian
        "ditahan", "polisi", "ditangkap", "penjara",
        # Swahili
        "kukamatwa", "polisi", "kizuizini",
        # French
        "arrestation", "police", "détention",
        # Spanish
        "arresto", "policía", "detención",
        # Russian
        "арест", "полиция", "задержание",
        # Turkish
        "tutuklandım", "polis", "gözaltı",
    ],
    CaseType.LABOR: [
        "employer", "fired", "wrongful termination", "wage", "salary", "unpaid",
        "workplace", "discrimination", "harassment", "union", "overtime",
        "not paid", "haven't paid", "hasn't paid", "placement fee",
        "recruitment agency", "domestic worker",
        # Urdu
        "ملازمت", "تنخواہ", "ملازم", "نوکری",
        # Bengali
        "নিয়োগকর্তা", "বেতন", "চাকরি", "মজুরি",
        # Hindi
        "नियोक्ता", "वेतन", "नौकरी", "मजदूरी",
        # Arabic
        "صاحب العمل", "راتب", "أجر", "فصل",
        # Indonesian
        "pemecatan", "upah", "majikan", "gaji", "PHK",
        # Swahili
        "mwajiri", "mshahara", "kufukuzwa kazi",
        # French
        "employeur", "salaire", "licenciement",
        # Spanish
        "empleador", "salario", "despido",
        # Portuguese
        "empregador", "salário", "demissão",
        # Russian
        "работодатель", "зарплата", "увольнение",
    ],
    CaseType.FAMILY: [
        "divorce", "custody", "child", "domestic violence", "abuse", "alimony",
        "marriage", "husband", "wife", "children taken", "took my children",
        "took the children", "talaq", "mehr", "maintenance",
        # Urdu
        "طلاق", "بچہ", "گھریلو تشدد", "بچے", "شوہر", "بیوی", "نان نفقہ",
        # Bengali
        "তালাক", "সন্তান", "গৃহহিংসা", "স্বামী", "স্ত্রী",
        # Hindi
        "तलाक", "बच्चे", "घरेलू हिंसा", "पति", "पत्नी",
        # Arabic
        "طلاق", "حضانة", "عنف أسري", "زوج", "زوجة",
        # Indonesian
        "perceraian", "hak asuh", "kekerasan rumah tangga", "suami", "istri",
        # Swahili
        "talaka", "mtoto", "ukatili wa nyumbani",
        # French
        "divorce", "garde", "violence conjugale",
        # Spanish
        "divorcio", "custodia", "violencia doméstica",
        # Zulu
        "ukushaywa", "abantwana",
    ],
    CaseType.IMMIGRATION: [
        "visa", "deportation", "deport", "asylum", "refugee", "immigration",
        "undocumented", "citizenship", "border", "stateless", "no documents",
        "passport confiscated", "kafala", "absconding charge",
        # Urdu
        "ویزا", "پناہ گزین", "بے وطن", "ملک بدری",
        # Bengali
        "ভিসা", "শরণার্থী", "নির্বাসন", "রোহিঙ্গা",
        # Arabic
        "لاجئ", "ترحيل", "تأشيرة", "لجوء",
        # Indonesian
        "deportasi", "suaka", "pengungsi", "visa",
        # French
        "expulsion", "asile", "réfugié", "visa",
        # Spanish
        "deportación", "asilo", "refugiado", "visa",
        # Russian
        "депортация", "убежище", "беженец", "виза",
    ],
    CaseType.CONSUMER: [
        "fraud", "scam", "refund", "consumer", "product", "defective",
        "warranty", "debt collector",
        # Urdu
        "دھوکہ", "واپسی", "صارف",
        # Arabic
        "احتيال", "استرداد", "مستهلك",
        # Indonesian
        "penipuan", "konsumen", "produk cacat",
        # French
        "fraude", "remboursement", "consommateur",
        # Spanish
        "fraude", "reembolso", "consumidor",
    ],
    CaseType.CIVIL: [
        "lawsuit", "sue", "contract", "breach", "damages", "compensation",
        "negligence",
        # Urdu
        "مقدمہ", "معاوضہ", "عدالت",
        # Arabic
        "دعوى", "تعويض", "عقد",
        # Indonesian
        "gugatan", "ganti rugi", "kontrak",
        # French
        "procès", "indemnisation", "contrat",
        # Spanish
        "demanda", "indemnización", "contrato",
    ],
    CaseType.HUMAN_RIGHTS: [
        "torture", "discrimination", "rights violation", "freedom", "arbitrary",
        "persecution", "execution", "killed", "murdered",
        # Urdu
        "تعذیب", "امتیازی سلوک", "ظلم",
        # Bengali
        "নির্যাতন", "বৈষম্য",
        # Arabic
        "تعذيب", "اضطهاد", "انتهاك حقوق",
        # Indonesian
        "penyiksaan", "diskriminasi",
        # French
        "torture", "discrimination", "persécution",
        # Spanish
        "tortura", "discriminación", "persecución",
        # Russian
        "пытки", "дискриминация", "преследование",
    ],
}

# ── Urgency keywords ──────────────────────────────────────────────────────────

URGENCY_CRITICAL_KEYWORDS = [
    "tonight", "today", "right now", "immediately", "emergency", "arrested",
    "being evicted", "locked out", "deported", "deportation tonight",
    "nowhere to sleep", "nowhere to go", "cannot contact", "don't know where",
    "being killed", "will be killed", "threatening to deport",
    # Urdu
    "آج رات", "ابھی", "فوری", "گرفتار",
    # Bengali
    "আজ রাতে", "এখনই", "জরুরি", "গ্রেফতার",
    # Hindi
    "आज रात", "अभी", "आपातकाल",
    # Arabic
    "الليلة", "الآن", "طوارئ", "اعتقل",
    # Indonesian
    "malam ini", "segera", "darurat", "ditangkap",
    # Swahili
    "usiku huu", "haraka", "dharura",
    # French
    "ce soir", "maintenant", "urgence", "arrêté",
    # Spanish
    "esta noche", "ahora", "urgente", "arrestado",
    # Russian
    "сегодня ночью", "сейчас", "срочно", "арестован",
    # Turkish
    "bu gece", "şimdi", "acil", "tutuklandım",
]

URGENCY_HIGH_KEYWORDS = [
    "tomorrow", "this week", "court date", "hearing", "deadline",
    "24 hours", "48 hours", "months unpaid", "haven't paid",
    # Urdu
    "کل", "عدالت", "مہینوں سے",
    # Bengali
    "কাল", "আদালত", "মাস ধরে",
    # Arabic
    "غداً", "المحكمة", "أشهر",
    # Indonesian
    "besok", "sidang", "tenggat", "berbulan-bulan",
    # Swahili
    "kesho", "mahakama", "miezi",
    # French
    "demain", "audience", "échéance",
    # Spanish
    "mañana", "audiencia", "plazo",
]

# ── Specialist flags ──────────────────────────────────────────────────────────

STATELESS_KEYWORDS = [
    "no documents", "no passport", "no id", "no papers", "undocumented",
    "stateless", "rohingya", "no nationality", "no legal status",
    "no citizenship", "لا وثائق", "بلا دستاویز",
    "কোনো কাগজ নেই", "কোনো পাসপোর্ট নেই",
    "sans papiers", "sin documentos", "без документов",
]

MINOR_KEYWORDS = [
    "year-old", "years old", "years-old",
    "my son", "my daughter", "my child", "my kid", "my baby",
    "14-year", "15-year", "16-year", "17-year", "13-year",
    "12-year", "11-year", "10-year", "minor", "juvenile",
    # Urdu
    "میرا بیٹا", "میری بیٹی", "بچہ", "بچی",
    # Bengali
    "আমার ছেলে", "আমার মেয়ে", "শিশু",
    # Hindi
    "मेरा बेटा", "मेरी बेटी", "बच्चा",
    # Arabic
    "ابني", "ابنتي", "طفل", "قاصر",
    # Indonesian
    "anak saya", "putra saya", "putri saya",
    # Swahili
    "mtoto wangu", "mwanangu",
    # French
    "mon fils", "ma fille", "mon enfant", "mineur",
    # Spanish
    "mi hijo", "mi hija", "mi hijo menor", "menor",
]

DEPORTATION_KEYWORDS = [
    "deport", "deportation", "threatening to deport", "remove", "removal order",
    "illegal entry", "send back", "will be sent", "return to",
    "ملک بدر", "ملک بدری", "بے دخل",
    "نির্বাসন", "ফেরত পাঠানো",
    "deportasi", "akan dideportasi",
    "expulsion", "expulsé", "deportación", "deportar",
    "депортация", "депортировать",
    "ترحيل", "يرحّلني",
]

TRAFFICKING_KEYWORDS = [
    "passport confiscated", "took my passport", "holding my passport",
    "confiscated my passport", "not allowed to leave", "cannot leave",
    "locked in", "cannot go out", "trafficking", "forced labour",
    "forced labor", "bonded labour", "debt bondage", "placement fee",
    "recruitment debt", "kafala", "domestic worker",
]

CHILD_ABDUCTION_KEYWORDS = [
    "took my children", "took the children", "took my kids", "took my son",
    "took my daughter", "children taken", "abducted", "kidnapped my child",
    "won't let me see", "denied access to my child",
    # Urdu
    "بچوں کو لے گئے", "بچے لے گئے",
    # Bengali
    "সন্তান নিয়ে গেছে", "বাচ্চা নিয়ে গেছে",
    # Hindi
    "बच्चों को ले गया", "बच्चे ले गए",
    # Arabic
    "اختطف أطفالي", "أخذ أطفالي",
    # French
    "a pris mes enfants", "enlèvement",
    # Spanish
    "se llevó a mis hijos", "secuestro",
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
    Supports 50+ countries with native script detection.
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
        try:
            return self._get_lang_detector()(text)
        except Exception:
            return "en"

    def detect_jurisdiction(self, text: str) -> tuple[str, str]:
        """
        Returns (country_code, jurisdiction_string).
        Step 1: Native script city lookup (Urdu, Bengali, Hindi, Arabic, etc.)
        Step 2: Latin-script keyword hints fallback.
        """
        # Native script — substring match anywhere in text
        for city, code in NATIVE_SCRIPT_CITIES.items():
            if city in text:
                print(f"[Classifier] Native script match: '{city}' → {code}")
                return code, code

        # Latin-script fallback
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
        if _check_keywords(text, ["arrest", "jail", "prison",
                                   "گرفتار", "গ্রেফতার", "ditangkap",
                                   "arrêté", "arrestado", "арестован"]):
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

        # Trafficking triad
        has_passport = _check_keywords(text, [
            "passport confiscated", "took my passport",
            "holding my passport", "confiscated my passport",
        ])
        has_unpaid = _check_keywords(text, [
            "not paid", "unpaid", "haven't paid", "hasn't paid",
            "no salary", "no wages", "7 months", "6 months", "5 months",
        ])
        has_no_movement = _check_keywords(text, [
            "not allowed to leave", "cannot leave",
            "locked in", "cannot go out",
        ])
        if has_passport and (has_unpaid or has_no_movement):
            flags["trafficking_indicators"] = True
        if _check_keywords(text, ["trafficking", "forced labour", "forced labor",
                                   "debt bondage", "kafala"]):
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

        # Urgency overrides
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
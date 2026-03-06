import sqlite3

conn = sqlite3.connect("jobs.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company TEXT,
    title TEXT,
    salary_from INTEGER,
    salary_to INTEGER,
    skills TEXT,
    level TEXT,
    category TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    interests TEXT,
    skills TEXT,
    history TEXT
)
""")

jobs_data = [
    ("TechNova", "Senior Python Developer", 120000, 180000, "Python, Django, PostgreSQL, Docker", "сложно", "IT"),
    ("DesignStudio", "UI/UX Designer", 80000, 120000, "Figma, Adobe XD, UI Design, Prototyping", "средне", "Дизайн"),
    ("DataVision", "Data Scientist", 100000, 160000, "Python, Machine Learning, TensorFlow, SQL", "сложно", "Наука"),
    ("CloudSys", "DevOps Engineer", 110000, 150000, "Kubernetes, Docker, AWS, CI/CD", "сложно", "IT"),
    ("PixelArt", "Graphic Designer", 60000, 90000, "Photoshop, Illustrator, CorelDRAW", "средне", "Дизайн"),
    ("StartupHub", "Junior Frontend Developer", 50000, 80000, "JavaScript, React, HTML, CSS", "легко", "IT"),
    ("AnalyticsPro", "Business Analyst", 75000, 110000, "Excel, SQL, Power BI, Requirements Analysis", "средне", "Бизнес"),
    ("InnovateLab", "Research Scientist", 95000, 150000, "Research, Python, Statistics, Experiments", "сложно", "Наука"),
    ("NeuralNet", "Machine Learning Engineer", 130000, 200000, "TensorFlow, PyTorch, Python, Deep Learning", "сложно", "IT"),
    ("BrandBoost", "Marketing Manager", 70000, 105000, "Marketing Strategy, Analytics, Content Management", "средне", "Маркетинг"),
    ("CodeFactory", "Full Stack Developer", 90000, 140000, "JavaScript, Node.js, React, MongoDB", "средне", "IT"),
    ("ArtGenius", "3D Artist", 70000, 110000, "Blender, 3D Modeling, Texturing, Animation", "средне", "Дизайн"),
    ("InfoTech", "Network Administrator", 65000, 95000, "Networking, Linux, Windows Server, Cisco", "средне", "IT"),
    ("Scientific", "Lab Technician", 40000, 65000, "Laboratory Techniques, Safety Protocols, Testing", "легко", "Наука"),
    ("CreativeHub", "Content Creator", 50000, 80000, "Video Editing, Photography, Social Media", "средне", "Дизайн"),
    ("WebGiant", "Backend Developer", 95000, 145000, "Python, Java, RESTful APIs, Microservices", "средне", "IT"),
    ("MediaWorks", "Motion Graphics Designer", 75000, 115000, "After Effects, Cinema 4D, Animation", "средне", "Дизайн"),
    ("DataCore", "Data Analyst", 70000, 105000, "SQL, Python, Tableau, Statistical Analysis", "средне", "IT"),
    ("AcademiaPro", "Research Assistant", 35000, 55000, "Research, Data Collection, Report Writing", "легко", "Наука"),
    ("MarketingGenius", "Social Media Manager", 50000, 80000, "Social Media, Content Strategy, Analytics", "средне", "Маркетинг"),
    ("SystemsPlus", "System Administrator", 80000, 120000, "Windows, Linux, Active Directory, Backup", "средне", "IT"),
    ("InnovationHub", "Product Manager", 100000, 150000, "Product Strategy, Roadmapping, Analytics", "сложно", "Бизнес"),
    ("VisualStudio", "Web Designer", 65000, 100000, "Web Design, UX, Responsive Design, CMS", "средне", "Дизайн"),
    ("ResearchLab", "Physicist", 85000, 130000, "Physics, Experimental Design, Simulation", "сложно", "Наука"),
    ("ITConsult", "IT Project Manager", 85000, 130000, "Project Management, Agile, Leadership", "средне", "IT"),
    ("DesignForce", "Brand Designer", 70000, 110000, "Brand Design, Logo Design, Visual Identity", "средне", "Дизайн"),
    ("SmartData", "Software Engineer", 100000, 160000, "C++, Java, Software Architecture, Algorithms", "сложно", "IT"),
    ("CreativeThink", "Copywriter", 45000, 75000, "Writing, Social Media, Content Creation", "средне", "Маркетинг"),
    ("LabScience", "Chemist", 70000, 110000, "Chemistry, Laboratory Skills, Analysis, Safety", "средне", "Наука"),
    ("TechSupport", "Support Engineer", 40000, 65000, "Customer Support, Troubleshooting, Ticketing", "легко", "IT"),
]

cursor.executemany("""
INSERT INTO jobs (company, title, salary_from, salary_to, skills, level, category)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", jobs_data)

conn.commit()
conn.close()
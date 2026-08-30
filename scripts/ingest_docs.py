import os
import sys
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from dotenv import load_dotenv
from google import genai
from supabase import create_client
from rich.console import Console
from rich.progress import track

load_dotenv()
console = Console()

gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_SERVICE_KEY"))

DOCS = [
    {"id": "nafdac_food", "title": "NAFDAC Food Registration Requirements", "body": "NAFDAC", "category": "food_beverage", "content": """NAFDAC Food Product Registration Requirements Nigeria. All food products manufactured or imported into Nigeria for commercial sale must be registered with NAFDAC. Required documents: Completed NAFDAC application form, Certificate of Incorporation from CAC, Evidence of premises, GMP compliance evidence, Product samples minimum 3, List of ingredients with quantities, Safety evidence for ingredients, Proposed label artwork complying with NAFDAC labelling requirements, Nutritional information panel, Shelf life study report, Manufacturing flow chart, Water analysis report if water is ingredient, Application fee payment. NAFDAC labelling requirements: Product name, ingredients in descending order of weight, net content, NAFDAC registration number, manufacturer name and address, country of origin, best before date, storage instructions, nutritional information per serving and per 100g. Registration timeline 3 to 6 months for new food products. Annual renewal required. Small scale producers NAFDAC with SMEDAN simplified registration pathway for annual turnover below threshold. Reduced fees and streamlined documentation. Facility inspection required before registration granted. GMP standards mandatory."""},
    {"id": "nafdac_cosmetics", "title": "NAFDAC Cosmetics Registration Requirements", "body": "NAFDAC", "category": "cosmetics", "content": """NAFDAC Cosmetics Regulation Nigeria. All cosmetic products sold in Nigeria must be notified or registered with NAFDAC before commercial distribution. Cosmetics defined as products applied to human body for cleansing beautifying promoting attractiveness or altering appearance. Examples skin creams lotions hair products nail products lip products deodorants. NAFDAC Cosmetics Notification versus Registration: Low risk cosmetics notification pathway faster approximately 1 to 3 months. Higher risk or therapeutic cosmetics full registration required. Required documents: Completed NAFDAC application form for cosmetics, CAC certificate of incorporation or business name, Product formula ingredient list INCI nomenclature required, Certificate of analysis, Safety data for each ingredient, Proposed label conforming to NAFDAC cosmetics labelling guidelines, Product samples, GMP certificate for locally manufactured products, Import permit and manufacturer certificate for imported cosmetics. Prohibited and restricted ingredients: Hydroquinone above 2 percent prohibited in Nigeria. Mercury compounds prohibited. Kojic acid restricted concentration limits apply typically 1 percent or below. Corticosteroids in cosmetics prohibited unless prescription only. Products making therapeutic or drug claims reclassified as drugs. Cosmetics for children stricter scrutiny additional safety data required. Imported cosmetics require NAFDAC import permit and original manufacturer authorization for rebranding or relabelling. Health claims on cosmetics: Claims such as clinically proven medically tested or specific therapeutic outcomes may cause reclassification as drug or pharmaceutical product requiring different and more rigorous registration pathway."""},
    {"id": "nafdac_supplements", "title": "NAFDAC Dietary Supplement and Herbal Registration", "body": "NAFDAC", "category": "dietary_supplement", "content": """NAFDAC Dietary Supplement and Herbal Product Registration Nigeria. Dietary supplements and herbal medicines regulated by NAFDAC under separate guidelines from food and pharmaceutical drugs. Categories regulated: Herbal medicines plant based therapeutic products, Dietary supplements vitamins minerals amino acids botanicals, Traditional medicines. Registration requirements: Completed NAFDAC application form, CAC registration certificate, List of ingredients with quantities and INCI or pharmacopoeial names, Certificate of analysis for each ingredient, Safety and efficacy data, Proposed label complying with NAFDAC guidelines, Product samples minimum 6, GMP certificate for manufacturing facility, Stability data shelf life study. Health claims regulation: Structure function claims such as supports immune health permitted with substantiation. Disease claims such as treats diabetes prohibited unless registered as drug. Immune booster claims under increased NAFDAC scrutiny require scientific backing. Paediatric supplements for children under 12: Additional safety data required. Iron containing supplements for children have specific dosage caps. Child resistant packaging required for certain ingredients. NAFDAC review timeline longer for paediatric products. Herbal products timeline registration typically 6 to 12 months due to additional traditional use documentation and efficacy review. GMP compliance mandatory manufacturing facilities must pass NAFDAC GMP inspection. Imported supplements require NAFDAC import permit certificate of free sale from country of origin and manufacturer authorisation."""},
    {"id": "cac_registration", "title": "CAC Business Registration Requirements Nigeria", "body": "CAC", "category": "general", "content": """Corporate Affairs Commission CAC Business Registration Nigeria. Before applying for NAFDAC or SON registration business must first be registered with CAC. Business structures available: Business Name Sole Proprietorship or Partnership simplest for small businesses. Private Limited Company Ltd recommended for product businesses seeking investment or export. Public Limited Company PLC for publicly traded entities. Business Name Registration requirements: Proposed business name minimum 2 options in order of preference, Nature of business description, Proprietor valid ID national ID passport or driver licence, Proprietor signature specimen, Current passport photograph, Address of business physical address required, Payment of registration fee. Private Limited Company requirements: Proposed company name, Memorandum and Articles of Association, Details of minimum 1 director max 50 shareholders for private company, Details of company secretary, Registered address in Nigeria, Share capital declaration, Payment of registration fees. Timeline Business Name registration typically 1 to 3 business days online via CAC portal. Company incorporation typically 5 to 10 business days. CAC registration prerequisite for NAFDAC application. NAFDAC requires valid CAC certificate before processing product registration. CAC registration number also required for opening corporate bank account, tax registration with FIRS, NEPC exporter registration."""},
    {"id": "son_standards", "title": "Standards Organisation of Nigeria SON Consumer Goods Standards", "body": "SON", "category": "general", "content": """Standards Organisation of Nigeria SON role in consumer goods compliance. SON responsible for developing and enforcing standards for products and services in Nigeria. Key SON functions relevant to consumer goods founders: Product certification SON certification mark, Mandatory conformity assessment for regulated products, Standards for packaging and labelling, Quality mark scheme for locally manufactured goods. Products requiring mandatory SON certification: Edible oils and fats, Bottled water and beverages, Selected food products, Packaging materials. SON Product Certification process: Application to SON, Document review product specification test reports, Product testing at SON accredited laboratory, Factory inspection if locally manufactured, Certification granted if product meets relevant Nigerian Industrial Standard NIS, Annual surveillance audits. SON and food products: Certain food products require both NAFDAC registration and SON certification. Edible oils flour and packaged water commonly require both. SON and packaging: Net weight accuracy is SON enforcement area. Products must contain stated net quantity within acceptable tolerance limits. Underweight packaging is an offence. SON import inspection: Imported goods covered under SON mandatory conformity assessment require pre shipment inspection and SON import permit before clearing customs. NAFDAC and SON have Memorandum of Understanding to avoid duplication. For food products NAFDAC is primary regulator but SON standards for packaging and labelling still apply."""},
    {"id": "nafdac_import", "title": "NAFDAC Import Permit and Export Certificate Requirements", "body": "NAFDAC", "category": "import", "content": """NAFDAC Import and Export Regulations for Consumer Goods Nigeria. Import of regulated products into Nigeria: All NAFDAC regulated products food cosmetics supplements drugs medical devices require valid NAFDAC import permit before importation. NAFDAC Import Permit requirements: Completed NAFDAC import permit application, CAC registration certificate, Proforma invoice from foreign supplier, Manufacturer certificate confirming manufacturer details, Certificate of free sale from country of origin, Product registration certificate if already registered in Nigeria, Test report Certificate of analysis, Full product label. Imported products must also be registered with NAFDAC if to be sold in Nigeria. Import permit and product registration are separate requirements. Rebranding and relabelling imported products: Requires manufacturer written authorisation. Rebranding facility must be registered with NAFDAC. The rebranded product may require its own NAFDAC registration separate from the original. NAFDAC Export Certificate: Nigerian manufacturers wishing to export NAFDAC regulated products require NAFDAC certificate of free sale or export certificate, valid product registration in Nigeria, GMP compliance certificate, application and fee payment. NEPC Nigerian Export Promotion Council exporters should register with NEPC for exporter registration certificate, access to export incentives and market information, export expansion grant where applicable. Products exported to UK must comply with UK Food Safety Act 1990. Products for EU must comply with EU cosmetics or food regulations as applicable."""},
]

CHUNK_SIZE = 400

def chunk_text(text, size=CHUNK_SIZE):
    words = text.split()
    chunks = []
    i = 0
    while i < len(words):
        chunks.append(" ".join(words[i:i+size]))
        i += size - 50
    return chunks

def get_embedding(text):
    response = gemini_client.models.embed_content(
        model="models/gemini-embedding-2",
        contents=text
    )
    return response.embeddings[0].values

def ingest_all():
    console.print("[bold cyan]Oja Document Ingestion[/bold cyan]")
    total = 0
    for doc in track(DOCS, description="Embedding and storing..."):
        chunks = chunk_text(doc["content"])
        for i, chunk in enumerate(chunks):
            chunk_id = f"{doc['id']}_chunk_{i}"
            embedding = get_embedding(chunk)
            time.sleep(0.1)
            supabase.table("oja_documents").upsert({
                "id": chunk_id,
                "doc_id": doc["id"],
                "title": doc["title"],
                "body": doc["body"],
                "category": doc["category"],
                "content": chunk,
                "embedding": embedding,
                "source": "synthetic"
            }).execute()
            total += 1
    console.print(f"[bold green]Done. {total} chunks stored.[/bold green]")

if __name__ == "__main__":
    ingest_all()

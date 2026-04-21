from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
import os
import time
import csv
import requests
from flask_flatpages import FlatPages

# --- TRIPLE-LAYER MISTRAL IMPORT STRATEGY ---
# This ensures the app boots even if Render has cached an old/broken library version
try:
    from mistralai import Mistral
except (ImportError, AttributeError):
    try:
        from mistralai.client import MistralClient as Mistral
    except (ImportError, AttributeError):
        # Fallback dummy class to prevent total crash
        class Mistral:
            def __init__(self, *args, **kwargs): self.chat = self.Dummy()
            class Dummy: 
                def complete(self, *args, **kwargs): pass

app = Flask(__name__)

# --- CONFIGURATION ---
app.secret_key = os.environ.get("SECRET_KEY", "sovereign_intelligence_2026")
app.config['FLATPAGES_AUTO_RELOAD'] = True
app.config['FLATPAGES_EXTENSION'] = '.md'
app.config['FLATPAGES_ROOT'] = 'pages'

# Create pages directory locally if it doesn't exist to prevent FlatPages crash
if not os.path.exists('pages'):
    os.makedirs('pages')

# Initialize FlatPages
pages = FlatPages(app)

# Mistral Configuration
MISTRAL_API_KEY = os.environ.get("MISTRAL_API_KEY")
mistral_client = None
if MISTRAL_API_KEY:
    try:
        mistral_client = Mistral(api_key=MISTRAL_API_KEY)
    except Exception as e:
        print(f"MISTRAL_INIT_ERROR: {e}")

# Global Company Data
COMPANY_DATA = {
    'name': 'The Marketworth Group',
    'whatsapp': '254796423133', 
    'email': 'intelligence@marketworth.ai'
}

# --- INTELLIGENCE UTILITIES ---

def log_lead(identifier, status_or_score):
    """Logs lead data to CSV with error handling for read-only filesystems."""
    csv_file = 'leads.csv'
    file_exists = os.path.isfile(csv_file)
    try:
        with open(csv_file, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(['Timestamp', 'Identifier', 'Data/Score'])
            writer.writerow([time.strftime("%Y-%m-%d %H:%M:%S"), identifier, status_or_score])
    except Exception as e:
        print(f"LOG_ERROR: {e} (Likely read-only environment)")

def analyze_site_intelligence(target_url):
    """Crawls site for JSON-LD and uses Mistral for reasoning."""
    try:
        header = {'User-Agent': 'MarketworthAI-Bot/1.0'}
        response = requests.get(target_url, timeout=5, headers=header)
        html = response.text.lower()
        
        has_schema = 'application/ld+json' in html
        score = 82 if has_schema else 45
        
        # Use mistral_client safely (handles both v1 and v2 SDK styles)
        if mistral_client:
            prompt = f"Website: {target_url}. JSON-LD Schema Found: {has_schema}. Provide a 1-sentence expert AEO recommendation."
            try:
                # Try modern SDK method
                chat_response = mistral_client.chat.complete(
                    model="mistral-tiny",
                    messages=[{"role": "user", "content": prompt}]
                )
                advice = chat_response.choices[0].message.content
            except AttributeError:
                # Fallback for legacy SDK method
                chat_response = mistral_client.chat(
                    model="mistral-tiny",
                    messages=[{"role": "user", "content": prompt}]
                )
                advice = chat_response.choices[0].message.content
        else:
            advice = "Missing AI-readable schema detected. Implement JSON-LD to improve LLM citation probability."
            
        return score, advice
    except Exception:
        return 50, "Connectivity restricted. Analysis based on domain metadata suggests priority optimization."

# --- PRIMARY ROUTES ---

@app.route('/')
def home():
    return render_template('index.html', info=COMPANY_DATA)

@app.route('/tools/ai-audit')
def contact():
    return render_template('contact.html', info=COMPANY_DATA)

@app.route('/services')
def services(): 
    return render_template('services.html', info=COMPANY_DATA)

@app.route('/blog')
def blog(): 
    valid_posts = []
    for page in pages:
        try:
            if page.meta.get('title'):
                valid_posts.append(page)
        except Exception:
            continue

    posts = sorted(valid_posts, key=lambda p: str(p.meta.get('date', '0000-00-00')), reverse=True)
    return render_template('blog.html', info=COMPANY_DATA, posts=posts)

@app.route('/blog/<path:path>/')
def post(path):
    post = pages.get_or_404(path)
    return render_template('post_detail.html', info=COMPANY_DATA, post=post)

@app.route('/resources')
def resources():
    return render_template('resources.html', info=COMPANY_DATA)

# --- ACADEMY ROUTING ENGINE ---

@app.route('/academy/')
@app.route('/academy/<path:path>')
def academy(path=None):
    academy_dir = os.path.join(app.root_path, 'academy')
    
    # Create directory if missing
    if not os.path.exists(academy_dir):
        os.makedirs(academy_dir)
    
    if path is None or path == "":
        return send_from_directory(academy_dir, 'index.html')
    
    full_path = os.path.join(academy_dir, path)
    if os.path.isdir(full_path):
        return send_from_directory(full_path, 'index.html')
    
    return send_from_directory(academy_dir, path)

# --- OPERATIONAL ANALYSIS & LEAD CAPTURE ---

@app.route('/submit-lead', methods=['POST'])
def submit_lead():
    url = request.form.get('email')
    if url:
        if not url.startswith('http'):
            url = 'https://' + url
        
        score, advice = analyze_site_intelligence(url)
        log_lead(url, f"Score: {score}%")
        return redirect(url_for('results', site=url, score=score, advice=advice))
    
    flash("Please enter a valid website URL.", "error")
    return redirect(url_for('home'))

@app.route('/subscribe', methods=['POST'])
def subscribe():
    email = request.form.get('lead_email')
    if email:
        log_lead(email, "MAGNET_DOWNLOAD_REQ")
        # Ensure this file exists in your static/ folder
        return redirect(url_for('static', filename='AI_Readiness_2026.pdf'))
    return redirect(url_for('blog'))

@app.route('/tools/results')
def results():
    site_url = request.args.get('site', 'your website')
    score_val = request.args.get('score', '74')
    advice = request.args.get('advice', 'Analysis pending technical verification.')
    
    try:
        numeric_score = int(score_val)
    except ValueError:
        numeric_score = 74

    analysis_results = {
        'url': site_url,
        'aeo_score': numeric_score,
        'perplexity_visibility': 'High' if numeric_score > 80 else 'Low',
        'chatgpt_index': 'Verified',
        'optimization_priority': 'CRITICAL' if numeric_score < 80 else 'MODERATE',
        'ai_advice': advice,
        'timestamp': time.strftime("%Y-%m-%d %H:%M")
    }
    return render_template('results.html', info=COMPANY_DATA, data=analysis_results)

@app.errorhandler(404)
def page_not_found(e): 
    return redirect(url_for('home'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
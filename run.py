from flask import Flask, request, jsonify, send_from_directory
import google.generativeai as genai
import os
import re
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)

users = {}

@app.route("/signup", methods=["POST"])
def signup():
    data = request.json
    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    if email in users:
        return jsonify({"error": "User  already exists"}), 400

    users[email] = {"name": name, "password": password}
    return jsonify({"message": "User  created successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    user = users.get(email)
    if user and user["password"] == password:
        return jsonify({"message": "Login successful"}), 200
    return jsonify({"error": "Invalid credentials"}), 401
 


genai.configure(api_key="AIzaSyC10gnIogn1voJf0TqVInQzfKnYJdON76A")
model = genai.GenerativeModel("gemini-1.5-flash")


@app.route("/")
def home():
    return send_from_directory(os.getcwd(), "frontend.html")


def format_mcqs(questions_text):
    html_output = ""
    
    # Split by question numbers (handles both "1." and "Question 1:" formats)
    question_blocks = re.split(r'(?=\n?\d+\.|\nQuestion\s+\d+:)', questions_text)
    question_blocks = [q.strip() for q in question_blocks if q.strip()]
    
    for block in question_blocks:
        if not block:
            continue
            
        # Extract question number and text
        question_match = re.match(r'^(?:(?P<num>\d+)\.|Question\s+(?P<num2>\d+):)\s*(?P<text>.*?)(?=\n[A-D]\.|\n\([A-D]|$)', block, re.DOTALL)
        
        if not question_match:
            continue
            
        question_num = question_match.group('num') or question_match.group('num2')
        question_text = question_match.group('text').strip()
        
        html_output += f'<div class="border-2 border-gray-300 rounded-lg p-4 mb-4 shadow-sm">'
        html_output += f'<p class="font-bold mb-2">{question_num}. {question_text}</p>'
        
        # Extract options
        options_section = block[question_match.end():].strip()
        options = re.findall(r'^\s*([A-D])[\.\)]\s*(.*?)(?=\n[A-D][\.\)]|\nAnswer:|$)', options_section, re.MULTILINE | re.DOTALL)
        
        html_output += '<div class="pl-4">'
        for option_letter, option_text in options:
            html_output += f'<p class="mb-1">{option_letter}. {option_text.strip()}</p>'
        html_output += '</div>'
        
        # Extract correct answer
        answer_match = re.search(r'Answer:\s*([A-D])', block, re.IGNORECASE)
        if answer_match:
            html_output += f'''
            <div class="mt-3">
                <button class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">Show Answer</button>
                <p class="hidden mt-2 font-bold text-green-600">Correct Answer: {answer_match.group(1)}</p>
            </div>
            '''
        
        html_output += '</div>'
    
    return html_output

def format_assessment(questions_text):
    html_output = ""
    questions = re.split(r'(?=Question\s+\d+:)', questions_text)
    
    for question in questions:
        if not question.strip():
            continue
            
        parts = re.split(r'(Answer:)', question, maxsplit=1, flags=re.IGNORECASE)
        question_text = parts[0].strip()
        answer_text = parts[-1].strip() if len(parts) > 2 else "No answer provided"
        
        html_output += f'''
        <div class="question-box">
            <div class="question">{question_text}</div>
            <div class="answer hidden">{answer_text}</div>
            <button class="show-answer-btn">Show Answer</button>
        </div>
        '''
    
    return html_output

def format_case_study(questions_text):
    html_output = ""
    
    case_study_match = re.search(r'(Case Study|CASE STUDY|Scenario)(?:\s*\d+)?:?\s*(.*?)(?=\d+\.|\bQuestion\s+\d+:|$)', questions_text, re.DOTALL | re.IGNORECASE)
    
    if case_study_match:
        case_study_title = case_study_match.group(1).strip()
        case_study_text = case_study_match.group(2).strip()
        
        html_output += '<div class="border-2 border-gray-300 rounded-lg p-4 mb-4 shadow-sm">'
        
        html_output += f'<h3 class="font-bold text-xl mb-2">{case_study_title}</h3>'
        html_output += f'<p class="mb-4">{case_study_text}</p>'
        
        remaining_text = questions_text[len(case_study_match.group(0)):].strip()
        
        question_blocks = re.split(r'(?=\d+\.|\bQuestion\s+\d+:)', remaining_text)
        question_blocks = [q.strip() for q in question_blocks if q.strip()]
        
        for q_block in question_blocks:
            question_parts = q_block.split("Answer:", 1)
            
            if len(question_parts) > 0:
                question_text = question_parts[0].strip()
                html_output += f'<p class="font-bold mt-3 mb-2">{question_text}</p>'
                
                if len(question_parts) > 1:
                    answer_text = question_parts[1].strip()
                    html_output += f'''
                    <div class="mt-2 mb-4">
                        <button class="bg-blue-500 hover:bg-blue-600 text-white px-3 py-1 rounded text-sm">Show Answer</button>
                        <p class="hidden mt-2">{answer_text}</p>
                    </div>
                    '''
        
        html_output += '</div>'
    else:
        html_output += f'<div class="border-2 border-gray-300 rounded-lg p-4 mb-4 shadow-sm"><p>{questions_text}</p></div>'
    
    return html_output

def format_ppt_content(ppt_text):
    html_output = ""
    
    slides = re.split(r'(?=Slide\s+\d+:|^\d+\.\s+)', ppt_text, flags=re.MULTILINE)
    
    if len(slides) <= 1:
        slides = ppt_text.split('\n\n')
    
    slides = [s.strip() for s in slides if s.strip()]
    
    for slide in slides:
        html_output += '<div class="border-2 border-gray-300 rounded-lg p-4 mb-4 shadow-sm bg-gray-50">'
        
        title_match = re.match(r'(Slide\s+\d+:|^\d+\.\s+)(.*?)(?=\n|$)', slide, re.MULTILINE)
        
        if title_match:
            slide_number = title_match.group(1).strip()
            slide_title = title_match.group(2).strip()
            
            html_output += f'<h3 class="font-bold text-lg mb-2">{slide_number} {slide_title}</h3>'
            
            content = slide[len(title_match.group(0)):].strip()
            
            if re.search(r'^\s*[-•*]\s+', content, re.MULTILINE):
                bullet_points = re.split(r'\n(?=\s*[-•*]\s+)', content)
                html_output += '<ul class="list-disc pl-5 space-y-1">'
                for point in bullet_points:
                    point = re.sub(r'^\s*[-•*]\s+', '', point).strip()
                    html_output += f'<li>{point}</li>'
                html_output += '</ul>'
            else:
                paragraphs = content.split('\n')
                for para in paragraphs:
                    if para.strip():
                        html_output += f'<p class="mb-2">{para.strip()}</p>'
        else:
            if re.search(r'^\s*[-•*]\s+', slide, re.MULTILINE):
                bullet_points = re.split(r'\n(?=\s*[-•*]\s+)', slide)
                html_output += '<ul class="list-disc pl-5 space-y-1">'
                for point in bullet_points:
                    point = re.sub(r'^\s*[-•*]\s+', '', point).strip()
                    html_output += f'<li>{point}</li>'
                html_output += '</ul>'
            else:
                paragraphs = slide.split('\n')
                for para in paragraphs:
                    if para.strip():
                        html_output += f'<p class="mb-2">{para.strip()}</p>'
        
        html_output += '</div>'
    
    return html_output

def generate_questions(topic, difficulty, question_type, num_questions):
    if question_type.lower() == "mcqs":
        prompt = f"Generate {num_questions} multiple choice questions on '{topic}' with {difficulty} difficulty. Each MCQ should have 4 options labeled A, B, C, D with one correct answer clearly indicated at the end with 'Answer: X'. Format the output with the question number followed by the question text, then options A through D, and finally mark the correct answer."
    
    elif question_type.lower() == "assessment type":
        prompt = f"Generate {num_questions} assessment questions on '{topic}' with {difficulty} difficulty.For each question, follow this exact format:Question [number]: [question text] Answer: [detailed answer] Example:Question 1: Explain the concept of gravity. Answer: Gravity is a natural force that attracts objects with mass toward each other."
    
    elif question_type.lower() == "case study":
        prompt = f"Generate 1 case study on '{topic}' with {difficulty} difficulty. Start with 'Case Study:' followed by a detailed scenario. Then include {num_questions} questions labeled as 'Question 1:', 'Question 2:', etc. related to the case study. For each question, include an 'Answer:' section immediately after each question. All in the same content."
    
    response = model.generate_content(prompt)

    if response and hasattr(response, 'candidates'):
        raw_text = response.candidates[0].content.parts[0].text.strip()
        
        if question_type.lower() == "mcqs":
            return format_mcqs(raw_text)
        elif question_type.lower() == "assessment type":
            return format_assessment(raw_text)
        elif question_type.lower() == "case study":
            return format_case_study(raw_text)
        else:
            return raw_text
    else:
        return "Failed to generate questions."

def generate_ppt_content(topic, num_slides):
    prompt = f"Generate content for a {num_slides}-slide PowerPoint presentation on '{topic}'. Format each slide with 'Slide 1:', 'Slide 2:', etc. Each slide should have a clear title and key bullet points. The first slide should be an introduction and the last slide should be a summary or conclusion."
    
    response = model.generate_content(prompt)

    if response and hasattr(response, 'candidates'):
        raw_text = response.candidates[0].content.parts[0].text.strip()
        return format_ppt_content(raw_text)
    else:
        return "Failed to generate PPT content."

@app.route("/generate_questions", methods=["POST"])
def generate_questions_api():
    data = request.json
    topic = data.get("topic")
    difficulty = data.get("difficulty")
    question_type = data.get("question_type")
    num_questions = int(data.get("num_questions", 5))

    questions = generate_questions(topic, difficulty, question_type, num_questions)
    return jsonify({"questions": questions})

@app.route("/generate_ppt", methods=["POST"])
def generate_ppt_api():
    data = request.json
    topic = data.get("topic")
    num_slides = int(data.get("num_slides", 5))

    ppt_content = generate_ppt_content(topic, num_slides)
    return jsonify({"ppt_content": ppt_content})

if __name__ == "__main__":
    app.run(debug=True)

class Config:
    GEMINI_API_KEY = "AIzaSyC10gnIogn1voJf0TqVInQzfKnYJdON76A"
    MAX_RETRIES = 3
    TIMEOUT = 30

app = Flask(__name__)
app.config.from_object(Config)

try:
    genai.configure(api_key=Config.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-1.5-flash")
except Exception as e:
    print(f"Error initializing Gemini API: {e}")
    raise

def handle_api_errors(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    return decorated_function

@app.route("/")
@handle_api_errors
def home():
    try:
        return send_from_directory(os.getcwd(), "frontend.html")
    except FileNotFoundError:
        return "Frontend file not found", 404

@app.route("/generate_questions", methods=["POST"])
@handle_api_errors
def generate_questions_api():
    data = request.json
    if not all(key in data for key in ["topic", "difficulty", "question_type"]):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        num_questions = int(data.get("num_questions", 5))
        if num_questions <= 0:
            return jsonify({"error": "Number of questions must be positive"}), 400
    except ValueError:
        return jsonify({"error": "Invalid number format"}), 400

    questions = generate_questions(
        data["topic"],
        data["difficulty"],
        data["question_type"],
        num_questions
    )
    return jsonify({"questions": questions})

question_cache = {}
def generate_questions(topic, difficulty, question_type, num_questions):
    cache_key = f"{topic}_{difficulty}_{question_type}_{num_questions}"
    
    if cache_key in question_cache:
        return question_cache[cache_key]

   
    question_cache[cache_key] = formatted_output
    return formatted_output

@app.route("/generate_ppt", methods=["POST"])
@handle_api_errors
def generate_ppt_api():
    data = request.json
    if "topic" not in data:
        return jsonify({"error": "Topic is required"}), 400

    try:
        num_slides = int(data.get("num_slides", 5))
        if not (1 <= num_slides <= 20):  
            return jsonify({"error": "Number of slides must be between 1 and 20"}), 400
    except ValueError:
        return jsonify({"error": "Invalid number format"}), 400

    ppt_content = generate_ppt_content(data["topic"], num_slides)
    return jsonify({"ppt_content": ppt_content})


def cleanup_cache():
    if len(question_cache) > 100: 
        question_cache.clear()

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 5000))
        app.run(host="0.0.0.0", port=port, debug=True)
    except Exception as e:
        print(f"Failed to start server: {e}")
        
    app.run(debug=True)
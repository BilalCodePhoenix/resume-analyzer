from flask import Flask, render_template, request
from rapidfuzz import fuzz
import os #
import re
import PyPDF2
import spacy
import re

app = Flask(__name__) #initialize flask app

# Configure upload folder
UPLOAD_FOLDER = 'uploads' #folder to store uploaded files
ALLOWED_EXTENSIONS = {'pdf'}# only allow pdf files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #
                                             
# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")# loads a pre-trained english language model/ used for text analysis

def allowed_file(filename):# ensures that the uploaded file is a pdf
    return filename and '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def extract_text_from_pdf(pdf_path):#open the pdf file using pydf2 reads every page and extract the full text
    text = ""
    with open(pdf_path, "rb") as pdf_file:
        reader = PyPDF2.PdfReader(pdf_file)
        for page in reader.pages:
            text += page.extract_text() or ""
    return text

def normalize_text(s):#  added code after
    s = s.lower().strip()
    s = re.sub(r'\s+', ' ', s)  # remove extra spaces
    s = re.sub(r'[^a-z0-9\s\+\#]', '', s)  # remove unwanted chars but keep +, #
    return s


def analyze_resume(text):# analyze the resume text to extract sections like skills, education, and experience
    sections = {"skills": [], "education": [], "experience": []}# dictionary to store extracted sections
    current_section = None  

    headers = {# dictionary to map section headers to keywords/iterate through each each line of the resume text (finding the keywords that signal the start of a section)
        "skills": [
            "skills", "technical skills", "key skills", "strengths", "core competencies", "areas of expertise", "abilities"
        ],
        "education": [
            "education", "academic background", "qualifications", "academic qualifications", "educational background",
            "degrees", "certifications"
        ],
        "experience": [
            "experience", "work experience", "professional experience", "internship", "internships", "employment history",
            "projects", "project experience", "work history", "professional background", "intern experience", "roles"
        ]
    }

    ignore_keywords = [# keywords to ignore while extracting skills, education, and experience
        "nationality", "date of birth", "dob", "email", "phone", "contact", "address", "linkedin", "personal details", "name"
    ]

    print("Input Text:", text)  # Debugging: Print the input text

    for line in text.splitlines():# iterate through each line of the resume text
        line_clean = line.strip().lower()# strips() removes extra spaces and converts to lowercase
        found_section = None# initialize found_section to None
        for section, header_list in headers.items():# for every line it checks if the line matches any headers from the dictionary/ it finds a match(like skills, education, experience)
            if any(h in line_clean for h in header_list):
                found_section = section
                break

        if found_section:# if a section header is found, set current_section to that section/if a ssection header was just found, or if the line is blank, skip it and move on
            current_section = found_section
            continue
        elif line.strip() == "":
            continue

        if current_section == "skills":#if the current section is skills
            if not any(kw in line_clean for kw in ignore_keywords):# if the line does not contain any ignore keywords, it processes the skills
                for skill in line.replace(';', ',').replace('•', ',').replace('·', ',').split(','):#removes semicolons and bullet points, splits by commas unwanted characters
                    skill_clean = skill.strip(" -•·")# cleans up the skill string
                    if skill_clean and len(skill_clean.split()) <= 7:# checks if the skill is not empty and has 7 or fewer words / max words allowed for a skill is 7 then it will be added to the skill section
                        sections[current_section].append(skill_clean)# then it will added to the skills section

        elif current_section == "education":# if the cureent section is education
            edu_keywords = [# checks if the line has words related to education like bachelor, master, university
                "bachelor", "master", "phd", "university", "college", "degree", "school", "intermediate",
                "matric", "cgpa", "percentage", "gpa", "year", "certification", "course"
            ]
            if any(kw in line_clean for kw in edu_keywords) or any(char.isdigit() for char in line_clean):# if the line contains any education-related keywords or digits, it processes the education
                sections[current_section].append(line.strip())#adds the line to the education section

        elif current_section == "experience": # if the current section is experience
            if line.strip():# checks if the line is not empty
                match = re.search(r'\[([^\[\]]+)\]', line)# searches for text within square brackets in the line
                if match:# if a match is found, it extracts the organization name
                    org = match.group(1).strip()#initializes org variable with the matched group
                    sections[current_section].append(org)# adds the organization name to the experience section
                else:
                    sections[current_section].append(line.strip())# if no square brackets are found, it adds the line as is to the experience section/ if no match, just adds the full cleaned line to the experince section

    for key in sections:#converts each sections list to a set to remove duplicates and then converts it back to a list and stored cleaned results
        cleaned = list(set([l for l in sections[key] if l]))# removes empty strings from the list
        sections[key] = cleaned# updates the sections dictionary with cleaned lists

    # print("Extracted Sections:", sections)  # Debugging: Print the extracted sections '''changed code'''

    return sections# returns the sections dictionary containing skills, education, and experience

@app.route('/')# flask backend woute for the home page
def home():
    return render_template('front.html') #this will render the front.html template

@app.route('/user', methods=['GET', 'POST'])# route for the user page where users can upload their resume and ideal resume or job description
def seeker():# function to handle the user page logic(seeker function)
    result = None# initializes result to None/ prepares emplty variable to hold the final result and and analysis output
    # ideal_analysis = None# same as result, but for the ideal resume or job description
    # jd_analysis = None# same as result, but for the job description text

    if request.method == 'POST':# gets the resume and ideal resume or job description from the form submission/ if the request method is POST, it means the user has submitted the form
        user_file = request.files.get('resume_file')# gets the uploaded resume file
        ideal_file = request.files.get('ideal_file')# gets the uploaded ideal resume file
        jd_text = request.form.get('jd_text', '').strip()# gets the job description text from the form, if provided and strips() means it removes and unnecessary whitespace
        user_text = ideal_text2 = None # initializes user_text and ideal_text2 to None/ these will hold the extracted text from the uploaded files

        # Extract text from user's resume
        if user_file and allowed_file(user_file.filename):# checks if the user_file is provided and is a valid file type                                                         funciton    1 yours resume 
            user_path = os.path.join(app.config['UPLOAD_FOLDER'], user_file.filename)# constructs the file path for the uploaded resume
            user_file.save(user_path)# it saves the uploaded file to the specified path
            user_text = extract_text_from_pdf(user_path)# it extracts the text from the uploaded resume file
            
            
        
        
        # Extract text from ideal resume or use pasted job description
        if ideal_file and allowed_file(ideal_file.filename):# checks if the ideal_file is provided and is a valid file type                                                       function  2 uploaded resume /ideal
            ideal_path = os.path.join(app.config['UPLOAD_FOLDER'], ideal_file.filename)#saves the ideal file to the uploaded folder
            ideal_file.save(ideal_path)# it saves the uploaded ideal file to the specified path
            ideal_text2 = extract_text_from_pdf(ideal_path)#it extratcs the text from the uploaded ideal file
            

            # for job description text
        elif jd_text:# if the job description text is provided, it uses that as the ideal text                                                                                    if jd is provied
            ideal_text2 = jd_text #if the job description text is provided, it uses that as the ideal text

        # Analyze and compare
        if user_text and ideal_text2: # comparing
            user_sections = analyze_resume(user_text)# analyzes the user's resume text
            ideal_sections = analyze_resume(ideal_text2)# analyzes the ideal resume or job description text

            user_skills = [normalize_text(s) for s in user_sections['skills']]
            ideal_skills = [normalize_text(s) for s in ideal_sections['skills']]

            user_edu = [normalize_text(e) for e in user_sections['education']]
            ideal_edu = [normalize_text(e) for e in ideal_sections['education']]

            user_exp = [normalize_text(e) for e in user_sections['experience']]
            ideal_exp = [normalize_text(e) for e in ideal_sections['experience']]

            # ✅ fuzzy matching
            def fuzzy_match(set_a, set_b, threshold=85):
                matches = set()
                for a in set_a:
                    for b in set_b:
                        if fuzz.partial_ratio(a, b) >= threshold:
                            matches.add(b)
                return matches

            matched_skills = fuzzy_match(user_skills, ideal_skills)
            missing_skills = set(ideal_skills) - matched_skills

            matched_edu = fuzzy_match(user_edu, ideal_edu)
            missing_edu = set(ideal_edu) - matched_edu

            matched_exp = fuzzy_match(user_exp, ideal_exp)
            missing_exp = set(ideal_exp) - matched_exp

            skills_score = len(matched_skills) / len(ideal_skills) * 100 if ideal_skills else 0
            edu_score = len(matched_edu) / len(ideal_edu) * 100 if ideal_edu else 0
            exp_score = len(matched_exp) / len(ideal_exp) * 100 if ideal_exp else 0

            overall_score = round((skills_score + edu_score + exp_score) / 3,2)
            # Prepare the result for rendering
            #shows the section-wise match between the user's resume and the ideal resume or job description
            #shows clear match and missing data for each section and final overall score
            result = f"""  
            <h4>Section-wise Match (Your Resume vs. Ideal Resume/Job Description)</h4>
            <b>Skills Present in Both:</b> {', '.join(matched_skills) if matched_skills else 'None'}<br>
            <b>Skills Missing in Your Resume:</b> <span style='color:red'>{', '.join(missing_skills) if missing_skills else 'None'}</span><br><br>
            <b>Education Present in Both:</b> {', '.join(matched_edu) if matched_edu else 'None'}<br>
            <b>Education Missing in Your Resume:</b> <span style='color:red'>{', '.join(missing_edu) if missing_edu else 'None'}</span><br><br>
            <b>Experience Present in Both:</b> {', '.join(matched_exp) if matched_exp else 'None'}<br>
            <b>Experience Missing in Your Resume:</b> <span style='color:red'>{', '.join(missing_exp) if missing_exp else 'None'}</span><br>
            <hr>
            <b>Overall Similarity Score:</b> <span style='font-size:1.3em;color:#007bff'>{overall_score}%</span>
            """

    return render_template('seeker.html', result=result)# displays the result on the seeker.html tamplate

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return render_template('hello.html', error="No file part")
    file = request.files['file']
    if file.filename == '':
        return render_template('hello.html', error="No selected file")
    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        extracted_text = extract_text_from_pdf(filepath)
        if not extracted_text.strip():
            return render_template('hello.html', error="Could not extract text from the PDF. It may be scanned or empty.")
        analysis = analyze_resume(extracted_text)
        return render_template('hello.html', extracted_text=extracted_text, analysis=analysis)
    return render_template('hello.html', error="Invalid file format. Please upload a PDF.")

if __name__ == '__main__':
    app.run(debug=True)
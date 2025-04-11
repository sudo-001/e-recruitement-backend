import pypdf
import pypdf
import google.generativeai as genai
import os
import json
import numpy as np
import random
from copy import deepcopy
import pypdf
import matplotlib.pyplot as plt


# Configure Gemini API (replace with your actual API key)
GOOGLE_API_KEY = "AIzaSyCoGPcEuJifNcE_BqTCZB533P0qizuJ4xk"# os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)
MODEL_NAME = "gemini-1.5-pro"
model = genai.GenerativeModel(MODEL_NAME)


def extract_text_from_pdf(pdf_path):
    """Extracts text content from a PDF file."""
    try:
        with open(pdf_path, 'rb') as file:
            reader = pypdf.PdfReader(file)
            text = ""
            for page_num in range(len(reader.pages)):
                page = reader.pages[page_num]
                text += page.extract_text()
        return text
    except FileNotFoundError:
        print(f"Error: PDF file not found at {pdf_path}")
        return None
    except Exception as e:
        print(f"Error reading PDF file: {e}")
        return None

def extract_resume_information(resume_text):
    # (Same resume extraction code from previous answers)
    # prompt = f"""
    # You are an expert resume parsing assistant.  Your task is to extract key information from the following resume text.
    # Output the information in JSON format.  If a piece of information is not explicitly stated in the resume, leave that field blank ("").  Be concise.
    # Capture also the test scores for each candidate from the resume.

    # Here's the resume text:

    # {resume_text}

    # Output the JSON as follows:

    # {{
    #     "name": "",
    #     "email": "",
    #     "phone_number": "",
    #     "summary": "",
    #     "skills": [],
    #     "number_of_years_experience": "",
    #     "experience": [
    #         {{
    #             "title": "",
    #             "company": "",
    #             "dates": "",
    #             "description": ""
    #         }}
    #     ],
    #     "education": [
    #         {{
    #             "degree": "",
    #             "major": "",
    #             "university": "",
    #             "graduation_date": ""
    #         }}
    #     ],
    #     "test_scores": {{ #NEW: Test Scores
    #         "technical_tests": "", #Example.  Adjust to your tests.
    #         "psychometric_tests": ""
    #     }}
    # }}

    # """
    
    prompt = f"""
    You are an expert resume parsing assistant. Your task is to extract key information from the following resume text and output it in JSON format.
    If a piece of information is not explicitly stated in the resume, leave that field blank (""). Be concise.  Return the number of years of experience as a string.
    Capture also the test scores for each candidate from the resume.  If the number of years of experience isn't directly stated, estimate it based on the dates of employment.

    Here's the resume text:

    {resume_text}

    Output the JSON as follows:

    {{
        "name": "",
        "email": "",
        "phone_number": "",
        "summary": "",
        "skills": [],
        "number_of_years_experience": "",
        "experience": [
            {{
                "title": "",
                "company": "",
                "dates": "",
                "description": ""
            }}
        ],
        "education": [
            {{
                "degree": "",
                "major": "",
                "university": "",
                "graduation_date": ""
            }}
        ],
        "test_scores": {{
            "technical_tests": "",
            "psychometric_tests": ""
        }},
        "number_of_experiences": 0  
    }}

    At the end of the JSON, include one last field "number_of_experiences" which should be an integer equal to the number of entries present in the "experience" array.

    Make sure the entire output is valid JSON.
    """

    try:
        response = model.generate_content(prompt)  # Use generate_content for text-only input
        json_string = response.text
        # Attempt to parse the JSON
        import json
        extracted_data = json.loads(json_string)
        return extracted_data
    except Exception as e:
        print(f"Error extracting information: {e}")
        print(f"Response text: {response.text if 'response' in locals() else 'No response received'}")
        return None


# resume_text = extract_text_from_pdf("./Carick-Appolinaire-ATEZONG-YMELE-FlowCV-Resume-20250215.pdf")
# if resume_text:
#     extracted_data = extract_resume_information(resume_text)
#     print(extracted_data)
# else:
#     print("No text extracted from the PDF.")
# Test the function with a sample PDF file
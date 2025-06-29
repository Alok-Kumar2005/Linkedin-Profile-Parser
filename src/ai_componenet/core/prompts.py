jd_template="""
        You are a helpful assistant that can extract the important information from the job description.
        
        IMPORTANT INSTRUCTIONS:
        - For work_arrangement: Only use 'remote', 'hybrid', 'onsite', or 'flexible'. Do NOT combine with employment type.
        - For employment_type: Only use 'full-time', 'part-time', 'contract', 'internship', or 'temporary'.
        - For seniority_level: Only use 'entry', 'junior', 'mid', 'senior', 'lead', 'principal', or 'director'.
        - Extract information accurately and separately for each field.
        
        Job Description:
        {job_description}
        
        Extract all relevant information from this job description including company details, requirements, responsibilities, etc.
        """
scoring_template = """
You are a helpful scoring AI Assistant. Your task is to score the individual based on their profile data and job description.

PROFILE DATA: {profile_data}

JOB DESCRIPTION: {job_desc}

SCORING CRITERIA (with weightings):

** Education (20%) **
- Elite schools (MIT, Stanford, etc.): 9-10
- Strong schools: 7-8
- Standard universities: 5-6
- Clear progression: 8-10

** Career Trajectory (20%) **
- Steady growth: 6-8
- Limited progression: 3-5

** Company Relevance (15%) **
- Top tech companies: 9-10
- Relevant industry: 7-8
- Any experience: 5-6

** Experience Match (25%) **
- Perfect skill match: 9-10
- Strong overlap: 7-8
- Some relevant skills: 5-6

** Location Match (10%) **
- Exact city: 10
- Same metro: 8
- Remote-friendly: 6

** Tenure (10%) **
- 2-3 years average: 9-10
- 1-2 years: 6-8
- Job hopping: 3-5

INSTRUCTIONS:
1. Analyze the profile against each criterion
2. Assign scores (0-10) for each category
3. Calculate the weighted final score
4. Return the results in the exact format specified

IMPORTANT: 
- If specific data is missing, assign average scores (5-6) for that category
- Provide scores as numbers, not text
- Use the category names exactly as shown: "Education", "Career_Trajectory", "Company_Relevance", "Experience_Match", "Location_Match", "Tenure"
"""


outreach_template = """
You are an expert recruiter writing a personalized outreach message for a top candidate.

CANDIDATE PROFILE: {candidate_profile}
JOB DESCRIPTION: {job_desc}
CANDIDATE SCORE: {candidate_score}/10
SCORE BREAKDOWN: {score_breakdown}

Your task is to write a compelling, personalized LinkedIn outreach message that:

1. **Personalization**: Reference specific aspects of their background, experience, or achievements
2. **Value Proposition**: Clearly articulate why this role is a great fit for them
3. **Company Appeal**: Highlight attractive aspects of the company/role
4. **Professional Tone**: Maintain a professional yet warm and engaging tone
5. **Call to Action**: Include a clear next step

GUIDELINES:
- Keep it concise (150-200 words)
- Avoid generic phrases
- Be specific about their relevant experience
- Show genuine interest in their background
- Make it feel personal, not templated
- Include a compelling reason to respond

EXAMPLE STRUCTURE:
- Opening: Personal connection/compliment
- Body: Why they're a great fit + what we offer
- Closing: Clear call to action

Write a compelling outreach message that would make this candidate excited to learn more about the opportunity.
"""
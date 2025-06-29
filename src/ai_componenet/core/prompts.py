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
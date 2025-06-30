# Linkedin-Profile-Parser

## Create and activate environment
```
uv venv
.venv\Scripts\activate
```

## Install dependencies
```
uv add -r requirements.txt
```

## Run file
```
uvicorn main:app --reload
```

## Pull from docker
```
docker pull alok8090/linkedin-profile-parser:0.1.0
```


### Project Overview
- We jot a Job description from the hiring managers and our model will go through Linkedin and search for the best candidate that fits for given position 
- Used langchain , langgraph and other libraries to make these project
- we can divide these project in 4 phases

## Phase 1
- here i make all the required tools and llm related files
- tools like tavily_tool and data_of_linkedin_url 
- tavily tool will search on the linkedin for given Open position on linkedin
- data_of_linkedin_url it will retrieve the data of the individuals from the linkedin
- ```get_llm.py``` two format of llm 
    1. take prompt and llm model and gave output
    2. take prompt, llm and output base model for structured output

## Phase 2
- Nodes are created in the sequential form 
- there are several nodes with special ability and tool that perform specific task
- ```JobDescriptionNode``` these will get the important data from the Job description in structured format using structured output
- ```LinkedInProfileNode``` on the basis of the given data it will fetch the linkedin to get individals
    1. use tavily_tool to search on linkedin
    2. Store links of user
- ```FetchURLNode``` these will fetch the data of the profile that selcted by upper node
    1. Use `data_of_linkedin_url` to do that
    2. Store the data in list
- ```ScoringNode``` these node will score the individauls on the basis of there data and Jon description and stored in a List
- ```BestCandidateNode``` these node will find the best candidate and generate the outreach message for them

## Phase 3
- Database are created
- To store the data of JD and individauls i created a database that store data
- ```JobDescription``` these will store the important data from the JD
- ```LinkedInCandidate``` these will store the data of the candidates
- Use id of the JobDescription table to foregin key of LinkedinCandidate to store data

## Phase 4
- Backend and Docker code
- Using FastAPI for backend



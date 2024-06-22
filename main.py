from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import requests
import re
import uvicorn
from typing import List, Optional


# Disable SSL warnings


app = FastAPI()

class CompanyRequest(BaseModel):
    company: str

class ContactInfoResponse(BaseModel):
    website: str
    phones: List[str]
    emails: List[str]
    facebook_links: List[str]
    instagram_links: List[str]
    twitter_links: List[str]
    youtube_links: List[str]

def get_company_domain(company):
    response = requests.get(f'https://autocomplete.clearbit.com/v1/companies/suggest?query={company}')
    data = response.json()
    if len(data) > 0:
        return data[0]['domain']
    return None

def fetch_website_content(url):
    try:
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            return response.text
        return None
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error fetching website content: {e}")

def extract_info(content, regex):
    return list(set(re.findall(regex, content)))

@app.post("/get_contact_info", response_model=ContactInfoResponse)
def get_contact_info(request: CompanyRequest):
    company = request.company
    domain = get_company_domain(company)
    
    if not domain:
        raise HTTPException(status_code=404, detail="The company website not found, please check the company name again")
    
    url = f"https://www.{domain}"
    content = fetch_website_content(url)
    
    if not content:
        raise HTTPException(status_code=500, detail="Unable to retrieve content from the website.")
    
    phone_regex = r"\+?[1-9][0-9]{7,14}"
    email_regex = r"[\w\.-]+@[\w\.-]+"
    facebook_regex = r'https?://(www\.)?facebook\.com/([a-zA-Z0-9.\-_/]+)/?'
    instagram_regex = r'https?://(www\.)?instagram\.com/([a-zA-Z0-9._]+)/?'
    twitter_regex = r'https?://(www\.)?twitter\.com/([a-zA-Z0-9.\-_/]+)/?'
    youtube_regex = r'https?://(www\.)?youtube\.com/(user|channel)/([a-zA-Z0-9.\-_/]+)/?'
    
    phones = extract_info(content, phone_regex)
    emails = extract_info(content, email_regex)
    facebook_links = extract_info(content, facebook_regex)
    instagram_links = extract_info(content, instagram_regex)
    twitter_links = extract_info(content, twitter_regex)
    youtube_links = extract_info(content, youtube_regex)
    
    return ContactInfoResponse(
        website=url,
        phones=phones,
        emails=emails,
        facebook_links=facebook_links,
        instagram_links=instagram_links,
        twitter_links=twitter_links,
        youtube_links=youtube_links
    )

if __name__ == "__main__":
  
    uvicorn.run(app, host="0.0.0.0", port=8000)


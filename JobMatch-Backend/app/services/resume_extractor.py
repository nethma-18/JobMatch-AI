import re

class ResumeExtractorService:
    def __init__(self):
        # Basic Regex patterns for parsing non-AI fields
        self.email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
        # Basic phone pattern: matches standard international and US formats loosely
        self.phone_pattern = re.compile(r'(?:\+?\d{1,3}[\s.-]?)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}')
        # URL pattern: matches http/https and www domains commonly found in resumes
        self.url_pattern = re.compile(r'(https?://[^\s]+|www\.[^\s]+|linkedin\.com/in/[^\s]+|github\.com/[^\s]+)')

    def extract_basic_info(self, text: str) -> dict:
        """
        Performs basic non-AI parsing of resume text.
        Returns a structured dictionary with obvious information.
        """
        if not text:
            return {
                "email": None,
                "phone": None,
                "urls": []
            }

        # Find all emails
        emails = self.email_pattern.findall(text)
        email = emails[0] if emails else None

        # Find all phones
        phones = self.phone_pattern.findall(text)
        phone = phones[0] if phones else None

        # Find all URLs
        urls = list(set(self.url_pattern.findall(text)))

        return {
            "email": email,
            "phone": phone,
            "urls": urls
        }

resume_extractor_service = ResumeExtractorService()

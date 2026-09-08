import re
from typing import List, Optional, Dict, Any
from app.backend.schemas.profiles import (
    CandidateProfile, ContactInfo, EducationItem, ExperienceItem, ProjectItem
)
from nlp.preprocessing import clean_text, detect_sections
from nlp.skill_extractor import skill_extractor


class ResumeParser:
    EMAIL_REGEX = re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+")
    PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}")
    LINKEDIN_REGEX = re.compile(r"linkedin\.com/in/[a-zA-Z0-9_-]+", re.IGNORECASE)
    GITHUB_REGEX = re.compile(r"github\.com/[a-zA-Z0-9_-]+", re.IGNORECASE)
    YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")

    DEGREE_PATTERNS = [
        re.compile(r"\b(Ph\.?D\.?|Doctor of Philosophy)\b", re.IGNORECASE),
        re.compile(r"\b(M\.?S\.?|Master of Science|M\.?Tech\.?|MBA|Master of Arts)\b", re.IGNORECASE),
        re.compile(r"\b(B\.?S\.?|Bachelor of Science|B\.?Tech\.?|B\.?E\.?|Bachelor of Arts|Bachelor of Engineering)\b", re.IGNORECASE),
        re.compile(r"\b(Associate Degree|High School Diploma)\b", re.IGNORECASE),
    ]

    def parse(self, raw_text: str, filename: str = "resume.pdf") -> CandidateProfile:
        text = clean_text(raw_text)
        sections = detect_sections(text)

        contact = self._extract_contact(text, sections.get("header", ""))
        name = self._extract_name(sections.get("header", ""), text, filename)
        skills_dict = skill_extractor.extract_skills(text)
        education = self._extract_education(sections.get("education", ""))
        experience = self._extract_experience(sections.get("experience", ""))
        projects = self._extract_projects(sections.get("projects", ""))
        certifications = self._extract_list_items(sections.get("certifications", ""))
        achievements = self._extract_list_items(sections.get("achievements", ""))
        summary = sections.get("summary", "")

        return CandidateProfile(
            name=name,
            contact=contact,
            summary=summary if summary else None,
            skills=skills_dict["all_skills"],
            programming_languages=skills_dict["programming_languages"],
            frameworks=skills_dict["frameworks"],
            tools=skills_dict["tools"],
            databases=skills_dict["databases"],
            cloud_devops=skills_dict["cloud_devops"],
            education=education,
            experience=experience,
            projects=projects,
            certifications=certifications,
            achievements=achievements,
            raw_text=text
        )

    def _extract_name(self, header_text: str, full_text: str, filename: str) -> str:
        # Check first 3 lines of header
        lines = [line.strip() for line in (header_text or full_text).split("\n") if line.strip()]
        for line in lines[:3]:
            # Remove emails, phones, URLs
            cleaned = self.EMAIL_REGEX.sub("", line)
            cleaned = self.PHONE_REGEX.sub("", cleaned)
            cleaned = self.LINKEDIN_REGEX.sub("", cleaned)
            cleaned = self.GITHUB_REGEX.sub("", cleaned)
            cleaned = re.sub(r"[|•\-–—]", " ", cleaned).strip()
            # If line is 2-4 words and alphabetic, it's likely a name
            words = cleaned.split()
            if 2 <= len(words) <= 4 and all(w.isalpha() for w in words):
                return " ".join(words).title()

        # Fallback to filename without extension if name not parsed
        base_name = filename.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        words = [w for w in base_name.split() if w.isalpha()]
        if words:
            return " ".join(words).title()
        return "Candidate"

    def _extract_contact(self, full_text: str, header_text: str) -> ContactInfo:
        search_scope = (header_text + "\n" + full_text[:1000]) if header_text else full_text[:1500]

        email_match = self.EMAIL_REGEX.search(search_scope)
        phone_match = self.PHONE_REGEX.search(search_scope)
        linkedin_match = self.LINKEDIN_REGEX.search(search_scope)
        github_match = self.GITHUB_REGEX.search(search_scope)

        return ContactInfo(
            email=email_match.group(0) if email_match else None,
            phone=phone_match.group(0) if phone_match else None,
            linkedin=f"https://{linkedin_match.group(0)}" if linkedin_match else None,
            github=f"https://{github_match.group(0)}" if github_match else None,
            location=None
        )

    def _extract_education(self, edu_text: str) -> List[EducationItem]:
        if not edu_text:
            return []
        items = []
        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]

        for line in lines:
            degree_found = None
            for pat in self.DEGREE_PATTERNS:
                m = pat.search(line)
                if m:
                    degree_found = m.group(0)
                    break

            if degree_found:
                years = self.YEAR_REGEX.findall(line)
                grad_year = years[-1] if years else None
                # Rest of line as institution/field
                remainder = line.replace(degree_found, "")
                if grad_year:
                    remainder = remainder.replace(grad_year, "")
                cleaned_inst = re.sub(r"[,|\-•()]+", " ", remainder).strip()

                items.append(EducationItem(
                    degree=degree_found,
                    institution=cleaned_inst if cleaned_inst else "University",
                    year=grad_year
                ))

        return items

    def _extract_experience(self, exp_text: str) -> List[ExperienceItem]:
        if not exp_text:
            return []
        items = []
        chunks = re.split(r"\n(?=[A-Z][a-zA-Z\s]{2,40}(?:\||–|-|,|\bat\b))", exp_text)

        for chunk in chunks:
            lines = [l.strip() for l in chunk.split("\n") if l.strip()]
            if not lines:
                continue
            title_line = lines[0]
            desc = "\n".join(lines[1:]) if len(lines) > 1 else ""
            skills = skill_extractor.extract_skills(chunk)["all_skills"]

            # Try to split title and company
            parts = re.split(r"[|–\-•,]|\bat\b", title_line)
            title = parts[0].strip() if parts else "Software Engineer"
            company = parts[1].strip() if len(parts) > 1 else None

            # Look for duration
            years = self.YEAR_REGEX.findall(title_line)
            duration = " - ".join(years) if len(years) >= 2 else (years[0] if years else None)

            items.append(ExperienceItem(
                title=title,
                company=company,
                duration=duration,
                description=desc,
                skills_used=skills
            ))

        return items

    def _extract_projects(self, proj_text: str) -> List[ProjectItem]:
        if not proj_text:
            return []

        def is_bullet(line: str) -> bool:
            s = line.strip()
            return bool(re.match(r"^[\s•●\-\*–—>]", s)) or s.startswith(("\u25cf", "\u2022", "-", "*", ">", "•"))

        def is_project_header(line: str) -> bool:
            s = line.strip()
            if not s:
                return False
            if is_bullet(s):
                return False
            # Wrapped continuation lines starting with lowercase are never headers
            if s[0].islower():
                return False
            # Project titles do not end with terminal punctuation
            if s.endswith((".", ";", ",")):
                return False
            # Title with separator (—, –, |, :) or links
            if any(sep in s for sep in ["|", "—", "–", " - ", "http", "github"]):
                return True
            # Short title-cased or uppercase phrase of 1-8 words
            words = s.split()
            if 1 <= len(words) <= 8 and (all(w[0].isupper() for w in words if w.isalpha()) or s.isupper()):
                return True
            return False

        lines = [l.strip() for l in proj_text.split("\n") if l.strip()]
        chunks: List[List[str]] = []
        curr: List[str] = []

        for line in lines:
            if is_project_header(line) and curr:
                chunks.append(curr)
                curr = [line]
            else:
                curr.append(line)
        if curr:
            chunks.append(curr)

        items = []
        for chunk_lines in chunks:
            if not chunk_lines:
                continue
            title_line = chunk_lines[0]
            parts = [p.strip() for p in title_line.split("|")]
            main_title = parts[0]
            url = None
            for p in parts[1:]:
                if "http" in p.lower():
                    url = p
                elif "github" in p.lower():
                    url = "https://github.com"

            subparts = re.split(r"\s*[—–]\s*|\s+-\s+", main_title)
            proj_name = subparts[0].strip() if subparts else main_title.strip()

            desc_lines = chunk_lines[1:]
            if len(subparts) == 3:
                desc_lines.insert(0, subparts[1].strip())
            elif len(subparts) == 2 and not any(k in subparts[1].lower() for k in ["python", "react", "javascript", "api", "cv", "ml", "opencv"]):
                desc_lines.insert(0, subparts[1].strip())

            desc = "\n".join(desc_lines)
            chunk_full_text = "\n".join(chunk_lines)
            techs = skill_extractor.extract_skills(chunk_full_text)["all_skills"]

            items.append(ProjectItem(
                name=proj_name,
                description=desc,
                technologies=techs,
                url=url
            ))

        return items

    def _extract_list_items(self, text: str) -> List[str]:
        if not text:
            return []
        items = []
        for line in text.split("\n"):
            cleaned = re.sub(r"^[\s•\-*>\d.]+", "", line).strip()
            if cleaned and len(cleaned) > 2:
                items.append(cleaned)
        return items


resume_parser = ResumeParser()

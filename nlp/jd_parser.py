import re
from typing import List, Optional, Dict, Any
from app.backend.schemas.profiles import JobProfile
from nlp.preprocessing import clean_text
from nlp.skill_extractor import skill_extractor


class JobDescriptionParser:
    YEARS_EXP_REGEX = re.compile(
        r"(\d+)\s*(?:\+|-\s*\d+)?\s*(?:years?|yrs?)(?:\s+of)?(?:\s+[a-zA-Z]+){0,3}\s*(?:experience|exp|development|software|work)?",
        re.IGNORECASE
    )
    
    ROLE_LEVEL_PATTERNS = {
        "Staff": re.compile(r"\b(staff|principal)\b", re.IGNORECASE),
        "Lead": re.compile(r"\b(lead|architect|tech lead|engineering manager)\b", re.IGNORECASE),
        "Senior": re.compile(r"\b(senior|sr\.?)\b", re.IGNORECASE),
        "Mid-Level": re.compile(r"\b(mid|intermediate)\b", re.IGNORECASE),
        "Junior": re.compile(r"\b(junior|jr\.?|entry level|associate|graduate)\b", re.IGNORECASE)
    }

    DEGREE_PATTERNS = [
        re.compile(r"\b(Bachelor(?:'s)?|B\.?S\.?|B\.?Tech)\b", re.IGNORECASE),
        re.compile(r"\b(Master(?:'s)?|M\.?S\.?|M\.?Tech)\b", re.IGNORECASE),
        re.compile(r"\b(Ph\.?D\.?|Doctorate)\b", re.IGNORECASE)
    ]

    def parse(self, raw_text: str, default_title: Optional[str] = None) -> JobProfile:
        text = clean_text(raw_text)

        job_title = default_title or self._extract_job_title(text)
        role_level = self._extract_role_level(job_title, text)
        min_exp = self._extract_years_experience(text)
        education_reqs = self._extract_education(text)

        sections = self._split_jd_sections(text)

        req_skills_dict = skill_extractor.extract_skills(sections.get("required", text))
        pref_skills_dict = skill_extractor.extract_skills(sections.get("preferred", ""))
        all_skills_dict = skill_extractor.extract_skills(text)

        required_skills = req_skills_dict["all_skills"]
        preferred_skills = [s for s in pref_skills_dict["all_skills"] if s not in required_skills]

        if not required_skills:
            required_skills = all_skills_dict["all_skills"]

        responsibilities = self._extract_bullet_points(sections.get("responsibilities", ""))
        domain_reqs = all_skills_dict["ai_ml_domain"] + all_skills_dict["system_design"]

        return JobProfile(
            job_title=job_title,
            role_level=role_level,
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            responsibilities=responsibilities,
            technologies=all_skills_dict["all_skills"],
            education_requirements=education_reqs,
            min_years_experience=min_exp,
            domain_requirements=sorted(list(set(domain_reqs))),
            keywords=all_skills_dict["all_skills"],
            raw_text=text
        )

    def _extract_job_title(self, text: str) -> str:
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        for line in lines[:5]:
            lower = line.lower()
            if any(term in lower for term in ["engineer", "developer", "architect", "scientist", "analyst", "manager", "lead"]):
                cleaned = re.sub(r"^(?:job\s+title|role|position)[:\-\s]+", "", line, flags=re.IGNORECASE).strip()
                if len(cleaned.split()) <= 8:
                    return cleaned
        return lines[0] if lines else "Software Engineer"

    def _extract_role_level(self, title: str, text: str) -> str:
        for level, pat in self.ROLE_LEVEL_PATTERNS.items():
            if pat.search(title) or pat.search(text[:300]):
                return level
        return "Mid-Level"

    def _extract_years_experience(self, text: str) -> Optional[int]:
        m = self.YEARS_EXP_REGEX.search(text)
        if m:
            try:
                return int(m.group(1))
            except (ValueError, TypeError):
                pass
        return None

    def _extract_education(self, text: str) -> List[str]:
        found = []
        for pat in self.DEGREE_PATTERNS:
            m = pat.search(text)
            if m:
                found.append(m.group(0))
        return list(set(found))

    def _split_jd_sections(self, text: str) -> Dict[str, str]:
        sections = {"general": [], "required": [], "preferred": [], "responsibilities": []}
        current_sec = "general"

        for line in text.split("\n"):
            stripped = line.strip().lower()
            if any(h in stripped for h in ["preferred", "nice to have", "plus", "bonus", "desirable", "good to have"]):
                current_sec = "preferred"
            elif any(h in stripped for h in ["requirement", "must have", "qualifications", "what you need", "what we're looking for"]):
                current_sec = "required"
            elif any(h in stripped for h in ["responsibilities", "what you'll do", "what you will do", "role overview", "day to day"]):
                current_sec = "responsibilities"

            sections[current_sec].append(line)

        return {k: "\n".join(v).strip() for k, v in sections.items()}

    def _extract_bullet_points(self, text: str) -> List[str]:
        bullets = []
        for line in text.split("\n"):
            cleaned = re.sub(r"^[\s•\-*>\d.]+", "", line).strip()
            # Ignore headers ending in colon
            if cleaned.endswith(":"):
                continue
            if len(cleaned) > 10 and not any(h == cleaned.lower() for h in ["responsibilities", "requirements", "qualifications"]):
                bullets.append(cleaned)
        return bullets[:8]


jd_parser = JobDescriptionParser()

import re
import os
from typing import List, Optional, Dict, Any, Tuple
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

    MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    DATE_RANGE_REGEX = re.compile(
        rf"(?:{MONTHS}\.?\s+)?\b(?:19|20)\d{{2}}\b\s*(?:[–\-—]|to)\s*(?:Present|Current|Ongoing|(?:{MONTHS}\.?\s+)?\b(?:19|20)\d{{2}}\b)",
        re.IGNORECASE
    )
    CERT_REGEX = re.compile(r"\b(?:certified|certification|certificate|licence|license)\b", re.IGNORECASE)
    ROLE_KEYWORDS = ["contributor", "ambassador", "engineer", "developer", "intern", "fellow", "lead", "manager", "consultant", "analyst", "specialist", "assistant", "researcher"]

    def parse(self, raw_text: str, filename: str = "resume.pdf", file_path: Optional[str] = None) -> CandidateProfile:
        text = clean_text(raw_text)
        sections = detect_sections(text)

        pdf_uris: List[str] = []
        if file_path and file_path.lower().endswith(".pdf") and os.path.exists(file_path):
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for page in reader.pages:
                    if "/Annots" in page:
                        for annot in page["/Annots"]:
                            obj = annot.get_object()
                            a = obj.get("/A", {})
                            uri = a.get("/URI", None)
                            if uri and str(uri) not in pdf_uris:
                                pdf_uris.append(str(uri))
            except Exception:
                pass

        contact = self._extract_contact(text, sections.get("header", ""), pdf_uris=pdf_uris)
        name = self._extract_name(sections.get("header", ""), text, filename)
        skills_dict = skill_extractor.extract_skills(text)
        education = self._extract_education(sections.get("education", ""))
        experience, certs_from_exp = self._extract_experience(sections.get("experience", ""))
        projects = self._extract_projects(sections.get("projects", ""), pdf_uris=pdf_uris)
        certifications = self._extract_list_items(sections.get("certifications", ""))
        if certs_from_exp:
            for c in certs_from_exp:
                if c not in certifications:
                    certifications.append(c)
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

    def _extract_contact(self, full_text: str, header_text: str, pdf_uris: Optional[List[str]] = None) -> ContactInfo:
        search_scope = (header_text + "\n" + full_text[:1000]) if header_text else full_text[:1500]

        email_match = self.EMAIL_REGEX.search(search_scope)
        phone_match = self.PHONE_REGEX.search(search_scope)
        linkedin_match = self.LINKEDIN_REGEX.search(search_scope)
        github_match = self.GITHUB_REGEX.search(search_scope)

        linkedin_url = f"https://{linkedin_match.group(0)}" if linkedin_match else None
        github_url = f"https://{github_match.group(0)}" if github_match else None

        # Fallback to PDF annotations / URIs
        if pdf_uris:
            if not linkedin_url:
                l_uri = next((u for u in pdf_uris if "linkedin.com/in/" in u.lower()), None)
                if l_uri:
                    linkedin_url = l_uri
            if not github_url:
                g_uri = next((u for u in pdf_uris if re.match(r"^https?://(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?$", u, re.IGNORECASE)), None)
                if g_uri:
                    github_url = g_uri

        # Extract location: e.g. 'New Delhi, India', 'San Francisco, CA'
        location = None
        loc_match = re.search(r"\b([A-Z][a-zA-Z\s]{2,20},\s*[A-Z][a-zA-Z\s]{2,20})\b", header_text or full_text[:500])
        if loc_match:
            cand = loc_match.group(1).strip()
            if not any(w in cand.lower() for w in ["university", "college", "school", "gmail", "engineer", "developer", "science"]):
                location = cand

        return ContactInfo(
            email=email_match.group(0) if email_match else None,
            phone=phone_match.group(0) if phone_match else None,
            linkedin=linkedin_url,
            github=github_url,
            location=location
        )

    def _extract_education(self, edu_text: str) -> List[EducationItem]:
        if not edu_text:
            return []
        items = []
        lines = [l.strip() for l in edu_text.split("\n") if l.strip()]

        extended_degrees = [
            re.compile(r"\b(Ph\.?D\.?|Doctor of Philosophy)\b", re.IGNORECASE),
            re.compile(r"\b(M\.?S\.?|Master of Science|M\.?Tech\.?|MBA|Master of Arts)\b", re.IGNORECASE),
            re.compile(r"\b(Bachelor of Technology|Bachelor of Science|Bachelor of Engineering|B\.?Tech\.?|B\.?S\.?|B\.?E\.?)\b", re.IGNORECASE),
            re.compile(r"\b(Class XII|Class X|High School|Senior Secondary)\b", re.IGNORECASE),
            re.compile(r"\b(Associate Degree|High School Diploma)\b", re.IGNORECASE),
        ]

        visited = set()
        for i, line in enumerate(lines):
            if i in visited:
                continue
            deg = None
            for p in extended_degrees:
                m = p.search(line)
                if m:
                    deg = m.group(0)
                    break
            if not deg:
                continue
            visited.add(i)

            field = None
            inst = None
            year = None

            years = self.YEAR_REGEX.findall(line)
            if years:
                year = " - ".join(years) if len(years) >= 2 else years[-1]

            rem = line.replace(deg, "").strip(" —–-|•,")
            if year:
                rem = rem.replace(year, "").replace("Expected", "").strip(" —–-|•,")

            if any(u in rem.lower() for u in ["university", "institute", "college", "campus", "school", "indraprastha"]):
                inst = rem
            elif rem:
                field = rem

            # Inspect line i+1 for specialization or university
            if i + 1 < len(lines) and (i + 1) not in visited:
                next_l = lines[i + 1]
                if any(w in next_l.lower() for w in ["in artificial", "in computer", "in data", "in software", "in information", "cgpa", "gpa"]):
                    in_m = re.search(r"\bin\s+([A-Za-z\s&]+?)(?:\s*[—–|-]|\s+CGPA|\s+GPA|$)", next_l, re.IGNORECASE)
                    if in_m:
                        field = in_m.group(1).strip()
                    visited.add(i + 1)
                elif any(u in next_l.lower() for u in ["university", "institute", "college", "campus"]) and not inst:
                    inst_years = self.YEAR_REGEX.findall(next_l)
                    if inst_years and not year:
                        year = inst_years[-1]
                    inst = re.sub(r"[,|\-•–—()]+", " ", next_l).strip()
                    visited.add(i + 1)

            if not inst:
                inst = "University"

            # Clean school names
            if deg in ["Class XII", "Class X"]:
                inst = re.sub(r"\(CBSE\)|\b\d+(?:\.\d+)?%?\b|[%·|–—,\s]+", " ", inst).strip()
                inst = re.sub(r"\s+", " ", inst).strip()

            # Canonicalize BTech
            canonical_deg = deg
            if "bachelor of technology" in deg.lower() or "btech" in deg.lower():
                canonical_deg = "BTech"

            items.append(EducationItem(
                degree=canonical_deg,
                institution=inst,
                year=year,
                field_of_study=field
            ))

        return items

    def _extract_experience(self, exp_text: str) -> Tuple[List[ExperienceItem], List[str]]:
        if not exp_text:
            return [], []

        raw_lines = [l.strip() for l in exp_text.split("\n") if l.strip()]
        exp_lines = []
        extracted_certs = []

        # Step 1: Filter out lines that are clearly certifications rather than employment roles
        for line in raw_lines:
            s = line.strip()
            has_date = bool(self.DATE_RANGE_REGEX.search(s))
            has_cert = bool(self.CERT_REGEX.search(s))

            if has_cert and not has_date:
                cleaned_c = re.sub(r"^[•●\-\*–—>\d.]+\s*", "", s).strip()
                if cleaned_c:
                    extracted_certs.append(cleaned_c)
            else:
                exp_lines.append(line)

        # Step 2: Group lines into distinct experience roles
        def is_experience_header(line_text: str) -> bool:
            clean_l = re.sub(r"^[•●\-\*–—>\d.]+\s*", "", line_text).strip()
            if self.DATE_RANGE_REGEX.search(clean_l):
                return True
            if any(sep in clean_l for sep in ["|", "—", "–"]) and any(kw in clean_l.lower() for kw in self.ROLE_KEYWORDS):
                return True
            return False

        chunks: List[List[str]] = []
        curr_chunk: List[str] = []

        for line in exp_lines:
            if is_experience_header(line) and curr_chunk:
                chunks.append(curr_chunk)
                curr_chunk = [line]
            else:
                curr_chunk.append(line)
        if curr_chunk:
            chunks.append(curr_chunk)

        items = []
        for chunk in chunks:
            if not chunk:
                continue
            raw_title_line = re.sub(r"^[•●\-\*–—>\d.]+\s*", "", chunk[0]).strip()

            # Extract duration cleanly
            duration = None
            date_m = self.DATE_RANGE_REGEX.search(raw_title_line)
            if date_m:
                duration = date_m.group(0).strip()
                title_line = raw_title_line.replace(duration, "").strip(" |–-—•,")
            else:
                years = self.YEAR_REGEX.findall(raw_title_line)
                duration = " - ".join(years) if len(years) >= 2 else (years[0] if years else None)
                title_line = raw_title_line

            # Extract title and company without letting dates/Present contaminate
            company = None
            if " at " in title_line:
                parts = title_line.split(" at ", 1)
                title, company = parts[0].strip(), parts[1].strip()
            elif "|" in title_line:
                parts = title_line.split("|", 1)
                title, company = parts[0].strip(), parts[1].strip()
            elif "–" in title_line or "—" in title_line:
                parts = re.split(r"[–—]", title_line, 1)
                title, company = parts[0].strip(), parts[1].strip()
            else:
                title = title_line if title_line else "Software Engineer"

            # Clean company if it looks like a date/status
            if company and any(c.lower() in company.lower() for c in ["present", "current", "202"]):
                company = None

            desc = "\n".join(chunk[1:]) if len(chunk) > 1 else ""
            skills = skill_extractor.extract_skills("\n".join(chunk))["all_skills"]

            items.append(ExperienceItem(
                title=title,
                company=company,
                duration=duration,
                description=desc,
                skills_used=skills
            ))

        return items, extracted_certs

    def _extract_projects(self, proj_text: str, pdf_uris: Optional[List[str]] = None) -> List[ProjectItem]:
        if not proj_text:
            return []

        def is_bullet(line: str) -> bool:
            s = line.strip()
            return bool(re.match(r"^[\s•●\-\*–—>]", s)) or s.startswith(("\u25cf", "\u2022", "-", "*", ">", "•"))

        def is_project_header(line: str) -> bool:
            s = line.strip()
            if not s or is_bullet(s):
                return False
            # Wrapped continuation lines starting with lowercase are never headers
            if s[0].islower():
                return False
            # Project titles do not end with terminal punctuation
            if s.endswith((".", ";", ",")):
                return False
            # Headers have separators or are short capitalized phrases
            if any(sep in s for sep in ["—", "–", "|", " - "]):
                return True
            words = s.split()
            if 1 <= len(words) <= 8 and all(w[0].isupper() for w in words if w.isalpha()):
                return True
            return False

        lines = [l.strip() for l in proj_text.split("\n") if l.strip()]
        projects_raw: List[List[str]] = []
        curr_proj: List[str] = []
        in_bullets = False

        for line in lines:
            if is_bullet(line):
                in_bullets = True
                curr_proj.append(line)
            elif is_project_header(line):
                if in_bullets and curr_proj:
                    projects_raw.append(curr_proj)
                    curr_proj = [line]
                    in_bullets = False
                else:
                    curr_proj.append(line)
            else:
                curr_proj.append(line)

        if curr_proj:
            projects_raw.append(curr_proj)

        items = []
        for chunk in projects_raw:
            if not chunk:
                continue
            header_lines = [l for l in chunk if not is_bullet(l) and is_project_header(l)]
            bullet_lines = [l for l in chunk if l not in header_lines]
            if not header_lines:
                non_bullets = [l for l in chunk if not is_bullet(l)]
                if not non_bullets:
                    continue
                header_lines = [non_bullets[0]]
                bullet_lines = [l for l in chunk if l != non_bullets[0]]

            raw_title = header_lines[0]
            parts = [p.strip() for p in raw_title.split("|")]
            subparts = re.split(r"\s*[—–]\s*|\s+-\s+", parts[0])
            name = subparts[0].strip() if subparts else parts[0].strip()

            url = None
            # Check for inline URL first
            for hl in header_lines:
                for p in hl.split("|"):
                    if "http" in p.lower():
                        url = p.strip()
                        break
                if url:
                    break

            # If no inline URL, match project name against pdf_uris
            if not url and pdf_uris:
                name_words = [w.lower() for w in re.split(r"\W+", name) if len(w) > 3]
                for u in pdf_uris:
                    if "github.com/" in u.lower() and "/" in u.replace("https://github.com/", ""):
                        repo_name = u.rstrip("/").split("/")[-1].lower().replace("-", "_")
                        if any(w in repo_name for w in name_words):
                            url = u
                            break

            if not url:
                for hl in header_lines:
                    if "github" in hl.lower():
                        url = "https://github.com"
                        break

            desc_lines = []
            if len(subparts) > 1:
                desc_lines.append(subparts[1].strip())
            for hl in header_lines[1:]:
                if hl.lower() in ["github", "link", "demo", "live"]:
                    continue
                desc_lines.append(hl)
            desc_lines.extend(bullet_lines)

            techs = skill_extractor.extract_skills("\n".join(chunk))["all_skills"]
            items.append(ProjectItem(
                name=name,
                description="\n".join(desc_lines),
                technologies=techs,
                url=url
            ))

        return items

    def _extract_list_items(self, text: str) -> List[str]:
        if not text:
            return []
        items = []
        for line in text.split("\n"):
            s = line.strip()
            if not s:
                continue
            is_bullet = bool(re.match(r"^[\s•●\-\*–—>\d.]+", line))
            cleaned = re.sub(r"^[\s•●\-\*–—>\d.]+", "", line).strip()

            # Merge wrapped continuation lines into previous item
            if not is_bullet and items and (s.startswith("(") or s[0].islower() or len(s.split()) < 8):
                items[-1] = items[-1] + " " + s
            elif cleaned and len(cleaned) > 2:
                items.append(cleaned)
        return items


resume_parser = ResumeParser()


from typing import List, Dict, Tuple, Set
from app.backend.schemas.profiles import CandidateProfile, JobProfile
from app.backend.schemas.matching import (
    MatchAnalysisResponse, SkillMatchItem, SkillGapReport,
    SkillGapItem, MatchScoreExplanation
)
from nlp.similarity import calculate_semantic_similarity


class MatchingEngine:
    def __init__(self):
        # Priority map for domain skills when ranking interview gaps
        self.high_importance_keywords = {
            "System Design", "Microservices", "Distributed Systems", "SQL", "PostgreSQL",
            "Python", "Docker", "Kubernetes", "Machine Learning", "Large Language Models",
            "RAG", "Data Structures", "Algorithms"
        }

    def analyze_match(self, candidate: CandidateProfile, job: JobProfile) -> MatchAnalysisResponse:
        cand_skills_set = set(candidate.skills)
        cand_text = candidate.raw_text or ""
        cand_lower = cand_text.lower()

        # Combine all JD skills with requirement flag
        all_jd_skills: List[Tuple[str, bool]] = []
        for s in job.required_skills:
            all_jd_skills.append((s, True))
        for s in job.preferred_skills:
            if s not in job.required_skills:
                all_jd_skills.append((s, False))

        skill_breakdown: List[SkillMatchItem] = []
        strong_skills: List[str] = []
        matched_skills: List[str] = []
        partially_matched_skills: List[str] = []
        missing_skills: List[str] = []
        gaps_to_rank: List[Dict] = []

        req_scores = []
        pref_scores = []

        for skill, is_required in all_jd_skills:
            # 1. Exact or alias match
            if skill in cand_skills_set:
                score = 95.0
                category = "Strong Match"
                context = f"Exact skill match: candidate profile contains '{skill}'."
            elif skill.lower() in cand_lower:
                score = 85.0
                category = "Strong Match"
                context = f"Mentioned directly in candidate resume text."
            else:
                # 2. Semantic similarity against candidate skills
                max_sim = 0.0
                best_match = ""
                for cs in candidate.skills:
                    sim = calculate_semantic_similarity(skill, cs)
                    if sim > max_sim:
                        max_sim = sim
                        best_match = cs

                # Also test similarity against resume experience text chunks
                text_sim = calculate_semantic_similarity(skill, cand_text[:2000])
                effective_sim = max(max_sim, text_sim * 0.9)
                score = round(effective_sim * 100.0, 1)

                if score >= 75.0:
                    category = "Strong Match"
                    context = f"Semantically related to candidate skill '{best_match}' ({score}%)."
                elif score >= 55.0:
                    category = "Matched"
                    context = f"Partially aligned with candidate background '{best_match}'."
                elif score >= 35.0:
                    category = "Partially Matched"
                    context = f"Limited conceptual overlap with '{best_match}'."
                else:
                    score = min(score, 25.0)
                    category = "Missing"
                    context = "Not found or demonstrated in candidate profile."

            skill_item = SkillMatchItem(
                skill=skill,
                match_score=score,
                category=category,
                is_required=is_required,
                context_found=context
            )
            skill_breakdown.append(skill_item)

            if is_required:
                req_scores.append(score)
            else:
                pref_scores.append(score)

            # Categorize into gap buckets
            if category == "Strong Match":
                strong_skills.append(skill)
            elif category == "Matched":
                matched_skills.append(skill)
            elif category == "Partially Matched":
                partially_matched_skills.append(skill)
                gaps_to_rank.append({"skill": skill, "is_req": is_required, "score": score})
            else:
                missing_skills.append(skill)
                gaps_to_rank.append({"skill": skill, "is_req": is_required, "score": score})

        # Calculate coverage components
        avg_req = (sum(req_scores) / len(req_scores)) if req_scores else 70.0
        avg_pref = (sum(pref_scores) / len(pref_scores)) if pref_scores else 60.0

        # Calculate overall semantic similarity between full profiles
        doc_semantic_sim = calculate_semantic_similarity(
            candidate.raw_text[:2500] if candidate.raw_text else " ".join(candidate.skills),
            job.raw_text[:2500] if job.raw_text else job.job_title + " " + " ".join(job.required_skills)
        )
        doc_semantic_score = round(doc_semantic_sim * 100.0, 1)

        # Experience & Education alignment score
        exp_score = 75.0
        if job.min_years_experience:
            candidate_years = len(candidate.experience) * 2  # heuristic estimate: 2 yrs per role
            if candidate_years >= job.min_years_experience:
                exp_score = 95.0
            elif candidate_years >= job.min_years_experience - 1:
                exp_score = 80.0
            else:
                exp_score = 50.0

        # Overall weighted match score
        # 50% Required skills + 15% Preferred skills + 25% Semantic similarity + 10% Experience alignment
        overall_score = round(
            (avg_req * 0.50) + (avg_pref * 0.15) + (doc_semantic_score * 0.25) + (exp_score * 0.10),
            1
        )
        overall_score = max(0.0, min(100.0, overall_score))

        # Match Category Classification
        if overall_score >= 75.0:
            match_category = "Strong Match"
        elif overall_score >= 50.0:
            match_category = "Moderate Match"
        else:
            match_category = "Weak Match"

        # Prioritize gaps based on job relevance (is_required), weakness gap (100 - score), and core importance
        high_priority_gaps: List[SkillGapItem] = []
        
        # Sort gaps by priority weight
        def gap_priority_weight(gap):
            weight = (100.0 - gap["score"])
            if gap["is_req"]:
                weight += 50.0
            if gap["skill"] in self.high_importance_keywords:
                weight += 30.0
            return weight

        gaps_to_rank.sort(key=gap_priority_weight, reverse=True)

        for g in gaps_to_rank:
            priority = "High" if (g["is_req"] or g["skill"] in self.high_importance_keywords) else "Medium"
            high_priority_gaps.append(SkillGapItem(
                skill=g["skill"],
                is_required=g["is_req"],
                gap_priority=priority,
                current_proficiency_estimate=g["score"],
                recommended_topics=[
                    f"Core principles of {g['skill']}",
                    f"Interview practice questions on {g['skill']}",
                    f"Production scenarios with {g['skill']}"
                ]
            ))

        gap_report = SkillGapReport(
            strong_skills=strong_skills,
            matched_skills=matched_skills,
            partially_matched_skills=partially_matched_skills,
            missing_skills=missing_skills,
            high_priority_gaps=high_priority_gaps
        )

        explanation = MatchScoreExplanation(
            required_skills_coverage=round(avg_req, 1),
            preferred_skills_coverage=round(avg_pref, 1),
            semantic_similarity_score=doc_semantic_score,
            experience_education_alignment=exp_score,
            summary_explanation=(
                f"Candidate exhibits a {overall_score}% {match_category}. "
                f"Required skill coverage is {round(avg_req, 1)}%, with {len(strong_skills)} strong matches "
                f"and {len(missing_skills)} identified missing areas. "
                f"Overall semantic document similarity is {doc_semantic_score}%."
            )
        )

        return MatchAnalysisResponse(
            overall_match_score=overall_score,
            match_category=match_category,
            skill_breakdown=skill_breakdown,
            gap_report=gap_report,
            explanation=explanation
        )


matching_engine = MatchingEngine()

from typing import Optional, List
from sqlalchemy.orm import Session
from database.models import User, Resume, JobDescription, SkillGapAnalysis


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_user(self, name: str, email: Optional[str] = None, target_role: Optional[str] = None) -> User:
        if email:
            user = self.db.query(User).filter(User.email == email).first()
            if user:
                if target_role and not user.target_role:
                    user.target_role = target_role
                    self.db.commit()
                    self.db.refresh(user)
                return user

        user = User(name=name, email=email, target_role=target_role)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def list_users(self) -> List[User]:
        return self.db.query(User).order_by(User.created_at.desc()).all()

    def save_resume(self, user_id: Optional[int], filename: str, file_type: str, raw_text: str, parsed_profile: dict) -> Resume:
        resume = Resume(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            raw_text=raw_text,
            parsed_profile=parsed_profile
        )
        self.db.add(resume)
        self.db.commit()
        self.db.refresh(resume)
        return resume

    def get_resume(self, resume_id: int) -> Optional[Resume]:
        return self.db.query(Resume).filter(Resume.id == resume_id).first()

    def get_latest_resume_for_user(self, user_id: int) -> Optional[Resume]:
        return self.db.query(Resume).filter(Resume.user_id == user_id).order_by(Resume.created_at.desc()).first()

    def save_job_description(self, user_id: Optional[int], title: str, raw_text: str, parsed_profile: dict) -> JobDescription:
        jd = JobDescription(
            user_id=user_id,
            title=title,
            raw_text=raw_text,
            parsed_profile=parsed_profile
        )
        self.db.add(jd)
        self.db.commit()
        self.db.refresh(jd)
        return jd

    def get_job_description(self, jd_id: int) -> Optional[JobDescription]:
        return self.db.query(JobDescription).filter(JobDescription.id == jd_id).first()

    def get_latest_job_description_for_user(self, user_id: int) -> Optional[JobDescription]:
        return self.db.query(JobDescription).filter(JobDescription.user_id == user_id).order_by(JobDescription.created_at.desc()).first()

    def save_skill_gap_analysis(self, user_id: Optional[int], resume_id: Optional[int], jd_id: Optional[int],
                                overall_match_score: float, match_category: str,
                                detailed_matches: dict, skill_gaps: dict) -> SkillGapAnalysis:
        analysis = SkillGapAnalysis(
            user_id=user_id,
            resume_id=resume_id,
            jd_id=jd_id,
            overall_match_score=overall_match_score,
            match_category=match_category,
            detailed_matches=detailed_matches,
            skill_gaps=skill_gaps
        )
        self.db.add(analysis)
        self.db.commit()
        self.db.refresh(analysis)
        return analysis

    def get_latest_skill_gap_analysis(self, user_id: Optional[int] = None) -> Optional[SkillGapAnalysis]:
        query = self.db.query(SkillGapAnalysis)
        if user_id:
            query = query.filter(SkillGapAnalysis.user_id == user_id)
        return query.order_by(SkillGapAnalysis.created_at.desc()).first()

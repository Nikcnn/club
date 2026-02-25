from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.core.deps import get_current_organization_tg, get_current_candidate_tg
from apps.db.dependencies import get_db
from apps.employment.enums import ProfileChangeSource
from apps.employment.models import CandidateProfile, EmploymentMatch, Vacancy
from apps.employment.schemas import (
    CandidateHistoryResponse,
    CandidateRegisterRequest,
    CandidateResponse,
    CandidateUpdateRequest,
    EmailValidateResponse,
    EmploymentOrganizationRegisterRequest,
    MatchResponse,
    MatchStatusUpdateRequest,
    OrganizationEmailValidateRequest,
    OrganizationMeResponse,
    ReactionRequest,
    ReactionResponse,
    RecommendationItem,
    TgCheckRequest,
    TgCheckResponse,
    VacancyCreateRequest,
    VacancyResponse,
    VacancyUpdateRequest,
    VacancyStatusUpdateRequest, TgMatchContextRequest,
)
from apps.employment.services import EmploymentService
from apps.users.models import User

router = APIRouter(prefix="/employment", tags=["Employment"])


@router.post("/tg/check", response_model=TgCheckResponse)
async def tg_check(schema: TgCheckRequest, db: AsyncSession = Depends(get_db)):
    tg = await EmploymentService.tg_check(db, schema.model_dump())
    return TgCheckResponse(
        telegram_id=tg.telegram_id,
        is_blocked=tg.is_blocked,
        is_linked=bool(tg.linked_candidate_id or tg.linked_organization_id),
        available_roles=["candidate", "organization"],
    )


@router.post("/organizations/validate-email", response_model=EmailValidateResponse)
async def validate_org_email(schema: OrganizationEmailValidateRequest, db: AsyncSession = Depends(get_db)):
    available = await EmploymentService.validate_organization_email(db, str(schema.email))
    return EmailValidateResponse(email=schema.email, available=available)


@router.post("/organizations/register", status_code=status.HTTP_201_CREATED)
async def register_org(schema: EmploymentOrganizationRegisterRequest, db: AsyncSession = Depends(get_db)):
    org = await EmploymentService.register_organization(db, schema)
    return {"id": org.id, "email": org.email}


@router.get("/organizations/me", response_model=OrganizationMeResponse)
async def organization_me(db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    vacancies = list((await db.execute(select(Vacancy).where(Vacancy.organization_id == current_organization.id))).scalars().all())
    return OrganizationMeResponse(id=current_organization.id, email=current_organization.email, name=current_organization.name, city=current_organization.city, vacancies=vacancies)


@router.post("/candidates/register", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def register_candidate(schema: CandidateRegisterRequest, db: AsyncSession = Depends(get_db)):
    return await EmploymentService.register_candidate(db, schema)


@router.get("/candidates/me", response_model=CandidateResponse)
async def candidate_me(current_candidate: CandidateProfile = Depends(get_current_candidate_tg)):
    return current_candidate


@router.patch("/candidates/me", response_model=CandidateResponse)
async def candidate_update(schema: CandidateUpdateRequest, db: AsyncSession = Depends(get_db), current_candidate: CandidateProfile = Depends(get_current_candidate_tg)):
    return await EmploymentService.update_candidate(db, current_candidate.id, schema, ProfileChangeSource.WEB)


@router.get("/candidates/me/history", response_model=list[CandidateHistoryResponse])
async def candidate_history(db: AsyncSession = Depends(get_db), current_candidate: CandidateProfile = Depends(get_current_candidate_tg)):
    return await EmploymentService.get_candidate_history(db, current_candidate.id)


@router.get("/candidates/me/history/{version_no}", response_model=CandidateHistoryResponse)
async def candidate_history_version(version_no: int, db: AsyncSession = Depends(get_db), current_candidate: CandidateProfile = Depends(get_current_candidate_tg)):
    items = await EmploymentService.get_candidate_history(db, current_candidate.id)
    for item in items:
        if item.version_no == version_no:
            return item
    raise HTTPException(status_code=404, detail="Version not found")


@router.post("/vacancies", response_model=VacancyResponse, status_code=status.HTTP_201_CREATED)
async def create_vacancy(schema: VacancyCreateRequest, db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    return await EmploymentService.create_vacancy(db, current_organization.id, schema)


@router.get("/vacancies/my", response_model=list[VacancyResponse])
async def my_vacancies(db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    return list((await db.execute(select(Vacancy).where(Vacancy.organization_id == current_organization.id))).scalars().all())


@router.get("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def get_vacancy(vacancy_id: int, db: AsyncSession = Depends(get_db)):
    vacancy = (await db.execute(select(Vacancy).where(Vacancy.id == vacancy_id))).scalars().first()
    if not vacancy:
        raise HTTPException(status_code=404, detail="Vacancy not found")
    return vacancy


@router.patch("/vacancies/{vacancy_id}", response_model=VacancyResponse)
async def patch_vacancy(vacancy_id: int, schema: VacancyUpdateRequest, db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    return await EmploymentService.update_vacancy(db, vacancy_id, current_organization.id, schema)


@router.patch("/vacancies/{vacancy_id}/status", response_model=VacancyResponse)
async def patch_vacancy_status(vacancy_id: int, schema: VacancyStatusUpdateRequest, db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    return await EmploymentService.update_vacancy_status(db, vacancy_id, current_organization.id, schema.status)


@router.get("/recommendations/vacancies-for-candidate", response_model=list[RecommendationItem])
async def rec_vacancies(db: AsyncSession = Depends(get_db), current_candidate: CandidateProfile = Depends(get_current_candidate_tg)):
    return await EmploymentService.candidate_recommendations(db, current_candidate)


@router.get("/vacancies/{vacancy_id}/recommended-candidates", response_model=list[RecommendationItem])
async def rec_candidates(vacancy_id: int, db: AsyncSession = Depends(get_db), current_organization: User = Depends(get_current_organization_tg)):
    vacancy = await EmploymentService.get_vacancy_for_org(db, vacancy_id, current_organization.id)
    return await EmploymentService.vacancy_recommendations(db, vacancy)


@router.get("/match-explanations")
async def match_explanations(vacancy_id: int, candidate_id: int):
    return {"vacancy_id": vacancy_id, "candidate_id": candidate_id, "message": "v1.1 endpoint"}


@router.post("/reactions", response_model=ReactionResponse)
async def reactions(
    schema: ReactionRequest,
    db: AsyncSession = Depends(get_db),
    idempotency_key: str | None = Header(default=None, alias="Idempotency-Key"),
):
    if not idempotency_key:
        raise HTTPException(status_code=400, detail="Idempotency-Key header is required")
    reaction, match, replay = await EmploymentService.submit_reaction(db, schema, idempotency_key)
    return ReactionResponse(
        reaction_id=reaction.id,
        match_id=match.id if match else None,
        match_status=match.status if match else None,
        idempotent_replay=replay,
    )

@router.post("/matches/by-context", response_model=MatchResponse)
async def get_match_by_context(schema: TgMatchContextRequest, db: AsyncSession = Depends(get_db)):
    return await EmploymentService.get_match_by_tg_context(db, schema.role, schema.tg_user_id, schema.vacancy_id)

@router.get("/matches", response_model=list[MatchResponse])
async def list_matches(
    candidate_id: int | None = None,
    organization_id: int | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await EmploymentService.list_matches(db, candidate_id, organization_id)


@router.get("/matches/{match_id}", response_model=MatchResponse)
async def get_match(match_id: int, db: AsyncSession = Depends(get_db)):
    match = (await db.execute(select(EmploymentMatch).where(EmploymentMatch.id == match_id))).scalars().first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return match


@router.patch("/matches/{match_id}/status", response_model=MatchResponse)
async def patch_match_status(match_id: int, schema: MatchStatusUpdateRequest, db: AsyncSession = Depends(get_db)):
    return await EmploymentService.update_match_status(db, match_id, schema)

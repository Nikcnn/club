from __future__ import annotations

import json
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any

from fastapi import HTTPException
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.employment.ai_service import EmploymentAIService
from apps.employment.enums import EntityType, MatchStatus, ProfileChangeSource, ReactionAction, VacancyStatus
from apps.employment.models import CandidateProfile, CandidateProfileHistory, EmploymentMatch, EmploymentReaction, TgInfo, Vacancy
from apps.employment.qdrant import (
    search_candidates_for_vacancy,
    search_vacancies_for_candidate,
    upsert_candidate_vector,
    upsert_vacancy_vector,
)
from sqlalchemy.exc import IntegrityError
from apps.employment.schemas import (
    CandidateRegisterRequest,
    CandidateUpdateRequest,
    EmploymentOrganizationRegisterRequest,
    MatchStatusUpdateRequest,
    ReactionRequest,
    VacancyCreateRequest,
    VacancyUpdateRequest,
)
from apps.organizations.models import Organization
from apps.users.models import UserRole
from apps.users.services import UserService
from apps.users.utils import get_password_hash


class EmploymentService:
    @staticmethod
    async def tg_check(db: AsyncSession, payload: dict[str, Any]) -> TgInfo:
        tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == payload["telegram_id"]))).scalars().first()
        if not tg:
            tg = TgInfo(telegram_id=payload["telegram_id"])
            # на всякий случай — если поля есть в модели
            if getattr(tg, "is_active", None) is None:
                tg.is_active = True
            if getattr(tg, "is_blocked", None) is None:
                tg.is_blocked = False
            db.add(tg)

        tg.telegram_username = payload.get("telegram_username")
        tg.first_name = payload.get("first_name")
        tg.last_name = payload.get("last_name")

        # если запись уже была, а флаги пустые — нормализуем
        if getattr(tg, "is_active", None) is None:
            tg.is_active = True
        if getattr(tg, "is_blocked", None) is None:
            tg.is_blocked = False

        tg.last_seen_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(tg)
        return tg

    @staticmethod
    async def validate_organization_email(db: AsyncSession, email: str) -> bool:
        return await UserService.get_by_email(db, email) is None

    @staticmethod
    async def register_organization(db: AsyncSession, schema: EmploymentOrganizationRegisterRequest) -> Organization:
        if await UserService.get_by_email(db, schema.email):
            raise HTTPException(status_code=400, detail="Email already registered")

        org = Organization(
            email=schema.email,
            hashed_password=get_password_hash(schema.password),
            role=UserRole.ORGANIZATION,
            is_active=True,
            name=schema.name,
            city=schema.city,
            description=schema.description,
            website=schema.website,
        )
        db.add(org)
        await db.flush()  # чтобы получить org.id до commit

        if schema.telegram_id:
            tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == schema.telegram_id))).scalars().first()

            # ✅ если TgInfo ещё нет — создаём (раньше тут была главная проблема)
            if not tg:
                tg = TgInfo(telegram_id=schema.telegram_id)
                # дефолты
                if getattr(tg, "is_active", None) is None:
                    tg.is_active = True
                if getattr(tg, "is_blocked", None) is None:
                    tg.is_blocked = False
                db.add(tg)
                await db.flush()

            # ✅ защита от “двойной привязки”
            if getattr(tg, "linked_candidate_id", None):
                raise HTTPException(status_code=400, detail="Telegram already linked to a candidate")
            if getattr(tg, "linked_organization_id", None) and tg.linked_organization_id != org.id:
                raise HTTPException(status_code=400, detail="Telegram already linked to another organization")

            tg.linked_organization_id = org.id
            # если флаги пустые — нормализуем
            if getattr(tg, "is_active", None) is None:
                tg.is_active = True
            if getattr(tg, "is_blocked", None) is None:
                tg.is_blocked = False
            tg.last_seen_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(org)
        return org


    @staticmethod
    async def register_candidate(db: AsyncSession, schema: CandidateRegisterRequest) -> CandidateProfile:
        existing = (await db.execute(select(CandidateProfile).where(CandidateProfile.email == schema.email))).scalars().first()
        if existing:
            raise HTTPException(status_code=400, detail="Candidate with this email already exists")

        candidate = CandidateProfile(
            email=str(schema.email),
            description_json=schema.description_json,
            links=schema.links,
            category=schema.category,
            city=schema.city,
            resume_text=schema.resume_text,
        )
        db.add(candidate)
        await db.flush()

        await EmploymentService._create_history(db, candidate, ProfileChangeSource.WEB)

        if schema.telegram_id:
            tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == schema.telegram_id))).scalars().first()

            # ✅ если TgInfo ещё нет — создаём
            if not tg:
                tg = TgInfo(telegram_id=schema.telegram_id)
                if getattr(tg, "is_active", None) is None:
                    tg.is_active = True
                if getattr(tg, "is_blocked", None) is None:
                    tg.is_blocked = False
                db.add(tg)
                await db.flush()

            if getattr(tg, "linked_organization_id", None):
                raise HTTPException(status_code=400, detail="Telegram already linked to an organization")
            if getattr(tg, "linked_candidate_id", None) and tg.linked_candidate_id != candidate.id:
                raise HTTPException(status_code=400, detail="Telegram already linked to another candidate")

            tg.linked_candidate_id = candidate.id
            if getattr(tg, "is_active", None) is None:
                tg.is_active = True
            if getattr(tg, "is_blocked", None) is None:
                tg.is_blocked = False
            tg.last_seen_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(candidate)
        await upsert_candidate_vector(candidate.id, EmploymentService._candidate_payload(candidate))
        return candidate


    @staticmethod
    async def update_candidate(db: AsyncSession, candidate_id: int, schema: CandidateUpdateRequest, source: ProfileChangeSource) -> CandidateProfile:
        candidate = (await db.execute(select(CandidateProfile).where(CandidateProfile.id == candidate_id))).scalars().first()
        if not candidate:
            raise HTTPException(status_code=404, detail="Candidate not found")
        for key, value in schema.model_dump(exclude_unset=True).items():
            setattr(candidate, key, value)
        await EmploymentService._create_history(db, candidate, source)
        await db.commit()
        await db.refresh(candidate)
        await upsert_candidate_vector(candidate.id, EmploymentService._candidate_payload(candidate))
        return candidate

    @staticmethod
    async def _create_history(db: AsyncSession, candidate: CandidateProfile, source: ProfileChangeSource) -> None:
        last_version = (
            await db.execute(select(func.max(CandidateProfileHistory.version_no)).where(CandidateProfileHistory.candidate_id == candidate.id))
        ).scalar_one_or_none() or 0
        history = CandidateProfileHistory(
            candidate_id=candidate.id,
            version_no=last_version + 1,
            snapshot_json=EmploymentService._candidate_payload(candidate),
            change_source=source,
        )
        db.add(history)

    @staticmethod
    def _candidate_payload(candidate: CandidateProfile) -> dict[str, Any]:
        return {
            "email": candidate.email,
            "description_json": candidate.description_json,
            "links": candidate.links,
            "category": candidate.category,
            "city": candidate.city,
            "resume_text": candidate.resume_text,
        }

    @staticmethod
    async def get_candidate_history(db: AsyncSession, candidate_id: int) -> list[CandidateProfileHistory]:
        res = await db.execute(
            select(CandidateProfileHistory)
            .where(CandidateProfileHistory.candidate_id == candidate_id)
            .order_by(CandidateProfileHistory.version_no.desc())
        )
        return list(res.scalars().all())

    @staticmethod
    async def create_vacancy(db: AsyncSession, organization_id: int, schema: VacancyCreateRequest) -> Vacancy:
        vacancy = Vacancy(
            organization_id=organization_id,
            position_title=schema.position_title or schema.role_search or "",
            description_json=schema.description_json,
            city=schema.city,
            employment_type=schema.employment_type,
            is_remote=schema.is_remote,
            status=VacancyStatus.DRAFT,
        )
        db.add(vacancy)
        await db.commit()
        await db.refresh(vacancy)
        await upsert_vacancy_vector(vacancy.id, {"position_title": vacancy.position_title, **vacancy.description_json})
        return vacancy

    @staticmethod
    async def update_vacancy(db: AsyncSession, vacancy_id: int, organization_id: int, schema: VacancyUpdateRequest) -> Vacancy:
        vacancy = await EmploymentService.get_vacancy_for_org(db, vacancy_id, organization_id)
        data = schema.model_dump(exclude_unset=True)
        if "role_search" in data and "position_title" not in data:
            data["position_title"] = data["role_search"]
        data.pop("role_search", None)
        for k, v in data.items():
            setattr(vacancy, k, v)
        await db.commit()
        await db.refresh(vacancy)
        await upsert_vacancy_vector(vacancy.id, {"position_title": vacancy.position_title, **vacancy.description_json})
        return vacancy

    @staticmethod
    async def update_vacancy_status(db: AsyncSession, vacancy_id: int, organization_id: int, status: VacancyStatus) -> Vacancy:
        vacancy = await EmploymentService.get_vacancy_for_org(db, vacancy_id, organization_id)
        vacancy.status = status
        await db.commit()
        await db.refresh(vacancy)
        return vacancy

    @staticmethod
    async def get_vacancy_for_org(db: AsyncSession, vacancy_id: int, organization_id: int) -> Vacancy:
        vacancy = (
            await db.execute(
                select(Vacancy).where(and_(Vacancy.id == vacancy_id, Vacancy.organization_id == organization_id))
            )
        ).scalars().first()
        if not vacancy:
            raise HTTPException(status_code=404, detail="Vacancy not found")
        return vacancy

    @staticmethod
    async def submit_reaction(
        db: AsyncSession,
        schema,  # ReactionRequest (TG формат)
        idempotency_key: str,
    ) -> tuple[EmploymentReaction, EmploymentMatch | None, bool]:

        # 0) идемпотентность по ключу
        existing_key = (
            await db.execute(select(EmploymentReaction).where(EmploymentReaction.idempotency_key == idempotency_key))
        ).scalars().first()
        if existing_key:
            match = await EmploymentService._find_match_for_reaction(db, existing_key)
            return existing_key, match, True

        # 1) находим TgInfo по telegram_id
        tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == schema.telegram_id))).scalars().first()
        if not tg:
            raise HTTPException(status_code=404, detail="Telegram profile not found")

        # 2) вычисляем initiator/target из TG-контекста
        if schema.role == EntityType.CANDIDATE:
            if not tg.linked_candidate_id:
                raise HTTPException(status_code=404, detail="Telegram is not linked to candidate")

            vacancy = (await db.execute(select(Vacancy).where(Vacancy.id == schema.vacancy_id))).scalars().first()
            if not vacancy:
                raise HTTPException(status_code=404, detail="Vacancy not found")

            initiator_entity_type = EntityType.CANDIDATE
            initiator_entity_id = tg.linked_candidate_id

            target_entity_type = EntityType.ORGANIZATION
            target_entity_id = vacancy.organization_id

        elif schema.role == EntityType.ORGANIZATION:
            # С ТВОИМ ВХОДОМ НЕЛЬЗЯ ОПРЕДЕЛИТЬ КАНДИДАТА, КОТОРОГО ЛАЙКНУЛИ
            # (vacancy_id не несёт candidate_id)
            raise HTTPException(
                status_code=400,
                detail="For role=organization you must provide candidate context (candidate_id). With current payload it is impossible.",
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid role")

        # 3) request_hash — теперь хешируем TG payload
        canonical_payload = json.dumps(schema.model_dump(mode="json"), sort_keys=True, separators=(",", ":"))
        request_hash = sha256(canonical_payload.encode("utf-8")).hexdigest()

        # 4) создаём реакцию уже в канонических полях модели
        reaction = EmploymentReaction(
            initiator_entity_type=initiator_entity_type,
            initiator_entity_id=initiator_entity_id,
            target_entity_type=target_entity_type,
            source=ProfileChangeSource.TELEGRAM_BOT,
            target_entity_id=target_entity_id,
            vacancy_id=schema.vacancy_id,
            action=schema.action,
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            processed_at=datetime.now(timezone.utc),
        )

        db.add(reaction)

        # 5) дедуп по target (у тебя уже было)
        try:
            await db.flush()
        except IntegrityError as exc:
            await db.rollback()
            if not EmploymentService._is_duplicate_reaction_target(exc):
                raise

            existing_target = (
                await db.execute(
                    select(EmploymentReaction).where(
                        and_(
                            EmploymentReaction.initiator_entity_type == initiator_entity_type,
                            EmploymentReaction.initiator_entity_id == initiator_entity_id,
                            EmploymentReaction.target_entity_type == target_entity_type,
                            EmploymentReaction.target_entity_id == target_entity_id,
                            EmploymentReaction.vacancy_id == schema.vacancy_id,
                        )
                    )
                )
            ).scalars().first()

            if not existing_target:
                raise

            match = await EmploymentService._find_match_for_reaction(db, existing_target)
            return existing_target, match, True

        # 6) матч-логика (reverse LIKE)
        match = None
        if schema.action == ReactionAction.LIKE:
            reverse = (
                await db.execute(
                    select(EmploymentReaction).where(
                        and_(
                            EmploymentReaction.initiator_entity_type == target_entity_type,
                            EmploymentReaction.initiator_entity_id == target_entity_id,
                            EmploymentReaction.target_entity_type == initiator_entity_type,
                            EmploymentReaction.target_entity_id == initiator_entity_id,
                            or_(
                                EmploymentReaction.vacancy_id == schema.vacancy_id,
                                EmploymentReaction.vacancy_id.is_(None),
                            ),
                            EmploymentReaction.action == ReactionAction.LIKE,
                        )
                    )
                )
            ).scalars().first()

            if reverse:
                # здесь всё детерминировано: initiator всегда candidate (мы выше запретили org)
                candidate_id = initiator_entity_id
                organization_id = target_entity_id

                match = (
                    await db.execute(
                        select(EmploymentMatch).where(
                            and_(
                                EmploymentMatch.candidate_id == candidate_id,
                                EmploymentMatch.organization_id == organization_id,
                                EmploymentMatch.vacancy_id == (schema.vacancy_id or reverse.vacancy_id),
                            )
                        )
                    )
                ).scalars().first()

                if not match:
                    match = EmploymentMatch(
                        candidate_id=candidate_id,
                        organization_id=organization_id,
                        vacancy_id=schema.vacancy_id or reverse.vacancy_id,
                        status=MatchStatus.MUTUAL_MATCHED,
                        matched_at=datetime.now(timezone.utc),
                    )
                    db.add(match)
                else:
                    match.status = MatchStatus.MUTUAL_MATCHED
                    match.matched_at = datetime.now(timezone.utc)

        await db.commit()
        await db.refresh(reaction)
        if match:
            await db.refresh(match)
        return reaction, match, False
    @staticmethod
    def _is_duplicate_reaction_target(exc: IntegrityError) -> bool:
        return "uq_employment_reaction_target" in str(getattr(exc, "orig", exc))

    @staticmethod
    async def get_match_by_tg_context(db: AsyncSession, role: EntityType, tg_user_id: str,
                                      vacancy_id: int) -> EmploymentMatch:
        tg = (await db.execute(select(TgInfo).where(TgInfo.telegram_id == tg_user_id))).scalars().first()
        if not tg:
            raise HTTPException(status_code=404, detail="Telegram profile not found")

        if role == EntityType.CANDIDATE:
            if not tg.linked_candidate_id:
                raise HTTPException(status_code=404, detail="Telegram is not linked to candidate")
            q = select(EmploymentMatch).where(
                and_(
                    EmploymentMatch.candidate_id == tg.linked_candidate_id,
                    EmploymentMatch.vacancy_id == vacancy_id,
                )
            )
            match = (await db.execute(q.order_by(EmploymentMatch.updated_at.desc()))).scalars().first()
        else:
            if not tg.linked_organization_id:
                raise HTTPException(status_code=404, detail="Telegram is not linked to organization")
            q = select(EmploymentMatch).where(
                and_(
                    EmploymentMatch.organization_id == tg.linked_organization_id,
                    EmploymentMatch.vacancy_id == vacancy_id,
                )
            )
            match = (await db.execute(q.order_by(EmploymentMatch.updated_at.desc()))).scalars().first()

        if not match:
            raise HTTPException(status_code=404, detail="Match not found for provided context")
        return match

    @staticmethod
    async def _find_match_for_reaction(db: AsyncSession, reaction: EmploymentReaction) -> EmploymentMatch | None:
        candidate_id = reaction.initiator_entity_id if reaction.initiator_entity_type == EntityType.CANDIDATE else reaction.target_entity_id
        organization_id = reaction.initiator_entity_id if reaction.initiator_entity_type == EntityType.ORGANIZATION else reaction.target_entity_id
        return (
            await db.execute(
                select(EmploymentMatch).where(
                    and_(
                        EmploymentMatch.candidate_id == candidate_id,
                        EmploymentMatch.organization_id == organization_id,
                        EmploymentMatch.vacancy_id == reaction.vacancy_id,
                    )
                )
            )
        ).scalars().first()

    @staticmethod
    async def list_matches(db: AsyncSession, candidate_id: int | None = None, organization_id: int | None = None) -> list[EmploymentMatch]:
        q = select(EmploymentMatch)
        if candidate_id:
            q = q.where(EmploymentMatch.candidate_id == candidate_id)
        if organization_id:
            q = q.where(EmploymentMatch.organization_id == organization_id)
        q = q.order_by(EmploymentMatch.updated_at.desc())
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def update_match_status(db: AsyncSession, match_id: int, schema: MatchStatusUpdateRequest) -> EmploymentMatch:
        match = (await db.execute(select(EmploymentMatch).where(EmploymentMatch.id == match_id))).scalars().first()
        if not match:
            raise HTTPException(status_code=404, detail="Match not found")
        match.status = schema.status
        if schema.status in {MatchStatus.CLOSED, MatchStatus.ARCHIVED, MatchStatus.EXPIRED}:
            match.closed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(match)
        return match

    @staticmethod
    async def candidate_recommendations(db: AsyncSession, candidate: CandidateProfile) -> list[dict[str, Any]]:
        items = await search_vacancies_for_candidate(EmploymentService._candidate_payload(candidate))
        scored: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            score = max(0.1, 1 - index * 0.1)
            explanation = await EmploymentAIService.generate_explanation(EmploymentService._candidate_payload(candidate), item, score)
            scored.append({
                "entity_id": int(item.get("entity_id", 0)),
                "match_score": score,
                "match_percent_display": EmploymentAIService.build_match_percent(score),
                "confidence": EmploymentAIService.build_confidence(score),
                "explanation": explanation,
            })
        return sorted(scored, key=lambda x: x["match_score"], reverse=True)

    @staticmethod
    async def vacancy_recommendations(db: AsyncSession, vacancy: Vacancy) -> list[dict[str, Any]]:
        items = await search_candidates_for_vacancy({"position_title": vacancy.position_title, **vacancy.description_json})
        scored: list[dict[str, Any]] = []
        for index, item in enumerate(items):
            score = max(0.1, 1 - index * 0.1)
            explanation = await EmploymentAIService.generate_explanation(item, {"position_title": vacancy.position_title}, score)
            scored.append({
                "entity_id": int(item.get("entity_id", 0)),
                "match_score": score,
                "match_percent_display": EmploymentAIService.build_match_percent(score),
                "confidence": EmploymentAIService.build_confidence(score),
                "explanation": explanation,
            })
        return sorted(scored, key=lambda x: x["match_score"], reverse=True)

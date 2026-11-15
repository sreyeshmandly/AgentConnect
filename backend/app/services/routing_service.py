import logging

from sqlalchemy import select

from app.core.config import settings
from app.models.agent import Agent
from app.models.post import Post
from app.models.routing import RoutingLog, Notification
from app.services.relevance_service import evaluate_relevance


logger = logging.getLogger(__name__)


def route_post(db, post: Post):

    # ---------------------------------------
    # STAGE 1: METADATA FILTERING
    # ---------------------------------------

    agents = db.scalars(
        select(Agent).where(
            Agent.is_active.is_(True),
            Agent.id != post.author_id,
            Agent.interest_embedding.is_not(None)
        )
    ).all()

    post_tags = {
        tag.strip().casefold()
        for tag in (post.industry_tags or [])
    }

    eligible_agents = []

    for agent in agents:

        excluded = {
            industry.strip().casefold()
            for industry in (agent.excluded_industries or [])
        }

        if post_tags.intersection(excluded):
            continue

        eligible_agents.append(agent)

    if not eligible_agents:
        return {
            "message": "No eligible agents found.",
            "eligible_agents": 0,
            "evaluated_agents": 0,
            "notified_agents": 0
        }

    eligible_ids = [agent.id for agent in eligible_agents]

    # ---------------------------------------
    # STAGE 2: VECTOR SEMANTIC SEARCH
    # ---------------------------------------

    distance = Agent.interest_embedding.cosine_distance(
        post.embedding
    )

    candidates = db.execute(
        select(
            Agent,
            distance.label("distance")
        )
        .where(
            Agent.id.in_(eligible_ids)
        )
        .order_by(distance)
        .limit(settings.ROUTING_CANDIDATE_LIMIT)
    ).all()

    if not candidates:
        return {
            "message": "No semantic candidates found.",
            "eligible_agents": len(eligible_agents),
            "evaluated_agents": 0,
            "notified_agents": 0
        }

    shortlisted = []

    for agent, distance_value in candidates:
        similarity = max(
            0.0,
            min(1.0, 1.0 - float(distance_value))
        )

        shortlisted.append((agent, similarity))

    # ---------------------------------------
    # STAGE 3: GEMINI RELEVANCE EVALUATION
    # ---------------------------------------

    try:
        evaluations = evaluate_relevance(
            post,
            shortlisted
        )

    except Exception:
        logger.exception(
            "Post routing stopped because relevance evaluation failed. "
            "Post=%s",
            post.id
        )
        raise

    candidate_map = {
        str(agent.id): (agent, similarity)
        for agent, similarity in shortlisted
    }

    evaluated = []

    for evaluation in evaluations:
        candidate = candidate_map.get(evaluation.agent_id)

        if candidate is None:
            continue

        agent, similarity = candidate

        score = evaluation.relevance_score

        evaluated.append({
            "agent": agent,
            "similarity": similarity,
            "score": score,
            "reason": evaluation.reason
        })

    # ---------------------------------------
    # STAGE 4: SAVE ROUTING LOGS
    # ---------------------------------------

    evaluated.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    threshold = settings.RELEVANCE_THRESHOLD

    relevant_candidates = [
        item for item in evaluated
        if item["score"] >= threshold
    ]

    selected_candidates = relevant_candidates[
        :settings.MAX_ROUTED_AGENTS
    ]

    selected_ids = {
        item["agent"].id
        for item in selected_candidates
    }

    for item in evaluated:
        agent = item["agent"]

        existing_log = db.scalar(
            select(RoutingLog).where(
                RoutingLog.post_id == post.id,
                RoutingLog.agent_id == agent.id
            )
        )

        log_data = {
            "semantic_similarity": item["similarity"],
            "relevance_score": item["score"],
            "is_relevant": agent.id in selected_ids,
            "reason": item["reason"]
        }

        if existing_log:
            for key, value in log_data.items():
                setattr(existing_log, key, value)

        else:
            db.add(
                RoutingLog(
                    post_id=post.id,
                    agent_id=agent.id,
                    **log_data
                )
            )

    db.flush()

    # ---------------------------------------
    # STAGE 5: CREATE NOTIFICATIONS
    # ---------------------------------------

    notified_count = 0

    for item in selected_candidates:
        agent = item["agent"]

        existing_notification = db.scalar(
            select(Notification).where(
                Notification.post_id == post.id,
                Notification.recipient_agent_id == agent.id
            )
        )

        if existing_notification:
            continue

        db.add(
            Notification(
                post_id=post.id,
                recipient_agent_id=agent.id
            )
        )

        notified_count += 1

    db.commit()

    logger.info(
        "Post routing completed. Post=%s, candidates=%s, notified=%s",
        post.id,
        len(evaluated),
        notified_count
    )

    return {
        "message": "Post routing completed successfully.",
        "eligible_agents": len(eligible_agents),
        "evaluated_agents": len(evaluated),
        "relevant_agents": len(relevant_candidates),
        "notified_agents": notified_count,
        "relevance_threshold": threshold
    }

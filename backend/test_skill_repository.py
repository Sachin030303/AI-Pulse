"""Test Skills repository CRUD operations."""

import json
from uuid import uuid4

from app.db.session import SessionLocal
from app.schemas.skill import SkillCreate, SkillUpdate
from app.repositories.skill_repository import (
    create_skill,
    get_skill_by_id,
    get_skill_by_name,
    list_skills,
    update_skill,
    delete_skill,
    get_skill_stats,
)


def main():
    db = SessionLocal()
    skill_id = None
    test_name = f"Test Python {uuid4().hex[:8]}"

    try:
        print("\n=== TEST 1: CREATE SKILL ===")

        payload = SkillCreate(
            name=test_name,
            category="Programming",
            proficiency_level="Intermediate",
            target_level="Advanced",
            progress=60,
            priority="High",
            status="Learning",
            description="Temporary skill for testing",
        )

        skill = create_skill(db, payload)
        skill_id = skill.id

        assert skill.id is not None
        assert skill.name == test_name

        print(f"Skill ID: {skill_id}")
        print(f"Name: {skill.name}")
        print(f"Progress: {skill.progress}")
        print("CREATE PASSED")

        print("\n=== TEST 2: GET SKILL BY ID ===")

        skill = get_skill_by_id(db, skill_id)

        assert skill is not None
        assert skill.name == test_name

        print("GET BY ID PASSED")

        print("\n=== TEST 3: GET SKILL BY NAME ===")

        skill = get_skill_by_name(
            db,
            test_name.lower(),
        )

        assert skill is not None
        assert skill.id == skill_id

        print("CASE-INSENSITIVE LOOKUP PASSED")

        print("\n=== TEST 4: UPDATE SKILL ===")

        payload = SkillUpdate(
            progress=75,
            status="Practicing",
            notes="Repository update test",
        )

        skill = update_skill(
            db,
            skill,
            payload,
        )

        assert skill.progress == 75
        assert skill.status == "Practicing"

        print(f"Updated progress: {skill.progress}")
        print(f"Updated status: {skill.status}")
        print("UPDATE PASSED")

        print("\n=== TEST 5: LIST AND FILTER SKILLS ===")

        skills, total = list_skills(
            db=db,
            category="Programming",
            priority="High",
            status="Practicing",
            q=test_name,
            page=1,
            page_size=10,
        )

        assert total == 1
        assert skills[0].id == skill_id

        print(f"Matching skills: {total}")
        print("FILTERING PASSED")

        print("\n=== TEST 6: SKILL STATISTICS ===")

        stats = get_skill_stats(db)

        print(json.dumps(stats, indent=2))

        assert stats["total_skills"] >= 1
        assert stats["practicing"] >= 1
        assert stats["high_priority_skills"] >= 1

        print("STATISTICS PASSED")

        print("\n=== TEST 7: DELETE SKILL ===")

        skill = get_skill_by_id(db, skill_id)

        delete_skill(db, skill)

        assert get_skill_by_id(db, skill_id) is None

        skill_id = None

        print("DELETE PASSED")

        print("\n=== FINAL DATABASE STATISTICS ===")

        print(json.dumps(
            get_skill_stats(db),
            indent=2,
        ))

        print("\nALL 7 SKILLS REPOSITORY TESTS PASSED")

    finally:
        db.rollback()

        try:
            if skill_id is not None:
                remaining = get_skill_by_id(db, skill_id)

                if remaining is not None:
                    delete_skill(db, remaining)
        finally:
            db.close()


if __name__ == "__main__":
    main()
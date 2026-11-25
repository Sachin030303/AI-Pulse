
"""Test Progress Tracking repository CRUD operations."""

import json
from datetime import date, timedelta
from uuid import uuid4

from app.db.session import SessionLocal
from app.schemas.progress import (
    LearningGoalCreate,
    LearningGoalUpdate,
    ImplementationLogCreate,
    ImplementationLogUpdate,
)
from app.repositories.progress_repository import (
    create_learning_goal,
    get_learning_goal_by_id,
    list_learning_goals,
    update_learning_goal,
    delete_learning_goal,
    create_implementation_log,
    get_implementation_log_by_id,
    list_implementation_logs,
    update_implementation_log,
    delete_implementation_log,
    get_progress_stats,
)


def main():
    db = SessionLocal()

    goal_id = None
    log_id = None

    unique_id = uuid4().hex[:8]
    goal_title = f"Test FastAPI Goal {unique_id}"
    log_title = f"Test Coding Session {unique_id}"

    today = date.today()

    try:
        print("\n=== TEST 1: CREATE LEARNING GOAL ===")

        goal = create_learning_goal(
            db,
            LearningGoalCreate(
                title=goal_title,
                description="Temporary learning goal for testing",
                status="In Progress",
                priority="High",
                progress=40,
                start_date=today - timedelta(days=7),
                target_date=today - timedelta(days=1),
            ),
        )

        goal_id = goal.id

        assert goal.id is not None
        assert goal.progress == 40

        print(f"Goal ID: {goal_id}")
        print("CREATE GOAL PASSED")

        print("\n=== TEST 2: RETRIEVE AND FILTER GOALS ===")

        retrieved = get_learning_goal_by_id(db, goal_id)

        assert retrieved is not None
        assert retrieved.title == goal_title

        goals, total = list_learning_goals(
            db=db,
            status="In Progress",
            priority="High",
            q=goal_title,
            overdue_only=True,
        )

        assert total == 1
        assert goals[0].id == goal_id

        print("GOAL RETRIEVAL AND FILTERING PASSED")

        print("\n=== TEST 3: UPDATE LEARNING GOAL ===")

        goal = update_learning_goal(
            db,
            goal,
            LearningGoalUpdate(
                progress=65,
            ),
        )

        assert goal.progress == 65
        assert goal.status == "In Progress"

        print("Updated progress: 65%")
        print("UPDATE GOAL PASSED")

        print("\n=== TEST 4: CREATE ACTIVITY LOG ===")

        log = create_implementation_log(
            db,
            ImplementationLogCreate(
                title=log_title,
                description="Temporary repository test",
                project_id=2,
                goal_id=goal_id,
                activity_type="Coding",
                duration_minutes=120,
                activity_date=today,
            ),
        )

        log_id = log.id

        assert log.id is not None
        assert log.project_id == 2
        assert log.goal_id == goal_id

        print(f"Log ID: {log_id}")
        print("CREATE ACTIVITY LOG PASSED")

        print("\n=== TEST 5: RETRIEVE AND FILTER LOGS ===")

        retrieved_log = get_implementation_log_by_id(
            db,
            log_id,
        )

        assert retrieved_log is not None
        assert retrieved_log.title == log_title

        logs, total = list_implementation_logs(
            db=db,
            project_id=2,
            goal_id=goal_id,
            activity_type="Coding",
            start_date=today,
            end_date=today,
            q=log_title,
        )

        assert total == 1
        assert logs[0].id == log_id

        print("LOG RETRIEVAL AND FILTERING PASSED")

        print("\n=== TEST 6: UPDATE ACTIVITY LOG ===")

        log = update_implementation_log(
            db,
            log,
            ImplementationLogUpdate(
                duration_minutes=150,
                activity_type="Testing",
            ),
        )

        assert log.duration_minutes == 150
        assert log.activity_type == "Testing"

        print("Updated duration: 150 minutes")
        print("UPDATE ACTIVITY LOG PASSED")

        print("\n=== TEST 7: PROGRESS STATISTICS ===")

        stats = get_progress_stats(db)

        print(json.dumps(stats, indent=2))

        assert stats["total_goals"] >= 1
        assert stats["in_progress"] >= 1
        assert stats["overdue_goals"] >= 1

        assert stats["total_logs"] >= 1
        assert stats["total_minutes"] >= 150

        assert any(
            item["activity_type"] == "Testing"
            and item["duration_minutes"] >= 150
            for item in stats["activity_by_type"]
        )

        print("PROGRESS STATISTICS PASSED")

        print("\n=== TEST 8: DELETE TEMPORARY RECORDS ===")

        delete_implementation_log(db, log)
        log_id = None

        assert get_implementation_log_by_id(
            db,
            retrieved_log.id,
        ) is None

        delete_learning_goal(db, goal)
        goal_id = None

        assert get_learning_goal_by_id(
            db,
            retrieved.id,
        ) is None

        print("DELETE OPERATIONS PASSED")

        print("\n=== FINAL DATABASE STATISTICS ===")

        print(json.dumps(
            get_progress_stats(db),
            indent=2,
        ))

        print(
            "\nALL 8 PROGRESS REPOSITORY TESTS PASSED"
        )

    finally:
        db.rollback()

        try:
            if log_id is not None:
                remaining_log = get_implementation_log_by_id(
                    db,
                    log_id,
                )

                if remaining_log is not None:
                    delete_implementation_log(
                        db,
                        remaining_log,
                    )

            if goal_id is not None:
                remaining_goal = get_learning_goal_by_id(
                    db,
                    goal_id,
                )

                if remaining_goal is not None:
                    delete_learning_goal(
                        db,
                        remaining_goal,
                    )

        finally:
            db.close()


if __name__ == "__main__":
    main()

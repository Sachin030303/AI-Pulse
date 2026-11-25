
"""Integration tests for Progress Tracking service."""

from datetime import date, timedelta
from uuid import uuid4

from app.db.session import SessionLocal
from app.models import LearningGoal, ImplementationLog
from app.schemas.progress import (
    LearningGoalCreate,
    LearningGoalUpdate,
    ImplementationLogCreate,
    ImplementationLogUpdate,
)
from app.services import progress_service as service


def main():
    db = SessionLocal()

    goal_ids = []
    log_ids = []

    token = uuid4().hex[:8]
    today = date.today()

    try:
        # ----------------------------------
        # TEST 1: CREATE IN-PROGRESS GOAL
        # ----------------------------------

        goal = service.add_learning_goal(
            db,
            LearningGoalCreate(
                title=f"FastAPI Learning {token}",
                progress=40,
                start_date=today,
                target_date=today + timedelta(days=10),
            ),
        )

        goal_ids.append(goal.id)

        assert goal.status == "In Progress"
        assert goal.progress == 40
        assert goal.completed_at is None

        print("PASS 1: Goal creation and status inference")

        # ----------------------------------
        # TEST 2: CREATE COMPLETED GOAL
        # ----------------------------------

        completed_goal = service.add_learning_goal(
            db,
            LearningGoalCreate(
                title=f"Completed Learning {token}",
                status="Completed",
            ),
        )

        goal_ids.append(completed_goal.id)

        assert completed_goal.progress == 100
        assert completed_goal.completed_at is not None

        print("PASS 2: Completed goal and timestamp")

        # ----------------------------------
        # TEST 3: COMPLETE EXISTING GOAL
        # ----------------------------------

        goal = service.modify_learning_goal(
            db,
            goal.id,
            LearningGoalUpdate(status="Completed"),
        )

        assert goal.status == "Completed"
        assert goal.progress == 100
        assert goal.completed_at is not None

        completion_time = goal.completed_at

        print("PASS 3: Automatic completion handling")

        # ----------------------------------
        # TEST 4: PRESERVE COMPLETION TIME
        # ----------------------------------

        goal = service.modify_learning_goal(
            db,
            goal.id,
            LearningGoalUpdate(
                description="Completed goal updated",
            ),
        )

        assert goal.completed_at == completion_time

        print("PASS 4: Completion timestamp preserved")

        # ----------------------------------
        # TEST 5: REOPEN COMPLETED GOAL
        # ----------------------------------

        goal = service.modify_learning_goal(
            db,
            goal.id,
            LearningGoalUpdate(
                status="In Progress",
                progress=30,
            ),
        )

        assert goal.status == "In Progress"
        assert goal.progress == 30
        assert goal.completed_at is None

        print("PASS 5: Goal reopening")

        # ----------------------------------
        # TEST 6: INVALID DATE REJECTION
        # ----------------------------------

        try:
            service.modify_learning_goal(
                db,
                goal.id,
                LearningGoalUpdate(
                    target_date=today - timedelta(days=1),
                ),
            )
        except service.InvalidProgressDataError:
            print("PASS 6: Invalid dates rejected")
        else:
            raise AssertionError(
                "Invalid dates were accepted"
            )

        # ----------------------------------
        # TEST 7: CREATE ACTIVITY LOG
        # ----------------------------------

        log = service.add_implementation_log(
            db,
            ImplementationLogCreate(
                title=f"Progress Testing {token}",
                project_id=2,
                goal_id=goal.id,
                activity_type="Coding",
                duration_minutes=60,
            ),
        )

        log_ids.append(log.id)

        assert log.project_id == 2
        assert log.goal_id == goal.id

        print("PASS 7: Linked activity log creation")

        # ----------------------------------
        # TEST 8: UPDATE ACTIVITY LOG
        # ----------------------------------

        log = service.modify_implementation_log(
            db,
            log.id,
            ImplementationLogUpdate(
                activity_type="Testing",
                duration_minutes=90,
            ),
        )

        assert log.activity_type == "Testing"
        assert log.duration_minutes == 90

        print("PASS 8: Activity log update")

        # ----------------------------------
        # TEST 9: FILTER ACTIVITY LOGS
        # ----------------------------------

        results = service.get_implementation_logs(
            db,
            project_id=2,
            goal_id=goal.id,
            activity_type="Testing",
            q=token,
        )

        assert results.total == 1
        assert results.items[0].id == log.id

        print("PASS 9: Activity log filtering")

        # ----------------------------------
        # TEST 10: INVALID REFERENCE
        # ----------------------------------

        try:
            service.add_implementation_log(
                db,
                ImplementationLogCreate(
                    title="Invalid Project Test",
                    project_id=999999999,
                ),
            )
        except service.ProgressReferenceNotFoundError:
            print("PASS 10: Invalid project rejected")
        else:
            raise AssertionError(
                "Invalid project reference was accepted"
            )

        # ----------------------------------
        # TEST 11: INVALID SKILL
        # ----------------------------------

        try:
            service.add_learning_goal(
                db,
                LearningGoalCreate(
                    title="Invalid Skill Test",
                    skill_id=999999999,
                ),
            )
        except service.ProgressReferenceNotFoundError:
            print("PASS 11: Invalid skill rejected")
        else:
            raise AssertionError(
                "Invalid skill reference was accepted"
            )

        # ----------------------------------
        # TEST 12: SERVICE STATISTICS
        # ----------------------------------

        stats = service.progress_statistics(db)

        assert stats.total_goals >= 2
        assert stats.completed >= 1
        assert stats.in_progress >= 1
        assert stats.total_logs >= 1
        assert stats.total_minutes >= 90

        print("PASS 12: Progress statistics")

        print("\nALL 12 SERVICE TESTS PASSED")

    finally:
        # Remove only records created by these tests.
        try:
            db.rollback()

            for log_id in log_ids:
                if db.get(ImplementationLog, log_id):
                    service.remove_implementation_log(
                        db,
                        log_id,
                    )

            for goal_id in goal_ids:
                if db.get(LearningGoal, goal_id):
                    service.remove_learning_goal(
                        db,
                        goal_id,
                    )

            print("Temporary test records cleaned up")

        finally:
            db.close()


if __name__ == "__main__":
    main()


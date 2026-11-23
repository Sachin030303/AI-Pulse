"""Test Projects repository and task management."""

import json
from datetime import date, timedelta
from uuid import uuid4

from app.db.session import SessionLocal
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectTaskCreate,
    ProjectTaskUpdate,
)
from app.repositories.project_repository import (
    create_project,
    get_project_by_id,
    get_project_by_name,
    list_projects,
    update_project,
    delete_project,
    create_task,
    get_task_by_id,
    list_tasks,
    update_task,
    delete_task,
    get_project_progress,
    get_project_stats,
)


def main():

    db = SessionLocal()

    project_id = None

    test_name = f"Test AI Project {uuid4().hex[:8]}"

    today = date.today()

    try:

        print("\n=== TEST 1: CREATE PROJECT ===")

        project = create_project(
            db,
            ProjectCreate(
                name=test_name,
                category="Artificial Intelligence",
                description="Temporary repository test",
                status="In Progress",
                priority="High",
                start_date=today - timedelta(days=10),
                due_date=today - timedelta(days=1),
            ),
        )

        project_id = project.id

        assert project.id is not None

        print(f"Project ID: {project_id}")
        print(f"Project Name: {project.name}")
        print("CREATE PROJECT PASSED")

        print("\n=== TEST 2: RETRIEVE PROJECT ===")

        project = get_project_by_id(
            db,
            project_id,
        )

        assert project is not None
        assert project.name == test_name

        project = get_project_by_name(
            db,
            test_name.lower(),
        )

        assert project is not None
        assert project.id == project_id

        print("PROJECT RETRIEVAL PASSED")

        print("\n=== TEST 3: UPDATE PROJECT ===")

        project = update_project(
            db,
            project,
            ProjectUpdate(
                description="Updated project description",
            ),
        )

        assert (
            project.description
            == "Updated project description"
        )

        print("UPDATE PROJECT PASSED")

        print("\n=== TEST 4: FILTER PROJECTS ===")

        projects, total = list_projects(
            db=db,
            category="Artificial Intelligence",
            status="In Progress",
            priority="High",
            q=test_name,
            page=1,
            page_size=10,
        )

        assert total == 1
        assert projects[0].id == project_id

        print("PROJECT FILTERING PASSED")

        print("\n=== TEST 5: CREATE PROJECT TASKS ===")

        task1 = create_task(
            db,
            project_id,
            ProjectTaskCreate(
                title="Build backend API",
                status="Completed",
                priority="High",
            ),
        )

        task2 = create_task(
            db,
            project_id,
            ProjectTaskCreate(
                title="Develop frontend",
                status="In Progress",
                priority="High",
            ),
        )

        task3 = create_task(
            db,
            project_id,
            ProjectTaskCreate(
                title="Deploy application",
                status="Not Started",
                priority="Medium",
                due_date=today - timedelta(days=1),
            ),
        )

        task4 = create_task(
            db,
            project_id,
            ProjectTaskCreate(
                title="Write documentation",
                status="Blocked",
                priority="Low",
            ),
        )

        task1_id = task1.id
        task2_id = task2.id
        task3_id = task3.id
        task4_id = task4.id

        assert task1.completed_at is not None
        assert task2.completed_at is None

        print("Four tasks created successfully")

        print("CREATE TASKS PASSED")

        print("\n=== TEST 6: LIST AND FILTER TASKS ===")

        tasks, total = list_tasks(
            db,
            project_id,
        )

        assert total == 4

        tasks, total = list_tasks(
            db=db,
            project_id=project_id,
            status="Completed",
        )

        assert total == 1
        assert tasks[0].id == task1_id

        print("TASK FILTERING PASSED")

        print("\n=== TEST 7: CALCULATE PROJECT PROGRESS ===")

        progress = get_project_progress(
            db,
            [project_id],
        )[project_id]

        print(json.dumps(progress, indent=2))

        assert progress["total_tasks"] == 4
        assert progress["completed_tasks"] == 1
        assert progress["progress"] == 25.0

        print("PROGRESS CALCULATION PASSED")

        print("\n=== TEST 8: COMPLETE A TASK ===")

        task = get_task_by_id(
            db,
            project_id,
            task2_id,
        )

        task = update_task(
            db,
            task,
            ProjectTaskUpdate(
                status="Completed",
            ),
        )

        assert task.status == "Completed"
        assert task.completed_at is not None

        progress = get_project_progress(
            db,
            [project_id],
        )[project_id]

        assert progress["progress"] == 50.0

        print("Progress increased to 50%")
        print("TASK COMPLETION PASSED")

        print("\n=== TEST 9: REOPEN A TASK ===")

        task = update_task(
            db,
            task,
            ProjectTaskUpdate(
                status="In Progress",
            ),
        )

        assert task.completed_at is None

        progress = get_project_progress(
            db,
            [project_id],
        )[project_id]

        assert progress["progress"] == 25.0

        print("Progress returned to 25%")
        print("TASK REOPENING PASSED")

        print("\n=== TEST 10: PROJECT STATISTICS ===")

        stats = get_project_stats(db)

        print(json.dumps(stats, indent=2))

        assert stats["total_projects"] >= 1
        assert stats["total_tasks"] >= 4
        assert stats["completed_tasks"] >= 1
        assert stats["blocked_tasks"] >= 1
        assert stats["overdue_projects"] >= 1
        assert stats["overdue_tasks"] >= 1

        print("STATISTICS PASSED")

        print("\n=== TEST 11: DELETE INDIVIDUAL TASK ===")

        task = get_task_by_id(
            db,
            project_id,
            task4_id,
        )

        delete_task(db, task)

        assert get_task_by_id(
            db,
            project_id,
            task4_id,
        ) is None

        print("DELETE TASK PASSED")

        print("\n=== TEST 12: CASCADE DELETE PROJECT ===")

        project = get_project_by_id(
            db,
            project_id,
        )

        delete_project(db, project)

        assert get_project_by_id(
            db,
            project_id,
        ) is None

        for task_id in [
            task1_id,
            task2_id,
            task3_id,
        ]:
            assert get_task_by_id(
                db,
                project_id,
                task_id,
            ) is None

        project_id = None

        print("Project and associated tasks deleted")
        print("CASCADE DELETE PASSED")

        print("\n=== FINAL DATABASE STATISTICS ===")

        print(json.dumps(
            get_project_stats(db),
            indent=2,
        ))

        print("\nALL 12 PROJECTS REPOSITORY TESTS PASSED")

    finally:

        db.rollback()

        try:
            if project_id is not None:

                remaining = get_project_by_id(
                    db,
                    project_id,
                )

                if remaining is not None:
                    delete_project(
                        db,
                        remaining,
                    )

        finally:
            db.close()


if __name__ == "__main__":
    main()
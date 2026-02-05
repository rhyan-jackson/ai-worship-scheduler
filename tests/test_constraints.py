import os
import sys
import unittest
from datetime import date
from typing import Set

from ortools.sat.python import cp_model

# --- IMPORT CONFIGURATION ---
# Allows importing modules from the parent 'project' directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Replace 'solver' and 'model' with your actual filenames if different
from src.model import Member, RoleDemand
from src.solver import ServiceSolver


class TestSolverConstraints(unittest.TestCase):
    """
    Test Suite focused on the 'Hard Constraints' of ServiceSolver.

    Goal:
    - Ensure the solver returns INFEASIBLE when business rules are violated.
    - Verify that critical filters (competence, availability) prevents variable creation.
    """

    def setUp(self):
        """
        Common setup used across multiple tests.
        """
        self.bass_player = Member(id=1, name="Bassist", roles={"Bass"}, max_shifts=5)
        self.drummer = Member(id=2, name="Drummer", roles={"Drums"}, max_shifts=5)

    def _solve_expecting_status(
        self, members, demands, unavailabilities, expected_status
    ) -> bool:
        """
        Helper method to reduce boilerplate in tests.

        Args:
            members: List of Member objects.
            demands: List of RoleDemand objects.
            unavailabilities: Set of unavailability tuples.
            expected_status: The cp_model status expected (e.g., INFEASIBLE).

        Returns:
            bool: True if the actual status matches the expected status.
        """
        solver = ServiceSolver(members, demands, unavailabilities)
        solver.build_model()
        status = solver.solve()
        return status == expected_status

    def test_min_quantity_constraint_insufficient_members(self):
        """
        SCENARIO:
        The demand requires 2 Bassists, but only 1 is available in the member list.

        EXPECTATION:
        INFEASIBLE. The solver should fail due to understaffing.
        """
        print("\n🧪 [Test] Min Quantity (Understaffing)...")

        demands = [
            RoleDemand(
                date=date(2025, 10, 27),
                event_type="Service",
                role="Bass",
                min_qty=2,  # <--- Requires 2
                max_qty=2,
            )
        ]

        # We provide only 1 bassist
        success = self._solve_expecting_status(
            members=[self.bass_player],
            demands=demands,
            unavailabilities=set(),
            expected_status=cp_model.INFEASIBLE,
        )

        self.assertTrue(
            success, "The solver should fail due to lack of qualified members."
        )

    def test_daily_uniqueness_constraint(self):
        """
        SCENARIO:
        The same member is required for 2 mandatory events on the SAME day.

        EXPECTATION:
        INFEASIBLE. A member cannot work two shifts on the same day
        (based on current daily_uniqueness logic).
        """
        print("\n🧪 [Test] Daily Uniqueness (Ubiquity)...")

        # Two mandatory demands on the same day for 'Bass'
        demands = [
            RoleDemand(
                date=date(2025, 10, 27),
                event_type="Morning",
                role="Bass",
                min_qty=1,
                max_qty=1,
            ),
            RoleDemand(
                date=date(2025, 10, 27),
                event_type="Evening",
                role="Bass",
                min_qty=1,
                max_qty=1,
            ),
        ]

        # Only 1 bassist exists
        success = self._solve_expecting_status(
            members=[self.bass_player],
            demands=demands,
            unavailabilities=set(),
            expected_status=cp_model.INFEASIBLE,
        )

        self.assertTrue(
            success,
            "The solver must not allow scheduling the same person twice on the same day.",
        )

    def test_competence_filter(self):
        """
        SCENARIO:
        There is a demand for 'Drums', but the only available member is a 'Bassist'.

        EXPECTATION:
        INFEASIBLE. The competence filter in `_create_variables` should prevent
        the creation of assignment variables for this member.
        """
        print("\n🧪 [Test] Competence Filter (Wrong Role)...")

        demands = [
            RoleDemand(
                date=date(2025, 10, 27),
                event_type="Service",
                role="Drums",  # <--- Requires Drums
                min_qty=1,
                max_qty=1,
            )
        ]

        # We pass only the Bassist
        success = self._solve_expecting_status(
            members=[self.bass_player],
            demands=demands,
            unavailabilities=set(),
            expected_status=cp_model.INFEASIBLE,
        )

        self.assertTrue(
            success,
            "The solver must not schedule someone without the required competence.",
        )

    def test_availability_filter(self):
        """
        SCENARIO:
        The member has the competence, but is listed in `unavailabilities` for that date.

        EXPECTATION:
        INFEASIBLE. The availability filter should prevent variable creation.
        """
        print("\n🧪 [Test] Availability Filter (Vacation/Block)...")

        target_date = date(2025, 10, 27)

        demands = [
            RoleDemand(
                date=target_date,
                event_type="Service",
                role="Bass",
                min_qty=1,
                max_qty=1,
            )
        ]

        # The Bassist is unavailable on this specific date
        unavailabilities = {(self.bass_player.id, target_date)}

        success = self._solve_expecting_status(
            members=[self.bass_player],
            demands=demands,
            unavailabilities=unavailabilities,
            expected_status=cp_model.INFEASIBLE,
        )

        self.assertTrue(
            success, "The solver must not schedule members marked as unavailable."
        )

    def test_rolling_window_fatigue(self):
        """
        SCENARIO:
        Member has a `max_shifts` of 2.
        We request 3 mandatory shifts within a short period (consecutive days).

        EXPECTATION:
        INFEASIBLE. The rolling window constraint should limit the sum of shifts
        within any 30-day period to `max_shifts`.
        """
        print("\n🧪 [Test] Rolling Window (Fatigue Management)...")

        # Member tires quickly (max 2 shifts per 30 days)
        tired_member = Member(id=99, name="Tired", roles={"Bass"}, max_shifts=2)

        # 3 Consecutive Demands
        demands = [
            RoleDemand(
                date=date(2025, 10, 1),
                event_type="E1",
                role="Bass",
                min_qty=1,
                max_qty=1,
            ),
            RoleDemand(
                date=date(2025, 10, 2),
                event_type="E2",
                role="Bass",
                min_qty=1,
                max_qty=1,
            ),
            RoleDemand(
                date=date(2025, 10, 3),
                event_type="E3",
                role="Bass",
                min_qty=1,
                max_qty=1,
            ),
        ]

        solver = ServiceSolver([tired_member], demands, set())
        solver.build_model()
        status = solver.solve()

        # Check: If logic is implemented, it should be INFEASIBLE.
        # If logic is 'pass', it will be OPTIMAL (Fail).
        if status == cp_model.OPTIMAL:
            self.fail(
                "❌ FAIL: Solver found a solution. Rolling Window constraint is likely missing or ineffective."
            )

        self.assertEqual(
            status,
            cp_model.INFEASIBLE,
            "Member exceeded max_shifts within the rolling window.",
        )


if __name__ == "__main__":
    unittest.main()

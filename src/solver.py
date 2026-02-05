from datetime import date
from pprint import pprint
from typing import Dict, List, Set, Tuple

from ortools.sat.python import cp_model

from .loader import load_data
from .model import Event, EventTemplate, Member, RoleDemand, TemplateRule


class ServiceSolver:
    def __init__(
        self,
        members: List[Member],
        demands: List[RoleDemand],
        unavailabilities: Set[Tuple[int, date]],
    ):
        self.members = members
        self.demands = demands
        self.unavailabilities = unavailabilities
        self.model = cp_model.CpModel()
        self.shifts = {}  # Map: (member_idx, demand_idx) -> cp_model.BoolVar

    def build_model(self):
        """
        Orchestrates the construction of the constraint programming model.
        It calls specialized private methods to add variables, constraints, and objectives.
        """

        # 1. Variables
        self._create_variables()

        # 2. Hard Constraints
        self._add_demand_constraints()
        self._add_daily_uniqueness_constraints()
        self._add_rolling_window_constraints()

        # 3. Objective (Soft Constraints)
        self._set_objective()

    def _create_variables(self):
        """
        Creates boolean decision variables X[m, d] for the solver.

        Logic:
        - Iterates through all members and demands.
        - Applies 'Hard Filters' immediately:
            1. Competence: Member must have the role required by the demand.
            2. Availability: Member must NOT be in the unavailability list for that date.
        - If filters pass, creates a NewBoolVar and stores it in self.shifts.
        """
        for m_idx, member in enumerate(self.members):
            for d_idx, demand in enumerate(self.demands):
                # Filter 1: Competence
                member_can_execute = demand.role in member.roles

                # Filter 2: Availability
                member_is_available = (
                    member.id,
                    demand.date,
                ) not in self.unavailabilities

                if member_can_execute and member_is_available:
                    self.shifts[(m_idx, d_idx)] = self.model.NewBoolVar(
                        f"shift_{m_idx}_{d_idx}"
                    )

    def _add_demand_constraints(self):
        """
        Orchestrator: Ensures all demand-related quantity rules are applied.
        Delegates specific rules to specialized private methods.
        """
        self._add_min_quantity_constraints()
        self._add_max_quantity_constraints()

    def _add_min_quantity_constraints(self):
        """
        Adds Hard Constraints for minimum role quantity.

        Logic:
        - Iterates through all demands.
        - For each demand 'd', identifies which members 'm' have a variable X[m, d].
        - Adds constraint: sum(X[*, d]) >= demand.min_qty
        """

        for d_idx, d in enumerate(self.demands):
            if not d.is_mandatory:
                continue

            vars = [
                self.shifts[(m_idx, d_idx)]
                for m_idx, _ in enumerate(self.members)
                if (m_idx, d_idx) in self.shifts
            ]

            self.model.Add(sum(vars) >= d.min_qty)

    def _add_max_quantity_constraints(self):
        """
        Adds Hard Constraints for maximum role quantity.

        Logic:
        - Iterates through all demands.
        - For each demand 'd', identifies which members 'm' have a variable X[m, d].
        - Adds constraint: sum(X[*, d]) <= demand.max_qty
        """
        for d_idx, d in enumerate(self.demands):
            vars = [
                self.shifts[(m_idx, d_idx)]
                for m_idx, _ in enumerate(self.members)
                if (m_idx, d_idx) in self.shifts
            ]

            self.model.Add(sum(vars) <= d.max_qty)

    def _add_daily_uniqueness_constraints(self):
        """
        Adds Hard Constraints to prevent double-booking on the same day.

        Logic:
        - Groups demands by date.
        - For each date and each member:
        - Gather all variables X[m, d] where 'd' occurs on that date.
        - Constraint: sum(X[m, *]) <= 1
        (A member can perform at most 1 task per day).
        """

        demand_by_date = {}
        for dmnd_id, demand in enumerate(self.demands):
            if demand.date not in demand_by_date:
                demand_by_date[demand.date] = []

            demand_by_date[demand.date].append(dmnd_id)

        for dt, d_ids in demand_by_date.items():
            for m_id, member in enumerate(self.members):
                vars = []
                for dmnd_id in d_ids:
                    if (m_id, dmnd_id) in self.shifts:
                        vars.append(self.shifts[(m_id, dmnd_id)])
                self.model.Add(sum(vars) <= 1)

    def _add_rolling_window_constraints(self):
        """
        Adds Hard Constraints for fatigue management (Rolling Window).

        Logic:
        - Sliding window of 30 days.
        - For each member 'm' and each day 't':
        - Consider a window [t, t+30].
        - Sum all shifts X[m, d] where demand 'd' is within this window.
        - Constraint: window_sum <= member.max_shifts
        """
        pass

    def _set_objective(self):
        """
        Defines the Objective Function to optimize for fairness.

        Logic:
        - Calculate total load for each member: L[m] = sum(all shifts of m).
        - Strategy: Minimize the sum of squared loads (L[m]^2).
        - This penalizes outliers (overworked members) more heavily than linear minimization,
        promoting a balanced distribution.
        """
        pass

    def solve(self):
        """
        Executes the solver engine.
        Returns:
            The status of the solution (OPTIMAL, FEASIBLE, INFEASIBLE, etc.)
        """

        self.solver = cp_model.CpSolver()
        # Defines max time or log
        # self.solver.parameters.max_time_in_seconds = 10.0
        # self.solver.parameters.log_search_progress = True

        status = self.solver.Solve(self.model)
        return status


if __name__ == "__main__":
    members, demands, unavailabilities = load_data()
    solver = ServiceSolver(members, demands, unavailabilities)
    shifts = solver.build_model()

    pprint(members)
    pprint(demands)
    pprint(shifts)

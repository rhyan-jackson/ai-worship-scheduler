import logging
from datetime import date
from pprint import pprint
from typing import Dict, List, Set, Tuple

from ortools.sat.python import cp_model

from .loader import load_data
from .model import Event, EventTemplate, Member, RoleDemand, TemplateRule

logger = logging.getLogger(__name__)


class ServiceSolver:
    def __init__(
        self,
        members: List[Member],
        demands: List[RoleDemand],
        unavailabilities: Set[Tuple[int, date]],
        limit_days: int = 30,
    ):
        self.members = members
        self.demands = demands
        self.unavailabilities = unavailabilities
        self.limit_days = limit_days
        self.model = cp_model.CpModel()
        self.shifts = {}  # Map: (member_idx, demand_idx) -> cp_model.BoolVar

        logger.info(
            f"ServiceSolver initialized with {len(members)} members and {len(demands)} demands."
        )

    def build_model(self):
        """
        Orchestrates the construction of the constraint programming model.
        It calls specialized private methods to add variables, constraints, and objectives.
        """
        logger.info("Starting model construction...")

        # Variables
        self._create_variables()

        # Hard Constraints
        self._add_demand_constraints()
        self._add_daily_uniqueness_constraints()
        self._add_rolling_window_constraints()

        # Objective (Soft Constraints)
        self._set_objective()

        logger.info("Model construction complete.")

    def _create_variables(self):
        """
        Creates boolean decision variables X[m, d] for the solver.

        Logic:
        - Iterates through all members and demands.
        - Applies 'Hard Filters' immediately:
            - Competence: Member must have the role required by the demand.
            - Availability: Member must NOT be in the unavailability list for that date.
        - If filters pass, creates a NewBoolVar and stores it in self.shifts.
        """
        for m_idx, member in enumerate(self.members):
            for d_idx, demand in enumerate(self.demands):
                # Competence
                member_can_execute = demand.role in member.roles

                # Availability
                member_is_available = (
                    member.id,
                    demand.date,
                ) not in self.unavailabilities

                if member_can_execute and member_is_available:
                    self.shifts[(m_idx, d_idx)] = self.model.NewBoolVar(
                        f"shift_{m_idx}_{d_idx}"
                    )

        logger.info(f"Created {len(self.shifts)} decision variables.")

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

    def _get_member_shifts(self, member_idx: int, demand_indices):
        """
        Helper to retrieve existing shift variables for a member
        given a list (or set) of demand indices.
        """
        return [
            self.shifts[(member_idx, d_idx)]
            for d_idx in demand_indices
            if (member_idx, d_idx) in self.shifts
        ]

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
                shift_vars = self._get_member_shifts(m_id, d_ids)
            if shift_vars:
                self.model.Add(sum(shift_vars) <= 1)

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

        demand_by_date = {}
        for dmnd_id, demand in enumerate(self.demands):
            if demand.date not in demand_by_date:
                demand_by_date[demand.date] = []

            demand_by_date[demand.date].append(dmnd_id)

        def date_inside_delta(start_date, check_date, limit_days) -> bool:
            diff = (check_date - start_date).days
            return 0 <= diff <= limit_days

        sorted_dates = sorted(demand_by_date.keys())

        for reference_date in sorted_dates:
            inside_timedelta = filter(
                lambda x: date_inside_delta(reference_date, x, self.limit_days),
                sorted_dates,
            )

            dmnd_ids = set()
            for peripheral_date in inside_timedelta:
                for dmnd_id in demand_by_date[peripheral_date]:
                    dmnd_ids.add(dmnd_id)

            for m_id, member in enumerate(self.members):
                for dmnd_id in dmnd_ids:
                    shift_vars = self._get_member_shifts(m_id, dmnd_ids)
                if shift_vars:
                    self.model.Add(sum(shift_vars) <= member.max_shifts)

    def _set_objective(self):
        """
        Defines the Objective Function to optimize for fairness.

        Logic:
        - Calculate total load for each member: L[m] = sum(all shifts of m).
        - Strategy: Minimize the sum of squared loads (L[m]^2).
        - This penalizes outliers (overworked members) more heavily than linear minimization,
        promoting a balanced distribution.
        """

        total_squared_loads = []
        all_demands = range(len(self.demands))
        upper_bound = len(self.demands)

        for m_id, member in enumerate(self.members):
            shift_vars = self._get_member_shifts(m_id, all_demands)
            load = self.model.NewIntVar(0, upper_bound, f"load_{m_id}")
            self.model.Add(load == sum(shift_vars))

            square = self.model.NewIntVar(0, upper_bound**2, f"sq_{m_id}")

            self.model.AddMultiplicationEquality(square, [load, load])

            total_squared_loads.append(square)

        self.model.Minimize(sum(total_squared_loads))

    def solve(self) -> List[Dict]:
        """
        Executes the solver engine and extracts the schedule.

        Returns:
            List[Dict]: A list of assignments (Date, Member, Role) if a solution is found.
            Returns an empty list if no solution is found.
        """
        logger.info("Starting solver optimization...")

        self.solver = cp_model.CpSolver()
        # Optional: Set parameters for speed vs optimality
        # self.solver.parameters.max_time_in_seconds = 30.0

        status = self.solver.Solve(self.model)
        logger.info(f"Solver finished. Status: {self.solver.StatusName(status)}")

        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            logger.warning("No feasible solution found.")
            return []

        # Extract results
        schedule = []
        for (m_idx, d_idx), var in self.shifts.items():
            if self.solver.Value(var) == 1:
                member = self.members[m_idx]
                demand = self.demands[d_idx]

                schedule.append(
                    {
                        "date": demand.date,
                        "event": demand.event_type,
                        "role": demand.role,
                        "member_id": member.id,
                        "member_name": member.name,
                    }
                )

        logger.info(f"Optimization successful. Scheduled {len(schedule)} assignments.")

        # Sort by date for readability
        return sorted(schedule, key=lambda x: x["date"])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    members, demands, unavailabilities = load_data()
    solver = ServiceSolver(members, demands, unavailabilities)
    solver.build_model()
    shifts = solver.solve()

    pprint(members)
    pprint(demands)
    pprint(shifts)

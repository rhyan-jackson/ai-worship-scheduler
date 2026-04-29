# AI Church Rotation

AI Church Rotation is an automated scheduling tool designed specifically for worship teams and church volunteer groups. Its purpose is to take the hassle out of monthly or quarterly planning by automatically assigning members to services based on their skills, availability, and specific event requirements.

## How the Algorithm Works

The core of the project relies on **Constraint Programming**. The application translates your real-world scheduling rules into a mathematical model and finds a feasible, optimal schedule.

In a short and concise form, the algorithm:
1. **Loads Requirements**: Looks at the schedule of events and determines exactly which roles (and how many people per role) are needed based on predefined templates.
2. **Applies Constraints**: Filters possible assignments to ensure:
   - Members are only assigned to roles they know.
   - Members are never scheduled on dates they marked as unavailable.
   - Members do not exceed their `max_shifts` quota for the period.
3. **Solves**: Computes the optimal combination of volunteers that fulfills all role minimums and maximums across all scheduled events.

## Usage Guide

To use the tool, you will primarily interact with two scripts.

### 1. Generating a Schedule Skeleton
Instead of manually typing out every single date for a month or year, you can generate a base schedule.
1. Open `src/generate_schedule_skeleton.py`.
2. Edit `START_DATE`, `END_DATE`, and `WEEKDAY_CONFIG` to match the period and recurring services you want to plan.
3. Run the script from your terminal:
   ```bash
   python -m src.generate_schedule_skeleton
   ```
This will automatically generate a `schedule.csv` inside your `data/` folder, mapping your dates to their respective service templates.

### 2. Running the Solver
Once all your data files (members, templates, schedule, etc.) are set up in the `data/` folder, you can run the optimization algorithm:
```bash
python main.py
```
This script will read the inputs, build the mathematical model, solve for the best schedule, and export the generated results to the `out/` directory.

## Data Files

The system relies on CSV files located in the `data/` directory to build the schedule. 

If you are just starting, **check the `example/` directory**. It contains properly formatted template files with dummy data that you can copy directly into your `data/` folder to use as a starting point.

Here is what each file represents:

* **`members.csv`**: Your roster of volunteers. Contains their `id`, `name`, the `roles` they are capable of playing (separated by semicolons, e.g., `Violão;Voz`), and their `max_shifts` allowed in this period.
* **`service_templates.csv`**: Defines what each type of service requires. For example, a "Domingo" template might require a minimum of 1 and maximum of 2 "Voz" (Vocals), 1 "Violão", etc.
* **`schedule.csv`**: The calendar of events. Maps a specific `date` (DD/MM/YYYY) to an `event_template` (e.g., "Domingo"). You can generate this using the skeleton script mentioned above.
* **`unavailabilities.csv`**: Time-offs and blockouts. Maps a member's `name` to a specific `date` they cannot serve.
* **`custom_demands.csv`**: Overrides for specific dates. Useful for special events where you might need to adjust the standard template quantities (e.g., requiring 0 keyboards or 3 guitars on a specific Sunday).
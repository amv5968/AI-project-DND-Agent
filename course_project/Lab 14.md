# Completed Use Case

### Use case completed: Roll Dice

The Roll Dice use case is implemented and working in the course project.

- The tool function 'roll_d20' is implemented to run skill checks and return structured outcomes.
- The command format '/roll player=Name skill=stealth dc=14' is parse and validated.
- The engine executes the dice tool during a turn and appends the deterministic roll
narration to DM context

### Implementation evidence
- 'course_project/tools.py' implements 'roll_d20(...)' and 'parse_roll_request(...)'.
- 'course_project/engine.py' calls '_run_tools(...)', executes 'roll_d20(...)', and
includes tool notes in the response pipeline.

## Example

Input:

- '/roll Player=Aria skill=stealth dc=14'

System behavior:

- Parses the roll request
- Rolls a d20
- Returns success/failure narration
- Uses that ouput to guide the DM response for the current turn
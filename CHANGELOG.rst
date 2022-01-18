=========
Changelog
=========

Version 0.2.3
===========

- Move logging from the CLI to own module
- Create generate-scenario command to create Monte-Carlo scenarios and move it out of the run command
- Save all results into a .zip rather than specifying three output files for detailed output, summary and parameters.
- Improve documentation
- Export parameter summary
- fix EIR calculation for floating rate loans
- Add Constant-Growth and Indexed LGD models
- Simplify results summary logic
- Remove Series plot functionality to reduce number of dependencies of the model (Matplotlib)
- Implement unit tests for the CLI
- Upgrade PyScaffold
- Add ability to make an .exe file of the model
- Implement TOX automation

Version 0.2
===========

- Change execution method to speed up calculations

Version 0.1
===========

- Add STAGE_MAP into the ASSUMPTION.xlsx
- Add a basic CLI
- Rename 'stage' in the account level data to 'watchlist' so that it is not confused with the stage produced by the model.

=========
Changelog
=========

Version 0.2.5-dev
=============
- improve EAD model flexibility by adding a default penalty percentage and penalty amount that could be added to the
  EAD if an account enters default.

Version 0.2.4
=============

- Integrate logging into the Z-model execution. Logs are now saved to ~/logs/Z-model
- Add user license requirements. The user license should be saved at ~/.z_model_license and should be valid for the
  model to execute otherwise an error is thrown.
- Add a user friendly GUI to the Z-model CLI. This is now the default entry point into the Z-model.

Version 0.2.3
=============

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

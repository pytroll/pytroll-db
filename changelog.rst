Changelog
=========

v?.?.? (2024-04-04)
-------------------
- Cleanup: remove all SQL related files and references


v0.2.0 (2015-03-13)
-------------------

Fix
~~~

- Bugfix: ellipsoid in wkt. [Martin Raspaud]

- Bugfix: convert linestring to wkb. [Martin Raspaud]

- Creation time is TIMESTAMP, not INTEGER. [Martin Raspaud]

- Bugfix: corrected prototype of create_file_uri function. [Martin
  Raspaud]

- Bugfix: parameter_type_id was not used... [Martin Raspaud]

Other
~~~~~

- Update changelog. [Martin Raspaud]

- Bump version: 0.1.0 → 0.2.0. [Martin Raspaud]

- Rename. [Martin Raspaud]

- Remove unneeded import. [Martin Raspaud]

- Change name. [Martin Raspaud]

- Fix setup and version stuff. [Martin Raspaud]

- Use failsafe "save" instead of "commit" [Martin Raspaud]

- Handle dataset messages. [Martin Raspaud]

- Switch boundaries to geometry to allow different srids. [Martin
  Raspaud]

- Refresh hl_file. [Martin Raspaud]

- Fix satellite names to follow oscar conventions. [Martin Raspaud]

- Replace satellite with platform_name. [Martin Raspaud]

- Fix missing import logging.handlers. [Martin Raspaud]

- Refresh db_recorder. [Martin Raspaud]

- Replace filename with uid. [Martin Raspaud]

- Fix pytroll_cleanup for local files. [Martin Raspaud]

- Don't discriminate of the file type to add in the database. [Martin
  Raspaud]

- Add some requirements in setup.py. [Martin Raspaud]

- Add setup and version files. [Martin Raspaud]

- Update db_recorder to new posttroll. [Martin Raspaud]

- Change readme to rst syntax. [Martin Raspaud]

- Merging doobie from pytroll sandbox. [Martin Raspaud]

- Update test example. [Martin Raspaud]

- Allow pytroll_cleanup to work if the scheme is "file" [Martin Raspaud]

- Moved db_recorder.py. [Martin Raspaud]

- Add ssh support for cleanup. [Martin Raspaud]

- Support for time based searches in the database. [Martin Raspaud]

- Cleanup missing files from the database. Support ssh. [Martin Raspaud]

- Fixed merge. [safusr.u]

- Pythonizing the get_within_area_of_interest method. [Martin Raspaud]

- More geolocation for the db. [safusr.u]

- Do not overwrite subsat track. [Martin Raspaud]

- Working with sub-satellite tracks. [Martin Raspaud]

- Added support for sub satellite track. [Martin Raspaud]

- Typo. [Martin Raspaud]

- Adding db to the installable packages. [Martin Raspaud]

- Testing postgis stuff. [Adam.Dybbroe]

- Updated after Nov2011 pytroll week. [Adam.Dybbroe]

- Adding PPS Cloudtype metadata to database. [Adam.Dybbroe]

- Added cascading deletes in tables used for table "file" [Adam.Dybbroe]

- Added a delete and get_files methods. Adapted to be able to use
  cascade deletes. [Adam.Dybbroe]

- Changed wellcome description (test) [Esben S. Nielsen]

- Added hrpt 1b type and eps 1b format. [Martin Raspaud]

- Fixed bug in hl_file assigning a filetype to a fileformat... [Martin
  Raspaud]

- Cosmetics. [Martin Raspaud]

- Added an example of a file checker producer and a db consumer. [Martin
  Raspaud]

- Finished test_pytroll_db_insert.py. [Martin Raspaud]

- Cosmetics. [Martin Raspaud]

- Upgraded test_pytroll_db_insert.py. [Martin Raspaud]

- Changed kwargs dict to explicit argument names. [Kristian Rune Larsen]

- Cleaning up pytroll_db, and formating examples. [Martin Raspaud]

- Updated sql alchemy interface. [Esben S. Nielsen]

- Merge branch 'master' of https://github.com/mraspaud/pytroll. [Esben
  S. Nielsen]

- Removed. [Adam.Dybbroe]

- Removed. [Adam.Dybbroe]

- Modified model. [Esben S. Nielsen]

- Added create_parameter_file and removed duplicate create_file.
  [Kristian Rune Larsen]

- More generic create functions for parameter_value and
  parameter_linestring, added documentation. [Kristian Rune Larsen]

- No password. [Kristian Rune Larsen]

- ... [Esben S. Nielsen]

- ... [Kristian Rune Larsen]

- ... [Esben S. Nielsen]

- First working version. [Esben S. Nielsen]

- Merge conflict solved. [Esben S. Nielsen]

- Fix one small bug and cleaning up a bit. [Adam.Dybbroe]

- Testing the adding of a parameter_linestring as well (ground track).
  [Adam.Dybbroe]

- Added more facade functions. [Esben S. Nielsen]

- Now we can save. [Esben S. Nielsen]

- Added create functions. [Esben S. Nielsen]

- ... [Esben S. Nielsen]

- ... [Esben S. Nielsen]

- ... [Esben S. Nielsen]

- Merge branch 'master' of https://github.com/mraspaud/pytroll. [Esben
  S. Nielsen]

- Added new insert test. [Kristian Rune Larsen]

- Uses metaclass for geography type. [Esben S. Nielsen]

- Modifed model. [Esben S. Nielsen]

- Merge branch 'master' of https://github.com/mraspaud/pytroll. [Esben
  S. Nielsen]

- Adaptations for SQLAlchemy 0.6.x: Changing functions:
  process_bind_param          process_result_value Instead of:
  result_processor          bind_processor. [Adam.Dybbroe]

- Added more relations. [Esben S. Nielsen]

- ... [Esben S. Nielsen]

- ... [Esben S. Nielsen]

- Added sqltypes. [Esben S. Nielsen]

- Added sqlalchemy geography type. [Esben S. Nielsen]

- New db version. [Esben S. Nielsen]

- Updated README. [Esben S. Nielsen]

- Added db indices and postgisify script. [Esben S. Nielsen]

- Some initial code and design for the pytroll project
  postgreSQL/postGIS database. [Adam Dybbroe]

- Initial commit. [Martin Raspaud]

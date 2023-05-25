backup_retention
================
backup_retention is a script to move/delete old backups, while keeping some selected ones.
It is highly configurable and can work with files or directories of any time and date format (except am/pm - who uses that on file names anyway?).

Example usage
-------------
Progressive Retention (default)

python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=12 years=10" --verbose --action=list
this makes sure that the following are retained:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (the first week, all files will be retained becuase of days=7, then the next 5 weeks only the latest per week)
- the latest file for the first 12 months (as the first 6 weeks are saved anyway, 10-11 additional files will be retained the first year)
- the latest file for the first 12 quarters (after the first 12 months (4 quarters), an additonal 8 quarters will be retained)
- the latest file for the first 10 years (the first 3 years are already covered by quarters=12. For the remaining 7 years, only one file per year is retained)
- files older than 10 years, and those not covered by the above statements will be listed, moved or deleted, depending on your action.

Cumulative Retention (add --method=cumulative to enable)

python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=8 years=5" --verbose --action=list --method=cumulative
this makes sure that the following are retained:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (starting after the first 7 days, the latest file in next 6 weeks will be retained)
- the latest file for the first 12 months (starting after the first 6 weeks+7 days, the latest file in next 12 months will be retained)
- the latest file for the first 8 quarters (starting after the first 12 months+6 weeks+7 days, the latest file in next 8 quarters (two years) will be retained)
- the latest file for the first 10 years (starting after the first 8 quarters+12 months+6 weeks+7 days, the latest file in next 10 years will be retained)
- files older than that, and those not covered by the above statements will be listed, moved or deleted, depending on your action.


You can experiment with the input parameters until you find something that works for you, then change --action=list to --action=delete or --action-move destination=/my_other_backup_space

The default action is list, to prevent accidental deletion.

To get a complete list of input parameters, use --help

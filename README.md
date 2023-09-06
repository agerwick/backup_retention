## backup_retention
backup_retention is a script to move/delete old backups, while keeping some selected ones. It is used to keep more of the recent backups, but remove some of them the older they get, so your backup space doesn't fill up but you still have backups from different times.
It is highly configurable and can work with files or directories of any time and date format (except am/pm - who uses that on file names anyway?).

**The script is meant to run on the backup server.** It assumes you have either multiple full backups or that you have copied hard links (with cp -l) between each backup, and that the directory for each backup has some variation of a date (with optional time) in it. Here's an example of a typical backup directory structure that would work fine:

    2023-05-27
    2023-05-29
    2023-05-30
    2023-05-31
    2023-06-02
    2023-06-03
    2023-08-25

or this:

    20230829T0100
    20230830T0100
    20230831T0100
    20230901T0100
    20230902T0100
    20230903T0100
    20230904T0100
    20230905T0100
    20230906T0100

or even this:

    2021/
        09/
            30/
                0100
        12/
            31/
                0100
    2022/
        03/
            31/
                0100
        04/
            30/
                0100

To run it automatically after your backup, add something like this at the end of your backup script:
    ssh backup_user@backup_server backup_retention.sh
This assumes you have a shell script called backup_retention.sh in your home directory on the backup server. You could run backup_retention.py with all the parameters directly, but from experience, it's practical to have the script on the backup server as this is where you'll be when you find out you have to many backups. Here's an example backup_retention.sh script:
    #!/bin/bash
    python ~/backup_retention/backup_retention.py ~/backup/ --retention "earliest latest=3 days=7 weeks=4 fortnights=4 months=10 quarters=6 years=10" --verbose --format='{YYYY}-{MM}-{DD}' --action=delete --method=cumulative


## Example usage

### Progressive Retention (add --method=progressive to enable)

`python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=12 years=10" --verbose --action=list **--method=progressive**`

The command above ensures the retention of specific files based on the following criteria:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (the first week, all files will be retained becuase of days=7, then the next 5 weeks only the latest per week)
- the latest file for the first 12 months (as the first 6 weeks are saved anyway, 10-11 additional files will be retained the first year)
- the latest file for the first 12 quarters (after the first 12 months (4 quarters), an additonal 8 quarters will be retained)
- the latest file for the first 10 years (the first 3 years are already covered by quarters=12. For the remaining 7 years, only one file per year is retained)
- files older than 10 years, and those not covered by the above statements will be listed, moved or deleted, depending on your action.

### Cumulative Retention (default)

`python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=8 years=5" --verbose --action=list **--method=cumulative**`

The command above ensures the retention of specific files based on the following criteria:
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

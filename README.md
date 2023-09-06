## backup_retention
backup_retention is a script to move/delete old backups, while keeping some selected ones. It is used to keep more of the recent backups, but remove some of them the older they get, so your backup space doesn't fill up but you still have backups from different times.
It is highly configurable and can work with files or directories of any time and date format (except am/pm - who uses that on file names anyway?).

**The script is meant to run on the backup server.** It assumes you have either multiple full backups or that you have copied hard links (with cp -l) between each backup, and that the directory for each backup has some variation of a date (with optional time) in it. You'll find examples of directory structures further down.

## Example usage

### Progressive Retention (add --method=progressive to enable)

`python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=12 years=10" --verbose --action=list --method=progressive`

The command above ensures the retention of specific files based on the following criteria:
- the latest 3 files, regardless of timestamp
- the latest file for the first 7 days
- the latest file for the first 6 weeks (the first week, all files will be retained becuase of days=7, then the next 5 weeks only the latest per week)
- the latest file for the first 12 months (as the first 6 weeks are saved anyway, 10-11 additional files will be retained the first year)
- the latest file for the first 12 quarters (after the first 12 months (4 quarters), an additonal 8 quarters will be retained)
- the latest file for the first 10 years (the first 3 years are already covered by quarters=12. For the remaining 7 years, only one file per year is retained)
- files older than 10 years, and those not covered by the above statements will be listed, moved or deleted, depending on your action.

Note that with *Progressive Retention*, it is pretty much guaranteed that some of the latest files will have multiple retention criteria applied to them at the same time. For example, the latest file will also be the latest file of the day, week, fortnight, quarter, half-year and year. This guarantees that the longest time period specified (in this case, years=10) will be the absolute cutoff for how long files will be stored.
If you only want to start counting the first 7 days *after* the latest 3 files, then you should use *Cumulative Retention*.

### Cumulative Retention (default)

`python backup_retention.py /home/me/my_backups --retention "latest=3 days=7 weeks=6 months=12 quarters=8 years=5" --verbose --action=list --method=cumulative`

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

## Backup diretory structures

Here are some examples of a typical backup directory structures that would work fine, and the matching format string:

    .
    ├── 2023-05-27
    ├── 2023-05-29
    ├── 2023-05-30
    ├── 2023-05-31
    ├── 2023-06-02
    ├── 2023-06-03
    └── 2023-08-25

    --format="{YYYY}-{MM}-{DD}"

or this:

    .
    ├── 20230829T0100
    ├── 20230830T0100
    ├── 20230831T0100
    ├── 20230901T0100
    ├── 20230902T0100
    ├── 20230903T0100
    ├── 20230904T0100
    ├── 20230905T0100
    └── 20230906T0100

    --format="{YYYY}{MM}{DD}T{hh}{mm}"

or even this:

    .
    ├── 2021
    │   ├── 09
    │   |   ├── 30
    │   |       └── 0100
    │   └── 12
    │       └── 31
    │   ├──     └── 0100
    ├── 2022
    │   ├── 03
    │   |   └── 31
    │   |       └── 0100
    │   └── 04
    │       └── 30
                └── 0100
    
    --format="{YYYY}/{MM}/{DD}/{hh}{mm}"

Even if you have multiple users' backups sorted under the same dated directories, you can run different backup retention schemes for each user (if you wish). Given this directory structure:

    .
    ├── 20230901
    │   ├── jack
    │   └── jill
    ├── 20230902
    │   ├── jack
    │   └── jill
    ├── 20230903
    │   ├── jack
    │   └── jill
    ├── 20230904
    │   ├── jack
    │   └── jill
    ├── 20230905
    │   ├── jack
    │   └── jill
    └── 20230906
        ├── jack
        └── jill

    --format "{YYYY}{MM}{DD}/jack"  # this will only apply to Jack's files
    --format "{YYYY}{MM}{DD}/jill"  # this will only apply to Jill's files
    --format "{YYYY}{MM}{DD}"       # this will apply to all files

In order to remove empty directories, you can simply run rmdir on all directories after backup_retention, as it will fail if the directory is not empty:

    rmdir `find "." -type d` 2> /dev/null

The above command will only delete the last empty subdirectory each time it's run, but if next time the parent directory is also empty, then it will be deleted too. So all empty directories will *eventually* be deleted. If this is a problem for you, you can run it multiple times :)


## Running backup_retention after each backup

To run the backup_retention script automatically after your backup, add something like this at the end of your backup script:

    ssh backup_user@backup_server backup_retention.sh

This assumes you have a shell script called backup_retention.sh in your home directory on the backup server. You could run backup_retention.py with all the parameters directly, but from experience, it's practical to have the script on the backup server as this is where you'll be when you find out you have to many backups, especially if you don't have access to all the computers backing up there at any given time. Here's an example backup_retention.sh script:

    #!/bin/bash
    python ~/backup_retention/backup_retention.py ~/backup/ --retention "earliest latest=3 days=7 weeks=4 fortnights=4 months=10 quarters=6 years=10" --verbose --format='{YYYY}-{MM}-{DD}' --action=delete --method=cumulative

It assumes your backups are in ~/backup/ on your backup server and that you have the backup_retention script in a directory with the same name, which you can achieve by executing this when you're in your home directory:

    git clone https://github.com/agerwick/backup_retention.git


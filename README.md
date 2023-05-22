backup_retention
================
backup_retention is a script to move/delete old backups, while keeping some selected ones.
It is highly configurable and can work with files or directories of any time and date format (except am/pm - who uses that on file names anyway?).

Example usage
-------------
python backup_retention.py /home/me/my_backups --retention "keep-last=3 keep-daily=1 keep-weekly=1 keep-monthly=1 keep-yearly=1" --verbose --action=list

You can experiment with the input parameters until you find something that works for you, then change --action=list to --action=delete or --action-move destination=/my_other_backup_space

The default action is list, to prevent accidental deletion.

To get a complete list of input parameters, use --help

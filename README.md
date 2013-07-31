AustinMunicipalCourtScraper
===========================

The Austin Municipal Court takes care of most extremely low level crimes like traffic violations and misc fines. This tool asks for a person's last name and DOB, and then grabs their entire Austin Municipal Court case history, and writes it to a CSV file.

- Each individual violation can easily have twenty or more "events" associated with it. Everything that happens in a case's progress is recorded and available online ... everything from when you first get the ticket, to when they send you a reminder to pay, to someone getting an late fee, to a case being dismissed. This tool records all events.

# Usage

    usage: austin_municipal_court_scraper.py [-h] LAST DOB CSVFILE

    This tool searches the publicly-accessible City of Austin Municipal Court for
    a designated person's court history. Basically, the municipal court is
    responsible for small fines and traffic tickets, so it grabs every 'event'
    that happened (missed payment, case dismissal, reminders sent, etc.) for each
    violation in a person's history. It writes the records to CSV.

    arguments:
      LAST        Person of interests' last name.
      DOB         Person of interests' date of birth in MM/DD/YYYY format.
      CSVFILE     Filename to write csv to

    optional arguments:
      -h, --help  show this help message and exit
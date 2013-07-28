#!/usr/bin/python
"""
This tool takes a person's last name and DOB, grabs their Austin
Municipal Court case history and writes it to a CSV file 
COPYLEFT Brandon Robertz 2012 GPLv3+
"""
import urllib
import urllib2
import cookielib
from BeautifulSoup import BeautifulSoup
import sys
import re
from datetime import datetime
import csv
import argparse

def search_municipal( LASTNAME, dob_month, dob_day, dob_year):
  """ Search the Austin Municipal Court site for a person's record by last
      name, and date of birth. Return the results as a list of lists. Each
      row contains an event in a particular case.

      Parameters:
        LASTNAME  : Last name to look up
        dob_month : Month of birth as a number
        dob_day   : Day of birth as a number
        dob_year  : Year of birth, full four-digit long year, i.e., 1971

      Returns:
        A list containing a list for every event in the person's municipal
        court case history.
  """
  # Timeout
  TIMEOUT = 180

  #dob:
  MONTH = str( dob_month) #"7"
  DAY   = str( dob_day)   #"20"
  YEAR  = str( dob_year)  #"1981"

  cj = cookielib.CookieJar()

  headers = {
    "HTTP_USER_AGENT" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; "
                        "rv:1.9.0.13) Gecko/2009073022 Firefox/3.0.13",
    "HTTP_ACCEPT" : "text/html,application/xhtml+xml,application/xml;"
                    " q=0.9,*/*; q=0.8",
    "Content-Type": "application/x-www-form-urlencoded"
  }

  url = "https://www.austintexas.gov/AmcPublicInquiry/pubportal.aspx"

  # Initialize session, cookie, get viewstate, etc
  opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))
  try:
    response = opener.open(url, None, TIMEOUT)
    content = response.read()
  except:
    print "[!] Error getting: %s" % url

  #Get viewstate
  soup = BeautifulSoup(content)
  viewstate = soup.find(id="__VIEWSTATE",type="hidden")
  viewstate = viewstate.attrs[3][1]
  if not viewstate:
    print "[!] No viewstate (for building POST request)"
    #return None

  # Build formdata
  formdata = ( ("__EVENTTARGET"   , "personCmd"),
               ("__EVENTARGUMENT" , ""),
               ("__VIEWSTATE"     , viewstate) )

  # Move to next page
  encoded = urllib.urlencode(formdata)
  try:
    response = opener.open(url, encoded, TIMEOUT)
    content = response.read()
  except:
    print "[!] Error getting: %s" % url

  # Get next viewstate
  soup = BeautifulSoup(content)
  viewstate = soup.find(id="__VIEWSTATE")
  viewstate = viewstate.attrs[3][1]
  if not viewstate:
    print "[!] No viewstate (for building POST request)"
    #return None

  # Url and form data
  url = "https://www.austintexas.gov/AmcPublicInquiry/search/psnsearch.aspx"
  formdata = ( ("__EVENTTARGET"           , ""),
               ("__EVENTARGUMENT"         , ""),
               ("__VIEWSTATE"             , viewstate),
               ("searchForm$lastNameCtl"  , LASTNAME),
               ("searchForm$dobCtl$month" , MONTH),
               ("searchForm$dobCtl$day"   , DAY),
               ("searchForm$dobCtl$year"  , YEAR),
               ("searchForm$submitCmd"    , "Search"))

  encoded = urllib.urlencode(formdata)
  try:
    response = opener.open(url, encoded, TIMEOUT)
    content = response.read()
  except:
    print "[!] Error getting: %s" % url

  #if "No records found" not in content:
  # Parse table, find link to case summary
  soup = BeautifulSoup(content)
  table = soup.find(id="resultsControl_gridCtl")
  if not table or "No records found" in content:
    print "[!] No results!"
    #return None

  td = table.findAll("td")

  # our id & name
  id = str( td[0].find(text=True))
  name = str( td[1].find(text=True))

  # build new query, for that we need viewstate and __resultsControl_...
  # viewstate
  viewstate = soup.find(id="__VIEWSTATE").attrs[3][1]
  if not viewstate:
    print "[!] Couldn't get viewstate. Can't build next POST request."
    return None
  # __resultsControl_gridCtl_state
  rc = soup.find(id="__resultsControl_gridCtl_state").attrs[3][1]
  if not rc:
    print "[!] No __resultsControl_gridCtl_state. Can't build POST request."
    return None
    
  # new query & url
  url = ( "https://www.austintexas.gov/AmcPublicInquiry/query/"
          "psnquery.aspx?id=%s&view=0&query=1" % id )

  # Get request
  try:
    response = opener.open(url, None, TIMEOUT)
    content = response.read()
  except:
    print "[!] Error getting: %s" % url

  # Get our case summary table
  soup  = BeautifulSoup(content)
  table = soup.find("table",id="eventsCtl_gridCtl")

  if not table:
    print "[!] No table found!"
    return None

  # Loop through table and turn it into a csv string
  rows = []
  for tr in table.findAll("tr"):
    row = []
    for td in tr.findAll("td"):
      for line in td:
        try:
          line = line.find(text=True).strip()
        except:
          pass
        row.append( line)
    if row:
      row.insert(0, name)
      row.insert(0, id)
      rows.append( row)
  # send it back
  if rows:
    return rows
  else:
    return None 

def write_csv( recs, OFILE):
  """ Write our senate voting record to disk.

      Parameters:
        recs  : our iterable list containing a senate voting record
        OFILE : the filename to write the CSV to
  """
  if ".csv" not in OFILE:
    filename = "%s.csv"%OFILE
  else:
    filename = OFILE
  print "[*] Writing to %s"%filename
  header = [ "PERSON_ID", "NAME", "CASE_ID", "VIOLATION",
             "EVENT", "DATE", "TIME" ]
  with open(filename, 'wb') as f:
    w = csv.writer(f, header)
    w.writerow( header)
    w.writerows( recs)

def argz():
  parser = argparse.ArgumentParser()
  desc =("This tool searches the publicly-accessible City of Austin "
         "Municipal Court for a designated person's court history. Basically,"
         " the municipal court is responsible for small fines and traffic "
         "tickets, so it grabs every 'event' that happened (missed payment, "
         " case dismissal, reminders sent, etc.) for each violation in a "
         "person's history. It writes the records to CSV.")
  parser = argparse.ArgumentParser(description=desc)
  parser.add_argument("LAST", type=str, help="Person of interests' last name.")
  parser.add_argument("DOB", type=str, help="Person of interests' date of "
                                            "birth in MM/DD/YYYY format.")
  parser.add_argument("CSVFILE", type=str, help="Filename to write csv to")
  return parser.parse_args()

def splitdob( dob_str):
  """ Take a DOB string in MM/DD/YYYY format and return tuple of month, day,
      and year of birth.
  """
  try:
    dob = datetime.strptime( dob_str, "%m/%d/%Y")
  except Exception as e:
    print "[!] Error parsing DOB: %s"%dob_str
    print "[!] %s"%e
    return None
  return dob.month, dob.day, dob.year

def main():
  args = argz()
  dob = splitdob( args.DOB)
  if not dob:
    print "[!] No DOB, exiting."
    sys.exit(1)
  # unpack
  month, day, year = dob
  print "[*] Split %s -> %s %s %s"%(args.DOB, month, day, year)
  # search municipal court
  print "[*] Searching ... LASTNAME: %s DOB: %s/%s/%s" % ( args.LAST, month,
                                                           day, year)
  results = search_municipal( args.LAST, month, day, year)
  # if on results, bail
  if not results:
    print "[!] Error getting records, exiting."
    sys.exit(1)
  print "[*] Scraped %s events from Municipal Court records"%len(results)
  # write the results to file
  write_csv( results, args.CSVFILE)
  print "[*] YES!"

if __name__ == "__main__":
  main()
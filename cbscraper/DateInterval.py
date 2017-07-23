import datetime

month_dict = {
    #ITA
    "gen":1,
    "feb":2,
    "mar":3,
    "apr":4,
    "mag":5,
    "giu":6,
    "lug":7,
    "ago":8,
    "set":9,
    "ott":10,
    "nov":11,
    "dic":12,

    #ENG (partial)
    "jan":1,
    "feb":2,
    "mar":3,
    "apr":4,
    "may":5,
    "jun":6,
    "jul":7,
    "aug":8,
    "sep":9,
    "oct":10,
    "nov":11,
    "dec":12,

}

month_sub = {
    # ENG (full)
    "january": "jan",
    "february": "feb",
    "march": "mar",
    "april": "apr",
    "may": "may",
    "june": "jun",
    "july": "jul",
    "august": "aug",
    "september": "sep",
    "october": "oct",
    "november": "nov",
    "december": "dec",
}

def processDate(date):
    # print("ORIGINAL_DATE: "+date+" => ",end='')

    date = date.lower()
    now = datetime.datetime.now()

    #output variables
    day = ''
    month = ''
    year = ''

    # Get the first 3 letters
    first3 = date[0:3].lower()

    # Replace month full name with short name (e.g. september -> sep)
    for key, value in month_sub.items():
        date = date.replace(key, value)

    # Use first 3 letters
    if first3 in month_dict:

        if len(date) == 3:
            #we only have the month. We hp. current year
            day = 1
            month = int(month_dict[first3])
            year = now.year

        elif date[3] == " " and date[4].isnumeric() and "," not in date:
            # e.g. "dic 2014"
            day = 1
            month = int(month_dict[first3])
            year = int(date[3:].strip(" ,"))

        elif date[3] == " " and date[4].isnumeric() and "," in date:
            # e.g. "Jul 26, 2015"
            comma = date.find(",")
            day = int(date[4:comma])
            month = int(month_dict[first3])
            year = int(date[comma + 1:].strip(" ,"))

        elif date[3] == "," and date[4] == " ":
            # e.g. "Sep, 2013"
            day = 1
            month = int(month_dict[first3])
            year = int(date[3:].strip(" ,"))

        else:
            print("ERRORE: FORMATO DATA NON RICONOSCIUTO: " + date)
            exit()

    elif date == "presente" or date == "current" or date=="present":
        #day = now.day
        #month = now.month
        #year = now.year
        return "current"

    elif date.isnumeric():
        day = 1
        month = 1
        year = int(date)

    elif date == '' or date == "unknown":
        pass

    else:
        print("ERRORE: FORMATO DATA NON TROVATO: '" + date + "'")
        exit()

    if year == '':
        return ''
    else:
        # print("year="+str(year)+" month="+str(month)+" day="+str(day))
        return datetime.date(year, month, day)



# class DateInterval
class DateInterval(object):
    def __init__(self):
        return

    def fromText(self, date_text):
        date_text = date_text.strip('\n\t ')
        if (len(date_text) == 0):
            self.start = "Unknown"
            self.end = "Unknown"
            return
        date_text = date_text.split('-')
        self.start = date_text[0].strip()
        if (len(date_text) > 1):
            self.end = date_text[1].split(u"\u00A0")[0].strip()
        else:
            self.end = "Unknown"

    def getStart(self):
        return self.start

    def getEnd(self):
        return self.end

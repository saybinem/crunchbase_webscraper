import datetime
import logging

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
    "may":5,
    "jun":6,
    "jul":7,
    "aug":8,
    "sep":9,
    "oct":10,
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

    #ITA
    "gennaio": "jan",
    "febbraio": "feb",
    "marzo": "mar",
    "aprile": "apr",
    "maggio": "may",
    "giugno": "jun",
    "luglio": "jul",
    "agosto": "aug",
    "settembre": "sep",
    "ottobre": "oct",
    "novembre": "nov",
    "dicembre": "dec",

}

def processDate(date):
    """
    Gets a string and returns a datetime.time object
    :param date:
    :return:
    """
    # print("ORIGINAL_DATE: "+date+" => ",end='')

    date = date.lower()
    now = datetime.datetime.now()

    #output variables
    day = None
    month = None
    year = None

    # Get the first 3 letters
    first3 = date[0:3].lower()

    # Replace month full name with short name (e.g. september -> sep)
    for key, value in month_sub.items():
        date = date.replace(key, value)

    # Use first 3 letters
    if first3 in month_dict:

        if len(date) == 3:
            # We only have the month -> missing
            #day = 1
            #month = int(month_dict[first3])
            #year = now.year
            pass

        elif date[3] == " " and len(date)==6 and date[4:6].isnumeric() and ("," not in date):
            # e.g. 'aug 31'
            #       012345
            pass

        elif date[3] == " " and len(date)==8 and date[4:8].isnumeric() and ("," not in date):
            # e.g. "dic 2014"
            #       01234567
            day = 1
            month = int(month_dict[first3])
            year = int(date[3:])

        elif date[3] == " " and len(date)==12 and date[4:6].isnumeric() and date[6]=="," and date[7]==" " and date[8:12].isnumeric():
            # e.g. "Jul 26, 2015"
                   #0123456789
            comma = date.find(",")
            day = int(date[4:comma])
            month = int(month_dict[first3])
            year = int(date[comma + 1:])

        elif date[3] == " " and len(date)==11 and date[4].isnumeric() and (date[5] == ",") and date[6]==" " and date[7:11].isnumeric():
            # e.g. "nov 1, 2011"
                   #0123456789
            comma = date.find(",")
            day = int(date[4:comma])
            month = int(month_dict[first3])
            year = int(date[comma + 1:])

        elif date[3] == "," and len(date) == 9 and date[4] == " " and date[5:9].isnumeric():
            # e.g. "Sep, 2013"
            #       012345678
            day = 1
            month = int(month_dict[first3])
            year = int(date[5:])

        else:
            raise Exception("ERRORE: PRIME TRE LETTERE SONO UN MESE MA FORMATO DATA NON RICONOSCIUTO: " + date)

    elif date in ["presente", "current", "present"]:
        day = now.day
        month = now.month
        year = now.year
        #return "current"

    elif date.isnumeric() and len(date)==4:
        # We only have the year
        day = 1
        month = 1
        year = int(date)

    elif date.isnumeric() and len(date)==3:
        # We have a mistyped year
        if date[0:2]=='20':
            date_before = date
            date = date[0:2] + "0" + date[2]
            day = 1
            month = 1
            year = int(date)
            logging.info("Mistyped {} corrected into {}".format(date_before, date))
        else:
            raise Exception("Unrecognized mistyped year: {}".format(date))

    elif date in ['', "unknown"]:
        # missing date
        pass

    else:
        raise Exception("ERRORE: FORMATO DATA NON TROVATO: '" + date + "'")

    # RETURN
    if year is None:
        return None
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

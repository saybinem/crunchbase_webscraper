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

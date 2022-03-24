class Year:
    regex = r"([0-9]{4})"

    def to_python(self, value):
        return int(value)

    def to_url(self, year: int):
        return str(year)


class Week:
    regex = r"([0-9]|[1-4][0-9]|5[0-3])"

    def to_python(self, value):
        return int(value)

    def to_url(self, week: int):
        return str(week)

class Calculations:
    def radial_decay(self, distance, max_distance):
        if distance > max_distance:
            return 0
        return 1 - (distance / max_distance)


class Validations:
    def isInt(self, s):
        try:
            int(s)
            return True
        except ValueError:
            return False
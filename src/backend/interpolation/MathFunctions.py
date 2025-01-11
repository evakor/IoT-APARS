class Calculations:
    def radial_decay(distance, max_distance):
        if distance > max_distance:
            return 0
        return 1 - (distance / max_distance)


class Validations:
    def isInt(s):
        try:
            int(s)
            return True
        except ValueError:
            return False
        
    def isFloat(s):
        try:
            float(s)
            return True
        except ValueError:
            return False
        
    def isNumeric(s):
        try:
            int(s)
            return True
        except Exception:
            return False
class Calculations:
    def radial_decay(self, distance: int, max_distance: int) -> float:
        if distance > max_distance:
            return 0.0
        return 1 - (distance / max_distance)


class Validations:
    def isInt(self, s: any) -> bool:
        try:
            int(s)
            return True
        except ValueError:
            return False
    
    def isFloat(self, s: any) -> bool:
        try:
            float(s)
            return True
        except ValueError:
            return False
    
    def isNumeric(self, s: any) -> bool:
        try:
            int(s)
            return True
        except Exception:
            return False
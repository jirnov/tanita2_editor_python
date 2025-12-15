import Tanita2

class Point(Tanita2.Point):
        def distance(self, point1, point2):
            return Tanita2.Point.distance(point1, point2)

        def bezier(self, points, k):
            return Tanita2.Point.bezier(self, points, k)

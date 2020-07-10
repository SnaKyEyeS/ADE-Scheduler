from itertools import product, chain, starmap, repeat
from collections import deque
from backend.events import EventOTHER, AcademicalEvent
from heapq import nsmallest
import operator
from typing import Iterable
from backend.courses import Course, merge_courses, View


class Schedule(Course):
    """
    A schedule is essentially a combination of courses stored as a master course, from which some events can be removed.

    :param courses: one or multiple courses
    :type courses: Iterable[Course]
    """
    def __init__(self, courses: Iterable[Course]):
        self.master_course = merge_courses(courses, name='schedule')

    def add_course(self, course: Course) -> None:
        """
        Adds a course to the schedule.

        :param course: the course to be added
        :type course: Course
        """
        self.master_course = merge_courses((self.master_course, course))

    def remove_course(self, course_code: str) -> None:
        """
        Removes a course from the schedule.

        :param course_code: the code of the course to be removed
        :type course_code: str
        """
        self.master_course.activities.drop(index=course_code, inplace=True)

    def update_course(self, course: Course) -> None:
        """
        Updates a course to the schedule.

        :param course: the course to be updated
        :type course: Course
        """
        self.remove_course(course_code=course.code)
        self.add_course(course)

    def get_events(self, view: View = None) -> Iterable[AcademicalEvent]:
        """
        Extracts all the events matching ids in the view list.
        :param view: if None extracts everything, otherwise must be a list of ids
        :return: the array of events
        """
        return self.master_course.get_events(view)

    def compute_best(self, fts=None, n_best=5, safe_compute=True, view=None):
        """
        Computes best schedules trying to minimize conflicts selecting, for each type of event, one event.
        :param fts: a list of event.CustomEvent objects
        :param n_best: number of best schedules to produce
        :param safe_compute: if True, ignore all redundant events at same time period
        :param view: list of ids to filter
        :return: the n_best schedules
        """
        df = self.activities

        if view is not None:
            valid = df.index.isin(values=view, level='id')
            df = df[valid]

        # We only take care of events which are not of type EvenOTHER
        valid = df.index.get_level_values('type') != EventOTHER
        df_main, df_other = df[valid], df[~valid]
        best = [[] for i in range(n_best)]  # We create an empty list which will contain best schedules

        for _, week_data in df_main.groupby('week'):
            if safe_compute:  # We remove events from same course that happen at the same time
                for _, data in week_data.groupby(level=['code', 'type']):
                    tmp = deque()  # Better for appending
                    # For each event in a given course, for a given type...
                    for index, row in data.iterrows():
                        e = row['event']
                        r = repeat(e)
                        # If that event overlaps with any of the events in tmp
                        if any(starmap(operator.xor, zip(tmp, r))):
                            week_data.drop(index=index, inplace=True, errors='ignore')
                        else:
                            # We append to left because last event is most likely to conflict (if sorted)
                            tmp.appendleft(e)

            events = [[data_id.values for _, data_id in data.groupby(level='id')]
                      for _, data in week_data.groupby(level=['code', 'type'])['event']]
            permutations = product(*events)

            if n_best == 1:
                best.extend(chain.from_iterable(min(permutations, key=lambda f: evaluate_week(f, fts))))
            else:
                temp = nsmallest(n_best, permutations, key=lambda f: evaluate_week(f, fts))
                n_temp = len(temp)
                for i in range(n_temp):
                    best[i].extend(chain.from_iterable(temp[i]))
                # If we could only find n_temp < n_best best scores, we fill the rest in with same values
                for j in range(n_temp, n_best):
                    best[j].extend(chain.from_iterable(temp[-1]))

        other = df_other['event'].values.flatten().tolist()
        if other:
            [schedule.extend(other) for schedule in best]
            return best
        else:
            return best


def evaluate_week(week: Iterable[AcademicalEvent], fts: Iterable[AcademicalEvent] = None) -> float:
    """
    Evaluates the how much a given week contains conflicts.
    :param week: an iterable of event.CustomEvent objects
    :param fts: a list of event.CustomEvent objects
    :return: the sum of all the conflicts
    """
    week = sorted(chain.from_iterable(week))  # We sort all the events

    if fts is not None:
        week = sorted(week + fts)  # We additionally sort the fts, within the week
    return sum(starmap(operator.mul, zip(week[:-1], week[1:])))  # We sum all the overlaps